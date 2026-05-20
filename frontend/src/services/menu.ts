import request from './request';
import type { ApiResponse } from '@/types';
import type {
  Menu,
  MenuCreateParams,
  MenuUpdateParams,
  UserMenu,
} from '@/types/menu';

export type { MenuCreateParams, MenuUpdateParams };

export async function getMenuTree(): Promise<ApiResponse<Menu[]>> {
  return request.get('/menus/tree');
}

export async function getUserMenus(): Promise<ApiResponse<UserMenu[]>> {
  return request.get('/menus/user-menus');
}

export async function createMenu(
  data: MenuCreateParams,
): Promise<ApiResponse<Menu>> {
  return request.post('/menus', data);
}

export async function updateMenu(
  id: number,
  data: MenuUpdateParams,
): Promise<ApiResponse<Menu>> {
  return request.put(`/menus/${id}`, data);
}

export async function deleteMenu(id: number): Promise<ApiResponse<null>> {
  return request.delete(`/menus/${id}`);
}
