import request from './request';
import type { ApiResponse, UserInfo } from '@/types';

export interface LoginParams {
  username: string;
  password: string;
}

export interface LoginResult {
  access_token: string;
  refresh_token: string;
}

export async function login(params: LoginParams): Promise<ApiResponse<LoginResult>> {
  return request.post('/auth/login', params);
}

export async function refreshToken(
  refreshTokenValue: string,
): Promise<ApiResponse<LoginResult>> {
  return request.post('/auth/refresh', { refresh_token: refreshTokenValue });
}

export async function getCurrentUser(): Promise<ApiResponse<UserInfo>> {
  return request.get('/auth/me');
}
