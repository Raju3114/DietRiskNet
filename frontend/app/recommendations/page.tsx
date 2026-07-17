'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '../../lib/store';
import ProtectedRoute from '../../components/ProtectedRoute';
import { motion } from 'framer-motion';
import { Sparkles, CheckCircle2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

interface Recommendation {
  category: string;
  content: string;
  explanation: string;
}

export default function RecommendationsPage() {
  const router = useRouter();
  const currentAnalysis = useAppStore((state) => state.currentAnalysis);

  useEffect(() => {
    if (!currentAnalysis) {
      router.push('/upload');
    }
  }, [currentAnalysis, router]);

  if (!currentAnalysis) return null;

  const { recommendations } = currentAnalysis;

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  } as const;

  const itemVariants = {
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
        <div>
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full border border-brand-emerald/20 bg-brand-emerald/5 text-brand-emerald text-[9px] font-bold uppercase tracking-widest mb-3 w-fit glow-emerald">
            <Sparkles className="h-3.5 w-3.5 text-brand-emerald animate-pulse" />
            <span>Clinical Recommendations</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center space-x-3">
            <span>ExplainDiet Advisory</span>
          </h1>
          <p className="text-zinc-550 text-[10px] font-extrabold uppercase tracking-wider mt-1">Personalized dietary adjustments compiled from RDI margins and XGBoost risk parameters.</p>
        </div>

        {/* ExplainDiet Intro Card */}
        <div className="p-6.5 rounded-2xl bg-charcoal-medium/55 border border-charcoal-border space-y-4 hover:border-brand-emerald/20 transition-all duration-300 shadow-md relative">
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full border border-brand-emerald/20 bg-brand-emerald/5 text-brand-emerald text-[9px] font-bold uppercase tracking-widest">
            <Sparkles className="h-3.5 w-3.5 text-brand-cyan" />
            <span>ExplainDiet Recommendation Engine</span>
          </div>
          <h2 className="text-sm font-extrabold text-white uppercase tracking-wider">Diagnostic Derivation Logic</h2>
          <p className="text-zinc-400 text-xs leading-relaxed font-semibold">
            Our recommendation engine combines predicted disease risks from the XGBoost classifiers with current nutritional input distributions, matching variables against reference bounds. Suggestions clarify the physiological path of your metabolism in response to specific food crops.
          </p>
        </div>

        {/* Recommendations list */}
        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="space-y-5 pt-4 border-t border-charcoal-border/50"
        >
          {recommendations.length > 0 ? (
            recommendations.map((rec: Recommendation, idx: number) => (
              <motion.div 
                key={idx} 
                variants={itemVariants}
                className="p-6 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border hover:border-brand-blue/20 transition-all duration-300 flex flex-col md:flex-row items-start gap-6 relative shadow-md"
              >
                <div className="p-3.5 rounded-xl bg-brand-emerald/10 text-brand-emerald shrink-0 border border-brand-emerald/15 glow-emerald shadow-sm">
                  <CheckCircle2 className="h-5 w-5" />
                </div>
                
                <div className="space-y-3.5 w-full">
                  <div className="flex items-center space-x-3">
                    <span className="text-[8px] font-extrabold text-brand-blue bg-brand-blue/10 border border-brand-blue/15 px-2.5 py-0.5 rounded uppercase tracking-widest">
                      {rec.category}
                    </span>
                  </div>
                  <h3 className="text-xs font-extrabold text-white leading-normal uppercase tracking-wider">{rec.content}</h3>
                  
                  <div className="p-4 rounded-xl bg-charcoal-dark/50 border border-charcoal-border/80 text-xs text-zinc-400 leading-relaxed font-semibold space-y-1">
                    <span className="font-extrabold text-zinc-300 block mb-1 uppercase tracking-wider text-[8px]">Clinical Explanation:</span>
                    <p className="leading-relaxed">{rec.explanation}</p>
                  </div>
                </div>
              </motion.div>
            ))
          ) : (
            <div className="p-16 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border text-center shadow-inner">
              <CheckCircle2 className="h-10 w-10 text-brand-emerald mx-auto mb-4" />
              <h3 className="text-xs font-bold text-white mb-1 uppercase tracking-wider">No Active Recommendations</h3>
              <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Log a new meal with YOLO crops to trigger recommendation mapping.</p>
            </div>
          )}
        </motion.div>

        {/* Navigation Action Buttons */}
        <div className="flex justify-between gap-4 mt-8 pt-6 border-t border-charcoal-border/50">
          <Link href="/predictions" className="px-6 py-3.5 bg-charcoal-medium border border-charcoal-border hover:bg-charcoal-light hover:border-zinc-700 text-zinc-350 hover:text-white text-[10px] font-bold uppercase tracking-widest rounded-xl text-center transition-all flex items-center space-x-2 cursor-pointer">
            <ArrowLeft className="h-4 w-4" />
            <span>Disease Risks</span>
          </Link>
          
          <Link href="/trends" className="px-6 py-3.5 bg-brand-blue hover:bg-brand-blue-hover text-white text-[10px] font-bold uppercase tracking-widest rounded-xl text-center flex items-center space-x-2 shadow-lg shadow-brand-blue/15 border border-brand-blue/20 transition-all cursor-pointer">
            <span>View Longitudinal Trends</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </ProtectedRoute>
  );
}

// Arrow icon helper
function ArrowRight(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      fill="none" 
      viewBox="0 0 24 24" 
      strokeWidth={2.5} 
      stroke="currentColor" 
      className="w-4 h-4"
      {...props}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
    </svg>
  );
}
