'use client';

import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAppStore } from '../lib/store';

export default function ClientProviders({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false,
        retry: 1,
      },
    },
  }));

  const theme = useAppStore((state) => state.theme);

  // Apply Light / Dark / System theme to the <html> element.
  useEffect(() => {
    const root = window.document.documentElement;
    const apply = (mode: 'light' | 'dark') => {
      if (mode === 'dark') {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    };

    if (theme === 'system') {
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      const onSystemChange = (e: MediaQueryListEvent) =>
        apply(e.matches ? 'dark' : 'light');
      apply(mq.matches ? 'dark' : 'light');
      mq.addEventListener('change', onSystemChange);
      return () => mq.removeEventListener('change', onSystemChange);
    }

    apply(theme);
  }, [theme]);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
