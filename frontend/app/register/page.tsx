'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../../lib/store';
import { api } from '../../services/api';
import { motion } from 'framer-motion';
import { Activity, Mail, Lock, User, Loader2, ArrowRight } from 'lucide-react';

export default function RegisterPage() {
  const router = useRouter();
  const { setAuth, token } = useAuthStore();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
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
      const res = await api.register({
        email,
        password,
        full_name: fullName,
      });
      setAuth(res.access_token, res.refresh_token, {
        id: res.user_id,
        email: res.email,
        full_name: res.full_name,
      });
      router.push('/dashboard');
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error.message || 'Registration failed. Try a different email.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-charcoal-dark text-white flex items-center justify-center p-6 selection:bg-brand-blue selection:text-white relative">
      {/* Glow Backdrops */}
      <div className="absolute inset-0 bg-brand-blue/5 rounded-full blur-[120px] pointer-events-none w-[400px] h-[400px] top-1/4 left-1/4" />
      <div className="absolute inset-0 bg-brand-cyan/5 rounded-full blur-[120px] pointer-events-none w-[400px] h-[400px] bottom-1/4 right-1/4" />
      
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="w-full max-w-md glass-panel p-8 rounded-3xl z-10 shadow-2xl relative"
      >
        {/* Brand logo */}
        <div className="flex flex-col items-center justify-center text-center mb-8">
          <Link href="/" className="flex items-center space-x-2.5 mb-3">
            <Activity className="h-8 w-8 text-brand-blue glow-blue animate-pulse" />
            <span className="font-bold text-2xl tracking-wide bg-gradient-to-r from-brand-blue to-brand-cyan bg-clip-text text-transparent">DietRiskNet</span>
          </Link>
          <h2 className="text-lg font-bold text-zinc-300 uppercase tracking-wider">Initialize Profile</h2>
          <p className="text-xs text-zinc-500 mt-1">Configure diagnostic clinical variables.</p>
        </div>

        {error && (
          <motion.div 
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 rounded-xl bg-brand-red/10 border border-brand-red/20 text-xs text-brand-red font-semibold uppercase tracking-wider"
          >
            {error}
          </motion.div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Full name field */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Full Name</label>
            <div className="relative">
              <User className="absolute left-4 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-zinc-500" />
              <input 
                type="text" 
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Dr. Naveen Kumar"
                className="w-full bg-charcoal-dark border border-charcoal-border focus:border-brand-blue/60 focus:ring-1 focus:ring-brand-blue/30 rounded-xl py-3 pl-11 pr-4 text-xs font-semibold text-white focus:outline-none transition-all placeholder:text-zinc-600"
              />
            </div>
          </div>

          {/* Email field */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-zinc-500" />
              <input 
                type="email" 
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="patient@dietrisknet.org"
                className="w-full bg-charcoal-dark border border-charcoal-border focus:border-brand-blue/60 focus:ring-1 focus:ring-brand-blue/30 rounded-xl py-3 pl-11 pr-4 text-xs font-semibold text-white focus:outline-none transition-all placeholder:text-zinc-600"
              />
            </div>
          </div>

          {/* Password field */}
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Password</label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-zinc-500" />
              <input 
                type="password" 
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 6 characters"
                className="w-full bg-charcoal-dark border border-charcoal-border focus:border-brand-blue/60 focus:ring-1 focus:ring-brand-blue/30 rounded-xl py-3 pl-11 pr-4 text-xs font-semibold text-white focus:outline-none transition-all placeholder:text-zinc-600"
              />
            </div>
          </div>

          {/* Submit Button */}
          <button 
            type="submit" 
            disabled={loading}
            className="w-full py-3.5 bg-brand-blue hover:bg-brand-blue-hover transition-colors font-bold text-white rounded-xl text-xs uppercase tracking-wider flex items-center justify-center space-x-2 cursor-pointer shadow-md shadow-brand-blue/15 disabled:bg-zinc-800 disabled:text-zinc-500 disabled:cursor-not-allowed border border-brand-blue/20"
          >
            {loading ? (
              <>
                <Loader2 className="h-4.5 w-4.5 animate-spin" />
                <span>Creating profile record...</span>
              </>
            ) : (
              <>
                <span>Register</span>
                <ArrowRight className="h-4.5 w-4.5" />
              </>
            )}
          </button>
        </form>

        <p className="mt-8 text-center text-xs text-zinc-500">
          Already registered?{' '}
          <Link href="/login" className="text-brand-blue hover:text-brand-blue-hover font-bold underline transition-colors">
            Login
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
