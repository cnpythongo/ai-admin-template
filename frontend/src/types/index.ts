export interface ApiResponse<T> {
  code: number;
  data: T;
  message: string;
}

export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface UserInfo {
  id: number;
  username: string;
  nickname?: string;
  avatar?: string;
  email?: string;
  phone?: string;
  is_superuser?: boolean;
  department_id?: number | null;
  department_name?: string | null;
  roles?: string[];
  permissions?: string[];
  created_at?: string;
}

// Re-export permission types
export type { PermissionType, Permission } from './permission';

// Re-export menu types
export type { Menu, UserMenu, MenuCreateParams, MenuUpdateParams } from './menu';
