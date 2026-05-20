import { useCallback, useEffect, useState } from 'react';
import {
  Button,
  DatePicker,
  Input,
  Typography,
  message,
  Select,
  Space,
  Table,
  Tag,
} from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { OperationLog } from '@/types/operation_log';
import { getOperationLogs, getLogModules } from '@/services/operation_log';

const { RangePicker } = DatePicker;

const actionLabels: Record<string, string> = {
  create: '新增',
  update: '修改',
  delete: '删除',
  list: '查询',
  login: '登录',
  export: '导出',
  reset_password: '重置密码',
  assign_roles: '分配角色',
};

export default function OperationLogPage() {
  const [data, setData] = useState<{
    items: OperationLog[];
    total: number;
    page: number;
    page_size: number;
  }>({ items: [], total: 0, page: 1, page_size: 10 });
  const [loading, setLoading] = useState(false);
  const [searchUsername, setSearchUsername] = useState('');
  const [searchModule, setSearchModule] = useState<string | undefined>(
    undefined,
  );
  const [searchAction, setSearchAction] = useState<string | undefined>(
    undefined,
  );
  const [searchStatus, setSearchStatus] = useState<number | undefined>(
    undefined,
  );
  const [timeRange, setTimeRange] = useState<[string, string] | null>(null);
  const [moduleOptions, setModuleOptions] = useState<
    { label: string; value: string }[]
  >([]);

  // Load module options
  useEffect(() => {
    getLogModules()
      .then((res) => {
        if (res.code === 0) {
          setModuleOptions(
            (res.data || []).map((m: string) => ({ label: m, value: m })),
          );
        }
      })
      .catch(() => {
        // Silently fail
      });
  }, []);

  const fetchLogs = useCallback(
    async (page = 1, pageSize = 10) => {
      setLoading(true);
      try {
        const res = await getOperationLogs({
          page,
          page_size: pageSize,
          username: searchUsername || undefined,
          module: searchModule,
          action: searchAction,
          status: searchStatus,
          start_time: timeRange?.[0],
          end_time: timeRange?.[1],
        });
        if (res.code === 0) {
          setData(res.data);
        } else {
          message.error(res.message || '获取操作日志失败');
        }
      } catch {
        message.error('获取操作日志失败');
      } finally {
        setLoading(false);
      }
    },
    [searchUsername, searchModule, searchAction, searchStatus, timeRange],
  );

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleSearch = () => {
    fetchLogs(1, data.page_size);
  };

  const handleReset = () => {
    setSearchUsername('');
    setSearchModule(undefined);
    setSearchAction(undefined);
    setSearchStatus(undefined);
    setTimeRange(null);
  };

  const handlePageChange = (page: number, pageSize: number) => {
    fetchLogs(page, pageSize);
  };

  const columns: ColumnsType<OperationLog> = [
    {
      title: '操作用户',
      dataIndex: 'username',
      key: 'username',
      width: 120,
    },
    {
      title: '模块',
      dataIndex: 'module',
      key: 'module',
      width: 100,
    },
    {
      title: '操作类型',
      dataIndex: 'action',
      key: 'action',
      width: 100,
      render: (action: string) => actionLabels[action] || action,
    },
    {
      title: '操作目标',
      dataIndex: 'target_name',
      key: 'target_name',
      width: 150,
      render: (text: string) => text || '-',
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 140,
    },
    {
      title: '请求路径',
      dataIndex: 'request_path',
      key: 'request_path',
      width: 200,
      ellipsis: true,
    },
    {
      title: '请求方法',
      dataIndex: 'request_method',
      key: 'request_method',
      width: 90,
      render: (method: string) => {
        if (!method) return '-';
        const colorMap: Record<string, string> = {
          GET: 'blue',
          POST: 'green',
          PUT: 'orange',
          DELETE: 'red',
        };
        return <Tag color={colorMap[method] || 'default'}>{method}</Tag>;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: number) =>
        status === 1 ? (
          <Tag color="green">成功</Tag>
        ) : (
          <Tag color="red">失败</Tag>
        ),
    },
    {
      title: '耗时(ms)',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      width: 90,
      render: (val: number | null) => (val != null ? val : '-'),
    },
    {
      title: '操作时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
    },
  ];

  return (
    <div style={{ padding: 24, background: '#fff', minHeight: '100%' }}>
      <Typography.Title level={4} style={{ marginTop: 0 }}>
        操作日志
      </Typography.Title>
      <Space style={{ marginBottom: 16 }} wrap>
        <Input
          placeholder="操作用户名"
          value={searchUsername}
          onChange={(e) => setSearchUsername(e.target.value)}
          style={{ width: 160 }}
          allowClear
          onPressEnter={handleSearch}
        />
        <Select
          placeholder="模块"
          value={searchModule}
          onChange={(value) => setSearchModule(value)}
          style={{ width: 140 }}
          allowClear
          options={moduleOptions}
        />
        <Select
          placeholder="操作类型"
          value={searchAction}
          onChange={(value) => setSearchAction(value)}
          style={{ width: 140 }}
          allowClear
          options={[
            { label: '新增', value: 'create' },
            { label: '修改', value: 'update' },
            { label: '删除', value: 'delete' },
            { label: '查询', value: 'list' },
            { label: '登录', value: 'login' },
            { label: '导出', value: 'export' },
          ]}
        />
        <Select
          placeholder="状态"
          value={searchStatus}
          onChange={(value) => setSearchStatus(value)}
          style={{ width: 120 }}
          allowClear
          options={[
            { label: '成功', value: 1 },
            { label: '失败', value: 0 },
          ]}
        />
        <RangePicker
          showTime
          onChange={(_, dateStrings) => {
            if (dateStrings[0] && dateStrings[1]) {
              setTimeRange([dateStrings[0], dateStrings[1]]);
            } else {
              setTimeRange(null);
            }
          }}
        />
        <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
          搜索
        </Button>
        <Button onClick={handleReset}>重置</Button>
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
    </div>
  );
}
