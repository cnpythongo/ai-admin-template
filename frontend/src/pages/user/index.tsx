import { useCallback, useEffect, useState } from 'react';
import {
  Badge,
  Button,
  Input,
  Typography,
  message,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  TreeSelect,
} from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { User, UserCreateParams } from '@/types/user';
import type { Department } from '@/types/department';
import type { Role } from '@/types/role';
import {
  createUser,
  deleteUser,
  getUsers,
  setUserStatus,
  updateUser,
} from '@/services/user';
import { getDepartmentTree } from '@/services/department';
import { getRoles } from '@/services/role';
import UserForm from './components/UserForm';
import RoleAssignModal from './components/RoleAssignModal';
import PasswordResetModal from './components/PasswordResetModal';

export default function UserPage() {
  const [data, setData] = useState<{
    items: User[];
    total: number;
    page: number;
    page_size: number;
  }>({ items: [], total: 0, page: 1, page_size: 10 });
  const [loading, setLoading] = useState(false);
  const [searchUsername, setSearchUsername] = useState('');
  const [searchEmail, setSearchEmail] = useState('');
  const [searchDeptId, setSearchDeptId] = useState<number | undefined>(
    undefined,
  );
  const [searchRoleId, setSearchRoleId] = useState<number | undefined>(
    undefined,
  );
  const [searchStatus, setSearchStatus] = useState<boolean | undefined>(
    undefined,
  );

  // Department tree data
  const [deptTree, setDeptTree] = useState<Department[]>([]);
  // Role options
  const [roleOptions, setRoleOptions] = useState<Role[]>([]);

  // Modal states
  const [formOpen, setFormOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [formLoading, setFormLoading] = useState(false);

  // Role assign modal
  const [roleAssignOpen, setRoleAssignOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  // Password reset modal
  const [passwordResetOpen, setPasswordResetOpen] = useState(false);
  const [resetUser, setResetUser] = useState<User | null>(null);

  // Load department tree and role list once
  useEffect(() => {
    getDepartmentTree().then((res) => {
      if (res.code === 0) {
        setDeptTree(res.data);
      }
    });
    getRoles({ page: 1, page_size: 100 }).then((res) => {
      if (res.code === 0) {
        setRoleOptions(res.data.items);
      }
    });
  }, []);

  const fetchUsers = useCallback(
    async (page = 1, pageSize = 10) => {
      setLoading(true);
      try {
        const res = await getUsers({
          page,
          page_size: pageSize,
          username: searchUsername || undefined,
          email: searchEmail || undefined,
          department_id: searchDeptId,
          role_id: searchRoleId,
          status: searchStatus,
        });
        if (res.code === 0) {
          setData(res.data);
        } else {
          message.error(res.message || '获取用户列表失败');
        }
      } catch {
        message.error('获取用户列表失败');
      } finally {
        setLoading(false);
      }
    },
    [searchUsername, searchEmail, searchDeptId, searchRoleId, searchStatus],
  );

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleSearch = () => {
    fetchUsers(1, data.page_size);
  };

  const handleReset = () => {
    setSearchUsername('');
    setSearchEmail('');
    setSearchDeptId(undefined);
    setSearchRoleId(undefined);
    setSearchStatus(undefined);
  };

  const handleAdd = () => {
    setEditingUser(null);
    setFormOpen(true);
  };

  const handleEdit = (record: User) => {
    setEditingUser(record);
    setFormOpen(true);
  };

  const handleDelete = async (record: User) => {
    try {
      const res = await deleteUser(record.id);
      if (res.code === 0) {
        message.success('删除成功');
        fetchUsers(data.page, data.page_size);
      } else {
        message.error(res.message || '删除失败');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      message.error(error?.response?.data?.message || '删除失败');
    }
  };

  const handleStatusToggle = async (record: User) => {
    try {
      const newStatus = !record.status;
      const res = await setUserStatus(record.id, { status: newStatus });
      if (res.code === 0) {
        message.success(newStatus ? '已启用' : '已禁用');
        fetchUsers(data.page, data.page_size);
      } else {
        message.error(res.message || '操作失败');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      message.error(error?.response?.data?.message || '操作失败');
    }
  };

  const handleFormConfirm = async (values: UserCreateParams) => {
    setFormLoading(true);
    try {
      if (editingUser) {
        const res = await updateUser(editingUser.id, values);
        if (res.code === 0) {
          message.success('更新成功');
          setFormOpen(false);
          fetchUsers(data.page, data.page_size);
        } else {
          message.error(res.message || '更新失败');
        }
      } else {
        const res = await createUser(values);
        if (res.code === 0) {
          message.success('创建成功');
          setFormOpen(false);
          fetchUsers(1, data.page_size);
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

  const handleAssignRoles = (record: User) => {
    setSelectedUser(record);
    setRoleAssignOpen(true);
  };

  const handleResetPassword = (record: User) => {
    setResetUser(record);
    setPasswordResetOpen(true);
  };

  const handlePageChange = (page: number, pageSize: number) => {
    fetchUsers(page, pageSize);
  };

  const columns: ColumnsType<User> = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 120,
    },
    {
      title: '昵称',
      dataIndex: 'nickname',
      key: 'nickname',
      width: 120,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      width: 180,
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      key: 'phone',
      width: 130,
    },
    {
      title: '部门',
      dataIndex: 'department_name',
      key: 'department_name',
      width: 120,
      render: (text: string | null) => text || '-',
    },
    {
      title: '角色',
      dataIndex: 'role_names',
      key: 'role_names',
      width: 200,
      render: (roles: string[]) =>
        roles.length > 0
          ? roles.map((r) => (
              <Tag key={r} color="blue">
                {r}
              </Tag>
            ))
          : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: boolean) =>
        status ? (
          <Badge status="success" text="启用" />
        ) : (
          <Badge status="error" text="禁用" />
        ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
    },
    {
      title: '操作',
      key: 'action',
      width: 340,
      render: (_: unknown, record: User) => (
        <Space>
          <Button type="link" size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description={`确定要删除用户 "${record.username}" 吗？`}
            onConfirm={() => handleDelete(record)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger>
              删除
            </Button>
          </Popconfirm>
          <Switch
            checked={record.status}
            onChange={() => handleStatusToggle(record)}
            size="small"
            checkedChildren="启用"
            unCheckedChildren="禁用"
          />
          <Button
            type="link"
            size="small"
            onClick={() => handleResetPassword(record)}
          >
            重置密码
          </Button>
          <Button
            type="link"
            size="small"
            onClick={() => handleAssignRoles(record)}
          >
            分配角色
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24, background: '#fff', minHeight: '100%' }}>
      <Typography.Title level={4} style={{ marginTop: 0 }}>
        用户管理
      </Typography.Title>
      <Space style={{ marginBottom: 16 }} wrap>
        <Input
          placeholder="用户名"
          value={searchUsername}
          onChange={(e) => setSearchUsername(e.target.value)}
          style={{ width: 160 }}
          allowClear
          onPressEnter={handleSearch}
        />
        <Input
          placeholder="邮箱"
          value={searchEmail}
          onChange={(e) => setSearchEmail(e.target.value)}
          style={{ width: 180 }}
          allowClear
          onPressEnter={handleSearch}
        />
        <TreeSelect
          placeholder="部门"
          value={searchDeptId}
          onChange={(value) => setSearchDeptId(value)}
          style={{ width: 160 }}
          allowClear
          treeData={deptTree}
          fieldNames={{ label: 'name', value: 'id' }}
        />
        <Select
          placeholder="角色"
          value={searchRoleId}
          onChange={(value) => setSearchRoleId(value)}
          style={{ width: 160 }}
          allowClear
          showSearch
          optionFilterProp="label"
          options={roleOptions.map((r) => ({
            label: r.name,
            value: r.id,
          }))}
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
          新增用户
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

      <UserForm
        open={formOpen}
        editingUser={editingUser}
        departmentTree={deptTree}
        roleOptions={roleOptions}
        onCancel={() => {
          setFormOpen(false);
          setEditingUser(null);
        }}
        onConfirm={handleFormConfirm}
        confirmLoading={formLoading}
      />

      <RoleAssignModal
        open={roleAssignOpen}
        user={selectedUser}
        roleOptions={roleOptions}
        onCancel={() => {
          setRoleAssignOpen(false);
          setSelectedUser(null);
        }}
        onSuccess={() => {
          setRoleAssignOpen(false);
          setSelectedUser(null);
          fetchUsers(data.page, data.page_size);
        }}
      />

      <PasswordResetModal
        open={passwordResetOpen}
        user={resetUser}
        onCancel={() => {
          setPasswordResetOpen(false);
          setResetUser(null);
        }}
        onSuccess={() => {
          setPasswordResetOpen(false);
          setResetUser(null);
        }}
      />
    </div>
  );
}
