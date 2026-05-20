import { useState } from 'react';
import { message, Modal, Typography } from 'antd';
import type { User } from '@/types/user';
import { resetPassword } from '@/services/user';

const { Text, Paragraph } = Typography;

interface PasswordResetModalProps {
  open: boolean;
  user: User | null;
  onCancel: () => void;
  onSuccess: () => void;
}

export default function PasswordResetModal({
  open,
  user,
  onCancel,
  onSuccess,
}: PasswordResetModalProps) {
  const [loading, setLoading] = useState(false);

  const handleOk = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const res = await resetPassword(user.id);
      if (res.code === 0) {
        message.success(`密码已重置为: ${res.data.password}`, 10);
        onSuccess();
      } else {
        message.error(res.message || '密码重置失败');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      message.error(error?.response?.data?.message || '密码重置失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="重置密码"
      open={open}
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={loading}
      okText="确认重置"
      cancelText="取消"
      destroyOnClose
    >
      <Paragraph>
        <Text strong>确定要重置用户 "{user?.username}" 的密码吗？</Text>
      </Paragraph>
      <Paragraph>
        <Text type="warning">
          重置后，密码将被恢复为默认密码（123456）。建议用户在首次登录后修改密码。
        </Text>
      </Paragraph>
    </Modal>
  );
}
