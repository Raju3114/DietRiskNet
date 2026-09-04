'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../lib/store';
import LandingNav from '../components/landing/LandingNav';
import HeroSection from '../components/landing/HeroSection';
import PipelineFlow from '../components/landing/PipelineFlow';
import TechnologyPanel from '../components/landing/TechnologyPanel';
import FinalCTA from '../components/landing/FinalCTA';
import '../components/landing/landing.css';

export default function LandingPage() {
  const token = useAuthStore((state) => state.token);
  const hasHydrated = useAuthStore((state) => state.hasHydrated);
  const router = useRouter();

  // Redirect already-authenticated users to the dashboard.
  React.useEffect(() => {
    if (hasHydrated && token) {
      router.replace('/dashboard');
    }
  }, [hasHydrated, token]);

  return (
    <div className="lr-root relative min-h-screen flex flex-col bg-background text-foreground font-sans selection:bg-brand-primary selection:text-white">
      {/* Subtle atmospheric background */}
      <div className="lr-atmos" aria-hidden="true">
        <div className="lr-grid" />
      </div>

      <LandingNav />

      <main className="flex-grow relative">
        <div className="max-w-[1280px] mx-auto w-full px-6">
          <HeroSection />
          <PipelineFlow />
          <TechnologyPanel />
          <FinalCTA />
        </div>
      </main>

      <footer className="relative z-10 border-t border-charcoal-border py-8 text-center text-[9px] uppercase tracking-widest text-muted-foreground w-full">
        <p>
          © 2026 DietRiskNet — AI-assisted dietary risk analytics. Not a medical
          device; consult a healthcare professional for medical decisions.
        </p>
      </footer>
    </div>
  );
}
