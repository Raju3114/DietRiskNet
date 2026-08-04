import { useAuthStore } from '../lib/store';

// NEXT_PUBLIC_API_URL is a build-time public environment variable.  In
// production it must point to the deployed backend (e.g. Render), e.g.
// https://<backend-host>/api.  When it is not configured the frontend falls
// back to the local development backend.  No production hostname is
// hard-coded in source.
let rawBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Normalize trailing slash
rawBase = rawBase.replace(/\/+$/, '');
// Ensure it ends with /api if it doesn't already
if (!rawBase.endsWith('/api') && !rawBase.includes('/api/')) {
  rawBase = `${rawBase}/api`;
}
const API_BASE = rawBase;

async function apiFetch(endpoint: string, options: RequestInit & { timeoutMs?: number } = {}) {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  const fullUrl = `${API_BASE}${cleanEndpoint}`;

  // Default request timeout.  The LLM-backed chat endpoints pass a much
  // longer timeout via `timeoutMs` so a slow-but-healthy local Ollama is
  // not aborted mid-generation.
  const timeoutMs = options.timeoutMs ?? 15000;

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
    console.warn(`[apiFetch] Aborting request to ${fullUrl} due to ${timeoutMs}ms timeout`);
    controller.abort();
  }, timeoutMs);

  const finalOptions = {
    ...options,
    headers,
    signal: controller.signal,
  };

  let response;
  try {
    response = await fetch(fullUrl, finalOptions);
    clearTimeout(timeoutId);
  } catch (fetchErr) {
    clearTimeout(timeoutId);
    const isAbort =
      fetchErr instanceof DOMException && fetchErr.name === 'AbortError';
    if (isAbort) {
      throw new Error('API request timed out. The server might be starting up, please try again in a few seconds.');
    }
    console.error(`[apiFetch] Fetch failed for ${fullUrl} with error:`, fetchErr);
    throw fetchErr;
  }

  // Try refreshing token once if unauthorized
  if (response.status === 401 && refreshToken) {
    try {
      const refreshUrl = `${API_BASE}/auth/refresh`;
      const refreshResponse = await fetch(refreshUrl, {
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
        response = await fetch(fullUrl, {
          ...options,
          headers,
        });
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

  // AI Dietitian chat (meal-specific)
  askAI: (mealId: number, message: string) =>
    apiFetch('/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ meal_id: mealId, message }),
      timeoutMs: 90000,
    }),

  // AI Nutrition Assistant (general nutrition coach)
  nutritionChat: (message: string, includeHistory: boolean = true) =>
    apiFetch('/nutrition-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, include_history: includeHistory }),
      timeoutMs: 90000,
    }),

  // Personalized nutrition coach analytics (dashboard)
  getNutritionAnalytics: () => apiFetch('/nutrition/analytics'),

  // Download meal report as PDF
  downloadReport: async (mealId: number): Promise<void> => {
    const token = useAuthStore.getState().token;
    const response = await fetch(`${API_BASE}/report/${mealId}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      throw new Error('Failed to download the meal report.');
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `dietrisknet-meal-${mealId}.pdf`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  },
};
export { API_BASE };
