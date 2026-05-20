export interface Department {
  id: number;
  name: string;
  parent_id: number | null;
  sort_order: number;
  status: boolean;
  children: Department[];
  created_at: string;
  updated_at: string;
}

export interface DepartmentCreateParams {
  name: string;
  parent_id?: number | null;
  sort_order?: number;
  status?: boolean;
}

export interface DepartmentUpdateParams {
  name?: string;
  parent_id?: number | null;
  sort_order?: number;
  status?: boolean;
}

export interface DepartmentUserItem {
  id: number;
  username: string;
  nickname?: string | null;
  email?: string | null;
  phone?: string | null;
  status: boolean;
  created_at?: string;
}
