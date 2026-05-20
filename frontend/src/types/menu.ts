export interface Menu {
  id: number;
  name: string;
  icon?: string | null;
  route_path?: string | null;
  component?: string | null;
  parent_id: number | null;
  sort_order: number;
  hidden: boolean;
  is_external_link: boolean;
  status: boolean;
  permission_ids: number[];
  children: Menu[];
  created_at: string;
  updated_at: string;
}

export interface UserMenu {
  id: number;
  name: string;
  icon?: string | null;
  route_path?: string | null;
  component?: string | null;
  parent_id: number | null;
  sort_order: number;
  hidden: boolean;
  is_external_link: boolean;
  children: UserMenu[];
}

export interface MenuCreateParams {
  name: string;
  icon?: string | null;
  route_path: string;
  component?: string | null;
  parent_id?: number | null;
  sort_order?: number;
  hidden?: boolean;
  is_external_link?: boolean;
  permission_ids?: number[];
}

export interface MenuUpdateParams {
  name?: string;
  icon?: string | null;
  route_path?: string;
  component?: string | null;
  parent_id?: number | null;
  sort_order?: number;
  hidden?: boolean;
  is_external_link?: boolean;
  permission_ids?: number[];
}
