import { useAuthStore } from '../lib/store';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const { token, refreshToken, setAuth, clearAuth } = useAuthStore.getState();
  
  const headers = new Headers(options.headers || {});
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }

  const finalOptions = {
    ...options,
    headers,
  };

  let response = await fetch(`${API_BASE}${endpoint}`, finalOptions);

  // Try refreshing token once if unauthorized
  if (response.status === 401 && refreshToken) {
    try {
      const refreshResponse = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (refreshResponse.ok) {
        const refreshData = await refreshResponse.json();
        setAuth(refreshData.access_token, refreshData.refresh_token, {
          id: refreshData.user_id,
          email: refreshData.email,
          full_name: refreshData.full_name,
        });

        // Retry original request
        headers.set('Authorization', `Bearer ${refreshData.access_token}`);
        response = await fetch(`${API_BASE}${endpoint}`, {
          ...options,
          headers,
        });
      } else {
        clearAuth();
      }
    } catch {
      clearAuth();
    }
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'API request failed');
  }

  return response.json();
}

export const api = {
  // Auth
  register: (body: Record<string, unknown>) =>
    apiFetch('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),

  login: (body: Record<string, unknown>) =>
    apiFetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),

  logout: (refreshToken: string) =>
    apiFetch('/auth/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),

  // Meal Upload and Analysis
  analyzeMeal: (imageFile: File, notes: string = '') => {
    const formData = new FormData();
    formData.append('file', imageFile);
    formData.append('notes', notes);

    return apiFetch('/analyze-meal', {
      method: 'POST',
      body: formData,
    });
  },

  // User & Dashboard
  getDashboard: () => apiFetch('/dashboard'),
  getHistory: () => apiFetch('/history'),
  getProfile: () => apiFetch('/profile'),
  
  updateProfile: (fullName: string) =>
    apiFetch('/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name: fullName }),
    }),

  updateSettings: (settings: Record<string, unknown>) =>
    apiFetch('/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    }),

  getTrends: (days: number = 30) => apiFetch(`/analytics/trends?days=${days}`),
};
export { API_BASE };
