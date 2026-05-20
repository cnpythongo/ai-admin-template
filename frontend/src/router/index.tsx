import { lazy, Suspense } from 'react';
import { Navigate, useRoutes, type RouteObject } from 'react-router-dom';
import AuthGuard from './auth_guard';

const Home = lazy(() => import('@/pages/home'));
const Login = lazy(() => import('@/pages/login'));
const UserPage = lazy(() => import('@/pages/user'));
const DepartmentPage = lazy(() => import('@/pages/department'));
const RolePage = lazy(() => import('@/pages/role'));
const PermissionPage = lazy(() => import('@/pages/permission'));
const MenuPage = lazy(() => import('@/pages/menu'));
const SystemConfigPage = lazy(() => import('@/pages/system-config'));
const OperationLogPage = lazy(() => import('@/pages/operation-log'));
const ProfilePage = lazy(() => import('@/pages/profile'));

const routes: RouteObject[] = [
  {
    path: '/login',
    element: (
      <Suspense fallback={null}>
        <Login />
      </Suspense>
    ),
  },
  {
    path: '/',
    element: (
      <AuthGuard>
        <Suspense fallback={null}>
          <Home />
        </Suspense>
      </AuthGuard>
    ),
    children: [
      // Default redirect: root → user management
      { index: true, element: <Navigate to="/system/user" replace /> },
      // System management pages
      {
        path: 'system/user',
        element: <Suspense fallback={null}><UserPage /></Suspense>,
      },
      {
        path: 'system/department',
        element: <Suspense fallback={null}><DepartmentPage /></Suspense>,
      },
      {
        path: 'system/role',
        element: <Suspense fallback={null}><RolePage /></Suspense>,
      },
      {
        path: 'system/permission',
        element: <Suspense fallback={null}><PermissionPage /></Suspense>,
      },
      {
        path: 'system/menu',
        element: <Suspense fallback={null}><MenuPage /></Suspense>,
      },
      {
        path: 'system/config',
        element: <Suspense fallback={null}><SystemConfigPage /></Suspense>,
      },
      {
        path: 'system/log',
        element: <Suspense fallback={null}><OperationLogPage /></Suspense>,
      },
      // Profile page
      {
        path: 'profile',
        element: <Suspense fallback={null}><ProfilePage /></Suspense>,
      },
    ],
  },
];

function AppRouter() {
  const element = useRoutes(routes);
  return element;
}

export default AppRouter;
