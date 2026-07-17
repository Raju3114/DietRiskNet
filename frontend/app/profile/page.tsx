'use client';

import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../../services/api';
import ProtectedRoute from '../../components/ProtectedRoute';
import { User, Settings, Loader2, Save, Scale, Activity } from 'lucide-react';
import { useAuthStore } from '../../lib/store';

interface UserSettings {
  age?: number | string | null;
  gender?: string;
  height?: number | string | null;
  weight?: number | string | null;
  activity_level?: string;
  existing_conditions?: string[];
}

interface UserProfile {
  full_name?: string;
  email?: string;
  settings?: UserSettings;
}

function parseNumericValue(val: unknown, fallback: number): number {
  if (val === null || val === undefined || val === '') return fallback;
  const num = Number(val);
  return Number.isNaN(num) ? fallback : num;
}

export default function ProfilePage() {
  const { updateUser: updateAuthUser } = useAuthStore();
  const [name, setName] = useState('');
  const [age, setAge] = useState<number | ''>(30);
  const [gender, setGender] = useState('Male');
  const [height, setHeight] = useState<number | ''>(170.0);
  const [weight, setWeight] = useState<number | ''>(70.0);
  const [activity, setActivity] = useState('Moderate');
  const [conditions, setConditions] = useState<string[]>([]);

  const computedBMI = React.useMemo(() => {
    if (!height || !weight) return null;
    const hMeter = Number(height) / 100;
    const wKg = Number(weight);
    if (hMeter <= 0 || wKg <= 0) return null;
    const bmiVal = wKg / (hMeter * hMeter);
    let category = 'Normal';
    let color = 'text-brand-emerald bg-brand-emerald/10 border-brand-emerald/20 glow-emerald';
    if (bmiVal < 18.5) {
      category = 'Underweight';
      color = 'text-brand-cyan bg-brand-cyan/10 border-brand-cyan/20 glow-cyan';
    } else if (bmiVal >= 25 && bmiVal < 30) {
      category = 'Overweight';
      color = 'text-brand-orange bg-brand-orange/10 border-brand-orange/20 glow-orange';
    } else if (bmiVal >= 30) {
      category = 'Obese';
      color = 'text-brand-red bg-brand-red/10 border-brand-red/20 glow-red';
    }
    return { value: bmiVal.toFixed(1), category, color };
  }, [height, weight]);

  const { data: profile, isLoading, refetch } = useQuery<UserProfile>({
    queryKey: ['profile'],
    queryFn: api.getProfile,
  });

  // Sync state manually since tanstack v5 changed onSuccess behavior
  React.useEffect(() => {
    if (profile) {
      const timer = setTimeout(() => {
        setName(profile.full_name || '');
        if (profile.settings) {
          setAge(parseNumericValue(profile.settings.age, 30));
          setGender(profile.settings.gender || 'Male');
          setHeight(parseNumericValue(profile.settings.height, 170.0));
          setWeight(parseNumericValue(profile.settings.weight, 70.0));
          setActivity(profile.settings.activity_level || 'Moderate');
          setConditions(profile.settings.existing_conditions || []);
        }
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [profile]);

  const profileMutation = useMutation({
    mutationFn: () => api.updateProfile(name),
    onSuccess: (data) => {
      updateAuthUser({ full_name: data.full_name });
    }
  });

  const settingsMutation = useMutation({
    mutationFn: () => api.updateSettings({
      age: age === '' || Number.isNaN(age) ? 30 : age,
      gender,
      height: height === '' || Number.isNaN(height) ? 170.0 : height,
      weight: weight === '' || Number.isNaN(weight) ? 70.0 : weight,
      activity_level: activity,
      existing_conditions: conditions
    }),
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await profileMutation.mutateAsync();
      await settingsMutation.mutateAsync();
      alert('Profile and demographics updated successfully. XGBoost diagnostic risk models will now evaluate using these parameters.');
      refetch();
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      alert(error.message || 'Failed to update demographics.');
    }
  };

  const handleConditionToggle = (cond: string) => {
    if (conditions.includes(cond)) {
      setConditions(conditions.filter((c) => c !== cond));
    } else {
      setConditions([...conditions, cond]);
    }
  };

  if (isLoading) {
    return (
      <ProtectedRoute>
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
          <div className="relative">
            <div className="h-10 w-10 border-4 border-brand-blue border-t-transparent rounded-full animate-spin" />
            <Activity className="absolute inset-0 m-auto h-4.5 w-4.5 text-brand-cyan animate-pulse" />
          </div>
          <span className="text-zinc-500 text-xs font-semibold uppercase tracking-widest animate-pulse">Loading demographic variables...</span>
        </div>
      </ProtectedRoute>
    );
  }

  const isSaving = profileMutation.isPending || settingsMutation.isPending;

  return (
    <ProtectedRoute>
      <div className="max-w-3xl mx-auto space-y-8 animate-fade-in font-sans">
        <div>
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full border border-brand-blue/20 bg-brand-blue/5 text-brand-blue text-[9px] font-bold uppercase tracking-widest mb-3 w-fit glow-blue">
            <User className="h-3.5 w-3.5 text-brand-blue" />
            <span>Clinical Demographics</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center space-x-3">
            <span>Profile Records</span>
          </h1>
          <p className="text-zinc-555 text-[10px] font-extrabold uppercase tracking-wider mt-1">Configure clinical metrics utilized for disease risk estimations.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border grid grid-cols-1 md:grid-cols-2 gap-6 shadow-md">
            {/* Full Name */}
            <div className="space-y-2">
              <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest block">Full Name</label>
              <input 
                type="text" 
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-charcoal-light/60 border border-charcoal-border/80 rounded-xl p-3 text-xs text-white placeholder-zinc-650 focus:outline-none focus:border-brand-blue/50 focus:ring-1 focus:ring-brand-blue/25 transition-all shadow-inner"
              />
            </div>

            {/* Email (Readonly) */}
            <div className="space-y-2 opacity-65">
              <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest block">Email Address</label>
              <input 
                type="email" 
                disabled
                value={profile?.email || ''}
                className="w-full bg-charcoal-light/40 border border-charcoal-border/50 rounded-xl p-3 text-xs text-zinc-500 cursor-not-allowed"
              />
            </div>
          </div>

          {/* XGBoost Demographics Card */}
          <div className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-6 shadow-md">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <h3 className="text-xs font-bold text-white flex items-center space-x-2.5 uppercase tracking-wider">
                <Settings className="h-4.5 w-4.5 text-brand-blue animate-pulse" />
                <span>Diagnostic Metric Vectors</span>
              </h3>

              {computedBMI && (
                <div className={`px-3.5 py-1.5 rounded-xl border text-[9px] font-extrabold uppercase tracking-widest flex items-center space-x-1.5 ${computedBMI.color}`}>
                  <span>Body Mass Index (BMI):</span>
                  <span className="font-mono text-xs">{computedBMI.value}</span>
                  <span>({computedBMI.category})</span>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Age */}
              <div className="space-y-2">
                <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest block">Age (Years)</label>
                <input 
                  type="number" 
                  min={1} 
                  max={120}
                  required
                  value={age === '' || Number.isNaN(age) ? '' : age}
                  onChange={(e) => {
                    const val = parseInt(e.target.value);
                    setAge(Number.isNaN(val) ? '' : val);
                  }}
                  className="w-full bg-charcoal-light/60 border border-charcoal-border/80 rounded-xl p-3 text-xs text-white placeholder-zinc-655 focus:outline-none focus:border-brand-blue/50 focus:ring-1 focus:ring-brand-blue/25 transition-all shadow-inner"
                />
              </div>

              {/* Gender */}
              <div className="space-y-2">
                <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest block">Gender</label>
                <select 
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                  className="w-full bg-charcoal-light/60 border border-charcoal-border/80 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-brand-blue/50 focus:ring-1 focus:ring-brand-blue/25 transition-all shadow-inner cursor-pointer"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>

              {/* Height */}
              <div className="space-y-2">
                <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest block">Height (cm)</label>
                <input 
                  type="number" 
                  step="0.1"
                  required
                  value={height === '' || Number.isNaN(height) ? '' : height}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value);
                    setHeight(Number.isNaN(val) ? '' : val);
                  }}
                  className="w-full bg-charcoal-light/60 border border-charcoal-border/80 rounded-xl p-3 text-xs text-white placeholder-zinc-655 focus:outline-none focus:border-brand-blue/50 focus:ring-1 focus:ring-brand-blue/25 transition-all shadow-inner"
                />
              </div>

              {/* Weight */}
              <div className="space-y-2">
                <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest block">Weight (kg)</label>
                <input 
                  type="number" 
                  step="0.1"
                  required
                  value={weight === '' || Number.isNaN(weight) ? '' : weight}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value);
                    setWeight(Number.isNaN(val) ? '' : val);
                  }}
                  className="w-full bg-charcoal-light/60 border border-charcoal-border/80 rounded-xl p-3 text-xs text-white placeholder-zinc-655 focus:outline-none focus:border-brand-blue/50 focus:ring-1 focus:ring-brand-blue/25 transition-all shadow-inner"
                />
              </div>

              {/* Activity Level */}
              <div className="space-y-2">
                <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest block">Activity Level</label>
                <select 
                  value={activity}
                  onChange={(e) => setActivity(e.target.value)}
                  className="w-full bg-charcoal-light/60 border border-charcoal-border/80 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-brand-blue/50 focus:ring-1 focus:ring-brand-blue/25 transition-all shadow-inner cursor-pointer"
                >
                  <option value="Sedentary">Sedentary</option>
                  <option value="Lightly Active">Lightly Active</option>
                  <option value="Moderately Active">Moderately Active</option>
                  <option value="Very Active">Very Active</option>
                </select>
              </div>
            </div>
          </div>

          {/* Existing Conditions Checklist */}
          <div className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-4 shadow-md">
            <h3 className="text-xs font-bold text-white flex items-center space-x-2.5 uppercase tracking-wider">
              <Scale className="h-4 w-4 text-brand-blue" />
              <span>Prior Conditions Checklist</span>
            </h3>
            <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Check existing diagnoses to align model outputs and medical explanations.</p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
              {[
                { id: 'diabetes', label: 'Diabetes', color: 'bg-brand-cyan/10 border-brand-cyan/20 text-brand-cyan active:bg-brand-cyan/20' },
                { id: 'hypertension', label: 'Hypertension', color: 'bg-brand-red/10 border-brand-red/20 text-brand-red active:bg-brand-red/20' },
                { id: 'heart_disease', label: 'Heart Disease', color: 'bg-brand-orange/10 border-brand-orange/20 text-brand-orange active:bg-brand-orange/20' },
                { id: 'deficiency', label: 'Deficiency', color: 'bg-brand-emerald/10 border-brand-emerald/20 text-brand-emerald active:bg-brand-emerald/20' }
              ].map((cond) => {
                const isSelected = conditions.includes(cond.id);
                return (
                  <button
                    key={cond.id}
                    type="button"
                    onClick={() => handleConditionToggle(cond.id)}
                    className={`
                      p-4 rounded-xl text-left border text-[9px] font-extrabold transition-all duration-200 uppercase tracking-widest cursor-pointer
                      ${isSelected 
                        ? `${cond.color} shadow-sm shadow-black/40 scale-[0.98]` 
                        : 'bg-charcoal-light/60 border-charcoal-border/80 text-zinc-400 hover:text-white'}
                    `}
                  >
                    {cond.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Save Button */}
          <button 
            type="submit" 
            disabled={isSaving}
            className="w-full py-4 bg-brand-blue hover:bg-brand-blue-hover text-white font-extrabold rounded-xl text-[10px] uppercase tracking-widest flex items-center justify-center space-x-2 shadow-lg cursor-pointer disabled:bg-charcoal-medium/50 disabled:text-zinc-600 disabled:border-charcoal-border disabled:cursor-not-allowed transition-all duration-300"
          >
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-white" />
                <span>Saving Demographics...</span>
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                <span>Save Diagnostic Profile</span>
              </>
            )}
          </button>
        </form>
      </div>
    </ProtectedRoute>
  );
}
