import { useEffect, useMemo } from 'react';
import { Form, Input, InputNumber, Modal, Radio, Select, Switch, TreeSelect } from 'antd';
import type { Permission } from '@/types';
import type { CreatePermissionParams, UpdatePermissionParams } from '@/services/permission';

const API_METHODS = ['GET', 'POST', 'PUT', 'DELETE'];

interface PermissionFormProps {
  open: boolean;
  editingPermission: Permission | null;
  permissionTree: Permission[];
  onCancel: () => void;
  onConfirm: (values: CreatePermissionParams | UpdatePermissionParams) => Promise<void>;
  confirmLoading: boolean;
}

function flattenTree(
  nodes: Permission[],
  excludeId?: number,
): { title: string; value: string; disabled: boolean }[] {
  const result: { title: string; value: string; disabled: boolean }[] = [];
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

export default function PermissionForm({
  open,
  editingPermission,
  permissionTree,
  onCancel,
  onConfirm,
  confirmLoading,
}: PermissionFormProps) {
  const [form] = Form.useForm();
  const typeValue = Form.useWatch('type', form);

  const treeData = useMemo(() => {
    const excludeId = editingPermission?.id;
    const flat = flattenTree(permissionTree, excludeId);
    const rootNode = { title: '顶级权限', value: '', disabled: false };
    return [rootNode, ...flat];
  }, [permissionTree, editingPermission]);

  useEffect(() => {
    if (open) {
      if (editingPermission) {
        form.setFieldsValue({
          name: editingPermission.name,
          code: editingPermission.code,
          type: editingPermission.type,
          parent_id: editingPermission.parent_id !== null ? String(editingPermission.parent_id) : '',
          api_path: editingPermission.api_path,
          api_method: editingPermission.api_method,
          sort_order: editingPermission.sort_order,
          status: editingPermission.status,
          remark: editingPermission.remark,
        });
      } else {
        form.resetFields();
      }
    }
  }, [open, editingPermission, form]);

  const handleOk = async () => {
    try {
      const raw = await form.validateFields();
      const values = {
        ...raw,
        parent_id: raw.parent_id !== '' ? Number(raw.parent_id) : null,
      };
      await onConfirm(values);
    } catch {
      // Validation failed, form will show error messages
    }
  };

  const isEditing = !!editingPermission;

  return (
    <Modal
      title={isEditing ? '编辑权限' : '新增权限'}
      open={open}
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={confirmLoading}
      destroyOnClose
      width={560}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ sort_order: 0, status: true, type: 'menu' }}
      >
        <Form.Item
          name="type"
          label="权限类型"
          rules={[{ required: true, message: '请选择权限类型' }]}
        >
          <Radio.Group disabled={isEditing}>
            <Radio.Button value="menu">菜单</Radio.Button>
            <Radio.Button value="button">按钮</Radio.Button>
            <Radio.Button value="api">API</Radio.Button>
          </Radio.Group>
        </Form.Item>

        <Form.Item
          name="name"
          label="权限名称"
          rules={[{ required: true, message: '请输入权限名称' }]}
        >
          <Input placeholder="请输入权限名称" maxLength={128} />
        </Form.Item>

        <Form.Item
          name="code"
          label="权限编码"
          rules={[
            { required: true, message: '请输入权限编码' },
            {
              pattern: /^[a-z]+:[a-z]+(:[a-z]+)?$/,
              message: '编码格式必须为 module:sub:action（小写字母）',
            },
          ]}
          normalize={(value: string) =>
            value
              .toLowerCase()
              .replace(/[\u4e00-\u9fa5\s]/g, '')
          }
        >
          <Input
            placeholder="格式: system:user:create"
            maxLength={128}
            disabled={isEditing}
          />
        </Form.Item>

        <Form.Item name="parent_id" label="上级权限">
          <TreeSelect
            treeData={treeData}
            placeholder="请选择上级权限"
            allowClear
            treeDefaultExpandAll
          />
        </Form.Item>

        {typeValue === 'api' && (
          <>
            <Form.Item
              name="api_path"
              label="API路径"
              rules={[{ required: true, message: '请输入API路径' }]}
            >
              <Input placeholder="示例: /api/v1/users" maxLength={255} />
            </Form.Item>

            <Form.Item
              name="api_method"
              label="HTTP方法"
              rules={[{ required: true, message: '请选择HTTP方法' }]}
            >
              <Select placeholder="请选择HTTP方法">
                {API_METHODS.map((method) => (
                  <Select.Option key={method} value={method}>
                    {method}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </>
        )}

        <Form.Item name="sort_order" label="排序">
          <InputNumber min={0} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item name="status" label="状态" valuePropName="checked">
          <Switch checkedChildren="启用" unCheckedChildren="禁用" />
        </Form.Item>

        <Form.Item name="remark" label="备注">
          <Input.TextArea rows={3} maxLength={500} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
