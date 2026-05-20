import request from './request';
import type { ApiResponse, PaginatedData } from '@/types';
import type {
  Department,
  DepartmentCreateParams,
  DepartmentUpdateParams,
  DepartmentUserItem,
} from '@/types/department';

export async function getDepartmentTree(): Promise<ApiResponse<Department[]>> {
  return request.get('/departments/tree');
}

export async function createDepartment(
  data: DepartmentCreateParams,
): Promise<ApiResponse<Department>> {
  return request.post('/departments/', data);
}

export async function updateDepartment(
  id: number,
  data: DepartmentUpdateParams,
): Promise<ApiResponse<Department>> {
  return request.put(`/departments/${id}`, data);
}

export async function deleteDepartment(id: number): Promise<ApiResponse<null>> {
  return request.delete(`/departments/${id}`);
}

export async function getDepartmentUsers(
  id: number,
  params?: { page?: number; page_size?: number },
): Promise<ApiResponse<PaginatedData<DepartmentUserItem>>> {
  return request.get(`/departments/${id}/users`, { params });
}
