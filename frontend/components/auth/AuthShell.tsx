'use client';

import React from 'react';
import { Activity } from 'lucide-react';

/**
 * Shared two-column authentication shell for Login / Register.
 *
 * Large screens: a low-intensity DietRiskNet context panel on the left
 * (system pipeline) and the auth card on the right.
 * Tablet / mobile: the context panel is hidden and the card centers,
 * preserving the existing single-card layout with no horizontal overflow.
 */

const PIPELINE: { label: string; sub?: string }[] = [
  { label: 'YOLOv8' },
  { label: 'EfficientNet-B3' },
  { label: 'Nutrition + DCI + NIS' },
  { label: 'Risk Analytics', sub: 'XGBoost + Risk Fusion' },
  { label: 'Explainable Guidance' },
];

/** Shared auth input styling — soft green-gray fill, clear focus, good contrast. */
export const authInput =
  'w-full rounded-xl border border-charcoal-border bg-charcoal-light/70 py-3 text-xs font-semibold text-foreground placeholder:text-muted-foreground/75 shadow-[inset_0_1px_2px_rgba(0,0,0,0.25)] focus:outline-none focus:border-brand-blue/70 focus:ring-2 focus:ring-brand-blue/25 transition-all duration-200';

/** Shared label styling for auth fields. */
export const authLabel =
  'text-[10px] font-bold text-muted-foreground uppercase tracking-widest';

/** Shared submit-button styling for auth forms. */
export const authButton =
  'w-full py-3.5 bg-brand-blue hover:bg-brand-blue-hover active:scale-[0.99] font-bold text-white rounded-xl text-xs uppercase tracking-wider flex items-center justify-center space-x-2 cursor-pointer shadow-md shadow-brand-blue/15 hover:shadow-lg hover:shadow-brand-blue/25 border border-brand-blue/20 transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue/50 focus-visible:ring-offset-2 focus-visible:ring-offset-charcoal-dark disabled:bg-zinc-800 disabled:text-zinc-500 disabled:cursor-not-allowed disabled:shadow-none disabled:active:scale-100';

export default function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-charcoal-dark text-foreground flex items-center justify-center p-6 relative selection:bg-brand-blue selection:text-white">
      {/* Restrained backdrop (kept very subtle) */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
        <div className="absolute top-1/4 -left-32 h-[480px] w-[480px] rounded-full bg-brand-blue/[0.045] blur-[120px]" />
        <div className="absolute bottom-1/4 -right-32 h-[480px] w-[480px] rounded-full bg-brand-cyan/[0.045] blur-[120px]" />
      </div>

      <div className="relative z-10 w-full max-w-6xl mx-auto grid items-center gap-12 lg:grid-cols-2">
        {/* Left — context panel (large screens only) */}
        <aside className="hidden lg:flex flex-col justify-center">
          <div className="flex items-center space-x-2.5 mb-7">
            <span className="h-9 w-9 rounded-xl bg-brand-blue/10 border border-brand-blue/20 flex items-center justify-center">
              <Activity className="h-5 w-5 text-brand-blue" aria-hidden="true" />
            </span>
            <span className="font-extrabold text-lg tracking-wide bg-gradient-to-r from-brand-blue to-brand-cyan bg-clip-text text-transparent">
              DietRiskNet
            </span>
          </div>

          <h1 className="text-3xl font-extrabold tracking-tight text-foreground leading-[1.15]">
            AI-Assisted Dietary
            <br />
            Intelligence
          </h1>
          <p className="mt-3 text-sm text-muted-foreground leading-relaxed max-w-sm">
            From meal recognition to personalized dietary risk insights.
          </p>

          <div className="mt-10">
            {PIPELINE.map((step, i) => (
              <div key={step.label} className="flex items-start">
                <div className="flex flex-col items-center mr-4" aria-hidden="true">
                  <span className="mt-1.5 h-2 w-2 rounded-full bg-brand-blue/45" />
                  {i < PIPELINE.length - 1 && (
                    <span className="mt-1.5 w-px h-4 bg-brand-blue/15" />
                  )}
                </div>
                <div className="pb-1">
                  <span className="text-xs font-semibold text-muted-foreground leading-6">
                    {step.label}
                  </span>
                  {step.sub && (
                    <span className="block text-[10px] font-medium text-muted-foreground/55 leading-4">
                      {step.sub}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          <p className="mt-10 text-[9px] font-medium uppercase tracking-[0.16em] text-muted-foreground/45">
            YOLOv8 · EfficientNet-B3 · XGBoost · DCI · NIS
          </p>
        </aside>

        {/* Right — auth card */}
        <div className="flex justify-center">{children}</div>
      </div>
    </div>
  );
}
