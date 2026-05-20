export interface User {
  id: number;
  username: string;
  nickname?: string | null;
  email?: string | null;
  phone?: string | null;
  avatar?: string | null;
  status: boolean;
  is_superuser: boolean;
  department_id?: number | null;
  department_name?: string | null;
  role_ids: number[];
  role_names: string[];
  created_at: string;
  updated_at: string;
}

export interface UserCreateParams {
  username: string;
  password?: string;
  nickname?: string;
  email?: string;
  phone?: string;
  status?: boolean;
  department_id?: number | null;
  role_ids?: number[];
}

export interface UserUpdateParams {
  nickname?: string;
  email?: string;
  phone?: string;
  status?: boolean;
  department_id?: number | null;
}

export interface UserSearchParams {
  page?: number;
  page_size?: number;
  username?: string;
  nickname?: string;
  email?: string;
  phone?: string;
  status?: boolean;
  department_id?: number;
  role_id?: number;
}

export interface UserStatusUpdate {
  status: boolean;
}

export interface UserRoleUpdate {
  role_ids: number[];
}

export interface ProfileUpdateParams {
  nickname?: string;
  email?: string;
  phone?: string;
}

export interface PasswordChangeParams {
  old_password: string;
  new_password: string;
  confirm_password: string;
}
