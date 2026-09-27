export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  role: 'USER' | 'ADMIN';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  user_id: string;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuthState {
  token: string | null;
  user: User | null;
}

const TOKEN_KEY = 'avom_access_token';
const USER_KEY = 'avom_user_data';
const ACTIVE_PROJECT_KEY = 'avom_active_project';

export const getStoredAuth = (): AuthState => {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    const userStr = localStorage.getItem(USER_KEY);
    const user = userStr ? JSON.parse(userStr) : null;
    return { token, user };
  } catch {
    return { token: null, user: null };
  }
};

export const setStoredAuth = (token: string, user: User) => {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

export const clearStoredAuth = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

export const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return {};
  return {
    Authorization: `Bearer ${token}`
  };
};

export const getActiveProject = (): { id: string; name: string } => {
  try {
    const raw = localStorage.getItem(ACTIVE_PROJECT_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    // fallback
  }
  return { id: 'default-proj', name: 'Default Production Workspace' };
};

export const setActiveProject = (id: string, name: string) => {
  localStorage.setItem(ACTIVE_PROJECT_KEY, JSON.stringify({ id, name }));
  window.dispatchEvent(new Event('avom_active_project_changed'));
};
