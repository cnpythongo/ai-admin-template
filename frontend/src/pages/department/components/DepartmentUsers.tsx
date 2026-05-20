import { useEffect, useState } from 'react';
import { Drawer, Table, Tag, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { Department, DepartmentUserItem } from '@/types/department';
import type { PaginatedData } from '@/types';
import { getDepartmentUsers } from '@/services/department';

interface DepartmentUsersProps {
  open: boolean;
  department: Department | null;
  onClose: () => void;
}

export default function DepartmentUsers({
  open,
  department,
  onClose,
}: DepartmentUsersProps) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<PaginatedData<DepartmentUserItem> | null>(null);

  useEffect(() => {
    if (open && department) {
      fetchUsers(department.id, 1);
    }
  }, [open, department]);

  const fetchUsers = async (id: number, page: number) => {
    setLoading(true);
    try {
      const res = await getDepartmentUsers(id, { page, page_size: 10 });
      if (res.code === 0) {
        setData(res.data);
      } else {
        message.error(res.message || '获取部门用户失败');
      }
    } catch {
      message.error('获取部门用户失败');
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (page: number) => {
    if (department) {
      fetchUsers(department.id, page);
    }
  };

  const columns: ColumnsType<DepartmentUserItem> = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      width: 150,
    },
    {
      title: '昵称',
      dataIndex: 'nickname',
      key: 'nickname',
      width: 150,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      width: 200,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: boolean) =>
        status ? (
          <Tag color="green">启用</Tag>
        ) : (
          <Tag color="red">禁用</Tag>
        ),
    },
  ];

  return (
    <Drawer
      title={`部门成员 - ${department?.name ?? ''}`}
      open={open}
      onClose={onClose}
      width={600}
    >
      <Table
        dataSource={data?.items ?? []}
        columns={columns}
        loading={loading}
        rowKey="id"
        pagination={{
          current: data?.page ?? 1,
          pageSize: data?.page_size ?? 10,
          total: data?.total ?? 0,
          onChange: handlePageChange,
          showSizeChanger: false,
        }}
      />
    </Drawer>
  );
}
