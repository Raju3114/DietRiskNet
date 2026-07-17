'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../lib/store';
import Sidebar from './Sidebar';
import { Loader2, Activity } from 'lucide-react';
import { motion } from 'framer-motion';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const token = useAuthStore((state) => state.token);
  const [checking, setChecking] = React.useState(true);

  useEffect(() => {
    if (!token) {
      router.push('/login');
    } else {
      const timer = setTimeout(() => {
        setChecking(false);
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [token, router]);

  if (checking || !token) {
    return (
      <div className="min-h-screen bg-charcoal-dark flex items-center justify-center text-white">
        <div className="flex flex-col items-center space-y-4">
          <div className="relative">
            <Loader2 className="h-10 w-10 animate-spin text-brand-blue" />
            <Activity className="absolute inset-0 m-auto h-4 w-4 text-brand-cyan animate-pulse" />
          </div>
          <span className="text-xs font-semibold uppercase tracking-widest text-zinc-500">Verifying session...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-charcoal-dark text-white flex flex-col lg:flex-row">
      <Sidebar />
      
      {/* Main content wrapper */}
      <main className="flex-grow lg:pl-64 pt-16 lg:pt-0 min-h-screen overflow-y-auto">
        <motion.div 
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="max-w-7xl mx-auto p-6 md:p-8"
        >
          {children}
        </motion.div>
      </main>
    </div>
  );
}
