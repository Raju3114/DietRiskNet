'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore, useAppStore } from '../lib/store';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Upload, TrendingUp, History, User,
  BookOpen, LogOut, Sun, Moon, Monitor, ShieldAlert, Sparkles, Menu, X, Activity, Salad
} from 'lucide-react';

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, clearAuth } = useAuthStore();
  const { theme, toggleTheme } = useAppStore();
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Hydration guard: theme/icon markup must match between the SSR pass and the
  // client pass, so we render the theme-dependent bits only after mount.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  const menuItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Log Meal', path: '/upload', icon: Upload },
    { name: 'Nutrition Assistant', path: '/nutrition', icon: Salad },
    { name: 'Disease Risk', path: '/predictions', icon: ShieldAlert },
    { name: 'ExplainDiet Recommendations', path: '/recommendations', icon: Sparkles },
    { name: 'Longitudinal Trends', path: '/trends', icon: TrendingUp },
    { name: 'Meal History', path: '/history', icon: History },
    { name: 'Research Overview', path: '/research', icon: BookOpen },
    { name: 'Profile Settings', path: '/profile', icon: User },
  ];

  const handleLogout = () => {
    clearAuth();
    router.push('/login');
  };

  const toggleMobileMenu = () => {
    setIsOpen(!isOpen);
  };

  const ThemeIcon = !mounted ? null : theme === 'dark' ? Moon : theme === 'system' ? Monitor : Sun;
  const themeLabel = !mounted ? '...' : theme === 'dark' ? 'Dark' : theme === 'system' ? 'System' : 'Light';

  return (
    <>
      {/* Mobile Header Bar */}
      <div className="lg:hidden flex items-center justify-between p-4 bg-sidebar text-sidebar-foreground border-b border-white/10 backdrop-blur-md z-40 fixed top-0 left-0 right-0 h-16">
        <div className="flex items-center space-x-2">
          <Activity className="h-6 w-6 text-gold" />
          <span className="font-bold text-lg tracking-wide bg-gradient-to-r from-sidebar-foreground to-gold bg-clip-text text-transparent">
            DietRiskNet
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme (light / dark / system)"
            className="p-2 rounded-lg bg-white/10 border border-white/10 text-sidebar-foreground hover:bg-white/15 transition-colors"
          >
            {ThemeIcon ? <ThemeIcon className="h-4.5 w-4.5 text-gold-soft" /> : <div className="h-4.5 w-4.5" />}
          </button>
          <button onClick={toggleMobileMenu} aria-label="Toggle navigation menu" className="p-2 rounded-lg bg-white/10 border border-white/10 text-sidebar-foreground hover:bg-white/15 transition-colors">
            {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Sidebar navigation container */}
      <aside className={`
        fixed inset-y-0 left-0 w-64 bg-sidebar text-sidebar-foreground border-r border-white/10 flex flex-col justify-between z-50 transition-transform duration-300 lg:translate-x-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div>
          {/* Logo Brand Header */}
          <div className="p-6 border-b border-white/10 flex items-center space-x-3 justify-between">
            <Link href="/dashboard" className="flex items-center space-x-3">
              <Activity className="h-6 w-6 text-gold" />
              <span className="font-extrabold text-lg tracking-wider bg-gradient-to-r from-sidebar-foreground via-sidebar-foreground to-gold bg-clip-text text-transparent">
                DIETRISKNET
              </span>
            </Link>
            <button onClick={toggleMobileMenu} aria-label="Close menu" className="lg:hidden text-sidebar-muted hover:text-sidebar-foreground transition-colors">
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* User profile capsule */}
          <div className="p-3 border border-white/10 bg-white/10 hover:bg-white/15 m-4 rounded-xl flex items-center space-x-3 shadow-sm transition-all duration-300 cursor-pointer" onClick={() => router.push('/profile')}>
            <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-brand-emerald to-gold flex items-center justify-center text-white font-extrabold text-xs shadow-md shrink-0">
              {(user?.full_name || 'C').charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-[8px] text-gold-soft font-extrabold uppercase tracking-widest block">User Profile</span>
              <span className="text-xs font-bold text-sidebar-foreground truncate block">
                {user?.full_name || 'Capstone User'}
              </span>
              <span className="text-[10px] text-sidebar-muted truncate block">
                {user?.email || 'patient@dietrisknet.org'}
              </span>
            </div>
          </div>

          {/* Links navigation list */}
          <nav className="px-4 py-2 space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.path;
              return (
                <Link
                  key={item.path}
                  href={item.path}
                  onClick={() => setIsOpen(false)}
                  aria-current={isActive ? 'page' : undefined}
                  className={`
                    group flex items-center space-x-3.5 px-4 py-3 rounded-xl text-[10px] font-bold uppercase tracking-wider transition-all duration-200 border relative
                    ${isActive
                      ? 'bg-white/10 text-sidebar-foreground border-white/15'
                      : 'border-transparent text-sidebar-muted hover:text-sidebar-foreground hover:bg-white/5 hover:border-white/10'}
                  `}
                >
                  {isActive && (
                    <motion.span
                      layoutId="activeIndicator"
                      className="absolute left-0 w-1 h-1/2 bg-gold rounded-r"
                      transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    />
                  )}
                  <Icon className={`h-4 w-4 transition-transform duration-200 group-hover:scale-110 ${isActive ? 'text-gold' : 'text-sidebar-muted group-hover:text-sidebar-foreground'}`} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Foot Control Panel (Theme selector, log out) */}
        <div className="p-4 border-t border-white/10 space-y-2">
          <button
            onClick={toggleTheme}
            aria-label={`Theme: ${themeLabel}`}
            className="flex items-center justify-between w-full px-4 py-3 rounded-xl hover:bg-white/5 text-[10px] font-bold uppercase tracking-wider text-sidebar-muted hover:text-sidebar-foreground transition-colors border border-transparent hover:border-white/10"
          >
            <span className="flex items-center space-x-3.5">
              {ThemeIcon ? <ThemeIcon className="h-4 w-4 text-gold-soft" /> : <div className="h-4 w-4" />}
              <span>{!mounted ? 'Mode' : `${themeLabel} Mode`}</span>
            </span>
            <span className="text-[8px] px-2 py-0.5 rounded bg-white/10 border border-white/10 text-sidebar-muted uppercase">
              {!mounted ? '...' : theme}
            </span>
          </button>

          <button
            onClick={handleLogout}
            className="flex items-center space-x-3.5 w-full px-4 py-3 rounded-xl hover:bg-white/5 hover:text-brand-red text-[10px] font-bold uppercase tracking-wider text-sidebar-muted transition-colors border border-transparent hover:border-white/10"
          >
            <LogOut className="h-4 w-4 text-sidebar-muted" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Mobile backdrop shadow */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={toggleMobileMenu}
            className="fixed inset-0 bg-black/70 z-30 lg:hidden backdrop-blur-sm"
          />
        )}
      </AnimatePresence>
    </>
  );
}
