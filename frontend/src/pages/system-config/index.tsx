import { useCallback, useEffect, useState } from 'react';
import { Button, Layout, Menu, Spin, Table, Typography, message } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { ConfigGroup, SystemConfig } from '@/types/system_config';
import {
  getConfigGroups,
  getConfigsByGroup,
  refreshConfigCache,
  updateConfig,
} from '@/services/system_config';
import ConfigForm from './components/ConfigForm';

const { Sider, Content } = Layout;

function SystemConfigPage() {
  const [groups, setGroups] = useState<ConfigGroup[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<string>('');
  const [configs, setConfigs] = useState<SystemConfig[]>([]);
  const [groupsLoading, setGroupsLoading] = useState(false);
  const [configsLoading, setConfigsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [editConfig, setEditConfig] = useState<SystemConfig | null>(null);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editLoading, setEditLoading] = useState(false);

  // Fetch groups on mount
  const fetchGroups = useCallback(async () => {
    setGroupsLoading(true);
    try {
      const response = await getConfigGroups();
      const groupList = response.data ?? [];
      setGroups(groupList);
      if (groupList.length > 0 && !selectedGroup) {
        setSelectedGroup(groupList[0].code);
      }
    } catch {
      void message.error('获取配置分组失败');
    } finally {
      setGroupsLoading(false);
    }
  }, [selectedGroup]);

  useEffect(() => {
    void fetchGroups();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch configs when selected group changes
  const fetchConfigs = useCallback(async (group: string) => {
    if (!group) return;
    setConfigsLoading(true);
    try {
      const response = await getConfigsByGroup(group);
      setConfigs(response.data ?? []);
    } catch {
      void message.error('获取配置列表失败');
      setConfigs([]);
    } finally {
      setConfigsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedGroup) {
      void fetchConfigs(selectedGroup);
    }
  }, [selectedGroup, fetchConfigs]);

  // Handle group selection
  const handleGroupSelect = (info: { key: string }) => {
    setSelectedGroup(info.key);
  };

  // Handle refresh cache
  const handleRefreshCache = async () => {
    setRefreshing(true);
    try {
      const response = await refreshConfigCache();
      void message.success(response.message || '缓存刷新成功');
      // Reload current configs
      if (selectedGroup) {
        await fetchConfigs(selectedGroup);
      }
    } catch {
      void message.error('刷新缓存失败');
    } finally {
      setRefreshing(false);
    }
  };

  // Handle edit config
  const handleEdit = (config: SystemConfig) => {
    setEditConfig(config);
    setEditModalOpen(true);
  };

  // Handle submit edit
  const handleSubmitEdit = async (
    id: number,
    value: string | number | boolean,
  ) => {
    setEditLoading(true);
    try {
      await updateConfig(id, value);
      void message.success('配置更新成功');
      setEditModalOpen(false);
      setEditConfig(null);
      if (selectedGroup) {
        await fetchConfigs(selectedGroup);
      }
    } catch {
      void message.error('配置更新失败');
    } finally {
      setEditLoading(false);
    }
  };

  // Handle cancel edit
  const handleCancelEdit = () => {
    setEditModalOpen(false);
    setEditConfig(null);
  };

  const columns: ColumnsType<SystemConfig> = [
    {
      title: '配置键',
      dataIndex: 'key',
      key: 'key',
      width: 200,
    },
    {
      title: '配置值',
      dataIndex: 'value',
      key: 'value',
      ellipsis: true,
      render: (value: string, record: SystemConfig) => {
        if (record.is_sensitive) {
          return <span style={{ color: '#999' }}>******</span>;
        }
        return value;
      },
    },
    {
      title: '值类型',
      dataIndex: 'value_type',
      key: 'value_type',
      width: 100,
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
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
      width: 100,
      render: (_: unknown, record: SystemConfig) => (
        <Button type="link" onClick={() => handleEdit(record)}>
          编辑
        </Button>
      ),
    },
  ];

  return (
    <Layout style={{ height: '100%' }}>
      <Sider
        width={220}
        style={{
          background: '#fff',
          borderRight: '1px solid #f0f0f0',
        }}
      >
        <Spin spinning={groupsLoading}>
          <div
            style={{ padding: '16px 16px 0', fontWeight: 600, fontSize: 14 }}
          >
            配置分组
          </div>
          <Menu
            mode="inline"
            selectedKeys={selectedGroup ? [selectedGroup] : []}
            onSelect={handleGroupSelect}
            style={{ borderRight: 0, marginTop: 8 }}
            items={groups.map((g) => ({
              key: g.code,
              label: g.name,
            }))}
          />
        </Spin>
      </Sider>
      <Content style={{ padding: 24, background: '#fff' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 16,
          }}
        >
          <Typography.Title level={4} style={{ margin: 0 }}>
            {selectedGroup ? `配置列表 - ${selectedGroup}` : '配置列表'}
          </Typography.Title>
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            loading={refreshing}
            onClick={handleRefreshCache}
          >
            刷新缓存
          </Button>
        </div>
        <Spin spinning={configsLoading}>
          <Table<SystemConfig>
            rowKey="id"
            columns={columns}
            dataSource={configs}
            pagination={false}
            locale={{ emptyText: '暂无配置数据' }}
          />
        </Spin>
      </Content>

      <ConfigForm
        open={editModalOpen}
        config={editConfig}
        loading={editLoading}
        onCancel={handleCancelEdit}
        onSubmit={handleSubmitEdit}
      />
    </Layout>
  );
}

export default SystemConfigPage;
