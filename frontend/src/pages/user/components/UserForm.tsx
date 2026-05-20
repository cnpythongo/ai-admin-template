import { useEffect } from 'react';
import { Form, Input, Modal, Select, TreeSelect } from 'antd';
import type { User, UserCreateParams } from '@/types/user';
import type { Department } from '@/types/department';
import type { Role } from '@/types/role';

interface UserFormProps {
  open: boolean;
  editingUser: User | null;
  departmentTree: Department[];
  roleOptions: Role[];
  onCancel: () => void;
  onConfirm: (values: UserCreateParams) => Promise<void>;
  confirmLoading: boolean;
}

export default function UserForm({
  open,
  editingUser,
  departmentTree,
  roleOptions,
  onCancel,
  onConfirm,
  confirmLoading,
}: UserFormProps) {
  const [form] = Form.useForm();

  useEffect(() => {
    if (open) {
      if (editingUser) {
        form.setFieldsValue({
          nickname: editingUser.nickname,
          email: editingUser.email,
          phone: editingUser.phone,
          department_id: editingUser.department_id,
          role_ids: editingUser.role_ids,
        });
      } else {
        form.resetFields();
      }
    }
  }, [open, editingUser, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      await onConfirm(values);
    } catch {
      // Validation failed, form will show error messages
    }
  };

  const isEdit = !!editingUser;

  return (
    <Modal
      title={isEdit ? '编辑用户' : '新增用户'}
      open={open}
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={confirmLoading}
      destroyOnClose
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ status: true }}
      >
        <Form.Item
          name="username"
          label="用户名"
          rules={[
            { required: true, message: '请输入用户名' },
            { min: 2, max: 128, message: '用户名长度在 2-128 个字符' },
          ]}
        >
          <Input placeholder="请输入用户名" maxLength={128} disabled={isEdit} />
        </Form.Item>

        {!isEdit && (
          <Form.Item
            name="password"
            label="密码"
            rules={[
              { min: 6, max: 128, message: '密码长度在 6-128 个字符' },
            ]}
          >
            <Input.Password
              placeholder="留空则使用默认密码 123456"
              maxLength={128}
            />
          </Form.Item>
        )}

        <Form.Item name="nickname" label="昵称">
          <Input placeholder="请输入昵称" maxLength={128} />
        </Form.Item>

        <Form.Item
          name="email"
          label="邮箱"
          rules={[{ type: 'email', message: '请输入正确的邮箱格式' }]}
        >
          <Input placeholder="请输入邮箱" maxLength={255} />
        </Form.Item>

        <Form.Item name="phone" label="手机号">
          <Input placeholder="请输入手机号" maxLength={32} />
        </Form.Item>

        <Form.Item name="department_id" label="部门">
          <TreeSelect
            placeholder="请选择部门"
            allowClear
            treeData={departmentTree}
            fieldNames={{ label: 'name', value: 'id' }}
          />
        </Form.Item>

        <Form.Item name="role_ids" label="角色">
          <Select
            mode="multiple"
            placeholder="请选择角色"
            allowClear
            showSearch
            optionFilterProp="label"
            options={roleOptions.map((r) => ({
              label: r.name,
              value: r.id,
            }))}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
