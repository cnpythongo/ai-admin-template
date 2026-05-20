import type React from 'react';
import { useAuthStore } from '@/stores/auth';

interface PermissionGateProps {
  perm: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

function PermissionGate({ perm, children, fallback = null }: PermissionGateProps) {
  const permissions = useAuthStore((state) => state.permissions);
  const isSuperuser = useAuthStore((state) => state.userInfo?.is_superuser);

  // Superusers have all permissions
  if (isSuperuser || permissions.includes('*') || permissions.includes(perm)) {
    return <>{children}</>;
  }

  return <>{fallback}</>;
}

export default PermissionGate;
