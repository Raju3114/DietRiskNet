'use client';

import React from 'react';
import {
  Sparkles,
  HeartPulse,
  Salad,
  MessageCircle,
  Activity,
  CheckCircle2,
  Leaf,
  AlertTriangle,
  HelpCircle,
} from 'lucide-react';
import type { AIDietitian } from '../../types';

/* ------------------------------------------------------------------ *
 * Health-level → design-token mapping
 * ------------------------------------------------------------------ */

interface LevelStyle {
  badge: string;
  gauge: string;
  label: string;
}

const LEVEL_STYLES: Record<string, LevelStyle> = {
  Excellent: {
    badge: 'bg-brand-emerald/10 text-brand-emerald border-brand-emerald/20',
    gauge: 'text-brand-emerald',
    label: 'Excellent',
  },
  Good: {
    badge: 'bg-brand-blue/10 text-brand-blue border-brand-blue/20',
    gauge: 'text-brand-blue',
    label: 'Good',
  },
  Moderate: {
    badge: 'bg-brand-orange/10 text-brand-orange border-brand-orange/20',
    gauge: 'text-brand-orange',
    label: 'Fair',
  },
  Fair: {
    badge: 'bg-brand-orange/10 text-brand-orange border-brand-orange/20',
    gauge: 'text-brand-orange',
    label: 'Fair',
  },
  'Needs improvement': {
    badge: 'bg-brand-red/10 text-brand-red border-brand-red/20',
    gauge: 'text-brand-red',
    label: 'Needs Improvement',
  },
  'Needs Improvement': {
    badge: 'bg-brand-red/10 text-brand-red border-brand-red/20',
    gauge: 'text-brand-red',
    label: 'Needs Improvement',
  },
};

function levelStyleFor(score: number, level?: string): LevelStyle {
  if (level && LEVEL_STYLES[level]) {
    return LEVEL_STYLES[level];
  }
  if (score >= 90) return LEVEL_STYLES.Excellent;
  if (score >= 75) return LEVEL_STYLES.Good;
  if (score >= 50) return LEVEL_STYLES.Moderate;
  return LEVEL_STYLES['Needs improvement'];
}

/* ------------------------------------------------------------------ *
 * Small building blocks
 * ------------------------------------------------------------------ */

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest">
      {children}
    </h3>
  );
}

function IconBadge({
  icon: Icon,
  tone,
}: {
  icon: React.ComponentType<{ className?: string }>;
  tone: string;
  label: string;
}) {
  return (
    <span
      className={`p-2 rounded-lg border ${tone} flex items-center justify-center shrink-0`}
      aria-hidden="true"
    >
      <Icon className="h-4 w-4" />
    </span>
  );
}

function ListItem({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <li className="flex items-start space-x-2.5">
      {icon}
      <span className="text-xs text-foreground leading-relaxed">{text}</span>
    </li>
  );
}

/* ------------------------------------------------------------------ *
 * Circular health score gauge
 * ------------------------------------------------------------------ */

function HealthScoreGauge({
  score,
  levelStyle,
}: {
  score: number;
  levelStyle: LevelStyle;
}) {
  const pct = Math.max(0, Math.min(100, score));
  const radius = 26;
  const circumference = 2 * Math.PI * radius;
  const dash = (pct / 100) * circumference;

  return (
    <div
      className="relative h-28 w-28 shrink-0"
      role="img"
      aria-label={`Health score ${score} out of 100, ${levelStyle.label}`}
    >
      <svg viewBox="0 0 64 64" className="h-full w-full -rotate-90">
        {/* track */}
        <circle
          cx="32"
          cy="32"
          r={radius}
          fill="none"
          strokeWidth="5"
          className="text-charcoal-light/70"
          stroke="currentColor"
        />
        {/* value */}
        <circle
          cx="32"
          cy="32"
          r={radius}
          fill="none"
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference}`}
          className={`${levelStyle.gauge} transition-all duration-500`}
          stroke="currentColor"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-black text-foreground tracking-tight font-mono leading-none">
          {pct}
        </span>
        <span className="text-[8px] text-muted-foreground font-bold uppercase tracking-widest mt-0.5">
          / 100
        </span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ *
 * Loading skeleton
 * ------------------------------------------------------------------ */

function SkeletonLine({ className = '' }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-lg bg-charcoal-light border border-charcoal-border/50 ${className}`}
      aria-hidden="true"
    />
  );
}

export function AIDietitianSkeleton() {
  return (
    <section
      aria-label="AI Dietitian analysis loading"
      className="p-6 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border shadow-md space-y-5"
    >
      <div className="flex items-center space-x-3">
        <SkeletonLine className="h-8 w-8 rounded-lg" />
        <SkeletonLine className="h-4 w-40" />
      </div>
      <div className="flex items-center space-x-5">
        <SkeletonLine className="h-28 w-28 rounded-full" />
        <div className="flex-1 space-y-2">
          <SkeletonLine className="h-3 w-2/3" />
          <SkeletonLine className="h-3 w-1/2" />
          <SkeletonLine className="h-3 w-3/4" />
        </div>
      </div>
      <div className="space-y-2">
        <SkeletonLine className="h-3 w-full" />
        <SkeletonLine className="h-3 w-11/12" />
        <SkeletonLine className="h-3 w-4/5" />
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ *
 * Main card
 * ------------------------------------------------------------------ */

interface AIDietitianCardProps {
  ai: AIDietitian;
  isLoading?: boolean;
}

export default function AIDietitianCard({
  ai,
  isLoading = false,
}: AIDietitianCardProps) {
  const levelStyle = levelStyleFor(ai.health_score, ai.health_level);
  const hasWarnings = ai.warnings.length > 0;

  if (isLoading) {
    return <AIDietitianSkeleton />;
  }

  return (
    <section
      aria-label="AI Dietitian analysis"
      className="rounded-2xl bg-charcoal-medium/50 border border-charcoal-border shadow-md overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center space-x-3 px-6 pt-5 pb-4 border-b border-charcoal-border/50">
        <IconBadge
          icon={Sparkles}
          tone="bg-gold/10 text-gold border-gold/25"
          label="AI Dietitian"
        />
        <div>
          <h2 className="text-sm font-extrabold text-foreground uppercase tracking-wider">
            AI Dietitian
          </h2>
          <p className="text-[9px] text-muted-foreground font-bold uppercase tracking-widest">
            Personalised clinical analysis
          </p>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Health Score + Meal Quality */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-5">
          <HealthScoreGauge score={ai.health_score} levelStyle={levelStyle} />
          <div className="flex-1 space-y-3">
            <div className="flex items-center space-x-2">
              <HeartPulse className="h-4 w-4 text-brand-cyan" aria-hidden="true" />
              <SectionLabel>Health Level</SectionLabel>
              <span
                className={`px-2.5 py-0.5 rounded-full border text-[9px] font-extrabold uppercase tracking-widest ${levelStyle.badge}`}
              >
                {levelStyle.label}
              </span>
            </div>
            <div className="flex items-start space-x-2">
              <Salad className="h-4 w-4 text-brand-emerald mt-0.5 shrink-0" aria-hidden="true" />
              <div>
                <SectionLabel>Meal Quality</SectionLabel>
                <p className="text-xs text-foreground leading-relaxed mt-0.5">
                  {ai.meal_quality || '—'}
                </p>
              </div>
            </div>
            <p className="text-[10px] text-muted-foreground leading-relaxed">
              {ai.health_explanation}
            </p>
          </div>
        </div>

        {/* AI Summary */}
        <div className="p-4 rounded-xl bg-charcoal-dark/50 border border-charcoal-border flex items-start space-x-3">
          <IconBadge
            icon={MessageCircle}
            tone="bg-brand-cyan/10 text-brand-cyan border-brand-cyan/15"
            label="Summary"
          />
          <div>
            <SectionLabel>AI Summary</SectionLabel>
            <p className="text-xs text-foreground leading-relaxed mt-1">{ai.summary}</p>
          </div>
        </div>

        {/* Risk Explanation */}
        <div className="p-4 rounded-xl bg-brand-blue/5 border border-brand-blue/15 flex items-start space-x-3">
          <IconBadge
            icon={Activity}
            tone="bg-brand-blue/10 text-brand-blue border-brand-blue/15"
            label="Risk"
          />
          <div>
            <SectionLabel>Risk Explanation</SectionLabel>
            <p className="text-xs text-foreground leading-relaxed mt-1">
              {ai.risk_explanation}
            </p>
          </div>
        </div>

        {/* Recommendations */}
        {ai.recommendations.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="h-4 w-4 text-brand-emerald" aria-hidden="true" />
              <SectionLabel>Recommendations</SectionLabel>
            </div>
            <ul className="space-y-2.5">
              {ai.recommendations.map((rec, idx) => (
                <ListItem
                  key={`rec-${idx}`}
                  icon={
                    <CheckCircle2
                      className="h-4 w-4 text-brand-emerald mt-0.5 shrink-0"
                      aria-hidden="true"
                    />
                  }
                  text={rec}
                />
              ))}
            </ul>
          </div>
        )}

        {/* Healthier Alternatives */}
        {ai.healthier_alternatives.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Leaf className="h-4 w-4 text-brand-emerald" aria-hidden="true" />
              <SectionLabel>Healthier Alternatives</SectionLabel>
            </div>
            <div className="flex flex-wrap gap-2">
              {ai.healthier_alternatives.map((alt, idx) => (
                <span
                  key={`alt-${idx}`}
                  className="px-3 py-1.5 rounded-xl bg-charcoal-dark border border-charcoal-border text-[10px] font-bold text-brand-emerald uppercase tracking-wider"
                >
                  {alt}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Warnings (only if non-empty) */}
        {hasWarnings && (
          <div
            className="p-4 rounded-xl bg-brand-red/5 border border-brand-red/15 flex items-start space-x-3"
            role="alert"
          >
            <IconBadge
              icon={AlertTriangle}
              tone="bg-brand-red/10 text-brand-red border-brand-red/15"
              label="Warning"
            />
            <ul className="space-y-2">
              {ai.warnings.map((warning, idx) => (
                <ListItem
                  key={`warn-${idx}`}
                  icon={
                    <AlertTriangle
                      className="h-4 w-4 text-brand-red mt-0.5 shrink-0"
                      aria-hidden="true"
                    />
                  }
                  text={warning}
                />
              ))}
            </ul>
          </div>
        )}

        {/* Follow-up questions (chips, no chat yet) */}
        {ai.follow_up_questions.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <HelpCircle className="h-4 w-4 text-brand-blue" aria-hidden="true" />
              <SectionLabel>You may want to ask</SectionLabel>
            </div>
            <div className="flex flex-wrap gap-2">
              {ai.follow_up_questions.map((question, idx) => (
                <button
                  key={`q-${idx}`}
                  type="button"
                  disabled
                  aria-label={`Suggested question: ${question}`}
                  title="Ask AI chat is coming soon"
                  className="px-3 py-2 rounded-xl bg-charcoal-dark border border-charcoal-border text-[10px] font-bold text-brand-blue hover:border-brand-blue/40 transition-all cursor-not-allowed"
                >
                  {question}
                </button>
              ))}
            </div>
            <p className="text-[9px] text-muted-foreground">
              Interactive chat is coming soon.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
