import request from './request';
import type { ApiResponse } from '@/types';
import type { ConfigGroup, SystemConfig } from '@/types/system_config';

export async function getConfigGroups(): Promise<ApiResponse<ConfigGroup[]>> {
  return request.get('/system-configs/groups');
}

export async function getConfigsByGroup(
  group: string,
): Promise<ApiResponse<SystemConfig[]>> {
  return request.get('/system-configs', { params: { group } });
}

export async function updateConfig(
  id: number,
  value: string | number | boolean | Record<string, unknown> | unknown[],
): Promise<ApiResponse<SystemConfig>> {
  return request.put(`/system-configs/${id}`, { value });
}

export async function refreshConfigCache(): Promise<ApiResponse<{ count: number }>> {
  return request.post('/system-configs/refresh-cache');
}
