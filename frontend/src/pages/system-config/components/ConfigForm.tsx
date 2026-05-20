import { useEffect, useState } from 'react';
import { Button, Form, Input, InputNumber, Modal, Select, Switch } from 'antd';
import type { SystemConfig } from '@/types/system_config';

interface ConfigFormProps {
  open: boolean;
  config: SystemConfig | null;
  loading: boolean;
  onCancel: () => void;
  onSubmit: (id: number, value: string | number | boolean) => Promise<void>;
}

function ConfigForm({ open, config, loading, onCancel, onSubmit }: ConfigFormProps) {
  const [form] = Form.useForm();
  const [modifySensitive, setModifySensitive] = useState(false);

  useEffect(() => {
    if (open) {
      setModifySensitive(false);
      if (config) {
        if (config.is_sensitive && config.value === '******') {
          form.resetFields();
          form.setFieldsValue({ _sensitive_placeholder: '******' });
        } else {
          const parsedValue = parseValue(config.value, config.value_type);
          form.setFieldsValue({ value: parsedValue });
        }
      } else {
        form.resetFields();
      }
    }
  }, [open, config, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      if (config) {
        await onSubmit(config.id, values.value);
      }
    } catch {
      // Validation failed, form will show errors
    }
  };

  return (
    <Modal
      title={`编辑配置: ${config?.key ?? ''}`}
      open={open}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleOk}>
          保存
        </Button>,
      ]}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        style={{ marginTop: 16 }}
      >
        <Form.Item label="配置键">
          <Input value={config?.key} disabled />
        </Form.Item>
        <Form.Item label="值类型">
          <Input value={config?.value_type} disabled />
        </Form.Item>
        {config?.is_sensitive && !modifySensitive ? (
          <>
            <Form.Item label="配置值">
              <Form.Item name="_sensitive_placeholder" noStyle>
                <Input disabled value="******" />
              </Form.Item>
            </Form.Item>
            <Button
              type="link"
              onClick={() => {
                setModifySensitive(true);
                form.setFieldsValue({ value: '' });
              }}
              style={{ marginBottom: 16 }}
            >
              修改敏感值
            </Button>
          </>
        ) : (
          <Form.Item
            label="配置值"
            name="value"
            rules={[{ required: true, message: '请输入配置值' }]}
          >
            {renderValueControl(config?.value_type ?? 'string')}
          </Form.Item>
        )}
        {config?.remark && (
          <Form.Item label="备注">
            <Input value={config.remark} disabled />
          </Form.Item>
        )}
      </Form>
    </Modal>
  );
}

function parseValue(value: string, valueType: string): string | number | boolean {
  switch (valueType) {
    case 'integer':
      return Number(value);
    case 'boolean':
      return value === 'true';
    default:
      return value;
  }
}

function renderValueControl(valueType: string) {
  switch (valueType) {
    case 'integer':
      return <InputNumber style={{ width: '100%' }} />;
    case 'boolean':
      return <Switch />;
    case 'json':
      return (
        <Input.TextArea
          rows={6}
          placeholder='请输入 JSON 格式数据，例如: {"key": "value"}'
        />
      );
    case 'select':
      return (
        <Select
          placeholder="请选择"
          // Options would typically come from config metadata or props
          options={[]}
        />
      );
    default: // string
      return <Input placeholder="请输入配置值" />;
  }
}

export default ConfigForm;
