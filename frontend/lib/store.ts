import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, MealAnalysis } from '../types';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  hasHydrated: boolean;
  setHasHydrated: (state: boolean) => void;
  setAuth: (token: string, refreshToken: string, user: User) => void;
  clearAuth: () => void;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      user: null,
      hasHydrated: false,
      setHasHydrated: (hasHydrated) => set({ hasHydrated }),
      setAuth: (token, refreshToken, user) => set({ token, refreshToken, user }),
      clearAuth: () => set({ token: null, refreshToken: null, user: null }),
      updateUser: (userData) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...userData } : null,
        })),
    }),
    {
      name: 'dietrisknet-auth',
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);

export type ThemeMode = 'light' | 'dark' | 'system';

interface AppState {
  currentAnalysis: MealAnalysis | null;
  setCurrentAnalysis: (analysis: MealAnalysis | null) => void;
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
  hasHydrated: boolean;
  setHasHydrated: (state: boolean) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      currentAnalysis: null,
      setCurrentAnalysis: (analysis) => set({ currentAnalysis: analysis }),
      theme: 'system',
      setTheme: (theme) => set({ theme }),
      hasHydrated: false,
      setHasHydrated: (hasHydrated) => set({ hasHydrated }),
      // Cycle light -> dark -> system (three-state selector).
      toggleTheme: () =>
        set((state) => ({
          theme:
            state.theme === 'light' ? 'dark'
            : state.theme === 'dark' ? 'system'
            : 'light',
        })),
    }),
    {
      name: 'dietrisknet-app',
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);

