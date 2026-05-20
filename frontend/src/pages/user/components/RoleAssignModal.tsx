import { useEffect, useState } from 'react';
import { message, Modal, Select } from 'antd';
import type { User } from '@/types/user';
import type { Role } from '@/types/role';
import { assignUserRoles } from '@/services/user';

interface RoleAssignModalProps {
  open: boolean;
  user: User | null;
  roleOptions: Role[];
  onCancel: () => void;
  onSuccess: () => void;
}

export default function RoleAssignModal({
  open,
  user,
  roleOptions,
  onCancel,
  onSuccess,
}: RoleAssignModalProps) {
  const [selectedRoleIds, setSelectedRoleIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && user) {
      setSelectedRoleIds(user.role_ids);
    }
  }, [open, user]);

  const handleOk = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const res = await assignUserRoles(user.id, { role_ids: selectedRoleIds });
      if (res.code === 0) {
        message.success('角色分配成功');
        onSuccess();
      } else {
        message.error(res.message || '角色分配失败');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      message.error(error?.response?.data?.message || '角色分配失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={`分配角色 - ${user?.username || ''}`}
      open={open}
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={loading}
      destroyOnClose
    >
      <Select
        mode="multiple"
        style={{ width: '100%' }}
        placeholder="请选择角色"
        value={selectedRoleIds}
        onChange={(values) => setSelectedRoleIds(values)}
        showSearch
        optionFilterProp="label"
        options={roleOptions.map((r) => ({
          label: r.name,
          value: r.id,
        }))}
      />
    </Modal>
  );
}
