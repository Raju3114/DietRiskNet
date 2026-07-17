'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '../../lib/store';
import ProtectedRoute from '../../components/ProtectedRoute';
import { ShieldAlert, Sparkles, Scale, Heart, Info, Droplet } from 'lucide-react';
import Link from 'next/link';

export default function PredictionsPage() {
  const router = useRouter();
  const currentAnalysis = useAppStore((state) => state.currentAnalysis);

  useEffect(() => {
    if (!currentAnalysis) {
      router.push('/upload');
    }
  }, [currentAnalysis, router]);

  if (!currentAnalysis) return null;

  const { predictions, fusion } = currentAnalysis;

  const getRiskBg = (risk: number) => {
    if (risk < 0.3) return 'bg-brand-emerald/10 border-brand-emerald/20 text-brand-emerald';
    if (risk < 0.6) return 'bg-brand-orange/10 border-brand-orange/20 text-brand-orange';
    return 'bg-brand-red/10 border-brand-red/20 text-brand-red';
  };

  const getFusionColor = (lvl: string) => {
    switch (lvl.toLowerCase()) {
      case 'low': return 'text-brand-emerald border-brand-emerald/20 bg-brand-emerald/10 glow-emerald';
      case 'moderate': return 'text-brand-orange border-brand-orange/20 bg-brand-orange/10 glow-orange';
      case 'high': return 'text-brand-red border-brand-red/20 bg-brand-red/10 glow-red';
      default: return 'text-brand-blue border-brand-blue/20 bg-brand-blue/10 glow-blue';
    }
  };

  const diseaseList = [
    { name: 'Diabetes Mellitus', risk: predictions.diabetes_risk, desc: 'XGBoost clinical model evaluating glucose-insulin patterns, BMI, and family demographics.', icon: Droplet, color: 'text-brand-cyan border-brand-cyan/15 bg-brand-cyan/5' },
    { name: 'Obesity Index', risk: predictions.obesity_risk, desc: 'Obesity dataset features evaluating calorie surpluses, dietary frequencies, and activity.', icon: Scale, color: 'text-brand-orange border-brand-orange/15 bg-brand-orange/5' },
    { name: 'Hypertension Stress', risk: predictions.hypertension_risk, desc: 'Blood pressure models examining sodium-salt ratios and clinical volume indices.', icon: Heart, color: 'text-brand-red border-brand-red/15 bg-brand-red/5' },
    { name: 'Nutritional Deficiency', risk: predictions.deficiency_risk, desc: 'RDA percentages examining vitamin C, Vitamin D, folate, calcium, and iron levels.', icon: Info, color: 'text-brand-emerald border-brand-emerald/15 bg-brand-emerald/5' },
  ];

  return (
    <ProtectedRoute>
      <div className="space-y-8 animate-fade-in font-sans">
        <div>
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full border border-brand-red/20 bg-brand-red/5 text-brand-red text-[9px] font-bold uppercase tracking-widest mb-3 w-fit glow-red">
            <ShieldAlert className="h-3.5 w-3.5 text-brand-red animate-pulse" />
            <span>Clinical Risk Forecasting</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center space-x-3">
            <span>Metabolic Risk Assessment</span>
          </h1>
          <p className="text-zinc-550 text-[10px] font-extrabold uppercase tracking-wider mt-1">Independent XGBoost diagnostic forecasts compiled via patient demographics and meal nutrition trends.</p>
        </div>

        {/* Fusion Summary */}
        <div className="p-8 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border flex flex-col md:flex-row items-center justify-between gap-8 hover:border-brand-blue/20 transition-all duration-300 shadow-md relative overflow-hidden">
          <div className="space-y-3 max-w-xl">
            <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full border border-brand-blue/20 bg-brand-blue/5 text-brand-blue text-[9px] font-bold uppercase tracking-widest">
              <Sparkles className="h-3.5 w-3.5 text-brand-cyan animate-pulse" />
              <span>Weighted Risk Fusion</span>
            </div>
            <h2 className="text-xl font-extrabold text-white uppercase tracking-wider"> unified metabolic index</h2>
            <p className="text-zinc-400 text-xs leading-relaxed font-semibold">
              We compile predictions, timing consistency parameters (DCI), and nutrient baseline deviations (NIS) into a single risk profile using an IEEE-validated weights matrix.
            </p>
          </div>
          
          <div className="text-center bg-charcoal-dark/60 border border-charcoal-border/80 px-8 py-6.5 rounded-xl min-w-[220px] shadow-inner">
            <span className="text-[9px] text-zinc-500 font-bold uppercase tracking-widest block mb-2.5">Fused Risk Probability</span>
            <span className="text-5xl font-black text-white block font-mono">{(fusion.fused_score * 100).toFixed(0)}%</span>
            <span className={`inline-block mt-3.5 px-3 py-1 rounded-full text-[9px] font-extrabold border uppercase tracking-wider ${getFusionColor(fusion.risk_level)}`}>
              {fusion.risk_level} Risk Level
            </span>
          </div>
        </div>

        {/* Diagnostic Disease Cards Grid */}
        <div className="space-y-4 pt-4 border-t border-charcoal-border/50">
          <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest flex items-center space-x-2">
            <ShieldAlert className="h-4 w-4 text-brand-blue" />
            <span>Target Disease Classifier Outcomes</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {diseaseList.map((disease, idx) => {
              const Icon = disease.icon;
              return (
                <div key={idx} className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border flex flex-col justify-between space-y-4 shadow-md hover:border-brand-blue/20 transition-all duration-300">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3.5">
                      <div className={`p-3 rounded-xl border ${disease.color} shadow-md`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <h4 className="text-xs font-extrabold text-white uppercase tracking-wider">{disease.name}</h4>
                        <span className="text-[8px] text-zinc-500 font-extrabold uppercase tracking-widest block mt-1">XGBoost Classifier</span>
                      </div>
                    </div>
                    
                    <span className={`px-3 py-1.5 rounded-xl text-[9px] font-extrabold border uppercase tracking-wider ${getRiskBg(disease.risk)}`}>
                      {(disease.risk * 100).toFixed(0)}% Risk
                    </span>
                  </div>

                  <p className="text-xs text-zinc-400 leading-relaxed font-semibold">{disease.desc}</p>
                  
                  {/* Progress bar */}
                  <div className="space-y-1">
                    <div className="w-full bg-charcoal-dark rounded-full h-1 overflow-hidden border border-charcoal-border/30">
                      <div 
                        className={`h-full rounded-full transition-all duration-500 ${
                          disease.risk < 0.3 ? 'bg-brand-emerald' : (disease.risk < 0.6 ? 'bg-brand-orange' : 'bg-brand-red')
                        }`}
                        style={{ width: `${disease.risk * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Navigation Action Buttons */}
        <div className="flex justify-end gap-4 mt-8 pt-6 border-t border-charcoal-border/50">
          <Link href="/analysis" className="px-6 py-3.5 bg-charcoal-medium border border-charcoal-border hover:bg-charcoal-light hover:border-zinc-700 text-zinc-350 hover:text-white text-[10px] font-bold uppercase tracking-widest rounded-xl text-center transition-all cursor-pointer">
            Back to Meal Nutrition
          </Link>
          <Link href="/recommendations" className="px-6 py-3.5 bg-brand-blue hover:bg-brand-blue-hover text-white text-[10px] font-bold uppercase tracking-widest rounded-xl text-center flex items-center justify-center space-x-2 shadow-lg shadow-brand-blue/15 border border-brand-blue/20 transition-all cursor-pointer">
            <span>View Recommendations</span>
            <Sparkles className="h-4 w-4 text-brand-cyan" />
          </Link>
        </div>
      </div>
    </ProtectedRoute>
  );
}
