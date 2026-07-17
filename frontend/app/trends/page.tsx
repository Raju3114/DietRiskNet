'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import ProtectedRoute from '../../components/ProtectedRoute';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, AreaChart, Area, Legend 
} from 'recharts';
import { TrendingUp, CalendarRange, Activity } from 'lucide-react';

export default function TrendsPage() {
  const [days, setDays] = useState(30);

  const { data, isLoading, error } = useQuery({
    queryKey: ['trends', days],
    queryFn: () => api.getTrends(days),
  });

  const timeframes = [
    { label: 'Last 7 Days', value: 7 },
    { label: 'Last 14 Days', value: 14 },
    { label: 'Last 30 Days', value: 30 },
  ];

  if (isLoading) {
    return (
      <ProtectedRoute>
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
          <div className="relative">
            <div className="h-10 w-10 border-4 border-brand-blue border-t-transparent rounded-full animate-spin" />
            <Activity className="absolute inset-0 m-auto h-4.5 w-4.5 text-brand-cyan animate-pulse" />
          </div>
          <span className="text-zinc-500 text-xs font-semibold uppercase tracking-widest animate-pulse">Compiling daily trends...</span>
        </div>
      </ProtectedRoute>
    );
  }

  if (error || !data) {
    return (
      <ProtectedRoute>
        <div className="p-8 rounded-2xl bg-charcoal-medium border border-brand-red/20 text-center max-w-md mx-auto my-12 shadow-lg">
          <CalendarRange className="h-12 w-12 text-brand-red mx-auto mb-4" />
          <p className="text-brand-red font-bold uppercase tracking-wider text-sm">Failed to retrieve historical trends</p>
          <p className="text-zinc-500 text-xs mt-1">Please ensure that the backend API endpoint is accessible.</p>
        </div>
      </ProtectedRoute>
    );
  }

  const chartData = data.trends;

  return (
    <ProtectedRoute>
      <div className="space-y-8 animate-fade-in font-sans">
        {/* Header navigation bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-charcoal-border/50 pb-6">
          <div>
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full border border-brand-blue/20 bg-brand-blue/5 text-brand-blue text-[9px] font-bold uppercase tracking-widest mb-3 w-fit glow-blue">
              <TrendingUp className="h-3.5 w-3.5 text-brand-blue" />
              <span>Historical Inferences</span>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center space-x-3">
              <span>Longitudinal Analytics</span>
            </h1>
            <p className="text-zinc-550 text-[10px] font-extrabold uppercase tracking-wider mt-1">Audit daily calories, macronutrient weights, portion metrics, and disease trends over time.</p>
          </div>

          {/* Timeframe picker */}
          <div className="flex bg-charcoal-medium/80 p-1 rounded-xl border border-charcoal-border w-fit">
            {timeframes.map((tf) => (
              <button
                key={tf.value}
                onClick={() => setDays(tf.value)}
                className={`
                  px-4 py-2.5 rounded-lg text-[9px] font-bold uppercase tracking-widest transition-all duration-200 cursor-pointer
                  ${days === tf.value 
                    ? 'bg-brand-blue text-white shadow-md border border-brand-blue/20' 
                    : 'text-zinc-400 hover:text-white border border-transparent'}
                `}
              >
                {tf.label}
              </button>
            ))}
          </div>
        </div>

        {chartData.length === 0 ? (
          <div className="p-16 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border text-center shadow-inner max-w-lg mx-auto my-12">
            <CalendarRange className="h-10 w-10 text-zinc-600 mx-auto mb-4 animate-pulse" />
            <h3 className="text-xs font-bold text-white mb-1 uppercase tracking-wider">No Historical Logs Found</h3>
            <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest leading-relaxed">Log meals regularly over a few days to view longitudinal charts.</p>
          </div>
        ) : (
          /* Charts Layout Grid */
          <div className="grid grid-cols-1 gap-8">
            {/* Calorie Intake Progression */}
            <div className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-4 shadow-md hover:border-brand-blue/15 transition-all duration-200">
              <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Daily Calorie Intake (kcal)</h3>
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorCalories" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#2563EB" stopOpacity={0.25}/>
                        <stop offset="95%" stopColor="#2563EB" stopOpacity={0.0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                    <XAxis dataKey="date" stroke="#71717a" fontSize={8} tickLine={false} />
                    <YAxis stroke="#71717a" fontSize={8} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.08)', borderRadius: '12px', color: '#fff', fontSize: 10 }} />
                    <Area type="monotone" dataKey="calories" name="Calories" stroke="#2563EB" strokeWidth={2.5} fillOpacity={1} fill="url(#colorCalories)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Macronutrient Area Stacked Chart */}
            <div className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-4 shadow-md hover:border-brand-blue/15 transition-all duration-200">
              <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Macronutrient Distribution (grams)</h3>
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                    <XAxis dataKey="date" stroke="#71717a" fontSize={8} tickLine={false} />
                    <YAxis stroke="#71717a" fontSize={8} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.08)', borderRadius: '12px', color: '#fff', fontSize: 10 }} />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em' }} />
                    <Area type="monotone" dataKey="carbs" stackId="1" name="Carbs" stroke="#06B6D4" fill="#06B6D4" fillOpacity={0.15} />
                    <Area type="monotone" dataKey="protein" stackId="1" name="Protein" stroke="#EF4444" fill="#EF4444" fillOpacity={0.15} />
                    <Area type="monotone" dataKey="fats" stackId="1" name="Fats" stroke="#2563EB" fill="#2563EB" fillOpacity={0.15} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* DCI & NIS Indices progressions */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-4 shadow-md hover:border-brand-blue/15 transition-all duration-200">
                <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Dietary Consistency (DCI) Trend</h3>
                <div className="h-[250px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                      <XAxis dataKey="date" stroke="#71717a" fontSize={8} tickLine={false} />
                      <YAxis domain={[0, 1]} stroke="#71717a" fontSize={8} tickLine={false} />
                      <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.08)', borderRadius: '12px', color: '#fff', fontSize: 10 }} />
                      <Line type="monotone" dataKey="dci" name="DCI Score" stroke="#10B981" strokeWidth={3} dot={{ r: 3, fill: '#10B981' }} activeDot={{ r: 5 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-4 shadow-md hover:border-brand-blue/15 transition-all duration-200">
                <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Nutrient Imbalance (NIS) Trend</h3>
                <div className="h-[250px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                      <XAxis dataKey="date" stroke="#71717a" fontSize={8} tickLine={false} />
                      <YAxis stroke="#71717a" fontSize={8} tickLine={false} />
                      <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.08)', borderRadius: '12px', color: '#fff', fontSize: 10 }} />
                      <Line type="monotone" dataKey="nis" name="NIS Score" stroke="#F59E0B" strokeWidth={3} dot={{ r: 3, fill: '#F59E0B' }} activeDot={{ r: 5 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Disease Risk progressions */}
            <div className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-4 shadow-md hover:border-brand-blue/15 transition-all duration-200">
              <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">XGBoost Disease Risk Probabilities Progression</h3>
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                    <XAxis dataKey="date" stroke="#71717a" fontSize={8} tickLine={false} />
                    <YAxis domain={[0, 1]} stroke="#71717a" fontSize={8} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.08)', borderRadius: '12px', color: '#fff', fontSize: 10 }} />
                    <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em' }} />
                    <Line type="monotone" dataKey="diabetes_risk" name="Diabetes Risk" stroke="#06B6D4" strokeWidth={2} dot={{ r: 2 }} />
                    <Line type="monotone" dataKey="obesity_risk" name="Obesity Risk" stroke="#F59E0B" strokeWidth={2} dot={{ r: 2 }} />
                    <Line type="monotone" dataKey="hypertension_risk" name="Hypertension Risk" stroke="#EF4444" strokeWidth={2} dot={{ r: 2 }} />
                    <Line type="monotone" dataKey="deficiency_risk" name="Deficiency Risk" stroke="#10B981" strokeWidth={2} dot={{ r: 2 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}
      </div>
    </ProtectedRoute>
  );
}
