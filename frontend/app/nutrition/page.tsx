'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Send, Loader2, Salad, Sparkles, Flame, Beef, Wheat, Droplet, Target, TrendingUp, Activity } from 'lucide-react';
import ProtectedRoute from '../../components/ProtectedRoute';
import { api } from '../../services/api';
import type { NutritionAnalytics } from '../../types';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface QuickAction {
  emoji: string;
  label: string;
  prompt: string;
}

const QUICK_ACTIONS: QuickAction[] = [
  { emoji: '📊', label: 'Weekly Summary', prompt: 'Summarize my weekly nutrition based on my recent meals.' },
  { emoji: '🎯', label: 'My Goals', prompt: 'What goals should I set based on my recent meals?' },
  { emoji: '📈', label: 'Progress', prompt: 'How is my progress toward my nutrition goals?' },
  { emoji: '🥗', label: 'Meal Suggestions', prompt: 'Suggest healthy meals based on my eating habits.' },
  { emoji: '🛒', label: 'Grocery List', prompt: 'Generate a healthy grocery list for me.' },
  { emoji: '💧', label: 'Hydration', prompt: 'How can I improve my hydration?' },
  { emoji: '❤️', label: 'Improve My Diet', prompt: 'How can I improve my overall diet?' },
];

const RISK_TREND_DIRECTION: Record<string, string> = {
  decreased: '↓ decreasing',
  increased: '↑ increasing',
  stable: '↔ steady',
};

/** Human-readable trend arrow for an estimated-risk direction. */
const riskDirectionLabel = (direction: string): string =>
  RISK_TREND_DIRECTION[direction] ?? direction;

const SUGGESTED_PROMPTS = [
  'What is a balanced diet?',
  'Healthy cooking methods?',
  'Tips to reduce sugar intake',
  'Vegetarian meal ideas',
];

const FRIENDLY_ERROR =
  'Sorry, I could not get an answer right now. Please try again in a moment.';

export default function NutritionPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [analytics, setAnalytics] = useState<NutritionAnalytics | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .getNutritionAnalytics()
      .then((res) => setAnalytics(res?.analytics ?? null))
      .catch(() => setAnalytics(null))
      .finally(() => setAnalyticsLoading(false));
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isSending]);

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || isSending) return;

    setMessages((prev) => [...prev, { role: 'user', content: trimmed }]);
    setInput('');
    setIsSending(true);

    try {
      const res = await api.nutritionChat(trimmed);
      const reply = res && typeof res.reply === 'string' ? res.reply : FRIENDLY_ERROR;
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }]);
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: FRIENDLY_ERROR }]);
    } finally {
      setIsSending(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <ProtectedRoute>
      <div className="space-y-6 animate-fade-in font-sans max-w-4xl mx-auto w-full">
        {/* Header */}
        <div>
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full border border-gold/30 bg-gold/10 text-brand-emerald text-[9px] font-bold uppercase tracking-widest mb-3 w-fit">
            <Sparkles className="h-3.5 w-3.5 text-gold" />
            <span>Personalized AI Nutrition Coach</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground flex items-center space-x-3">
            <Salad className="h-8 w-8 text-brand-emerald" />
            <span>Nutrition Coach</span>
          </h1>
          <p className="text-muted-foreground text-[10px] font-extrabold uppercase tracking-wider mt-1">
            Personalized insights from your meal history — meal planning, healthy eating, and dietary guidance.
          </p>
        </div>

        {/* Dashboard */}
        <section aria-label="Nutrition dashboard" className="rounded-2xl bg-charcoal-medium/50 border border-charcoal-border shadow-md p-5 space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-extrabold text-foreground uppercase tracking-wider">
              Your Weekly Nutrition Summary
            </h2>
            {analytics && (
              <span className="px-2.5 py-1 rounded-full bg-charcoal-dark border border-charcoal-border text-[9px] font-bold text-muted-foreground uppercase tracking-widest">
                {analytics.meals_analyzed} meal{analytics.meals_analyzed === 1 ? '' : 's'} in analysis window
              </span>
            )}
          </div>

          {analyticsLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 animate-pulse">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="h-16 rounded-xl bg-charcoal-light border border-charcoal-border/50" />
              ))}
            </div>
          ) : analytics && analytics.meals_analyzed > 0 ? (
            <>
              {/* Stat tiles */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatTile icon={Flame} tone="text-brand-orange" label="Avg Calories" value={`${analytics.avg_calories.toFixed(0)}`} unit="kcal" />
                <StatTile icon={Beef} tone="text-brand-red" label="Avg Protein" value={`${analytics.avg_protein.toFixed(1)}`} unit="g" />
                <StatTile icon={Wheat} tone="text-brand-cyan" label="Avg Carbs" value={`${analytics.avg_carbs.toFixed(1)}`} unit="g" />
                <StatTile icon={Droplet} tone="text-brand-blue" label="Avg Fat" value={`${analytics.avg_fats.toFixed(1)}`} unit="g" />
                <StatTile icon={Activity} tone="text-brand-emerald" label="Avg DCI" value={analytics.avg_dci != null && analytics.avg_dci > 0 ? `${Math.round(analytics.avg_dci * 100)}` : '—'} unit={analytics.avg_dci != null && analytics.avg_dci > 0 ? '/100' : ''} />
                <StatTile icon={Target} tone="text-brand-orange" label="Avg NIS" value={analytics.avg_nis > 0 ? `${analytics.avg_nis.toFixed(2)}` : '—'} unit="" />
                <StatTile icon={TrendingUp} tone="text-brand-cyan" label="Meals (last 7 days)" value={`${analytics.meals_this_week}`} unit="" />
                <StatTile
                  icon={Activity}
                  tone="text-brand-red"
                  label="Risk Trend (est.)"
                  value={analytics.risk_trend ? `${analytics.risk_trend.name} risk` : '—'}
                  unit={analytics.risk_trend ? riskDirectionLabel(analytics.risk_trend.direction) : ''}
                />
              </div>

              {/* Patterns */}
              {analytics.patterns.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-[9px] text-muted-foreground font-bold uppercase tracking-widest">Coach insights</p>
                  <ul className="space-y-1">
                    {analytics.patterns.map((pattern, idx) => (
                      <li key={idx} className="text-xs text-foreground flex items-start space-x-2">
                        <span className="text-brand-emerald" aria-hidden="true">•</span>
                        <span>{pattern}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Goals */}
              {analytics.goals.length > 0 && (
                <div className="space-y-2">
                  <p className="text-[9px] text-muted-foreground font-bold uppercase tracking-widest">Smart goals</p>
                  <p className="text-[8px] text-muted-foreground leading-4">
                    Progress is an estimate of how close your recent meals are to dietary targets —
                    guidance, not a clinical measurement.
                  </p>
                  <div className="space-y-1.5">
                    {analytics.goals.map((goal) => {
                      // Hydration is not measured — show it as guidance only,
                      // never as a fake personalized completion percentage.
                      if (goal.id === 'hydration') {
                        return (
                          <div key={goal.id} className="flex items-center space-x-3">
                            <span className="text-[10px] font-bold text-foreground w-40 shrink-0 truncate">{goal.title}</span>
                            <span className="text-[9px] text-muted-foreground">aim for ~2–3 L of water daily (guidance)</span>
                          </div>
                        );
                      }
                      // Consistency is only meaningful when DCI data exists.
                      const insufficient = goal.id === 'consistency' && (analytics.avg_dci == null || analytics.avg_dci <= 0);
                      return (
                        <div key={goal.id} className="flex items-center space-x-3">
                          <span className="text-[10px] font-bold text-foreground w-40 shrink-0 truncate">{goal.title}</span>
                          <div className="flex-1 h-2 rounded-full bg-charcoal-light border border-charcoal-border/50 overflow-hidden">
                            {!insufficient && (
                              <div
                                className={`h-full rounded-full ${
                                  goal.progress >= 0.6
                                    ? 'bg-brand-emerald'
                                    : goal.progress < 0.4
                                      ? 'bg-brand-red'
                                      : 'bg-brand-orange'
                                }`}
                                style={{ width: `${Math.max(2, goal.progress * 100)}%` }}
                              />
                            )}
                          </div>
                          <span className="text-[9px] font-bold text-muted-foreground w-16 text-right">
                            {insufficient ? '—' : `${Math.round(goal.progress * 100)}%`}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Habits */}
              {(analytics.positive_habits.length > 0 || analytics.habits_to_improve.length > 0) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {analytics.positive_habits.length > 0 && (
                    <div className="p-3 rounded-xl bg-brand-emerald/5 border border-brand-emerald/15">
                      <p className="text-[9px] text-brand-emerald font-bold uppercase tracking-widest mb-1">Positive habits</p>
                      <ul className="space-y-1">
                        {analytics.positive_habits.map((h, i) => (
                          <li key={i} className="text-[11px] text-foreground">✓ {h}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {analytics.habits_to_improve.length > 0 && (
                    <div className="p-3 rounded-xl bg-brand-orange/5 border border-brand-orange/15">
                      <p className="text-[9px] text-brand-orange font-bold uppercase tracking-widest mb-1">Areas to improve</p>
                      <ul className="space-y-1">
                        {analytics.habits_to_improve.map((h, i) => (
                          <li key={i} className="text-[11px] text-foreground">▲ {h}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Most common food */}
              {analytics.most_common_food && (
                <p className="text-[10px] text-muted-foreground">
                  Most common food: <span className="font-bold text-foreground">{analytics.most_common_food}</span>
                </p>
              )}
            </>
          ) : (
            <p className="text-[10px] text-muted-foreground font-semibold uppercase tracking-widest text-center py-6">
              Analyse a meal to unlock personalized nutrition insights.
            </p>
          )}
        </section>

        {/* Chat card */}
        <section aria-label="AI Nutrition Assistant chat" className="rounded-2xl bg-charcoal-medium/50 border border-charcoal-border shadow-md overflow-hidden">
          {/* Quick actions */}
          <div className="p-4 border-b border-charcoal-border/50">
            <p className="text-[9px] text-muted-foreground font-bold uppercase tracking-widest mb-2">Quick actions</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {QUICK_ACTIONS.map((action) => (
                <button
                  key={action.label}
                  type="button"
                  onClick={() => sendMessage(action.prompt)}
                  disabled={isSending}
                  className="flex items-center space-x-2 px-3 py-2.5 rounded-xl bg-charcoal-dark border border-charcoal-border hover:border-brand-emerald/40 hover:bg-charcoal-light transition-all cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed text-left"
                >
                  <span aria-hidden="true" className="text-base">{action.emoji}</span>
                  <span className="text-[10px] font-bold text-foreground uppercase tracking-wider">
                    {action.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Message list */}
          <div ref={scrollRef} className="max-h-[380px] overflow-y-auto p-4 space-y-3" aria-live="polite">
            {messages.length === 0 ? (
              <div className="text-center py-8 space-y-2">
                <Salad className="h-8 w-8 text-brand-emerald mx-auto" aria-hidden="true" />
                <p className="text-[10px] text-muted-foreground font-semibold uppercase tracking-widest">
                  Ask about meal planning, nutrition, or improving your diet.
                </p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={
                      msg.role === 'user'
                        ? 'max-w-[82%] px-4 py-2.5 rounded-2xl bg-brand-emerald text-white text-xs leading-relaxed shadow-md shadow-brand-emerald/15'
                        : 'max-w-[82%] px-4 py-2.5 rounded-2xl bg-charcoal-dark border border-charcoal-border text-foreground text-xs leading-relaxed'
                    }
                  >
                    {msg.content}
                  </div>
                </div>
              ))
            )}

            {/* Typing indicator */}
            {isSending && (
              <div className="flex justify-start">
                <div className="px-4 py-2.5 rounded-2xl bg-charcoal-dark border border-charcoal-border flex items-center space-x-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-brand-emerald animate-bounce" />
                  <span className="h-1.5 w-1.5 rounded-full bg-brand-emerald animate-bounce [animation-delay:120ms]" />
                  <span className="h-1.5 w-1.5 rounded-full bg-brand-emerald animate-bounce [animation-delay:240ms]" />
                  <span className="text-[9px] text-muted-foreground ml-1">coaching…</span>
                </div>
              </div>
            )}
          </div>

          {/* Suggested prompts */}
          <div className="px-4 pb-3 flex flex-wrap gap-2">
            {SUGGESTED_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => setInput(prompt)}
                className="px-3 py-1.5 rounded-xl bg-charcoal-dark border border-charcoal-border text-[10px] font-bold text-brand-emerald hover:border-brand-emerald/40 transition-all cursor-pointer"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input form */}
          <form onSubmit={handleSubmit} className="flex items-center space-x-2 p-4 pt-0">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about nutrition, meals, or diets…"
              aria-label="Message to the Nutrition Coach"
              disabled={isSending}
              className="flex-1 bg-charcoal-dark border border-charcoal-border focus:border-brand-emerald/60 focus:ring-1 focus:ring-brand-emerald/30 rounded-xl px-4 py-2.5 text-xs text-foreground focus:outline-none transition-all disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={isSending || !input.trim()}
              aria-label="Send message"
              className="px-4 py-2.5 rounded-xl bg-brand-emerald hover:bg-brand-emerald/90 text-white text-xs font-bold uppercase tracking-wider flex items-center justify-center space-x-1.5 transition-all cursor-pointer disabled:bg-charcoal-medium/50 disabled:text-muted-foreground disabled:cursor-not-allowed shadow-md shadow-brand-emerald/15"
            >
              {isSending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
              ) : (
                <Send className="h-3.5 w-3.5" aria-hidden="true" />
              )}
              <span>{isSending ? 'Coaching' : 'Send'}</span>
            </button>
          </form>

          <p className="px-4 pb-4 text-[9px] text-muted-foreground">
            Personalized coaching uses your meal history. It never diagnoses disease and never
            replaces professional medical advice.
          </p>
        </section>
      </div>
    </ProtectedRoute>
  );
}

function StatTile({
  icon: Icon,
  tone,
  label,
  value,
  unit,
}: {
  icon: React.ComponentType<{ className?: string }>;
  tone: string;
  label: string;
  value: string;
  unit: string;
}) {
  return (
    <div className="p-3 rounded-xl bg-charcoal-dark border border-charcoal-border flex flex-col justify-between min-h-[64px]">
      <div className="flex items-center justify-between">
        <span className="text-[8px] text-muted-foreground font-bold uppercase tracking-widest">{label}</span>
        <Icon className={`h-3.5 w-3.5 ${tone}`} aria-hidden="true" />
      </div>
      <span className="text-lg font-black text-foreground tracking-tight font-mono mt-1">
        {value} {unit && <span className="text-[9px] text-muted-foreground font-bold">{unit}</span>}
      </span>
    </div>
  );
}
