'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../lib/store';
import { api } from '../../services/api';
import { motion } from 'framer-motion';
import { Activity, Mail, Lock, Eye, EyeOff, Loader2, ArrowRight } from 'lucide-react';
import AuthShell, { authInput, authLabel, authButton } from '../../components/auth/AuthShell';

export default function LoginPage() {
  const router = useRouter();
  const { setAuth, token } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Redirect if already logged in
  React.useEffect(() => {
    if (token) {
      router.push('/dashboard');
    }
  }, [token, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await api.login({ email, password });
      setAuth(res.access_token, res.refresh_token, {
        id: res.user_id,
        email: res.email,
        full_name: res.full_name,
      });
      router.push('/dashboard');
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="w-full max-w-md glass-panel p-8 sm:p-9 rounded-3xl border border-charcoal-border shadow-[0_28px_70px_-32px_rgba(0,0,0,0.7)] ring-1 ring-white/[0.04]"
      >
        {/* Brand logo */}
        <div className="flex flex-col items-center justify-center text-center mb-8">
          <Link href="/" className="flex items-center space-x-2.5 mb-3" aria-label="DietRiskNet home">
            <Activity className="h-8 w-8 text-brand-blue glow-blue animate-pulse" aria-hidden="true" />
            <span className="font-bold text-2xl tracking-wide bg-gradient-to-r from-brand-blue to-brand-cyan bg-clip-text text-transparent">DietRiskNet</span>
          </Link>
          <h2 className="text-lg font-bold text-foreground uppercase tracking-wider">Welcome Back</h2>
          <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed max-w-xs">
            Access your dietary insights, meal history, and personalized risk analytics.
          </p>
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            role="alert"
            className="mb-6 p-4 rounded-xl bg-brand-red/10 border border-brand-red/20 text-xs text-brand-red font-semibold uppercase tracking-wider"
          >
            {error}
          </motion.div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Email field */}
          <div className="space-y-1.5">
            <label htmlFor="login-email" className={authLabel}>Email Address</label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-muted-foreground" aria-hidden="true" />
              <input
                id="login-email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className={`${authInput} pl-11 pr-4`}
              />
            </div>
          </div>

          {/* Password field */}
          <div className="space-y-1.5">
            <label htmlFor="login-password" className={authLabel}>Password</label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-muted-foreground" aria-hidden="true" />
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className={`${authInput} pl-11 pr-11`}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                aria-pressed={showPassword}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-charcoal-light/70 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue/40 transition-colors duration-200"
              >
                {showPassword ? <EyeOff className="h-4 w-4" aria-hidden="true" /> : <Eye className="h-4 w-4" aria-hidden="true" />}
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <button type="submit" disabled={loading} className={authButton}>
            {loading ? (
              <>
                <Loader2 className="h-4.5 w-4.5 animate-spin" />
                <span>Validating credentials...</span>
              </>
            ) : (
              <>
                <span>Sign In</span>
                <ArrowRight className="h-4.5 w-4.5" />
              </>
            )}
          </button>
        </form>

        <p className="mt-8 text-center text-xs text-muted-foreground">
          Don&apos;t have an account?{' '}
          <Link href="/register" className="text-brand-blue hover:text-brand-blue-hover font-bold underline underline-offset-2 transition-colors">
            Register
          </Link>
        </p>
      </motion.div>
    </AuthShell>
  );
}
