import { useAuthStore } from '../lib/store';

let rawBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Self-healing fallback: If running in browser on a production domain but base is localhost,
// dynamically switch to the production Render backend URL.
if (typeof window !== 'undefined' && 
    window.location.hostname !== 'localhost' && 
    window.location.hostname !== '127.0.0.1' && 
    rawBase.includes('localhost')) {
  console.warn('[api] Running in production but API_BASE points to localhost. Falling back to production Render backend.');
  rawBase = 'https://dietrisknet-backend.onrender.com/api';
}

// Normalize trailing slash
rawBase = rawBase.replace(/\/+$/, '');
// Ensure it ends with /api if it doesn't already
if (!rawBase.endsWith('/api') && !rawBase.includes('/api/')) {
  rawBase = `${rawBase}/api`;
}
const API_BASE = rawBase;

async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const fullUrl = `${API_BASE}${cleanEndpoint}`;

  console.log(`[apiFetch] Initiating request: ${options.method || 'GET'} ${fullUrl}`);

  let tokenState;
  try {
    tokenState = useAuthStore.getState();
  } catch (storeError) {
    console.error('[apiFetch] Failed to retrieve auth store state:', storeError);
  }

  const { token, refreshToken, setAuth, clearAuth } = tokenState || { token: null, refreshToken: null, setAuth: () => {}, clearAuth: () => {} };
  
  const headers = new Headers(options.headers || {});
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    console.warn(`[apiFetch] Aborting request to ${fullUrl} due to 15s timeout`);
    controller.abort();
  }, 15000);

  const finalOptions = {
    ...options,
    headers,
    signal: controller.signal,
  };

  console.log(`[apiFetch] Fetch options for ${fullUrl}:`, {
    method: finalOptions.method || 'GET',
    headers: Object.fromEntries(headers.entries()),
    bodyLength: finalOptions.body ? (typeof finalOptions.body === 'string' ? finalOptions.body.length : 'binary') : 0,
  });

  let response;
  try {
    response = await fetch(fullUrl, finalOptions);
    clearTimeout(timeoutId);
    console.log(`[apiFetch] Response status for ${fullUrl}: ${response.status} ${response.statusText}`);
  } catch (fetchErr: any) {
    clearTimeout(timeoutId);
    if (fetchErr.name === 'AbortError') {
      throw new Error('API request timed out. The server might be starting up, please try again in a few seconds.');
    }
    console.error(`[apiFetch] Fetch failed for ${fullUrl} with error:`, fetchErr);
    throw fetchErr;
  }

  // Try refreshing token once if unauthorized
  if (response.status === 401 && refreshToken) {
    console.log(`[apiFetch] Unauthorized (401). Attempting token refresh...`);
    try {
      const refreshUrl = `${API_BASE}/auth/refresh`;
      const refreshResponse = await fetch(refreshUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      console.log(`[apiFetch] Token refresh response status: ${refreshResponse.status}`);
      if (refreshResponse.ok) {
        const refreshData = await refreshResponse.json();
        setAuth(refreshData.access_token, refreshData.refresh_token, {
          id: refreshData.user_id,
          email: refreshData.email,
          full_name: refreshData.full_name,
        });

        // Retry original request
        headers.set('Authorization', `Bearer ${refreshData.access_token}`);
        console.log(`[apiFetch] Retrying original request to ${fullUrl} with new token`);
        response = await fetch(fullUrl, {
          ...options,
          headers,
        });
        console.log(`[apiFetch] Retried response status: ${response.status}`);
      } else {
        console.warn(`[apiFetch] Token refresh failed with status ${refreshResponse.status}. Clearing auth.`);
        clearAuth();
      }
    } catch (refreshErr) {
      console.error(`[apiFetch] Exception during token refresh:`, refreshErr);
      clearAuth();
    }
  }

  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errorData = await response.json();
      console.error(`[apiFetch] Error response payload for ${fullUrl}:`, errorData);
      errorDetail = errorData.detail || errorDetail;
    } catch (jsonErr) {
      console.warn(`[apiFetch] Failed to parse error response JSON for ${fullUrl}:`, jsonErr);
    }
    throw new Error(errorDetail);
  }

  try {
    const data = await response.json();
    console.log(`[apiFetch] Request successful for ${fullUrl}. Returning parsed JSON.`);
    return data;
  } catch (jsonErr) {
    console.error(`[apiFetch] Failed to parse successful response JSON for ${fullUrl}:`, jsonErr);
    throw jsonErr;
  }
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
