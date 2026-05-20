import request from './request';
import type { ApiResponse, PaginatedData } from '@/types';
import type {
  Role,
  RoleCreateParams,
  RoleUpdateParams,
  RolePermissionUpdateParams,
  RoleUserItem,
  RoleSearchParams,
} from '@/types/role';

export async function getRoles(
  params?: RoleSearchParams,
): Promise<ApiResponse<PaginatedData<Role>>> {
  return request.get('/roles', { params });
}

export async function createRole(
  data: RoleCreateParams,
): Promise<ApiResponse<Role>> {
  return request.post('/roles', data);
}

export async function updateRole(
  id: number,
  data: RoleUpdateParams,
): Promise<ApiResponse<Role>> {
  return request.put(`/roles/${id}`, data);
}

export async function deleteRole(id: number): Promise<ApiResponse<null>> {
  return request.delete(`/roles/${id}`);
}

export async function assignPermissions(
  id: number,
  data: RolePermissionUpdateParams,
): Promise<ApiResponse<null>> {
  return request.put(`/roles/${id}/permissions`, data);
}

export async function getRoleUsers(
  id: number,
  params?: { page?: number; page_size?: number },
): Promise<ApiResponse<PaginatedData<RoleUserItem>>> {
  return request.get(`/roles/${id}/users`, { params });
}

export async function getRolePermissionIds(
  id: number,
): Promise<ApiResponse<{ permission_ids: number[] }>> {
  return request.get(`/roles/${id}/permissions`);
}
