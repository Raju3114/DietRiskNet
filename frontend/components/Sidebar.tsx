'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore, useAppStore } from '../lib/store';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LayoutDashboard, Upload, TrendingUp, History, User, 
  BookOpen, LogOut, Sun, Moon, ShieldAlert, Sparkles, Menu, X, Activity
} from 'lucide-react';

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, clearAuth } = useAuthStore();
  const { theme, toggleTheme } = useAppStore();
  const [isOpen, setIsOpen] = useState(false);

  const menuItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Log Meal', path: '/upload', icon: Upload },
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

  return (
    <>
      {/* Mobile Header Bar */}
      <div className="lg:hidden flex items-center justify-between p-4 bg-charcoal-dark/95 border-b border-charcoal-border backdrop-blur-md text-white z-40 fixed top-0 left-0 right-0 h-16">
        <div className="flex items-center space-x-2">
          <Activity className="h-6 w-6 text-brand-blue animate-pulse" />
          <span className="font-bold text-lg tracking-wide bg-gradient-to-r from-brand-blue to-brand-cyan bg-clip-text text-transparent">DietRiskNet</span>
        </div>
        <div className="flex items-center space-x-2">
          <button 
            onClick={toggleTheme} 
            className="p-2 rounded-lg bg-charcoal-medium border border-charcoal-border text-zinc-300 hover:text-white transition-colors"
          >
            {theme === 'dark' ? <Sun className="h-4.5 w-4.5 text-amber-500" /> : <Moon className="h-4.5 w-4.5 text-brand-blue" />}
          </button>
          <button onClick={toggleMobileMenu} className="p-2 rounded-lg bg-charcoal-medium border border-charcoal-border text-zinc-300 hover:text-white transition-colors">
            {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Sidebar navigation container */}
      <aside className={`
        fixed inset-y-0 left-0 w-64 bg-charcoal-dark/90 backdrop-blur-xl border-r border-charcoal-border flex flex-col justify-between text-zinc-300 z-50 transition-transform duration-300 lg:translate-x-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div>
          {/* Logo Brand Header */}
          <div className="p-6 border-b border-charcoal-border flex items-center space-x-3 justify-between">
            <Link href="/dashboard" className="flex items-center space-x-3">
              <Activity className="h-6 w-6 text-brand-blue glow-blue" />
              <span className="font-extrabold text-lg tracking-wider bg-gradient-to-r from-brand-blue via-brand-cyan to-brand-emerald bg-clip-text text-transparent">
                DIETRISKNET
              </span>
            </Link>
            <button onClick={toggleMobileMenu} className="lg:hidden text-zinc-400 hover:text-white transition-colors">
              <X className="h-5 w-5" />
            </button>
          </div>
 
          {/* User profile capsule */}
          <div className="p-3 border border-charcoal-border bg-charcoal-medium/40 hover:bg-charcoal-medium/60 m-4 rounded-xl flex items-center space-x-3 shadow-sm hover:border-brand-blue/20 transition-all duration-300 cursor-pointer" onClick={() => router.push('/profile')}>
            <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-brand-blue to-brand-cyan flex items-center justify-center text-white font-extrabold text-xs shadow-md shadow-brand-blue/15 shrink-0">
              {(user?.full_name || 'C').charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-[8px] text-brand-blue font-extrabold uppercase tracking-widest block">Clinical Profile</span>
              <span className="text-xs font-bold text-white truncate block">
                {user?.full_name || 'Capstone User'}
              </span>
              <span className="text-[10px] text-zinc-400 truncate block">
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
                  className={`
                    group flex items-center space-x-3.5 px-4 py-3 rounded-xl text-[10px] font-bold uppercase tracking-wider transition-all duration-200 border relative
                    ${isActive 
                      ? 'bg-brand-blue/10 text-white border-brand-blue/25 shadow-sm shadow-brand-blue/5 glow-blue' 
                      : 'border-transparent text-zinc-400 hover:text-white hover:bg-charcoal-medium/50 hover:border-charcoal-border/50'}
                  `}
                >
                  {isActive && (
                    <motion.div 
                      layoutId="activeIndicator"
                      className="absolute left-0 w-1 h-1/2 bg-brand-blue rounded-r"
                      transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    />
                  )}
                  <Icon className={`h-4 w-4 transition-transform duration-200 group-hover:scale-110 ${isActive ? 'text-brand-blue' : 'text-zinc-500 group-hover:text-zinc-350'}`} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>
 
        {/* Foot Control Panel (Theme toggle, log out) */}
        <div className="p-4 border-t border-charcoal-border space-y-2">
          <button 
            onClick={toggleTheme}
            className="flex items-center justify-between w-full px-4 py-3 rounded-xl hover:bg-charcoal-medium/55 text-[10px] font-bold uppercase tracking-wider text-zinc-400 hover:text-white transition-colors border border-transparent hover:border-charcoal-border/50"
          >
            <span className="flex items-center space-x-3.5">
              {theme === 'dark' ? <Sun className="h-4 w-4 text-brand-orange" /> : <Moon className="h-4 w-4 text-brand-blue" />}
              <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
            </span>
            <span className="text-[8px] px-2 py-0.5 rounded bg-charcoal-medium/80 border border-charcoal-border text-zinc-450 uppercase">{theme}</span>
          </button>
          
          <button 
            onClick={handleLogout}
            className="flex items-center space-x-3.5 w-full px-4 py-3 rounded-xl hover:bg-brand-red/10 hover:text-brand-red text-[10px] font-bold uppercase tracking-wider text-zinc-400 transition-colors border border-transparent hover:border-brand-red/20"
          >
            <LogOut className="h-4 w-4 text-brand-red" />
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
