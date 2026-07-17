'use client';

import React from 'react';
import ProtectedRoute from '../../components/ProtectedRoute';
import { Info, Brain, Activity } from 'lucide-react';

export default function AboutPage() {
  return (
    <ProtectedRoute>
      <div className="max-w-3xl mx-auto space-y-8 animate-fade-in font-sans">
        <div>
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full border border-brand-cyan/20 bg-brand-cyan/5 text-brand-cyan text-[9px] font-bold uppercase tracking-widest mb-3 w-fit glow-cyan">
            <Info className="h-3.5 w-3.5 text-brand-cyan" />
            <span>Information Portal</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center space-x-3">
            <span>About DietRiskNet</span>
          </h1>
          <p className="text-zinc-500 text-xs font-semibold uppercase tracking-wider mt-1">Capstone vision and developmental framework.</p>
        </div>

        <div className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-6 shadow-md hover:border-brand-blue/20 transition-all duration-300">
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <Brain className="h-5 w-5 text-brand-blue" />
            <span>Project Vision</span>
          </h2>
          <p className="text-xs text-zinc-400 leading-relaxed font-semibold">
            DietRiskNet was conceptualized as a Capstone Project to address the global challenge of metabolic complications associated with modern dietary patterns. By marrying computer vision (YOLOv8 &amp; EfficientNet) with clinical-grade classifiers (XGBoost) and detailed nutritional tables, DietRiskNet provides individuals with diagnostic transparency.
          </p>
          <p className="text-xs text-zinc-400 leading-relaxed font-semibold">
            Our system acts as a personalized health advisor, illustrating how every food choice shifts clinical risk probability vectors, driving preventative care before complications manifest.
          </p>
        </div>

        <div className="p-6.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-6 shadow-md hover:border-brand-blue/20 transition-all duration-300">
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <Activity className="h-5 w-5 text-brand-cyan glow-cyan" />
            <span>Capstone Team &amp; Credits</span>
          </h2>
          <p className="text-xs text-zinc-400 leading-relaxed font-semibold">
            Developed by a team of Senior Software Architects, ML Engineers, and UI/UX designers dedicated to building robust medical AI systems.
          </p>
          <div className="pt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-charcoal-dark border border-charcoal-border flex items-center justify-between text-zinc-350 text-xs font-medium">
              <span>Primary Contact:</span>
              <span className="font-semibold text-white">info@dietrisknet.org</span>
            </div>
            <div className="p-4 rounded-xl bg-charcoal-dark border border-charcoal-border flex items-center justify-between text-zinc-350 text-xs font-medium">
              <span>Version:</span>
              <span className="font-semibold text-white">1.0.0 (Release)</span>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
