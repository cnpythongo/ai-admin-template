import { useCallback, useEffect, useState } from 'react';
import {
  Button,
  Empty,
  Typography,
  message,
  Popconfirm,
  Radio,
  Spin,
  Table,
  Tag,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { Permission, PermissionType } from '@/types';
import {
  deletePermission,
  getPermissionTree,
  type CreatePermissionParams,
  type UpdatePermissionParams,
} from '@/services/permission';
import { createPermission, updatePermission } from '@/services/permission';
import PermissionForm from './components/PermissionForm';

const TYPE_OPTIONS: { label: string; value: PermissionType | '' }[] = [
  { label: '全部', value: '' },
  { label: '菜单', value: 'menu' },
  { label: '按钮', value: 'button' },
  { label: 'API', value: 'api' },
];

const TYPE_COLORS: Record<PermissionType, string> = {
  menu: 'blue',
  button: 'green',
  api: 'orange',
};

const TYPE_LABELS: Record<PermissionType, string> = {
  menu: '菜单',
  button: '按钮',
  api: 'API',
};

export default function PermissionPage() {
  const [treeData, setTreeData] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(false);
  const [typeFilter, setTypeFilter] = useState<PermissionType | ''>('');
  const [formOpen, setFormOpen] = useState(false);
  const [editingPermission, setEditingPermission] = useState<Permission | null>(
    null,
  );
  const [formLoading, setFormLoading] = useState(false);

  const fetchTree = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getPermissionTree(typeFilter || undefined);
      if (res.code === 0) {
        setTreeData(res.data);
      } else {
        void message.error(res.message || '获取权限树失败');
      }
    } catch {
      void message.error('获取权限树失败');
    } finally {
      setLoading(false);
    }
  }, [typeFilter]);

  useEffect(() => {
    void fetchTree();
  }, [fetchTree]);

  const handleAdd = () => {
    setEditingPermission(null);
    setFormOpen(true);
  };

  const handleEdit = (record: Permission) => {
    setEditingPermission(record);
    setFormOpen(true);
  };

  const handleDelete = async (record: Permission) => {
    try {
      const res = await deletePermission(record.id);
      if (res.code === 0) {
        void message.success('删除成功');
        await fetchTree();
      } else {
        void message.error(res.message || '删除失败');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      void message.error(error?.response?.data?.message || '删除失败');
    }
  };

  const handleFormConfirm = async (
    values: CreatePermissionParams | UpdatePermissionParams,
  ) => {
    setFormLoading(true);
    try {
      if (editingPermission) {
        const res = await updatePermission(editingPermission.id, values);
        if (res.code === 0) {
          void message.success('更新成功');
          setFormOpen(false);
          await fetchTree();
        } else {
          void message.error(res.message || '更新失败');
        }
      } else {
        const res = await createPermission(values as CreatePermissionParams);
        if (res.code === 0) {
          void message.success('创建成功');
          setFormOpen(false);
          await fetchTree();
        } else {
          void message.error(res.message || '创建失败');
        }
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      void message.error(error?.response?.data?.message || '操作失败');
    } finally {
      setFormLoading(false);
    }
  };

  const columns: ColumnsType<Permission> = [
    {
      title: '权限名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '权限编码',
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: PermissionType) => (
        <Tag color={TYPE_COLORS[type]}>{TYPE_LABELS[type]}</Tag>
      ),
    },
    {
      title: 'API路径',
      dataIndex: 'api_path',
      key: 'api_path',
      render: (path: string | undefined, record: Permission) => {
        if (!path) return '-';
        return `${record.api_method ?? ''} ${path}`;
      },
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
      width: 180,
      render: (_: unknown, record: Permission) => (
        <span>
          <Button type="link" size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description={`确定要删除权限 "${record.name}" 吗？`}
            onConfirm={() => handleDelete(record)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger>
              删除
            </Button>
          </Popconfirm>
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
          权限管理
        </Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新增权限
        </Button>
      </div>
      <div style={{ marginBottom: 16 }}>
        <Radio.Group
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          optionType="button"
          buttonStyle="solid"
        >
          {TYPE_OPTIONS.map((opt) => (
            <Radio.Button key={opt.value} value={opt.value}>
              {opt.label}
            </Radio.Button>
          ))}
        </Radio.Group>
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
          !loading && <Empty description="暂无权限数据" />
        )}
      </Spin>

      <PermissionForm
        open={formOpen}
        editingPermission={editingPermission}
        permissionTree={treeData}
        onCancel={() => setFormOpen(false)}
        onConfirm={handleFormConfirm}
        confirmLoading={formLoading}
      />
    </div>
  );
}
