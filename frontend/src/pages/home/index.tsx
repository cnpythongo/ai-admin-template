import { useCallback, useEffect, useMemo, useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Avatar,
  Button,
  Dropdown,
  Layout,
  Menu,
  Spin,
  Tabs,
  Typography,
} from 'antd';
import {
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
} from '@ant-design/icons';
import * as Icons from '@ant-design/icons';
import { useAuthStore } from '@/stores/auth';
import { useTabStore } from '@/stores/tabs';
import { getUserMenus } from '@/services/menu';
import type { UserMenu } from '@/types/menu';
import type { MenuProps } from 'antd';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

function getIconComponent(
  iconName: string | null | undefined,
): React.ReactNode {
  if (!iconName) return null;
  const IconComp = (Icons as unknown as Record<string, React.ComponentType>)[
    iconName
  ];
  if (!IconComp) return null;
  return <IconComp />;
}

function toAntdMenuItems(menus: UserMenu[]): MenuProps['items'] {
  return menus
    .filter((m) => !m.hidden)
    .sort((a, b) => a.sort_order - b.sort_order)
    .map((m) => {
      const children = m.children?.length
        ? toAntdMenuItems(m.children)
        : undefined;
      if (!m.route_path && (!children || children.length === 0)) {
        return null;
      }
      return {
        key: m.route_path ?? m.id.toString(),
        icon: getIconComponent(m.icon),
        label: m.name,
        children,
      } as NonNullable<MenuProps['items']>[number];
    })
    .filter(Boolean);
}

function buildPathLabelMap(menus: UserMenu[]): Record<string, string> {
  const map: Record<string, string> = {};
  function walk(items: UserMenu[]) {
    for (const item of items) {
      if (item.route_path) map[item.route_path] = item.name;
      if (item.children) walk(item.children);
    }
  }
  walk(menus);
  return map;
}

function getTabLabel(
  path: string,
  pathLabelMap: Record<string, string>,
): string {
  if (pathLabelMap[path]) return pathLabelMap[path];
  const segments = path.split('/').filter(Boolean);
  if (segments.length > 0) {
    const last = segments[segments.length - 1];
    return last.charAt(0).toUpperCase() + last.slice(1);
  }
  return path;
}

function HomePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { userInfo, fetchUserInfo, logout } = useAuthStore();
  const { tabs, activeKey, addTab, removeTab, setActiveKey } = useTabStore();
  const [menus, setMenus] = useState<UserMenu[]>([]);
  const [collapsed, setCollapsed] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function init() {
      try {
        if (!userInfo) await fetchUserInfo();
        const res = await getUserMenus();
        if (!cancelled) setMenus(res.data);
      } catch {
        logout();
        navigate('/login', { replace: true });
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void init();
    return () => {
      cancelled = true;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const menuItems = useMemo(() => toAntdMenuItems(menus), [menus]);
  const pathLabelMap = useMemo(() => buildPathLabelMap(menus), [menus]);

  const selectedKeys = useMemo(() => [location.pathname], [location.pathname]);
  const defaultOpenKeys = useMemo(() => {
    const segments = location.pathname.split('/').filter(Boolean);
    const keys: string[] = [];
    for (let i = 1; i < segments.length; i++) {
      keys.push('/' + segments.slice(0, i).join('/'));
    }
    return keys;
  }, [location.pathname]);

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    addTab(key, getTabLabel(key, pathLabelMap));
    navigate(key);
  };

  const handleLogout = useCallback(() => {
    logout();
    navigate('/login', { replace: true });
  }, [logout, navigate]);

  const userDropdownItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
      onClick: () => {
        const path = '/profile';
        addTab(path, '个人中心');
        navigate(path);
      },
    },
    { type: 'divider' },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  const handleTabChange = (key: string) => {
    setActiveKey(key);
    navigate(key);
  };

  const handleTabRemove = (
    targetKey: React.MouseEvent | React.KeyboardEvent | string,
  ) => {
    const key = typeof targetKey === 'string' ? targetKey : '';
    const nextKey = removeTab(key);
    if (nextKey) navigate(nextKey);
  };

  useEffect(() => {
    if (location.pathname && pathLabelMap[location.pathname]) {
      addTab(location.pathname, getTabLabel(location.pathname, pathLabelMap));
    }
  }, [location.pathname, pathLabelMap]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
        }}
      >
        <Spin size="large" />
      </div>
    );
  }

  return (
    <Layout style={{ height: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
        trigger={null}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Text strong style={{ color: '#fff', fontSize: collapsed ? 18 : 20 }}>
            {collapsed ? 'AD' : 'AI Admin'}
          </Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={selectedKeys}
          defaultOpenKeys={defaultOpenKeys}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>

      <Layout style={{ overflow: 'hidden' }}>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed((prev) => !prev)}
          />
          <Dropdown menu={{ items: userDropdownItems }} placement="bottomRight">
            <div
              style={{
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <Avatar icon={<UserOutlined />} />
              <Text>{userInfo?.nickname || userInfo?.username || '用户'}</Text>
            </div>
          </Dropdown>
        </Header>

        <Tabs
          type="editable-card"
          hideAdd
          activeKey={activeKey}
          onChange={handleTabChange}
          onEdit={handleTabRemove}
          size="small"
          style={{ margin: 0, background: '#f5f5f5' }}
          tabBarStyle={{
            margin: 0,
            paddingLeft: 8,
            paddingTop: 4,
            background: '#f5f5f5',
          }}
          items={tabs.map((tab) => ({
            key: tab.key,
            label: tab.label,
            closable: tab.closable,
          }))}
        />

        <Content style={{ flex: 1, overflow: 'auto', background: '#fff' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}

export default HomePage;
