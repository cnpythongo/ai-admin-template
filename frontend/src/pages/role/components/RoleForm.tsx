import { useEffect } from 'react';
import { Form, Input, Modal, Switch } from 'antd';
import type { Role, RoleCreateParams } from '@/types/role';

interface RoleFormProps {
  open: boolean;
  editingRole: Role | null;
  onCancel: () => void;
  onConfirm: (values: RoleCreateParams) => Promise<void>;
  confirmLoading: boolean;
}

export default function RoleForm({
  open,
  editingRole,
  onCancel,
  onConfirm,
  confirmLoading,
}: RoleFormProps) {
  const [form] = Form.useForm();

  useEffect(() => {
    if (open) {
      if (editingRole) {
        form.setFieldsValue({
          name: editingRole.name,
          code: editingRole.code,
          status: editingRole.status,
          remark: editingRole.remark,
        });
      } else {
        form.resetFields();
      }
    }
  }, [open, editingRole, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      await onConfirm(values);
    } catch {
      // Validation failed, form will show error messages
    }
  };

  const handleCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Auto-lowercase, no spaces
    const val = e.target.value.toLowerCase().replace(/\s/g, '');
    form.setFieldsValue({ code: val });
  };

  return (
    <Modal
      title={editingRole ? '编辑角色' : '新增角色'}
      open={open}
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={confirmLoading}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ status: true }}
      >
        <Form.Item
          name="name"
          label="角色名称"
          rules={[{ required: true, message: '请输入角色名称' }]}
        >
          <Input placeholder="请输入角色名称" maxLength={128} />
        </Form.Item>

        <Form.Item
          name="code"
          label="角色编码"
          rules={[
            { required: true, message: '请输入角色编码' },
            {
              pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/,
              message: '编码必须以字母开头，只允许字母、数字和下划线',
            },
          ]}
        >
          <Input
            placeholder="请输入角色编码"
            maxLength={128}
            disabled={!!editingRole}
            onChange={handleCodeChange}
          />
        </Form.Item>

        <Form.Item name="status" label="状态" valuePropName="checked">
          <Switch checkedChildren="启用" unCheckedChildren="禁用" />
        </Form.Item>

        <Form.Item name="remark" label="备注">
          <Input.TextArea placeholder="请输入备注" maxLength={500} rows={4} />
        </Form.Item>
      </Form>
    </Modal>
  );
}
