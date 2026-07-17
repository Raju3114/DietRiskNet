'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import ProtectedRoute from '../../components/ProtectedRoute';
import { Calendar, Activity, Apple } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';

interface FoodItem {
  name: string;
}

interface HistoryMeal {
  id: string | number;
  created_at: string;
  items?: FoodItem[];
  risk_score: number;
  risk_level?: string;
  calories?: number;
  protein?: number;
  carbs?: number;
  fats?: number;
  dci?: number;
  nis?: number;
}

export default function HistoryPage() {
  const router = useRouter();

  const { data: history, isLoading, error } = useQuery({
    queryKey: ['history'],
    queryFn: api.getHistory,
  });

  if (isLoading) {
    return (
      <ProtectedRoute>
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
          <div className="relative">
            <div className="h-10 w-10 border-4 border-brand-blue border-t-transparent rounded-full animate-spin" />
            <Activity className="absolute inset-0 m-auto h-4.5 w-4.5 text-brand-cyan animate-pulse" />
          </div>
          <span className="text-zinc-500 text-xs font-semibold uppercase tracking-widest animate-pulse">Compiling meal history logs...</span>
        </div>
      </ProtectedRoute>
    );
  }

  if (error || !history) {
    return (
      <ProtectedRoute>
        <div className="p-8 rounded-2xl bg-charcoal-medium border border-brand-red/20 text-center max-w-md mx-auto my-12 shadow-lg">
          <Calendar className="h-12 w-12 text-brand-red mx-auto mb-4" />
          <p className="text-brand-red font-bold uppercase tracking-wider text-sm">Failed to retrieve history logs</p>
          <p className="text-zinc-500 text-xs mt-1">Please check if the backend API is up and running.</p>
        </div>
      </ProtectedRoute>
    );
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08
      }
    }
  } as const;

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 120, damping: 14 } }
  } as const;

  return (
    <ProtectedRoute>
      <div className="space-y-8 animate-fade-in font-sans">
        {/* Header */}
        <div className="border-b border-charcoal-border/50 pb-6">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full border border-brand-blue/20 bg-brand-blue/5 text-brand-blue text-[9px] font-bold uppercase tracking-widest mb-3 w-fit glow-blue">
            <Calendar className="h-3.5 w-3.5 text-brand-blue" />
            <span>Patient Records Log</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center space-x-3">
            <span>Meal History Log</span>
          </h1>
          <p className="text-zinc-550 text-[10px] font-extrabold uppercase tracking-wider mt-1">Review all registered meals and visual bounding box detections over time.</p>
        </div>

        {history.length === 0 ? (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="p-16 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border text-center shadow-inner max-w-lg mx-auto my-12 space-y-6"
          >
            <div className="mx-auto w-14 h-14 bg-charcoal-light border border-charcoal-border rounded-xl flex items-center justify-center">
              <Apple className="h-6 w-6 text-zinc-500" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-white mb-1 uppercase tracking-wider">No Meals Logged Yet</h3>
              <p className="text-[10px] text-zinc-505 font-bold uppercase tracking-widest leading-relaxed">Upload a photo of your meal to start tracking calories, macronutrients, and risks.</p>
            </div>
            <button 
              onClick={() => router.push('/upload')}
              className="px-6 py-3 bg-brand-blue hover:bg-blue-500 hover:shadow-brand-blue/10 border border-brand-blue/20 text-white text-[9px] font-bold uppercase tracking-widest rounded-xl shadow-lg transition-all duration-200 cursor-pointer"
            >
              Analyze Your First Meal
            </button>
          </motion.div>
        ) : (
          /* List timeline of meals */
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="space-y-6"
          >
            {history.map((meal: HistoryMeal) => {
              // Risk level color mapping
              const riskLevel = (meal.risk_level || 'low').toLowerCase();
              let riskBadgeClass = 'bg-brand-emerald/10 text-brand-emerald border-brand-emerald/20';
              let riskTextColor = 'text-brand-emerald';
              if (riskLevel === 'high') {
                riskBadgeClass = 'bg-brand-red/10 text-brand-red border-brand-red/20';
                riskTextColor = 'text-brand-red';
              } else if (riskLevel === 'moderate') {
                riskBadgeClass = 'bg-brand-orange/10 text-brand-orange border-brand-orange/20';
                riskTextColor = 'text-brand-orange';
              }

              return (
                <motion.div 
                  key={meal.id} 
                  variants={itemVariants}
                  className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-5 hover:border-brand-blue/20 transition-all duration-300 shadow-md"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-charcoal-border/50 pb-4">
                    <div>
                      <span className="text-[9px] text-zinc-500 font-bold uppercase tracking-widest">
                        {new Date(meal.created_at).toLocaleString()}
                      </span>
                      <h3 className="text-xs font-extrabold text-white mt-1 uppercase tracking-wider">
                        Logged {meal.items ? meal.items.length : 0} recognized item(s)
                      </h3>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <span className="text-[8px] text-zinc-500 uppercase tracking-widest font-bold block mb-1">Risk Assessment</span>
                        <span className={`text-xs font-bold uppercase tracking-wider ${riskTextColor}`}>
                          {(meal.risk_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className={`px-3 py-1.5 rounded-xl border text-[9px] font-extrabold uppercase tracking-widest ${riskBadgeClass}`}>
                        {meal.risk_level || 'LOW'}
                      </div>
                    </div>
                  </div>

                  {/* Items & Nutrition summary */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Bounding box list */}
                    <div className="space-y-2">
                      <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest block mb-1">Recognized Foods</span>
                      <div className="flex flex-wrap gap-1.5">
                        {meal.items && meal.items.length > 0 ? (
                          meal.items.map((it: FoodItem, idx: number) => (
                            <span 
                              key={idx} 
                              className="px-2.5 py-1 bg-charcoal-light border border-charcoal-border/50 rounded-lg text-[9px] font-bold text-brand-cyan uppercase tracking-wider"
                            >
                              {it.name}
                            </span>
                          ))
                        ) : (
                          <span className="text-[9px] text-zinc-650 uppercase tracking-wider font-bold">No crops identified</span>
                        )}
                      </div>
                    </div>

                    {/* Nutrients summary */}
                    <div className="space-y-2">
                      <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest block mb-1">Nutritional Breakdown</span>
                      <div className="grid grid-cols-2 gap-2 text-[9px] font-bold text-zinc-300 bg-charcoal-light/40 p-3.5 rounded-xl border border-charcoal-border/50">
                        <div className="flex justify-between border-b border-charcoal-border/30 pb-1">
                          <span className="text-zinc-500 uppercase tracking-wider">Calories:</span>
                          <span className="text-brand-orange font-bold font-mono">{(meal.calories || 0).toFixed(0)} kcal</span>
                        </div>
                        <div className="flex justify-between border-b border-charcoal-border/30 pb-1">
                          <span className="text-zinc-500 uppercase tracking-wider">Carbs:</span>
                          <span className="text-brand-cyan font-mono">{(meal.carbs || 0).toFixed(1)}g</span>
                        </div>
                        <div className="flex justify-between pt-1">
                          <span className="text-zinc-500 uppercase tracking-wider">Protein:</span>
                          <span className="text-brand-red font-mono">{(meal.protein || 0).toFixed(1)}g</span>
                        </div>
                        <div className="flex justify-between pt-1">
                          <span className="text-zinc-500 uppercase tracking-wider">Fats:</span>
                          <span className="text-brand-blue font-mono">{(meal.fats || 0).toFixed(1)}g</span>
                        </div>
                      </div>
                    </div>

                    {/* Indices */}
                    <div className="space-y-2">
                      <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest block mb-1">Diagnostic Indices</span>
                      <div className="grid grid-cols-2 gap-2 text-[9px] font-bold text-zinc-300 bg-charcoal-light/40 p-3.5 rounded-xl border border-charcoal-border/50">
                        <div className="flex flex-col justify-center border-r border-charcoal-border/30 pr-2">
                          <span className="text-zinc-500 uppercase tracking-wider block text-[8px]">Consistency (DCI)</span>
                          <span className="text-brand-emerald text-base font-black mt-1 font-mono">
                            {((meal.dci || 0) * 100).toFixed(0)}
                          </span>
                        </div>
                        <div className="flex flex-col justify-center pl-2">
                          <span className="text-zinc-500 uppercase tracking-wider block text-[8px]">Imbalance (NIS)</span>
                          <span className="text-brand-orange text-base font-black mt-1 font-mono">
                            {(meal.nis || 0).toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </div>
    </ProtectedRoute>
  );
}
