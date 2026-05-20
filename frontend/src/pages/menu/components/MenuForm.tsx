import { useEffect, useMemo, useState } from 'react';
import {
  Form,
  Input,
  InputNumber,
  Modal,
  Switch,
  TreeSelect,
} from 'antd';
import type { Menu, Permission } from '@/types';
import type { MenuCreateParams, MenuUpdateParams } from '@/types/menu';
import IconPicker from '@/components/IconPicker';
import { getPermissionTree } from '@/services/permission';

interface MenuFormProps {
  open: boolean;
  editingMenu: Menu | null;
  menuTree: Menu[];
  onCancel: () => void;
  onConfirm: (
    values: MenuCreateParams | MenuUpdateParams,
  ) => Promise<void>;
  confirmLoading: boolean;
}

function flattenTree(
  nodes: Menu[],
  excludeId?: number,
): { title: string; value: string; disabled: boolean }[] {
  const result: {
    title: string;
    value: string;
    disabled: boolean;
  }[] = [];
  for (const node of nodes) {
    const disabled = node.id === excludeId;
    result.push({
      title: node.name,
      value: String(node.id),
      disabled,
    });
    if (node.children && node.children.length > 0) {
      const children = flattenTree(node.children, excludeId);
      result.push(...children);
    }
  }
  return result;
}

function flattenPermissionTree(
  nodes: Permission[],
): { title: string; value: string; key: string }[] {
  const result: { title: string; value: string; key: string }[] = [];
  for (const node of nodes) {
    result.push({
      title: `${node.name} (${node.code})`,
      value: String(node.id),
      key: String(node.id),
    });
    if (node.children && node.children.length > 0) {
      const children = flattenPermissionTree(node.children);
      result.push(...children);
    }
  }
  return result;
}

export default function MenuForm({
  open,
  editingMenu,
  menuTree,
  onCancel,
  onConfirm,
  confirmLoading,
}: MenuFormProps) {
  const [form] = Form.useForm();
  const isExternalLink = Form.useWatch('is_external_link', form);
  const [permissionTree, setPermissionTree] = useState<Permission[]>([]);
  const [permLoading, setPermLoading] = useState(false);

  // Fetch permission tree on mount
  useEffect(() => {
    if (open) {
      setPermLoading(true);
      getPermissionTree()
        .then((res) => {
          if (res.code === 0) {
            setPermissionTree(res.data);
          }
        })
        .catch(() => {
          // Silently fail - permission selector will just be empty
        })
        .finally(() => {
          setPermLoading(false);
        });
    }
  }, [open]);

  const treeData = useMemo(() => {
    const excludeId = editingMenu?.id;
    const flat = flattenTree(menuTree, excludeId);
    const rootNode = {
      title: '顶级菜单',
      value: '',
      disabled: false,
    };
    return [rootNode, ...flat];
  }, [menuTree, editingMenu]);

  const permTreeData = useMemo(() => {
    return flattenPermissionTree(permissionTree);
  }, [permissionTree]);

  useEffect(() => {
    if (open) {
      if (editingMenu) {
        form.setFieldsValue({
          name: editingMenu.name,
          icon: editingMenu.icon,
          route_path: editingMenu.route_path,
          component: editingMenu.component,
          parent_id:
            editingMenu.parent_id !== null
              ? String(editingMenu.parent_id)
              : '',
          sort_order: editingMenu.sort_order,
          hidden: editingMenu.hidden,
          is_external_link: editingMenu.is_external_link,
          permission_ids: editingMenu.permission_ids.map(String),
        });
      } else {
        form.resetFields();
      }
    }
  }, [open, editingMenu, form]);

  const handleOk = async () => {
    try {
      const raw = await form.validateFields();
      const values: Record<string, unknown> = {
        ...raw,
        parent_id: raw.parent_id !== '' ? Number(raw.parent_id) : null,
        permission_ids: (raw.permission_ids ?? []).map(Number),
        icon: raw.icon || null,
        component: raw.component || null,
      };
      await onConfirm(values as MenuCreateParams | MenuUpdateParams);
    } catch {
      // Validation failed, form will show error messages
    }
  };

  const isEditing = !!editingMenu;

  return (
    <Modal
      title={isEditing ? '编辑菜单' : '新增菜单'}
      open={open}
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={confirmLoading}
      destroyOnClose
      width={640}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          sort_order: 0,
          hidden: false,
          is_external_link: false,
          permission_ids: [],
        }}
      >
        <Form.Item
          name="name"
          label="菜单名称"
          rules={[{ required: true, message: '请输入菜单名称' }]}
        >
          <Input placeholder="请输入菜单名称" maxLength={128} />
        </Form.Item>

        <Form.Item name="icon" label="图标">
          <IconPicker placeholder="请选择图标" />
        </Form.Item>

        <Form.Item
          name="route_path"
          label="路由路径"
          rules={[{ required: true, message: '请输入路由路径' }]}
        >
          <Input placeholder="示例: /system/user" maxLength={255} />
        </Form.Item>

        {!isExternalLink && (
          <Form.Item name="component" label="组件路径">
            <Input
              placeholder="示例: system/user/index"
              maxLength={255}
            />
          </Form.Item>
        )}

        <Form.Item name="parent_id" label="上级菜单">
          <TreeSelect
            treeData={treeData}
            placeholder="请选择上级菜单"
            allowClear
            treeDefaultExpandAll
          />
        </Form.Item>

        <Form.Item name="sort_order" label="排序">
          <InputNumber min={0} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="hidden"
          label="隐藏"
          valuePropName="checked"
          tooltip="开启后在侧边栏隐藏，但路由仍然存在"
        >
          <Switch checkedChildren="隐藏" unCheckedChildren="显示" />
        </Form.Item>

        <Form.Item
          name="is_external_link"
          label="外链"
          valuePropName="checked"
          tooltip="开启后该菜单将作为外部链接打开"
        >
          <Switch
            checkedChildren="外链"
            unCheckedChildren="内链"
          />
        </Form.Item>

        <Form.Item
          name="permission_ids"
          label="关联权限"
          tooltip="选择与此菜单关联的权限标识"
        >
          <TreeSelect
            treeData={permTreeData}
            placeholder="请选择关联权限"
            multiple
            allowClear
            treeDefaultExpandAll
            loading={permLoading}
            style={{ width: '100%' }}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
