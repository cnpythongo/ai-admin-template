import { useMemo, useState } from 'react';
import { Input, Popover } from 'antd';
import * as Icons from '@ant-design/icons';

// Commonly used icons for menu management
const COMMON_ICON_NAMES = [
  'SettingOutlined',
  'UserOutlined',
  'TeamOutlined',
  'SafetyOutlined',
  'MenuOutlined',
  'AppstoreOutlined',
  'DashboardOutlined',
  'FileOutlined',
  'FolderOutlined',
  'FolderOpenOutlined',
  'HomeOutlined',
  'KeyOutlined',
  'LockOutlined',
  'UnlockOutlined',
  'DatabaseOutlined',
  'CloudOutlined',
  'ToolOutlined',
  'CrownOutlined',
  'FlagOutlined',
  'StarOutlined',
  'HeartOutlined',
  'BellOutlined',
  'MailOutlined',
  'PhoneOutlined',
  'LinkOutlined',
  'GlobalOutlined',
  'BarChartOutlined',
  'PieChartOutlined',
  'LineChartOutlined',
  'TableOutlined',
  'FormOutlined',
  'CheckSquareOutlined',
  'OrderedListOutlined',
  'AuditOutlined',
  'ProfileOutlined',
  'ContainerOutlined',
  'BookOutlined',
  'ReadOutlined',
  'CodeOutlined',
  'ApiOutlined',
  'BugOutlined',
  'RocketOutlined',
  'ShoppingCartOutlined',
  'DollarOutlined',
  'NotificationOutlined',
  'MessageOutlined',
  'CalendarOutlined',
  'ClockCircleOutlined',
  'PaperClipOutlined',
  'AttachmentOutlined',
  'ExportOutlined',
  'ImportOutlined',
  'UploadOutlined',
  'DownloadOutlined',
  'SearchOutlined',
  'EyeOutlined',
  'EditOutlined',
  'DeleteOutlined',
  'PlusOutlined',
  'MinusOutlined',
];

interface IconPickerProps {
  value?: string | null;
  onChange?: (value: string) => void;
  placeholder?: string;
}

function getIconComponent(iconName: string): React.ReactNode {
  const IconComp = (Icons as unknown as Record<string, React.ComponentType>)[iconName];
  if (!IconComp) return null;
  return <IconComp />;
}

export default function IconPicker({
  value,
  onChange,
  placeholder = '请选择图标',
}: IconPickerProps) {
  const [searchText, setSearchText] = useState('');
  const [open, setOpen] = useState(false);

  const filteredIcons = useMemo(() => {
    if (!searchText) return COMMON_ICON_NAMES;
    const lower = searchText.toLowerCase();
    return COMMON_ICON_NAMES.filter((name) =>
      name.toLowerCase().includes(lower),
    );
  }, [searchText]);

  const content = (
    <div style={{ width: 360 }}>
      <Input
        placeholder="搜索图标名称"
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        style={{ marginBottom: 8 }}
        allowClear
      />
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 4,
          maxHeight: 240,
          overflowY: 'auto',
        }}
      >
        {filteredIcons.map((iconName) => {
          const isSelected = value === iconName;
          return (
            <div
              key={iconName}
              onClick={() => {
                onChange?.(iconName);
                setOpen(false);
                setSearchText('');
              }}
              style={{
                width: 40,
                height: 40,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                borderRadius: 4,
                border: isSelected
                  ? '2px solid #1677ff'
                  : '1px solid #d9d9d9',
                background: isSelected ? '#e6f4ff' : '#fff',
                fontSize: 18,
              }}
              title={iconName}
            >
              {getIconComponent(iconName)}
            </div>
          );
        })}
        {filteredIcons.length === 0 && (
          <div style={{ padding: 8, color: '#999' }}>无匹配图标</div>
        )}
      </div>
    </div>
  );

  return (
    <Popover
      content={content}
      trigger="click"
      open={open}
      onOpenChange={(visible) => {
        setOpen(visible);
        if (!visible) {
          setSearchText('');
        }
      }}
      placement="bottomLeft"
    >
      <Input
        placeholder={placeholder}
        value={value ?? undefined}
        onChange={(e) => onChange?.(e.target.value)}
        readOnly
        prefix={value ? getIconComponent(value) : undefined}
        style={{ cursor: 'pointer' }}
        addonAfter={
          value ? (
            <span
              style={{ cursor: 'pointer', color: '#ff4d4f' }}
              onClick={(e) => {
                e.stopPropagation();
                onChange?.('');
              }}
            >
              清除
            </span>
          ) : null
        }
      />
    </Popover>
  );
}
