import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth';

interface AuthGuardProps {
  children: React.ReactNode;
  requiredPermissions?: string[];
}

function AuthGuard({ children, requiredPermissions }: AuthGuardProps) {
  const token = useAuthStore((state) => state.token);
  const permissions = useAuthStore((state) => state.permissions);
  const location = useLocation();

  // Not logged in: redirect to login
  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check required permissions
  if (requiredPermissions && requiredPermissions.length > 0) {
    const hasPermission = requiredPermissions.some(
      (perm) => permissions.includes('*') || permissions.includes(perm),
    );
    if (!hasPermission) {
      // No permission: show 403 or redirect
      return <div>403 - 无权限访问</div>;
    }
  }

  return <>{children}</>;
}

export default AuthGuard;
