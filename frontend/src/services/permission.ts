import request from './request';
import type { ApiResponse, Permission, PermissionType } from '@/types';

export interface CreatePermissionParams {
  name: string;
  code: string;
  type: PermissionType;
  parent_id?: number | null;
  api_path?: string;
  api_method?: string;
  sort_order?: number;
  status?: boolean;
  remark?: string;
}

export interface UpdatePermissionParams {
  name?: string;
  parent_id?: number | null;
  api_path?: string;
  api_method?: string;
  sort_order?: number;
  status?: boolean;
  remark?: string;
}

export async function getPermissionTree(
  type?: PermissionType,
): Promise<ApiResponse<Permission[]>> {
  return request.get('/permissions/tree', { params: { type } });
}

export async function createPermission(
  data: CreatePermissionParams,
): Promise<ApiResponse<Permission>> {
  return request.post('/permissions', data);
}

export async function updatePermission(
  id: number,
  data: UpdatePermissionParams,
): Promise<ApiResponse<Permission>> {
  return request.put(`/permissions/${id}`, data);
}

export async function deletePermission(
  id: number,
): Promise<ApiResponse<null>> {
  return request.delete(`/permissions/${id}`);
}
