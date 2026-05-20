export interface OperationLog {
  id: number;
  user_id: number | null;
  username: string | null;
  module: string;
  action: string;
  target_id?: string | null;
  target_name?: string | null;
  ip_address?: string | null;
  request_method?: string | null;
  request_path?: string | null;
  status: number;
  duration_ms?: number | null;
  error_message?: string | null;
  created_at: string;
}

export interface OperationLogSearchParams {
  page?: number;
  page_size?: number;
  username?: string;
  module?: string;
  action?: string;
  status?: number;
  start_time?: string;
  end_time?: string;
}
