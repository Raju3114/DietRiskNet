'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import ProtectedRoute from '../../components/ProtectedRoute';
import { motion } from 'framer-motion';
import { 
  Activity, Flame, Beef, Wheat, Droplet, Sparkles, Scale, Info, PlusCircle, Calendar, ShieldCheck, Heart 
} from 'lucide-react';
import Link from 'next/link';

interface RecommendationItem {
  category: string;
  content: string;
  explanation: string;
}

interface RecentMealItem {
  created_at: string;
  items_count: number;
  calories: number;
  risk_score: number;
}

export default function Dashboard() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboard'],
    queryFn: api.getDashboard,
  });

  if (isLoading) {
    return (
      <ProtectedRoute>
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
          <div className="relative">
            <div className="h-10 w-10 border-4 border-brand-blue border-t-transparent rounded-full animate-spin" />
            <Activity className="absolute inset-0 m-auto h-4.5 w-4.5 text-brand-cyan animate-pulse" />
          </div>
          <span className="text-zinc-500 text-xs font-semibold uppercase tracking-widest animate-pulse">Compiling daily longitudinal analytics...</span>
        </div>
      </ProtectedRoute>
    );
  }

  if (error || !data) {
    return (
      <ProtectedRoute>
        <div className="p-8 rounded-2xl bg-charcoal-medium border border-brand-red/20 text-center max-w-md mx-auto my-12 shadow-lg">
          <ShieldCheck className="h-12 w-12 text-brand-red mx-auto mb-4" />
          <p className="text-brand-red font-bold uppercase tracking-wider text-sm">Failed to retrieve clinical data</p>
          <p className="text-zinc-500 text-xs mt-1">Please ensure that the backend API endpoint is accessible.</p>
          <button 
            onClick={() => refetch()} 
            className="mt-6 px-5 py-2.5 bg-brand-blue hover:bg-brand-blue-hover text-white text-xs font-bold uppercase tracking-wider rounded-xl transition-all shadow-md shadow-brand-blue/15"
          >
            Retry Fetch
          </button>
        </div>
      </ProtectedRoute>
    );
  }

  // Destructure dashboard data
  const { 
    daily_aggregated, daily_percentage_rdi, dci, dci_level, nis, nis_level,
    fused_risk_score, fused_risk_level, recent_meals, recommendations 
  } = data;

  // Helpers for colors and styling
  const getRiskLevelColor = (lvl: string) => {
    switch (lvl.toLowerCase()) {
      case 'low': return 'text-brand-emerald bg-brand-emerald/10 border-brand-emerald/20 glow-emerald';
      case 'moderate': return 'text-brand-orange bg-brand-orange/10 border-brand-orange/20 glow-orange';
      case 'high': return 'text-brand-red bg-brand-red/10 border-brand-red/20 glow-red';
      default: return 'text-brand-blue bg-brand-blue/10 border-brand-blue/20 glow-blue';
    }
  };

  const getRiskGaugeColorClass = (lvl: string) => {
    switch (lvl.toLowerCase()) {
      case 'low': return 'text-brand-emerald';
      case 'moderate': return 'text-brand-orange';
      case 'high': return 'text-brand-red';
      default: return 'text-brand-blue';
    }
  };

  const staggerContainer = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08
      }
    }
  } as const;

  const cardFadeIn = {
    hidden: { y: 15, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.4, ease: 'easeOut' }
    }
  } as const;

  return (
    <ProtectedRoute>
      <div className="space-y-8 animate-fade-in font-sans">
        {/* Title Brand Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-charcoal-border/50 pb-6">
          <div>
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full border border-brand-blue/20 bg-brand-blue/5 text-brand-blue text-[9px] font-bold uppercase tracking-widest mb-3 w-fit glow-blue">
              <Sparkles className="h-3.5 w-3.5 text-brand-cyan" />
              <span>Real-Time Diagnostic Profiling</span>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center space-x-3">
              <span>Healthcare Intelligence Center</span>
            </h1>
            <p className="text-zinc-550 text-[10px] font-extrabold uppercase tracking-wider mt-1">Cross-referencing vision food maps with clinical disease risk calculations.</p>
          </div>
          <Link href="/upload" className="inline-flex items-center space-x-2 px-5 py-3 bg-brand-blue hover:bg-brand-blue-hover text-white text-[10px] font-bold uppercase tracking-widest rounded-xl shadow-lg shadow-brand-blue/15 transition-all duration-300 border border-brand-blue/25">
            <PlusCircle className="h-4 w-4" />
            <span>Scan New Meal</span>
          </Link>
        </div>

        {/* Top level grid: Risk status + Indices */}
        <motion.div 
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-3 gap-6"
        >
          {/* Fused Risk Card */}
          <motion.div 
            variants={cardFadeIn}
            className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border hover:border-brand-blue/25 transition-all duration-300 flex flex-col justify-between shadow-md relative overflow-hidden group"
          >
            <div className="flex items-center justify-between mb-6">
              <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Weighted Unified Risk</span>
              <span className={`px-2.5 py-0.5 rounded-full text-[9px] font-extrabold border uppercase tracking-widest ${getRiskLevelColor(fused_risk_level)}`}>
                {fused_risk_level} Risk
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-5xl font-black text-white tracking-tighter">{(fused_risk_score * 100).toFixed(0)}%</span>
                <p className="text-[9px] text-zinc-500 font-bold uppercase tracking-widest mt-2.5">Fused metabolic hazard score</p>
              </div>
              <div className="w-18 h-18 relative">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                  <path className="text-charcoal-light/60" strokeWidth="2.8" stroke="currentColor" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  <path className={`${getRiskGaugeColorClass(fused_risk_level)} transition-all duration-500`} strokeDasharray={`${fused_risk_score * 100}, 100`} strokeWidth="3" strokeLinecap="round" stroke="currentColor" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <Activity className="h-4.5 w-4.5 text-zinc-650" />
                </div>
              </div>
            </div>
          </motion.div>

          {/* DCI Consistency Index Card */}
          <motion.div 
            variants={cardFadeIn}
            className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border hover:border-brand-emerald/25 transition-all duration-300 flex flex-col justify-between shadow-md group"
          >
            <div className="flex items-center justify-between mb-6">
              <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Dietary Consistency (DCI)</span>
              <span className="px-2.5 py-0.5 rounded-full text-[9px] font-extrabold bg-charcoal-light border border-charcoal-border text-zinc-300 uppercase tracking-widest">
                {dci_level}
              </span>
            </div>
            <div>
              <div className="flex items-baseline">
                <span className="text-5xl font-black text-white tracking-tighter">{(dci * 100).toFixed(0)}</span>
                <span className="text-zinc-500 text-xs font-bold ml-1">/100</span>
              </div>
              <p className="text-[9px] text-zinc-500 font-bold uppercase tracking-widest mt-3.5">Caloric distribution &amp; interval variance score.</p>
            </div>
          </motion.div>

          {/* NIS Imbalance Card */}
          <motion.div 
            variants={cardFadeIn}
            className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border hover:border-brand-orange/25 transition-all duration-300 flex flex-col justify-between shadow-md group"
          >
            <div className="flex items-center justify-between mb-6">
              <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Nutrient Imbalance (NIS)</span>
              <span className="px-2.5 py-0.5 rounded-full text-[9px] font-extrabold bg-charcoal-light border border-charcoal-border text-zinc-300 uppercase tracking-widest">
                {nis_level}
              </span>
            </div>
            <div>
              <span className="text-5xl font-black text-white tracking-tighter">{nis.toFixed(2)}</span>
              <p className="text-[9px] text-zinc-500 font-bold uppercase tracking-widest mt-5.5">Cumulative relative deviations from target RDIs.</p>
            </div>
          </motion.div>
        </motion.div>

        {/* Today's Nutritional Aggregations */}
        <div className="space-y-4">
          <h2 className="text-xs font-bold text-zinc-400 uppercase tracking-widest flex items-center space-x-2.5">
            <Heart className="h-4.5 w-4.5 text-brand-emerald glow-emerald" />
            <span>Daily Intake &amp; RDI Tracking</span>
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            {/* Calories Card */}
            <div className="p-4.5 rounded-xl bg-charcoal-medium/50 border border-charcoal-border space-y-3 hover:border-brand-orange/25 transition-all duration-200">
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 text-[10px] font-bold uppercase tracking-wider">Calories</span>
                <Flame className="h-4 w-4 text-brand-orange" />
              </div>
              <div>
                <span className="text-xl font-extrabold text-white">{daily_aggregated.calories.toFixed(0)}</span>
                <span className="text-[9px] text-zinc-500 font-bold ml-1">kcal</span>
              </div>
              <div className="w-full bg-charcoal-light rounded-full h-1 overflow-hidden border border-charcoal-border/30">
                <div className="bg-brand-orange h-full rounded-full transition-all duration-300" style={{ width: `${Math.min(100, daily_percentage_rdi.Calories)}%` }} />
              </div>
              <span className="text-[9px] text-zinc-500 font-bold block">{daily_percentage_rdi.Calories.toFixed(0)}% of RDI</span>
            </div>

            {/* Carbs Card */}
            <div className="p-4.5 rounded-xl bg-charcoal-medium/50 border border-charcoal-border space-y-3 hover:border-brand-cyan/25 transition-all duration-200">
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 text-[10px] font-bold uppercase tracking-wider">Carbs</span>
                <Wheat className="h-4 w-4 text-brand-cyan" />
              </div>
              <div>
                <span className="text-xl font-extrabold text-white">{daily_aggregated.carbs.toFixed(1)}</span>
                <span className="text-[9px] text-zinc-500 font-bold ml-1">g</span>
              </div>
              <div className="w-full bg-charcoal-light rounded-full h-1 overflow-hidden border border-charcoal-border/30">
                <div className="bg-brand-cyan h-full rounded-full transition-all duration-300" style={{ width: `${Math.min(100, daily_percentage_rdi.Carbs)}%` }} />
              </div>
              <span className="text-[9px] text-zinc-500 font-bold block">{daily_percentage_rdi.Carbs.toFixed(0)}% of RDI</span>
            </div>

            {/* Protein Card */}
            <div className="p-4.5 rounded-xl bg-charcoal-medium/50 border border-charcoal-border space-y-3 hover:border-brand-red/25 transition-all duration-200">
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 text-[10px] font-bold uppercase tracking-wider">Protein</span>
                <Beef className="h-4 w-4 text-brand-red" />
              </div>
              <div>
                <span className="text-xl font-extrabold text-white">{daily_aggregated.protein.toFixed(1)}</span>
                <span className="text-[9px] text-zinc-500 font-bold ml-1">g</span>
              </div>
              <div className="w-full bg-charcoal-light rounded-full h-1 overflow-hidden border border-charcoal-border/30">
                <div className="bg-brand-red h-full rounded-full transition-all duration-300" style={{ width: `${Math.min(100, daily_percentage_rdi.Protein)}%` }} />
              </div>
              <span className="text-[9px] text-zinc-500 font-bold block">{daily_percentage_rdi.Protein.toFixed(0)}% of RDI</span>
            </div>

            {/* Fat Card */}
            <div className="p-4.5 rounded-xl bg-charcoal-medium/50 border border-charcoal-border space-y-3 hover:border-brand-blue/25 transition-all duration-200">
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 text-[10px] font-bold uppercase tracking-wider">Fats</span>
                <Droplet className="h-4 w-4 text-brand-blue" />
              </div>
              <div>
                <span className="text-xl font-extrabold text-white">{daily_aggregated.fats.toFixed(1)}</span>
                <span className="text-[9px] text-zinc-500 font-bold ml-1">g</span>
              </div>
              <div className="w-full bg-charcoal-light rounded-full h-1 overflow-hidden border border-charcoal-border/30">
                <div className="bg-brand-blue h-full rounded-full transition-all duration-300" style={{ width: `${Math.min(100, daily_percentage_rdi.Fat)}%` }} />
              </div>
              <span className="text-[9px] text-zinc-500 font-bold block">{daily_percentage_rdi.Fat.toFixed(0)}% of RDI</span>
            </div>

            {/* Sodium Card */}
            <div className="p-4.5 rounded-xl bg-charcoal-medium/50 border border-charcoal-border space-y-3 hover:border-brand-cyan/25 transition-all duration-200">
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 text-[10px] font-bold uppercase tracking-wider">Sodium</span>
                <Scale className="h-4 w-4 text-brand-cyan" />
              </div>
              <div>
                <span className="text-xl font-extrabold text-white">{daily_aggregated.sodium.toFixed(0)}</span>
                <span className="text-[9px] text-zinc-500 font-bold ml-1">mg</span>
              </div>
              <div className="w-full bg-charcoal-light rounded-full h-1 overflow-hidden border border-charcoal-border/30">
                <div className="bg-brand-cyan h-full rounded-full transition-all duration-300" style={{ width: `${Math.min(100, daily_percentage_rdi.Sodium)}%` }} />
              </div>
              <span className="text-[9px] text-zinc-500 font-bold block">{daily_percentage_rdi.Sodium.toFixed(0)}% of RDI</span>
            </div>

            {/* Fiber Card */}
            <div className="p-4.5 rounded-xl bg-charcoal-medium/50 border border-charcoal-border space-y-3 hover:border-brand-emerald/25 transition-all duration-200">
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 text-[10px] font-bold uppercase tracking-wider">Fiber</span>
                <Info className="h-4 w-4 text-brand-emerald" />
              </div>
              <div>
                <span className="text-xl font-extrabold text-white">{daily_aggregated.fiber.toFixed(1)}</span>
                <span className="text-[9px] text-zinc-500 font-bold ml-1">g</span>
              </div>
              <div className="w-full bg-charcoal-light rounded-full h-1 overflow-hidden border border-charcoal-border/30">
                <div className="bg-brand-emerald h-full rounded-full transition-all duration-300" style={{ width: `${Math.min(100, daily_percentage_rdi.Fiber)}%` }} />
              </div>
              <span className="text-[9px] text-zinc-500 font-bold block">{daily_percentage_rdi.Fiber.toFixed(0)}% of RDI</span>
            </div>
          </div>
        </div>

        {/* ExplainDiet suggestions and Recent Meals */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recommendations Card */}
          <div className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-6 flex flex-col justify-between shadow-md">
            <div className="space-y-4">
              <h3 className="text-xs font-bold text-white flex items-center space-x-2 bg-charcoal-dark border border-charcoal-border/80 px-4 py-3 rounded-xl">
                <Sparkles className="h-4 w-4 text-brand-emerald glow-emerald animate-pulse" />
                <span className="uppercase tracking-wider">ExplainDiet Clinical Recommendations</span>
              </h3>

              <div className="space-y-3 max-h-[350px] overflow-y-auto pr-1">
                {recommendations.length > 0 ? (
                  recommendations.map((rec: RecommendationItem, idx: number) => (
                    <div key={idx} className="p-4 rounded-xl bg-charcoal-dark/50 border border-charcoal-border hover:border-brand-emerald/15 transition-all duration-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[8px] font-extrabold text-brand-emerald bg-brand-emerald/10 border border-brand-emerald/15 px-2.5 py-0.5 rounded uppercase tracking-widest">{rec.category}</span>
                      </div>
                      <h4 className="text-xs font-extrabold text-white leading-normal uppercase tracking-wider">{rec.content}</h4>
                      <p className="text-[10px] text-zinc-405 leading-relaxed font-semibold">{rec.explanation}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-[10px] text-zinc-500 text-center py-10 font-bold uppercase tracking-widest">No active dietary warnings compiled.</p>
                )}
              </div>
            </div>
            
            <Link href="/recommendations" className="block text-center text-[9px] font-extrabold uppercase tracking-widest text-brand-blue hover:text-brand-blue-hover transition-colors pt-4 border-t border-charcoal-border/50">
              Access Full Interactive Advice &rarr;
            </Link>
          </div>

          {/* Recent Meals List */}
          <div className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-6 flex flex-col justify-between shadow-md">
            <div className="space-y-4">
              <h3 className="text-xs font-bold text-white flex items-center space-x-2 bg-charcoal-dark border border-charcoal-border/80 px-4 py-3 rounded-xl">
                <Calendar className="h-4 w-4 text-brand-blue" />
                <span className="uppercase tracking-wider">Logged Diagnostics History</span>
              </h3>

              <div className="space-y-3 max-h-[350px] overflow-y-auto pr-1">
                {recent_meals.length > 0 ? (
                  recent_meals.map((meal: RecentMealItem, idx: number) => (
                    <div key={idx} className="p-4 rounded-xl bg-charcoal-dark/50 border border-charcoal-border flex items-center justify-between hover:border-brand-blue/15 transition-all duration-200">
                      <div>
                        <span className="text-[9px] text-zinc-500 font-bold uppercase tracking-widest">
                          {new Date(meal.created_at).toLocaleString()}
                        </span>
                        <h4 className="text-xs font-extrabold text-white mt-1 uppercase tracking-wider">Recognized {meal.items_count} crop(s)</h4>
                        <span className="text-[10px] text-brand-orange font-bold font-mono">{meal.calories.toFixed(0)} kcal total</span>
                      </div>
                      <div className="text-right">
                        <span className="text-[8px] text-zinc-500 font-bold block uppercase tracking-widest mb-1">Risk score</span>
                        <span className={`text-xs font-extrabold uppercase tracking-wider ${
                          meal.risk_score < 0.3 ? 'text-brand-emerald' : (meal.risk_score < 0.6 ? 'text-brand-orange' : 'text-brand-red')
                        }`}>
                          {(meal.risk_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-10">
                    <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest mb-4">No historical records logged yet.</p>
                    <Link href="/upload" className="inline-block px-4 py-2 bg-brand-blue/10 hover:bg-brand-blue/20 text-brand-blue border border-brand-blue/20 rounded-xl text-[9px] font-bold uppercase tracking-widest transition-all">
                      Analyze First Scan
                    </Link>
                  </div>
                )}
              </div>
            </div>
            
            <Link href="/history" className="block text-center text-[9px] font-extrabold uppercase tracking-widest text-brand-blue hover:text-brand-blue-hover transition-colors pt-4 border-t border-charcoal-border/50">
              Review Bounding Box Logs &rarr;
            </Link>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
