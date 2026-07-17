'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '../lib/store';
import { motion } from 'framer-motion';
import { Activity, ShieldAlert, Sparkles, Brain, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function LandingPage() {
  const token = useAuthStore((state) => state.token);
  const router = useRouter();

  // Redirect if already logged in
  React.useEffect(() => {
    if (token) {
      router.push('/dashboard');
    }
  }, [token, router]);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15
      }
    }
  } as const;

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.5, ease: "easeOut" }
    }
  } as const;

  return (
    <div className="min-h-screen bg-charcoal-dark text-white flex flex-col justify-between overflow-x-hidden selection:bg-brand-blue selection:text-white font-sans">
      {/* Header / Navbar */}
      <header className="max-w-7xl mx-auto w-full px-6 py-6 flex items-center justify-between z-10 border-b border-charcoal-border/50 backdrop-blur-md sticky top-0 bg-charcoal-dark/70">
        <div className="flex items-center space-x-3">
          <div className="h-9 w-9 rounded-xl bg-brand-blue/10 border border-brand-blue/20 flex items-center justify-center glow-blue">
            <Activity className="h-5 w-5 text-brand-blue" />
          </div>
          <span className="font-extrabold text-xl tracking-wider bg-gradient-to-r from-brand-blue via-brand-cyan to-brand-emerald bg-clip-text text-transparent">
            DIETRISKNET
          </span>
        </div>
        <div className="flex items-center space-x-4">
          <Link href="/login" className="px-4 py-2 text-[10px] font-bold uppercase tracking-widest text-zinc-400 hover:text-white transition-colors">
            Login
          </Link>
          <Link href="/register" className="px-5 py-2.5 text-[10px] font-bold uppercase tracking-widest bg-brand-blue hover:bg-brand-blue-hover text-white rounded-xl transition-all duration-300 shadow-md shadow-brand-blue/20 border border-brand-blue/20">
            Get Started
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-grow flex flex-col items-center justify-center text-center px-6 max-w-7xl mx-auto py-20 relative">
        {/* Decorative backdrop lights */}
        <div className="absolute top-10 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-brand-blue/8 rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute bottom-20 left-1/3 w-[300px] h-[300px] bg-brand-cyan/5 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute top-1/3 right-1/4 w-[250px] h-[250px] bg-brand-emerald/4 rounded-full blur-[80px] pointer-events-none" />

        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="flex flex-col items-center"
        >
          <motion.div 
            variants={itemVariants}
            className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full border border-brand-blue/20 bg-brand-blue/5 text-brand-blue text-[9px] font-bold uppercase tracking-widest mb-8 z-10 glow-blue"
          >
            <Sparkles className="h-3.5 w-3.5 text-brand-cyan animate-pulse" />
            <span>Clinical AI Predictive Systems Platform</span>
          </motion.div>

          <motion.h1 
            variants={itemVariants}
            className="text-4xl md:text-6xl lg:text-7xl font-extrabold tracking-tight mb-8 z-10 leading-[1.1] max-w-4xl"
          >
            Vision-Language Food Recognition &{' '}
            <span className="bg-gradient-to-r from-brand-blue via-brand-cyan to-brand-emerald bg-clip-text text-transparent">
              Disease-Risk Dietary Analytics
            </span>
          </motion.h1>

          <motion.p 
            variants={itemVariants}
            className="text-xs md:text-sm text-zinc-400 max-w-2xl mb-12 z-10 leading-relaxed font-semibold uppercase tracking-wider"
          >
            An advanced clinical diagnostics system. Detect nutritional profiles via YOLOv8 crops, map composition tables, compile DCI/NIS indices, and predict metabolic risks.
          </motion.p>

          <motion.div 
            variants={itemVariants}
            className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-6 z-10 mb-24"
          >
            <Link href="/register" className="group px-8 py-4 bg-white text-black hover:bg-zinc-200 font-extrabold rounded-xl transition-all duration-300 flex items-center space-x-2.5 shadow-xl text-[10px] uppercase tracking-widest border border-white">
              <span>Initialize Health Profile</span>
              <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
            </Link>
            <Link href="/about" className="px-8 py-4 bg-charcoal-medium border border-charcoal-border hover:bg-charcoal-light hover:border-zinc-700 transition-all duration-300 text-zinc-300 hover:text-white font-extrabold rounded-xl text-[10px] uppercase tracking-widest">
              Methodology Details
            </Link>
          </motion.div>

          {/* Interactive 7-Stage Workflow Visualization */}
          <motion.div 
            variants={itemVariants}
            className="w-full max-w-5xl z-10 mb-28 text-left"
          >
            <div className="text-center mb-10">
              <span className="text-[9px] text-brand-blue font-extrabold uppercase tracking-widest block mb-2">Automated Inference</span>
              <h2 className="text-xl md:text-2xl font-bold uppercase tracking-wider text-white">Interactive Processing Pipeline</h2>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-7 gap-3.5 relative">
              {[
                { step: "01", name: "Upload Meal", icon: Brain, desc: "Patient submits meal asset.", color: "text-brand-blue border-brand-blue/20 bg-brand-blue/5 glow-blue" },
                { step: "02", name: "YOLO Detection", icon: Activity, desc: "Localization of crop boundaries.", color: "text-brand-cyan border-brand-cyan/20 bg-brand-cyan/5 glow-cyan" },
                { step: "03", name: "EfficientNet", icon: Sparkles, desc: "B0 classifier identifies 360 items.", color: "text-brand-orange border-brand-orange/20 bg-brand-orange/5 glow-orange" },
                { step: "04", name: "Nutrition Lookup", icon: CheckCircle2, desc: "RDI mapping from database.", color: "text-brand-emerald border-brand-emerald/20 bg-brand-emerald/5 glow-emerald" },
                { step: "05", name: "Disease Risk", icon: ShieldAlert, desc: "XGBoost diagnostic classifiers.", color: "text-brand-red border-brand-red/20 bg-brand-red/5 glow-red" },
                { step: "06", name: "Risk Fusion", icon: Activity, desc: "Weighted clinical score formula.", color: "text-brand-blue border-brand-blue/20 bg-brand-blue/5 glow-blue" },
                { step: "07", name: "ExplainDiet", icon: Sparkles, desc: "Personalized action plan output.", color: "text-brand-emerald border-brand-emerald/20 bg-brand-emerald/5 glow-emerald" },
              ].map((stage, idx) => (
                <div key={idx} className="p-4.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border hover:border-zinc-700 transition-all duration-300 flex flex-col justify-between space-y-3 relative group">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-bold text-zinc-500 font-mono">{stage.step}</span>
                    <div className={`p-1.5 rounded-lg border ${stage.color}`}>
                      <stage.icon className="h-3.5 w-3.5" />
                    </div>
                  </div>
                  <div>
                    <h4 className="text-[10px] font-bold uppercase tracking-wider text-white group-hover:text-brand-cyan transition-colors">{stage.name}</h4>
                    <p className="text-[9px] text-zinc-500 leading-normal mt-1">{stage.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Research & Tech Showcase */}
          <motion.div 
            variants={itemVariants}
            className="grid grid-cols-1 md:grid-cols-3 gap-6.5 w-full z-10"
          >
            <div className="p-8 rounded-2xl bg-charcoal-medium/40 border border-charcoal-border hover:border-brand-blue/20 transition-all duration-300 flex flex-col items-center text-center group">
              <div className="p-4 rounded-xl bg-brand-cyan/5 text-brand-cyan mb-6 border border-brand-cyan/15 glow-cyan transition-transform group-hover:scale-105">
                <Brain className="h-6 w-6" />
              </div>
              <h3 className="text-xs font-bold mb-2.5 text-white uppercase tracking-widest">YOLOv8 &amp; EfficientNet</h3>
              <p className="text-[11px] text-zinc-400 leading-relaxed font-semibold">
                Dual-stage vision models execute object localization and deep crop classifications dynamically.
              </p>
            </div>

            <div className="p-8 rounded-2xl bg-charcoal-medium/40 border border-charcoal-border hover:border-brand-blue/20 transition-all duration-300 flex flex-col items-center text-center group">
              <div className="p-4 rounded-xl bg-brand-blue/5 text-brand-blue mb-6 border border-brand-blue/15 glow-blue transition-transform group-hover:scale-105">
                <Activity className="h-6 w-6" />
              </div>
              <h3 className="text-xs font-bold mb-2.5 text-white uppercase tracking-widest">XGBoost Diagnostics</h3>
              <p className="text-[11px] text-zinc-400 leading-relaxed font-semibold">
                Clinical parameters feed four targeted classifiers for Diabetes, Obesity, Hypertension, and Deficiencies.
              </p>
            </div>

            <div className="p-8 rounded-2xl bg-charcoal-medium/40 border border-charcoal-border hover:border-brand-blue/20 transition-all duration-300 flex flex-col items-center text-center group">
              <div className="p-4 rounded-xl bg-brand-emerald/5 text-brand-emerald mb-6 border border-brand-emerald/15 glow-emerald transition-transform group-hover:scale-105">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <h3 className="text-xs font-bold mb-2.5 text-white uppercase tracking-widest">ExplainDiet Engine</h3>
              <p className="text-[11px] text-zinc-400 leading-relaxed font-semibold">
                Translates biochemical markers into natural language explanations and daily medical guides.
              </p>
            </div>
          </motion.div>
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="border-t border-charcoal-border py-8 text-center text-[8px] uppercase tracking-widest text-zinc-550 w-full bg-charcoal-dark z-10">
        <p>&copy; 2026 DietRiskNet Platform. Structured on IEEE architecture paradigms. PyTorch and FastApi compiled.</p>
      </footer>
    </div>
  );
}
