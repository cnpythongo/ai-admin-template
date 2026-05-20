import { useCallback, useEffect, useState } from 'react';
import { message, Modal, Spin, Tree } from 'antd';
import type { DataNode } from 'antd/es/tree';
import type { Key } from 'react';
import type { Role } from '@/types/role';
import { assignPermissions, getRolePermissionIds } from '@/services/role';
import { getPermissionTree } from '@/services/permission';
import type { Permission } from '@/types';

function buildTreeData(permissions: Permission[]): DataNode[] {
  return permissions.map((perm) => ({
    key: perm.id,
    title: `${perm.name} (${perm.code})`,
    children: perm.children ? buildTreeData(perm.children) : [],
  }));
}

interface PermissionTreeProps {
  open: boolean;
  role: Role | null;
  onCancel: () => void;
}

export default function PermissionTree({
  open,
  role,
  onCancel,
}: PermissionTreeProps) {
  const [treeData, setTreeData] = useState<DataNode[]>([]);
  const [checkedKeys, setCheckedKeys] = useState<Key[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const fetchData = useCallback(async () => {
    if (!open || !role) return;

    setLoading(true);
    try {
      // Fetch permission tree
      const permRes = await getPermissionTree();
      if (permRes.code !== 0) {
        message.error(permRes.message || '获取权限树失败');
        return;
      }
      const tree = buildTreeData(permRes.data);
      setTreeData(tree);

      // Fetch current role permission IDs for pre-checking
      const permIdsRes = await getRolePermissionIds(role.id);
      if (permIdsRes.code === 0) {
        setCheckedKeys(permIdsRes.data.permission_ids);
      }
    } catch {
      message.error('获取权限数据失败');
    } finally {
      setLoading(false);
    }
  }, [open, role]);

  useEffect(() => {
    if (open) {
      fetchData();
    }
  }, [open, fetchData]);

  const handleOk = async () => {
    if (!role) return;

    setSubmitting(true);
    try {
      const res = await assignPermissions(role.id, {
        permission_ids: checkedKeys as number[],
      });
      if (res.code === 0) {
        message.success('权限分配成功');
        onCancel();
      } else {
        message.error(res.message || '权限分配失败');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      message.error(error?.response?.data?.message || '权限分配失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCheck = (
    checked: Key[] | { checked: Key[]; halfChecked: Key[] },
  ) => {
    const keys = Array.isArray(checked) ? checked : checked.checked;
    setCheckedKeys(keys);
  };

  return (
    <Modal
      title={`分配权限 - ${role?.name ?? ''}`}
      open={open}
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={submitting}
      width={600}
      destroyOnClose
    >
      <Spin spinning={loading}>
        {treeData.length > 0 ? (
          <Tree
            checkable
            defaultExpandAll
            treeData={treeData}
            checkedKeys={checkedKeys}
            onCheck={handleCheck}
            checkStrictly={false}
          />
        ) : (
          !loading && <div style={{ textAlign: 'center', padding: 24 }}>暂无权限数据</div>
        )}
      </Spin>
    </Modal>
  );
}
