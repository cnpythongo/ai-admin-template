import { useCallback, useEffect, useState } from 'react';
import {
  Button,
  Input,
  Typography,
  message,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
} from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { Role, RoleCreateParams } from '@/types/role';
import { createRole, deleteRole, getRoles, updateRole } from '@/services/role';
import RoleForm from './components/RoleForm';
import PermissionTree from './components/PermissionTree';
import RoleUsers from './components/RoleUsers';

export default function RolePage() {
  const [data, setData] = useState<{
    items: Role[];
    total: number;
    page: number;
    page_size: number;
  }>({ items: [], total: 0, page: 1, page_size: 10 });
  const [loading, setLoading] = useState(false);
  const [searchName, setSearchName] = useState('');
  const [searchStatus, setSearchStatus] = useState<boolean | undefined>(
    undefined,
  );
  const [formOpen, setFormOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [permTreeOpen, setPermTreeOpen] = useState(false);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [usersDrawerOpen, setUsersDrawerOpen] = useState(false);
  const [usersRole, setUsersRole] = useState<Role | null>(null);

  const fetchRoles = useCallback(
    async (page = 1, pageSize = 10) => {
      setLoading(true);
      try {
        const res = await getRoles({
          page,
          page_size: pageSize,
          name: searchName || undefined,
          status: searchStatus,
        });
        if (res.code === 0) {
          setData(res.data);
        } else {
          message.error(res.message || '获取角色列表失败');
        }
      } catch {
        message.error('获取角色列表失败');
      } finally {
        setLoading(false);
      }
    },
    [searchName, searchStatus],
  );

  useEffect(() => {
    fetchRoles();
  }, [fetchRoles]);

  const handleSearch = () => {
    fetchRoles(1, data.page_size);
  };

  const handleReset = () => {
    setSearchName('');
    setSearchStatus(undefined);
    // Will trigger re-fetch via useEffect since searchName/searchStatus change
  };

  const handleAdd = () => {
    setEditingRole(null);
    setFormOpen(true);
  };

  const handleEdit = (record: Role) => {
    setEditingRole(record);
    setFormOpen(true);
  };

  const handleDelete = async (record: Role) => {
    try {
      const res = await deleteRole(record.id);
      if (res.code === 0) {
        message.success('删除成功');
        fetchRoles(data.page, data.page_size);
      } else {
        message.error(res.message || '删除失败');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      message.error(error?.response?.data?.message || '删除失败');
    }
  };

  const handleFormConfirm = async (values: RoleCreateParams) => {
    setFormLoading(true);
    try {
      if (editingRole) {
        const res = await updateRole(editingRole.id, values);
        if (res.code === 0) {
          message.success('更新成功');
          setFormOpen(false);
          fetchRoles(data.page, data.page_size);
        } else {
          message.error(res.message || '更新失败');
        }
      } else {
        const res = await createRole(values);
        if (res.code === 0) {
          message.success('创建成功');
          setFormOpen(false);
          fetchRoles(1, data.page_size);
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

  const handleAssignPermissions = (record: Role) => {
    setSelectedRole(record);
    setPermTreeOpen(true);
  };

  const handleViewUsers = (record: Role) => {
    setUsersRole(record);
    setUsersDrawerOpen(true);
  };

  const handlePageChange = (page: number, pageSize: number) => {
    fetchRoles(page, pageSize);
  };

  const columns: ColumnsType<Role> = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '角色编码',
      dataIndex: 'code',
      key: 'code',
      width: 150,
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
      title: '用户数',
      dataIndex: 'user_count',
      key: 'user_count',
      width: 80,
    },
    {
      title: '备注',
      dataIndex: 'remark',
      key: 'remark',
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 320,
      render: (_: unknown, record: Role) => (
        <Space>
          <Button type="link" size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description={`确定要删除角色 "${record.name}" 吗？`}
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
            onClick={() => handleAssignPermissions(record)}
          >
            分配权限
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => handleViewUsers(record)}
          >
            成员
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24, background: '#fff', minHeight: '100%' }}>
      <Typography.Title level={4} style={{ marginTop: 0 }}>
        角色管理
      </Typography.Title>
      <Space style={{ marginBottom: 16 }}>
        <Input
          placeholder="角色名称"
          value={searchName}
          onChange={(e) => setSearchName(e.target.value)}
          style={{ width: 200 }}
          allowClear
          onPressEnter={handleSearch}
        />
        <Select
          placeholder="状态"
          value={searchStatus}
          onChange={(value) => setSearchStatus(value)}
          style={{ width: 120 }}
          allowClear
          options={[
            { label: '启用', value: true },
            { label: '禁用', value: false },
          ]}
        />
        <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
          搜索
        </Button>
        <Button onClick={handleReset}>重置</Button>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新增角色
        </Button>
      </Space>

      <Table
        columns={columns}
        dataSource={data.items}
        loading={loading}
        rowKey="id"
        pagination={{
          current: data.page,
          pageSize: data.page_size,
          total: data.total,
          onChange: handlePageChange,
          showSizeChanger: true,
          pageSizeOptions: [10, 20, 50],
        }}
      />

      <RoleForm
        open={formOpen}
        editingRole={editingRole}
        onCancel={() => setFormOpen(false)}
        onConfirm={handleFormConfirm}
        confirmLoading={formLoading}
      />

      <PermissionTree
        open={permTreeOpen}
        role={selectedRole}
        onCancel={() => {
          setPermTreeOpen(false);
          setSelectedRole(null);
        }}
      />

      <RoleUsers
        open={usersDrawerOpen}
        role={usersRole}
        onClose={() => {
          setUsersDrawerOpen(false);
          setUsersRole(null);
        }}
      />
    </div>
  );
}
