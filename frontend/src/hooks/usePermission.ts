import { useAuthStore } from '@/stores/auth';

export function usePermission() {
  const permissions = useAuthStore((state) => state.permissions);
  const isSuperuser = useAuthStore((state) => state.userInfo?.is_superuser);

  const hasPermission = (perm: string): boolean => {
    if (isSuperuser) return true;
    return permissions.includes('*') || permissions.includes(perm);
  };

  const hasAnyPermission = (...perms: string[]): boolean => {
    if (isSuperuser) return true;
    return perms.some((perm) => permissions.includes(perm));
  };

  const hasAllPermissions = (...perms: string[]): boolean => {
    if (isSuperuser) return true;
    return perms.every((perm) => permissions.includes(perm));
  };

  return {
    permissions,
    isSuperuser,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
  };
}
