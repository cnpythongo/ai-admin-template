import { useEffect, useState } from 'react';
import { Button, Card, Form, Input, message, Space, Spin } from 'antd';
import { getCurrentUser } from '@/services/auth';
import { updateProfile, changePassword } from '@/services/user';

export default function ProfilePage() {
  const [profileForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [username, setUsername] = useState('');

  useEffect(() => {
    fetchUserInfo();
  }, []);

  const fetchUserInfo = async () => {
    setLoading(true);
    try {
      const res = await getCurrentUser();
      if (res.code === 0) {
        setUsername(res.data.username);
        profileForm.setFieldsValue({
          nickname: res.data.nickname,
          email: res.data.email,
          phone: res.data.phone,
        });
      } else {
        message.error(res.message || '获取用户信息失败');
      }
    } catch {
      message.error('获取用户信息失败');
    } finally {
      setLoading(false);
    }
  };

  const handleProfileSave = async () => {
    try {
      const values = await profileForm.validateFields();
      setSavingProfile(true);
      const res = await updateProfile(values);
      if (res.code === 0) {
        message.success('个人资料更新成功');
        fetchUserInfo();
      } else {
        message.error(res.message || '更新失败');
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        return;
      }
      const error = err as { response?: { data?: { message?: string } } };
      message.error(error?.response?.data?.message || '更新失败');
    } finally {
      setSavingProfile(false);
    }
  };

  const handlePasswordChange = async () => {
    try {
      const values = await passwordForm.validateFields();
      if (values.new_password !== values.confirm_password) {
        message.error('两次输入的密码不一致');
        return;
      }
      setSavingPassword(true);
      const res = await changePassword({
        old_password: values.old_password,
        new_password: values.new_password,
        confirm_password: values.confirm_password,
      });
      if (res.code === 0) {
        message.success('密码修改成功');
        passwordForm.resetFields();
      } else {
        message.error(res.message || '密码修改失败');
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        return;
      }
      const error = err as { response?: { data?: { message?: string } } };
      message.error(error?.response?.data?.message || '密码修改失败');
    } finally {
      setSavingPassword(false);
    }
  };

  if (loading) {
    return (
      <Card title="个人中心">
        <div style={{ textAlign: 'center', padding: '50px 0' }}>
          <Spin size="large" />
        </div>
      </Card>
    );
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card title="个人资料">
        <Form
          form={profileForm}
          layout="vertical"
          style={{ maxWidth: 500 }}
        >
          <Form.Item label="用户名">
            <Input value={username} disabled />
          </Form.Item>

          <Form.Item
            name="nickname"
            label="昵称"
            rules={[{ max: 128, message: '昵称最长 128 个字符' }]}
          >
            <Input placeholder="请输入昵称" maxLength={128} />
          </Form.Item>

          <Form.Item
            name="email"
            label="邮箱"
            rules={[{ type: 'email', message: '请输入正确的邮箱格式' }]}
          >
            <Input placeholder="请输入邮箱" maxLength={255} />
          </Form.Item>

          <Form.Item name="phone" label="手机号">
            <Input placeholder="请输入手机号" maxLength={32} />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              onClick={handleProfileSave}
              loading={savingProfile}
            >
              保存修改
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="修改密码">
        <Form
          form={passwordForm}
          layout="vertical"
          style={{ maxWidth: 500 }}
        >
          <Form.Item
            name="old_password"
            label="旧密码"
            rules={[{ required: true, message: '请输入旧密码' }]}
          >
            <Input.Password placeholder="请输入旧密码" />
          </Form.Item>

          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码长度不能少于 6 位' },
            ]}
          >
            <Input.Password placeholder="请输入新密码" maxLength={128} />
          </Form.Item>

          <Form.Item
            name="confirm_password"
            label="确认新密码"
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password placeholder="请再次输入新密码" />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              onClick={handlePasswordChange}
              loading={savingPassword}
            >
              修改密码
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </Space>
  );
}
