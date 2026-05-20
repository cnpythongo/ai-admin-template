import { useEffect, useState } from 'react';
import { Form, Input, InputNumber, Modal, Switch, TreeSelect } from 'antd';
import type { Department, DepartmentCreateParams } from '@/types/department';

interface DepartmentFormProps {
  open: boolean;
  editingDepartment: Department | null;
  departmentTree: Department[];
  onCancel: () => void;
  onConfirm: (values: DepartmentCreateParams) => Promise<void>;
  confirmLoading: boolean;
}

function flattenTree(
  nodes: Department[],
  excludeId?: number,
): { title: string; value: number; disabled: boolean }[] {
  const result: { title: string; value: number; disabled: boolean }[] = [];
  for (const node of nodes) {
    // Exclude the node being edited and its descendants to prevent circular reference
    const disabled = node.id === excludeId;
    result.push({
      title: node.name,
      value: node.id,
      disabled,
    });
    if (node.children && node.children.length > 0) {
      const children = flattenTree(node.children, excludeId);
      result.push(...children);
    }
  }
  return result;
}

export default function DepartmentForm({
  open,
  editingDepartment,
  departmentTree,
  onCancel,
  onConfirm,
  confirmLoading,
}: DepartmentFormProps) {
  const [form] = Form.useForm();
  const [treeData, setTreeData] = useState<
    { title: string; value: string; disabled: boolean }[]
  >([]);

  useEffect(() => {
    if (open) {
      const excludeId = editingDepartment?.id;
      const flat = flattenTree(departmentTree, excludeId);
      const rootNode = { title: '顶级部门', value: '', disabled: false };
      setTreeData([rootNode, ...flat.map((n) => ({ ...n, value: String(n.value) }))]);

      if (editingDepartment) {
        form.setFieldsValue({
          name: editingDepartment.name,
          parent_id: editingDepartment.parent_id !== null ? String(editingDepartment.parent_id) : '',
          sort_order: editingDepartment.sort_order,
          status: editingDepartment.status,
        });
      } else {
        form.resetFields();
      }
    }
  }, [open, editingDepartment, departmentTree, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      await onConfirm(values);
    } catch {
      // Validation failed, form will show error messages
    }
  };

  return (
    <Modal
      title={editingDepartment ? '编辑部门' : '新增部门'}
      open={open}
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={confirmLoading}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ sort_order: 0, status: true }}
      >
        <Form.Item
          name="name"
          label="部门名称"
          rules={[{ required: true, message: '请输入部门名称' }]}
        >
          <Input placeholder="请输入部门名称" maxLength={128} />
        </Form.Item>

        <Form.Item name="parent_id" label="上级部门">
          <TreeSelect
            treeData={treeData}
            placeholder="请选择上级部门"
            allowClear
            treeDefaultExpandAll
          />
        </Form.Item>

        <Form.Item name="sort_order" label="排序">
          <InputNumber min={0} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item name="status" label="状态" valuePropName="checked">
          <Switch checkedChildren="启用" unCheckedChildren="禁用" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
