import { create } from 'zustand';
import type { UserInfo } from '@/types';
import { getCurrentUser as fetchCurrentUserApi } from '@/services/auth';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  userInfo: UserInfo | null;
  permissions: string[];
  setToken: (token: string | null, refreshToken?: string | null) => void;
  setUserInfo: (userInfo: UserInfo | null) => void;
  setPermissions: (permissions: string[]) => void;
  fetchUserInfo: () => Promise<void>;
  logout: () => void;
}

const getInitialToken = (): string | null => {
  try {
    return localStorage.getItem('token');
  } catch {
    return null;
  }
};

const getInitialRefreshToken = (): string | null => {
  try {
    return localStorage.getItem('refresh_token');
  } catch {
    return null;
  }
};

export const useAuthStore = create<AuthState>((set) => ({
  token: getInitialToken(),
  refreshToken: getInitialRefreshToken(),
  userInfo: null,
  permissions: [],

  setToken: (token, refreshToken) => {
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
    if (refreshToken !== undefined) {
      if (refreshToken) {
        localStorage.setItem('refresh_token', refreshToken);
      } else {
        localStorage.removeItem('refresh_token');
      }
      set({ token, refreshToken });
    } else {
      set({ token });
    }
  },

  setUserInfo: (userInfo) => {
    const permissions = userInfo?.permissions ?? [];
    set({ userInfo, permissions });
  },

  setPermissions: (permissions) => {
    set({ permissions });
  },

  fetchUserInfo: async () => {
    try {
      const response = await fetchCurrentUserApi();
      const userInfo = response.data;
      useAuthStore.getState().setUserInfo(userInfo);
    } catch {
      useAuthStore.getState().logout();
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    set({
      token: null,
      refreshToken: null,
      userInfo: null,
      permissions: [],
    });
  },
}));

export function useIsAuthenticated(): boolean {
  const token = useAuthStore((state) => state.token);
  return token !== null && token.length > 0;
}
