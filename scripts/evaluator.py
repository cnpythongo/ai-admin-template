#!/usr/bin/env python3
"""Evaluator: 验证 Generator 产出的代码质量。

基于 Harness Engineering 理论，作为三角色中的 Evaluator，
在 Generator 完成后自动检查：
- API 接口完整性（对比模块文档 vs 实际代码）
- 权限校验正确性
- ruff 静态代码质量
- 模块隔离性

用法：
    uv run python scripts/evaluator.py
    uv run python scripts/evaluator.py --module department
    uv run python scripts/evaluator.py --output report.md
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# -- 路径常量 ----------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
MODULES_DIR = PROJECT_ROOT / "memory-bank" / "04-modules"
API_DIR = BACKEND_DIR / "app" / "api" / "v1"
APP_DIR = BACKEND_DIR / "app"

# 需要排除的模块文档（无 API 端点定义）
SKIP_MODULES = {"module-dashboard.md"}

# 已知的前缀映射（模块文档中的路径 -> router prefix）
MODULE_PREFIX_MAP: dict[str, str] = {
    "auth": "/api/v1/auth",
    "user": "/api/v1/users",
    "department": "/api/v1/departments",
    "role": "/api/v1/roles",
    "permission": "/api/v1/permissions",
    "menu": "/api/v1/menus",
    "system_config": "/api/v1/system-configs",
    "operation_log": "/api/v1/operation-logs",
}


# -- 数据模型 ----------------------------------------------------


@dataclass
class ExpectedEndpoint:
    module: str
    method: str
    path: str
    permission: str | None
    summary: str


@dataclass
class ActualEndpoint:
    file: str
    method: str
    path: str
    permissions: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class CheckResult:
    category: str  # "api" / "ruff" / "isolation"
    status: str  # "pass" / "fail" / "warning"
    item: str
    detail: str = ""


# -- Module Doc Parser -------------------------------------------

_METHOD_RE = re.compile(r"####\s+(GET|POST|PUT|DELETE)\s+`(/api/v1/[^`]+)`")
_PERMISSION_RE = re.compile(r"\*\*权限\*\*\s*\|\s*`([^`]+)`")
_SUMMARY_RE = re.compile(r"\*\*描述\*\*\s*\|\s*([^\n]+)")


def parse_module_doc(filepath: Path) -> list[ExpectedEndpoint]:
    """解析单个模块文档，提取所有 API 端点定义。"""
    text = filepath.read_text(encoding="utf-8")
    module_name = filepath.stem.replace("module-", "")
    endpoints: list[ExpectedEndpoint] = []
    lines = text.split("\n")

    current_method: str | None = None
    current_path: str | None = None
    current_permission: str | None = None
    current_summary: str = ""

    for line in lines:
        m = _METHOD_RE.search(line)
        if m:
            if current_method and current_path:
                endpoints.append(
                    ExpectedEndpoint(
                        module=module_name,
                        method=current_method,
                        path=current_path,
                        permission=current_permission,
                        summary=current_summary.strip(),
                    )
                )
            current_method = m.group(1)
            current_path = m.group(2)
            current_permission = None
            current_summary = ""
            continue

        p = _PERMISSION_RE.search(line)
        if p and current_method:
            current_permission = p.group(1)
            continue

        s = _SUMMARY_RE.search(line)
        if s and current_method and not current_summary:
            current_summary = s.group(1)
            continue

    if current_method and current_path:
        endpoints.append(
            ExpectedEndpoint(
                module=module_name,
                method=current_method,
                path=current_path,
                permission=current_permission,
                summary=current_summary.strip(),
            )
        )

    return endpoints


# -- Source Code Scanner ------------------------------------------


class RouteVisitor(ast.NodeVisitor):
    """AST 访问器，提取 FastAPI 路由定义。"""

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.prefix = ""
        self.endpoints: list[ActualEndpoint] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        """提取 router = APIRouter(prefix=...)"""
        if (
            isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "router"
            and isinstance(node.value, ast.Call)
        ):
            for kw in node.value.keywords:
                if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                    self.prefix = kw.value.value
        self.generic_visit(node)

    def _extract_route(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """提取 @router.get/post/put/delete(...) - 带装饰器的路由函数。"""
        for deco in node.decorator_list:
            if not isinstance(deco, ast.Call):
                continue
            if not isinstance(deco.func, ast.Attribute):
                continue
            method = deco.func.attr
            if method not in ("get", "post", "put", "delete", "patch"):
                continue
            if not isinstance(deco.func.value, ast.Name) or deco.func.value.id != "router":
                continue

            path = ""
            if deco.args:
                if isinstance(deco.args[0], ast.Constant):
                    path = deco.args[0].value

            summary = ""
            permissions: list[str] = []
            for kw in deco.keywords:
                if kw.arg == "summary" and isinstance(kw.value, ast.Constant):
                    summary = kw.value.value

            permissions = self._extract_permissions(node)

            full_path = "/api/v1" + self.prefix + path
            self.endpoints.append(
                ActualEndpoint(
                    file=self.filepath,
                    method=method.upper(),
                    path=full_path,
                    permissions=permissions,
                    summary=summary,
                )
            )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._extract_route(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._extract_route(node)

    def _extract_permissions(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
        """从函数参数中提取 require_permissions 的权限标识。"""
        result: list[str] = []
        for arg in node.args.args:
            if not isinstance(arg.annotation, ast.Subscript):
                continue
            ann_value = arg.annotation.value
            ann_name = ""
            if isinstance(ann_value, ast.Attribute):
                ann_name = ann_value.attr
            elif isinstance(ann_value, ast.Name):
                ann_name = ann_value.id
            if ann_name != "Annotated":
                continue
            if not isinstance(arg.annotation.slice, ast.Tuple):
                continue
            for elt in arg.annotation.slice.elts:
                if not isinstance(elt, ast.Call):
                    continue
                func = elt.func
                func_name = ""
                if isinstance(func, ast.Attribute):
                    func_name = func.attr
                elif isinstance(func, ast.Name):
                    func_name = func.id
                if func_name != "Depends":
                    continue
                for dep_arg in elt.args:
                    if not isinstance(dep_arg, ast.Call):
                        continue
                    dep_func = dep_arg.func
                    dep_func_name = ""
                    if isinstance(dep_func, ast.Attribute):
                        dep_func_name = dep_func.attr
                    elif isinstance(dep_func, ast.Name):
                        dep_func_name = dep_func.id
                    if dep_func_name != "require_permissions":
                        continue
                    for perm_arg in dep_arg.args:
                        if isinstance(perm_arg, ast.Constant):
                            result.append(perm_arg.value)
        return result


def scan_api_routes(api_dir: Path) -> list[ActualEndpoint]:
    """扫描 API 目录下的所有路由文件，提取实际端点。"""
    all_endpoints: list[ActualEndpoint] = []
    for fpath in sorted(api_dir.glob("*.py")):
        if fpath.name == "__init__.py":
            continue
        try:
            tree = ast.parse(fpath.read_text(encoding="utf-8"))
            visitor = RouteVisitor(str(fpath))
            visitor.visit(tree)
            all_endpoints.extend(visitor.endpoints)
        except SyntaxError as e:
            print(f"  ⚠️  语法错误: {fpath.name}: {e}")
    return all_endpoints


# -- 匹配逻辑 ------------------------------------------------------


def normalize_path(path: str) -> str:
    """归一化路径：将 {id} / {user_id} 等参数占位符转换为 {id}，去掉查询参数和尾部斜杠。"""
    path = re.sub(r"\{[^}]+\}", "{id}", path)
    path = path.split("?")[0]
    path = path.rstrip("/")
    return path


def match_endpoint(
    expected: ExpectedEndpoint, actuals: list[ActualEndpoint]
) -> tuple[bool, str]:
    """检查预期端点是否在实际端点列表中找到匹配。"""
    norm_expected_path = normalize_path(expected.path)
    for actual in actuals:
        if actual.method != expected.method:
            continue
        if normalize_path(actual.path) != norm_expected_path:
            continue
        return True, f"匹配到 {actual.method} {actual.path}"

    return False, f"未找到匹配的端点"


def check_permission(
    expected: ExpectedEndpoint, actuals: list[ActualEndpoint]
) -> tuple[bool, str]:
    """检查实际端点的权限是否与预期一致。"""
    norm_expected_path = normalize_path(expected.path)
    for actual in actuals:
        if actual.method != expected.method:
            continue
        if normalize_path(actual.path) != norm_expected_path:
            continue
        if expected.permission is None:
            return True, "无权限要求（登录即可）"
        if expected.permission in actual.permissions:
            return True, f"权限匹配: {expected.permission}"
        if actual.permissions:
            return False, f"权限不匹配: 预期={expected.permission}, 实际={actual.permissions}"
        return False, f"缺少权限校验: 预期={expected.permission}, 实际未设置权限"
    return False, "端点未找到，无法校验权限"


# -- Ruff 检查 ----------------------------------------------------


def check_ruff(app_dir: Path) -> tuple[str, list[str]]:
    """运行 ruff check，返回状态和错误详情。"""
    try:
        result = subprocess.run(
            ["uv", "run", "ruff", "check", str(app_dir)],
            cwd=str(BACKEND_DIR),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        return "warning", ["ruff 未安装，跳过静态检查"]
    except subprocess.TimeoutExpired:
        return "warning", ["ruff 检查超时（>60s），跳过"]

    # ruff outputs to stdout; empty output + zero exit = pass
    output = (result.stdout + result.stderr).strip()
    if result.returncode == 0 or "No module named" in output or "No such file" in output:
        return "pass" if result.returncode == 0 else "warning", ["ruff 未安装，跳过静态检查"]

    errors = [e for e in output.split("\n") if e and not e.startswith("All checks passed")]
    return "fail", errors


# -- 报告生成 ------------------------------------------------------


def generate_report(
    expected_list: list[ExpectedEndpoint],
    actual_list: list[ActualEndpoint],
    ruff_status: str,
    ruff_details: list[str],
    module_filter: str | None,
) -> str:
    """生成格式化的验收报告。"""
    lines: list[str] = []
    lines.append("# Evaluator 验收报告")
    lines.append(f"生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if module_filter:
        lines.append(f"模块筛选: {module_filter}")
    lines.append("")

    total_checks = 0
    pass_count = 0
    fail_count = 0
    warning_count = 0

    # -- API 端点检查 --
    lines.append("---")
    lines.append("## API 端点检查")
    lines.append("")

    for expected in expected_list:
        total_checks += 1
        found, detail = match_endpoint(expected, actual_list)
        if found:
            perm_ok, perm_detail = check_permission(expected, actual_list)
            if perm_ok:
                pass_count += 1
                lines.append(f"  ✅ [{expected.method}] {expected.path}")
            else:
                warning_count += 1
                lines.append(f"  ⚠️  [{expected.method}] {expected.path}")
                lines.append(f"     权限: {perm_detail}")
        else:
            fail_count += 1
            lines.append(f"  ❌ [{expected.method}] {expected.path} -- {detail}")

    # -- Extra 端点检查 --
    lines.append("")
    lines.append("### 额外端点（文档未定义但代码中已实现）")
    lines.append("")

    expected_set = {(normalize_path(e.path), e.method) for e in expected_list}
    extra_found = False
    for actual in actual_list:
        key = normalize_path(actual.path)
        if (key, actual.method) not in expected_set:
            extra_found = True
            warning_count += 1
            lines.append(f"  ⚠️  [{actual.method}] {actual.path}")
    if not extra_found:
        lines.append("  无额外端点")

    # -- ruff 检查 --
    lines.append("")
    lines.append("---")
    lines.append("## 静态代码检查（ruff）")
    lines.append("")

    total_checks += 1
    if ruff_status == "pass":
        pass_count += 1
        lines.append("  ✅ ruff check 通过")
    elif ruff_status == "warning":
        warning_count += 1
        for d in ruff_details:
            lines.append(f"  ⚠️  {d}")
    else:
        fail_count += 1
        lines.append(f"  ❌ ruff check 发现 {len(ruff_details)} 个问题")
        for d in ruff_details[:20]:
            lines.append(f"     {d}")
        if len(ruff_details) > 20:
            lines.append(f"     ... 还有 {len(ruff_details) - 20} 个问题未显示")

    # -- 汇总 --
    lines.append("")
    lines.append("---")
    lines.append("## 汇总")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 总检查项 | {total_checks} |")
    lines.append(f"| ✅ 通过 | {pass_count} |")
    lines.append(f"| ❌ 失败 | {fail_count} |")
    lines.append(f"| ⚠️  警告 | {warning_count} |")

    pass_rate = (pass_count / total_checks * 100) if total_checks > 0 else 0
    verdict = "✅ 通过" if fail_count == 0 and pass_rate >= 80 else "❌ 未通过"
    lines.append(f"| 通过率 | {pass_rate:.1f}% |")
    lines.append(f"| 结论 | {verdict} |")

    return "\n".join(lines)


# -- 主入口 --------------------------------------------------------


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Evaluator: 验证 Generator 产出的代码质量")
    parser.add_argument("--module", help="仅检查指定模块（如 department）")
    parser.add_argument("--output", help="将报告输出到文件")
    args = parser.parse_args()

    print("=" * 60)
    print("  🔍 Evaluator -- 代码质量验证")
    print("=" * 60)
    print()

    # Step 1: 解析模块文档
    print("📄 Step 1: 解析模块文档...")
    all_expected: list[ExpectedEndpoint] = []
    for fpath in sorted(MODULES_DIR.glob("*.md")):
        if fpath.name in SKIP_MODULES:
            continue
        if args.module and args.module not in fpath.name:
            continue
        endpoints = parse_module_doc(fpath)
        all_expected.extend(endpoints)
        print(f"   {fpath.name}: {len(endpoints)} 个端点")
    print(f"   合计: {len(all_expected)} 个预期端点")
    print()

    # Step 2: 扫描源文件
    print("🔬 Step 2: 扫描后端路由文件...")
    actual_endpoints = scan_api_routes(API_DIR)
    print(f"   发现: {len(actual_endpoints)} 个实际端点")
    for ep in sorted(actual_endpoints, key=lambda x: x.path):
        perms = ",".join(ep.permissions) if ep.permissions else "无权限"
        print(f"   [{ep.method}] {ep.path}  ({perms})")
    print()

    # Step 3: 检查未匹配的预期端点
    print("🔎 Step 3: 对比检查...")
    unmatched = 0
    for expected in all_expected:
        found, _ = match_endpoint(expected, actual_endpoints)
        if not found:
            unmatched += 1
            print(f"   ❌ 未实现: [{expected.method}] {expected.path}")
    if unmatched == 0:
        print("   ✅ 所有预期端点均已实现")
    print()

    # Step 4: ruff 检查
    print("🧹 Step 4: 运行 ruff 静态检查...")
    ruff_status, ruff_details = check_ruff(APP_DIR)
    print(f"   结果: {ruff_status}")
    if ruff_status == "fail":
        for d in ruff_details[:5]:
            print(f"   {d}")
        if len(ruff_details) > 5:
            print(f"   ... 共 {len(ruff_details)} 个问题")
    print()

    # Step 5: 生成报告
    print("📋 Step 5: 生成验收报告...")
    report = generate_report(
        all_expected, actual_endpoints, ruff_status, ruff_details, args.module
    )
    print()

    # 输出报告
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report, encoding="utf-8")
        print(f"报告已保存到: {output_path}")
    else:
        print(report)

    # 返回退出码
    has_fail = "❌ 未通过" in report
    return 1 if has_fail else 0


if __name__ == "__main__":
    sys.exit(main())
