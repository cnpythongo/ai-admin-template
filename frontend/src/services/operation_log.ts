import request from './request';
import type { ApiResponse, PaginatedData } from '@/types';
import type {
  OperationLog,
  OperationLogSearchParams,
} from '@/types/operation_log';

export async function getOperationLogs(
  params?: OperationLogSearchParams,
): Promise<ApiResponse<PaginatedData<OperationLog>>> {
  return request.get('/operation-logs', { params });
}

export async function getLogModules(): Promise<ApiResponse<string[]>> {
  return request.get('/operation-logs/modules');
}

export async function getLogActions(
  module?: string,
): Promise<ApiResponse<string[]>> {
  return request.get('/operation-logs/actions', { params: { module } });
}
