export interface Role {
  id: number;
  name: string;
  code: string;
  status: boolean;
  remark?: string | null;
  user_count?: number;
  created_at: string;
  updated_at: string;
}

export interface RoleCreateParams {
  name: string;
  code: string;
  status?: boolean;
  remark?: string;
}

export interface RoleUpdateParams {
  name?: string;
  status?: boolean;
  remark?: string;
}

export interface RolePermissionUpdateParams {
  permission_ids: number[];
}

export interface RoleUserItem {
  id: number;
  username: string;
  nickname?: string | null;
  email?: string | null;
  status: boolean;
}

export interface RoleSearchParams {
  page?: number;
  page_size?: number;
  name?: string;
  status?: boolean;
}
