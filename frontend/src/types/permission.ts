export type PermissionType = 'menu' | 'button' | 'api';

export interface Permission {
  id: number;
  name: string;
  code: string;
  type: PermissionType;
  parent_id: number | null;
  api_path?: string;
  api_method?: string;
  sort_order: number;
  status: boolean;
  remark?: string;
  children: Permission[];
  created_at: string;
  updated_at: string;
}
