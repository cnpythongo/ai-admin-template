export type ConfigValueType = 'string' | 'integer' | 'boolean' | 'json' | 'select';

export interface SystemConfig {
  id: number;
  key: string;
  value: string;
  value_type: ConfigValueType;
  group: string;
  is_sensitive: boolean;
  sort_order: number;
  remark?: string;
  created_at: string;
  updated_at: string;
}

export interface ConfigGroup {
  name: string;
  code: string;
}
