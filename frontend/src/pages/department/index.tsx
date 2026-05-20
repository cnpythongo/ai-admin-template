import { useCallback, useEffect, useState } from 'react';
import {
  Button,
  Empty,
  Typography,
  message,
  Popconfirm,
  Spin,
  Table,
  Tag,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { Department, DepartmentCreateParams } from '@/types/department';
import {
  createDepartment,
  deleteDepartment,
  getDepartmentTree,
  updateDepartment,
} from '@/services/department';
import DepartmentForm from './components/DepartmentForm';
import DepartmentUsers from './components/DepartmentUsers';

export default function DepartmentPage() {
  const [treeData, setTreeData] = useState<Department[]>([]);
  const [loading, setLoading] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [editingDepartment, setEditingDepartment] = useState<Department | null>(
    null,
  );
  const [formLoading, setFormLoading] = useState(false);
  const [usersDrawerOpen, setUsersDrawerOpen] = useState(false);
  const [selectedDepartment, setSelectedDepartment] =
    useState<Department | null>(null);

  const fetchTree = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getDepartmentTree();
      if (res.code === 0) {
        setTreeData(res.data);
      } else {
        message.error(res.message || '获取部门树失败');
      }
    } catch {
      message.error('获取部门树失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTree();
  }, [fetchTree]);

  const handleAdd = () => {
    setEditingDepartment(null);
    setFormOpen(true);
  };

  const handleEdit = (record: Department) => {
    setEditingDepartment(record);
    setFormOpen(true);
  };

  const handleDelete = async (record: Department) => {
    try {
      const res = await deleteDepartment(record.id);
      if (res.code === 0) {
        message.success('删除成功');
        fetchTree();
      } else {
        message.error(res.message || '删除失败');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      message.error(error?.response?.data?.message || '删除失败');
    }
  };

  const handleFormConfirm = async (values: DepartmentCreateParams) => {
    setFormLoading(true);
    try {
      if (editingDepartment) {
        const res = await updateDepartment(editingDepartment.id, values);
        if (res.code === 0) {
          message.success('更新成功');
          setFormOpen(false);
          fetchTree();
        } else {
          message.error(res.message || '更新失败');
        }
      } else {
        const res = await createDepartment(values);
        if (res.code === 0) {
          message.success('创建成功');
          setFormOpen(false);
          fetchTree();
        } else {
          message.error(res.message || '创建失败');
        }
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      message.error(error?.response?.data?.message || '操作失败');
    } finally {
      setFormLoading(false);
    }
  };

  const handleViewUsers = (record: Department) => {
    setSelectedDepartment(record);
    setUsersDrawerOpen(true);
  };

  const columns: ColumnsType<Department> = [
    {
      title: '部门名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: boolean) =>
        status ? <Tag color="green">启用</Tag> : <Tag color="red">禁用</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      width: 280,
      render: (_: unknown, record: Department) => (
        <span>
          <Button type="link" size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description={`确定要删除部门 "${record.name}" 吗？`}
            onConfirm={() => handleDelete(record)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger>
              删除
            </Button>
          </Popconfirm>
          <Button
            type="link"
            size="small"
            onClick={() => handleViewUsers(record)}
          >
            成员
          </Button>
        </span>
      ),
    },
  ];

  return (
    <div style={{ padding: 24, background: '#fff', minHeight: '100%' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <Typography.Title level={4} style={{ margin: 0 }}>
          部门管理
        </Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新增部门
        </Button>
      </div>
      <Spin spinning={loading}>
        {treeData.length > 0 ? (
          <Table
            columns={columns}
            dataSource={treeData}
            rowKey="id"
            pagination={false}
            defaultExpandAllRows
            childrenColumnName="children"
          />
        ) : (
          !loading && <Empty description="暂无部门数据" />
        )}
      </Spin>

      <DepartmentForm
        open={formOpen}
        editingDepartment={editingDepartment}
        departmentTree={treeData}
        onCancel={() => setFormOpen(false)}
        onConfirm={handleFormConfirm}
        confirmLoading={formLoading}
      />

      <DepartmentUsers
        open={usersDrawerOpen}
        department={selectedDepartment}
        onClose={() => {
          setUsersDrawerOpen(false);
          setSelectedDepartment(null);
        }}
      />
    </div>
  );
}
