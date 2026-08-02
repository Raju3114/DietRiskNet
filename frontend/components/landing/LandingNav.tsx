'use client';

import React from 'react';
import Link from 'next/link';
import { Activity } from 'lucide-react';

export default function LandingNav() {
  return (
    <header className="lr-nav z-40">
      <div className="max-w-[1280px] mx-auto w-full px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-3" aria-label="DietRiskNet home">
          <span className="lr-logo-badge h-9 w-9 rounded-xl flex items-center justify-center">
            <Activity className="h-5 w-5 text-gold" aria-hidden="true" />
          </span>
          <span className="font-extrabold text-lg tracking-wider bg-gradient-to-r from-brand-primary to-gold bg-clip-text text-transparent">
            DietRiskNet
          </span>
        </Link>

        <nav className="flex items-center space-x-4" aria-label="Primary">
          <Link
            href="/login"
            className="px-4 py-2 text-xs font-bold uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors"
          >
            Login
          </Link>
          <Link
            href="/register"
            className="px-5 py-2.5 text-xs font-bold uppercase tracking-widest rounded-xl bg-brand-primary text-white shadow-md shadow-brand-primary/20 border border-brand-primary/20 transition-all duration-300 hover:bg-brand-primary-hover hover:-translate-y-0.5"
          >
            Get Started
          </Link>
        </nav>
      </div>
    </header>
  );
}
