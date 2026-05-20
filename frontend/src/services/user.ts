import request from './request';
import type { ApiResponse, PaginatedData } from '@/types';
import type {
  User,
  UserCreateParams,
  UserUpdateParams,
  UserSearchParams,
  UserRoleUpdate,
  ProfileUpdateParams,
  PasswordChangeParams,
} from '@/types/user';

export async function getUsers(
  params?: UserSearchParams,
): Promise<ApiResponse<PaginatedData<User>>> {
  return request.get('/users', { params });
}

export async function createUser(
  data: UserCreateParams,
): Promise<ApiResponse<User>> {
  return request.post('/users', data);
}

export async function updateUser(
  id: number,
  data: UserUpdateParams,
): Promise<ApiResponse<User>> {
  return request.put(`/users/${id}`, data);
}

export async function deleteUser(id: number): Promise<ApiResponse<null>> {
  return request.delete(`/users/${id}`);
}

export async function setUserStatus(
  id: number,
  data: { status: boolean },
): Promise<ApiResponse<User>> {
  return request.put(`/users/${id}/status`, data);
}

export async function resetPassword(
  id: number,
): Promise<ApiResponse<{ password: string }>> {
  return request.post(`/users/${id}/reset-password`);
}

export async function assignUserRoles(
  id: number,
  data: UserRoleUpdate,
): Promise<ApiResponse<User>> {
  return request.put(`/users/${id}/roles`, data);
}

export async function assignUserDepartment(
  id: number,
  data: { department_id: number | null },
): Promise<ApiResponse<User>> {
  return request.put(`/users/${id}/department`, data);
}

export async function updateProfile(
  data: ProfileUpdateParams,
): Promise<ApiResponse<User>> {
  return request.put('/auth/me', data);
}

export async function changePassword(
  data: PasswordChangeParams,
): Promise<ApiResponse<null>> {
  return request.put('/auth/me/password', data);
}
