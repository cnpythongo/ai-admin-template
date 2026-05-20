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
import {
  PlusOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  LinkOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import * as Icons from '@ant-design/icons';
import type { Menu } from '@/types/menu';
import {
  createMenu,
  deleteMenu,
  getMenuTree,
  updateMenu,
  type MenuCreateParams,
  type MenuUpdateParams,
} from '@/services/menu';
import MenuForm from './components/MenuForm';

function getIconElement(iconName: string | null | undefined): React.ReactNode {
  if (!iconName) return null;
  const IconComp = (
    Icons as unknown as Record<
      string,
      React.ComponentType<{ style?: React.CSSProperties }>
    >
  )[iconName];
  if (!IconComp) return null;
  return <IconComp style={{ fontSize: 16 }} />;
}

export default function MenuPage() {
  const [treeData, setTreeData] = useState<Menu[]>([]);
  const [loading, setLoading] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [editingMenu, setEditingMenu] = useState<Menu | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [parentMenu, setParentMenu] = useState<Menu | null>(null);

  const fetchTree = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getMenuTree();
      if (res.code === 0) {
        setTreeData(res.data);
      } else {
        void message.error(res.message || '获取菜单树失败');
      }
    } catch {
      void message.error('获取菜单树失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchTree();
  }, [fetchTree]);

  const handleAddRoot = () => {
    setEditingMenu(null);
    setParentMenu(null);
    setFormOpen(true);
  };

  const handleAddChild = (record: Menu) => {
    setEditingMenu(null);
    setParentMenu(record);
    setFormOpen(true);
  };

  const handleEdit = (record: Menu) => {
    setEditingMenu(record);
    setParentMenu(null);
    setFormOpen(true);
  };

  const handleDelete = async (record: Menu) => {
    try {
      const res = await deleteMenu(record.id);
      if (res.code === 0) {
        void message.success('删除成功');
        await fetchTree();
      } else {
        void message.error(res.message || '删除失败');
      }
    } catch (err: unknown) {
      const error = err as {
        response?: { data?: { message?: string } };
      };
      void message.error(error?.response?.data?.message || '删除失败');
    }
  };

  const handleFormConfirm = async (
    values: MenuCreateParams | MenuUpdateParams,
  ) => {
    setFormLoading(true);
    try {
      if (editingMenu) {
        const res = await updateMenu(editingMenu.id, values);
        if (res.code === 0) {
          void message.success('更新成功');
          setFormOpen(false);
          await fetchTree();
        } else {
          void message.error(res.message || '更新失败');
        }
      } else {
        const createValues = {
          ...values,
          parent_id:
            parentMenu?.id ?? (values as MenuCreateParams).parent_id ?? null,
        } as MenuCreateParams;
        const res = await createMenu(createValues);
        if (res.code === 0) {
          void message.success('创建成功');
          setFormOpen(false);
          await fetchTree();
        } else {
          void message.error(res.message || '创建失败');
        }
      }
    } catch (err: unknown) {
      const error = err as {
        response?: { data?: { message?: string } };
      };
      void message.error(error?.response?.data?.message || '操作失败');
    } finally {
      setFormLoading(false);
    }
  };

  const columns: ColumnsType<Menu> = [
    {
      title: '菜单名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Menu) => (
        <span>
          {getIconElement(record.icon)}
          <span style={{ marginLeft: record.icon ? 8 : 0 }}>{name}</span>
        </span>
      ),
    },
    {
      title: '图标',
      dataIndex: 'icon',
      key: 'icon',
      width: 80,
      render: (icon: string | null | undefined) =>
        icon ? <Tag>{icon}</Tag> : <span style={{ color: '#999' }}>-</span>,
    },
    {
      title: '路由路径',
      dataIndex: 'route_path',
      key: 'route_path',
      render: (path: string | null | undefined) =>
        path ?? <span style={{ color: '#999' }}>-</span>,
    },
    {
      title: '组件路径',
      dataIndex: 'component',
      key: 'component',
      render: (comp: string | null | undefined) =>
        comp ?? <span style={{ color: '#999' }}>-</span>,
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
      width: 80,
    },
    {
      title: '状态',
      key: 'status',
      width: 130,
      render: (_: unknown, record: Menu) => (
        <span>
          {record.hidden && (
            <Tag icon={<EyeInvisibleOutlined />} color="default">
              隐藏
            </Tag>
          )}
          {record.is_external_link && (
            <Tag icon={<LinkOutlined />} color="blue">
              外链
            </Tag>
          )}
          {!record.hidden && !record.is_external_link && (
            <Tag icon={<EyeOutlined />} color="green">
              显示
            </Tag>
          )}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 240,
      render: (_: unknown, record: Menu) => (
        <span>
          <Button
            type="link"
            size="small"
            onClick={() => handleAddChild(record)}
          >
            新增子菜单
          </Button>
          <Button type="link" size="small" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description={`确定要删除菜单 "${record.name}" 吗？`}
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
          菜单管理
        </Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAddRoot}>
          新增菜单
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
          !loading && <Empty description="暂无菜单数据" />
        )}
      </Spin>

      <MenuForm
        open={formOpen}
        editingMenu={editingMenu}
        menuTree={treeData}
        onCancel={() => setFormOpen(false)}
        onConfirm={handleFormConfirm}
        confirmLoading={formLoading}
      />
    </div>
  );
}
