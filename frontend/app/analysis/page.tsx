'use client';

import React, { useRef, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '../../lib/store';
import ProtectedRoute from '../../components/ProtectedRoute';
import AIDietitianCard from '../../components/analysis/AIDietitianCard';
import AIChatPanel from '../../components/analysis/AIChatPanel';
import {
  ArrowRight, ShieldAlert, Sparkles, Scale, Beef, Wheat, Droplet, Flame, Eye, Activity, FileDown, Loader2
} from 'lucide-react';
import Link from 'next/link';
import { API_BASE, api } from '../../services/api';

export default function AnalysisPage() {
  const router = useRouter();
  const currentAnalysis = useAppStore((state) => state.currentAnalysis);
  const hasHydrated = useAppStore((state) => state.hasHydrated);
  const imageContainerRef = useRef<HTMLDivElement>(null);
  
  const [scale, setScale] = useState({ x: 1, y: 1 });
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownloadReport = async () => {
    if (!currentAnalysis || isDownloading) return;
    setIsDownloading(true);
    try {
      await api.downloadReport(currentAnalysis.meal_id);
    } catch (err) {
      console.error('[downloadReport] Failed:', err);
    } finally {
      setIsDownloading(false);
    }
  };

  // Redirect if no analysis data
  useEffect(() => {
    if (hasHydrated && !currentAnalysis) {
      router.push('/upload');
    }
  }, [hasHydrated, currentAnalysis, router]);

  if (!hasHydrated || !currentAnalysis) return null;

  const { items, nutrition, dci, dci_level, nis, nis_level, image_path, ai_dietitian } = currentAnalysis;
  // Only aggregate nutrition visually when at least one recognized food has nutrition data —
  // never show a fabricated "0 kcal" for a meal with no recognized nutrition.
  const hasAnyRecognizedNutrition = items.some((it) => it.nutrition_available !== false);

  // Resolve backend server uploads path (remove static prefix or append base URL)
  const backendBase = API_BASE.replace(/\/api$/, '');
  const fullImageUrl = image_path 
    ? (image_path.startsWith('http') ? image_path : `${backendBase}${image_path}`)
    : '/favicon.ico';

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    const rect = img.getBoundingClientRect();
    
    // Original size vs rendered size scale factors
    setScale({
      x: rect.width / img.naturalWidth,
      y: rect.height / img.naturalHeight
    });
  };

  return (
    <ProtectedRoute>
      <div className="space-y-8 animate-fade-in font-sans">
        <div>
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full border border-brand-cyan/20 bg-brand-cyan/5 text-brand-cyan text-[9px] font-bold uppercase tracking-widest mb-3 w-fit glow-cyan">
            <Eye className="h-3.5 w-3.5 text-brand-cyan" />
            <span>Meal Analysis Report</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground flex items-center space-x-3">
            <span>Visual Crop Localizations</span>
          </h1>
          <p className="text-muted-foreground text-[10px] font-extrabold uppercase tracking-wider mt-1">Computer vision bounding box overlays and recognized nutritional profiles.</p>
        </div>

        {/* Vision overlays and recognized items */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* YOLO Detection Canvas Overlay */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-widest flex items-center space-x-2">
              <Activity className="h-4.5 w-4.5 text-brand-cyan" />
              <span>YOLOv8 Food Detection Overlay</span>
            </h3>
            
            <div 
              ref={imageContainerRef}
              className="relative rounded-2xl overflow-hidden border border-charcoal-border bg-charcoal-medium/30 flex justify-center items-center shadow-lg w-full p-2.5"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img 
                src={fullImageUrl} 
                alt="Meal scan" 
                onLoad={handleImageLoad}
                className="max-w-full max-h-[450px] object-contain rounded-xl"
              />

              {/* Bounding Boxes Layer */}
              {items.map((item, idx) => {
                if (item.x1 === undefined || item.y1 === undefined) return null;
                
                // Scale coordinates
                const left = item.x1 * scale.x;
                const top = item.y1 * scale.y;
                const width = (item.x2! - item.x1) * scale.x;
                const height = (item.y2! - item.y1) * scale.y;

                return (
                  <div 
                    key={idx}
                    className="absolute border-2 border-brand-cyan rounded flex flex-col group transition-all"
                    style={{
                      left: `${left}px`,
                      top: `${top}px`,
                      width: `${width}px`,
                      height: `${height}px`,
                      boxShadow: '0 0 15px rgba(6, 182, 212, 0.4)'
                    }}
                  >
                    <span className="absolute bottom-full left-0 bg-brand-cyan text-black font-extrabold text-[8px] px-2 py-0.5 rounded-t tracking-widest uppercase shadow">
                      {item.display_name || item.name} ({(item.confidence * 100).toFixed(0)}%)
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Mapped Nutrition Items list */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-widest flex items-center space-x-2">
              <Scale className="h-4.5 w-4.5 text-brand-blue" />
              <span>Segmented Biochemical Profiles</span>
            </h3>
            
            <div className="space-y-4 max-h-[450px] overflow-y-auto pr-1">
              {items.map((item, idx) => (
                <div key={idx} className="p-5.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-4 shadow-md hover:border-brand-blue/20 transition-all duration-300">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-[8px] text-brand-blue font-extrabold uppercase tracking-widest bg-brand-blue/10 border border-brand-blue/15 px-2 py-0.5 rounded">Segment #{idx + 1}</span>
                      <h4 className="text-xs font-extrabold text-foreground mt-2 uppercase tracking-wider">{item.display_name || item.name}</h4>
                    </div>
                    <span className="text-[9px] text-muted-foreground font-bold uppercase tracking-widest bg-charcoal-dark border border-charcoal-border px-3 py-1.5 rounded-xl shadow-inner">
                      Mass: {item.weight_g.toFixed(0)}g
                    </span>
                  </div>
                  
                  {item.nutrition_available === false ? (
                    <div className="rounded-xl bg-brand-orange/5 border border-brand-orange/20 p-3 text-center">
                      <span className="text-[9px] font-bold text-brand-orange uppercase tracking-widest">
                        Nutrition data unavailable for this recognized food
                      </span>
                    </div>
                  ) : (
                  <div className="grid grid-cols-4 gap-2 text-center bg-charcoal-dark/40 p-3 rounded-xl border border-charcoal-border/50">
                    <div>
                      <span className="text-[8px] text-muted-foreground font-bold uppercase tracking-widest block mb-1">Energy</span>
                      <span className="text-[10px] font-bold text-brand-orange font-mono">{item.calories.toFixed(0)} kcal</span>
                    </div>
                    <div>
                      <span className="text-[8px] text-muted-foreground font-bold uppercase tracking-widest block mb-1">Carbs</span>
                      <span className="text-[10px] font-bold text-brand-cyan font-mono">{item.carbs.toFixed(1)}g</span>
                    </div>
                    <div>
                      <span className="text-[8px] text-muted-foreground font-bold uppercase tracking-widest block mb-1">Protein</span>
                      <span className="text-[10px] font-bold text-brand-red font-mono">{item.protein.toFixed(1)}g</span>
                    </div>
                    <div>
                      <span className="text-[8px] text-muted-foreground font-bold uppercase tracking-widest block mb-1">Fats</span>
                      <span className="text-[10px] font-bold text-brand-blue font-mono">{item.fats.toFixed(1)}g</span>
                    </div>
                  </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Nutritional Aggregations */}
        <div className="space-y-4 pt-4 border-t border-charcoal-border/50">
          <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Aggregated Meal Nutrition</h2>
          
          {hasAnyRecognizedNutrition ? (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="p-4 rounded-xl bg-charcoal-medium/50 border border-charcoal-border flex items-center space-x-3 shadow-sm hover:border-brand-orange/20 transition-all duration-200">
              <Flame className="h-4.5 w-4.5 text-brand-orange shrink-0" />
              <div>
                <span className="text-[8px] text-muted-foreground font-bold uppercase tracking-widest block">Total Calories</span>
                <span className="text-xs font-extrabold text-foreground font-mono">{nutrition.calories.toFixed(0)} kcal</span>
              </div>
            </div>
            
            <div className="p-4 rounded-xl bg-charcoal-medium/50 border border-charcoal-border flex items-center space-x-3 shadow-sm hover:border-brand-cyan/20 transition-all duration-200">
              <Wheat className="h-4.5 w-4.5 text-brand-cyan shrink-0" />
              <div>
                <span className="text-[8px] text-muted-foreground font-bold uppercase tracking-widest block">Carbohydrates</span>
                <span className="text-xs font-extrabold text-foreground font-mono">{nutrition.carbs.toFixed(1)}g</span>
              </div>
            </div>
            
            <div className="p-4 rounded-xl bg-charcoal-medium/50 border border-charcoal-border flex items-center space-x-3 shadow-sm hover:border-brand-red/20 transition-all duration-200">
              <Beef className="h-4.5 w-4.5 text-brand-red shrink-0" />
              <div>
                <span className="text-[8px] text-muted-foreground font-bold uppercase tracking-widest block">Protein</span>
                <span className="text-xs font-extrabold text-foreground font-mono">{nutrition.protein.toFixed(1)}g</span>
              </div>
            </div>
            
            <div className="p-4 rounded-xl bg-charcoal-medium/50 border border-charcoal-border flex items-center space-x-3 shadow-sm hover:border-brand-blue/20 transition-all duration-200">
              <Droplet className="h-4.5 w-4.5 text-brand-blue shrink-0" />
              <div>
                <span className="text-[8px] text-muted-foreground font-bold uppercase tracking-widest block">Fats</span>
                <span className="text-xs font-extrabold text-foreground font-mono">{nutrition.fats.toFixed(1)}g</span>
              </div>
            </div>
            
            <div className="p-4 rounded-xl bg-charcoal-medium/50 border border-charcoal-border flex items-center space-x-3 shadow-sm hover:border-brand-cyan/20 transition-all duration-200 col-span-2 md:col-span-1">
              <Scale className="h-4.5 w-4.5 text-brand-cyan shrink-0" />
              <div>
                <span className="text-[8px] text-muted-foreground font-bold uppercase tracking-widest block">Sodium</span>
                <span className="text-xs font-extrabold text-foreground font-mono">{nutrition.sodium.toFixed(0)} mg</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-xl bg-brand-orange/5 border border-brand-orange/20 p-3 text-center">
            <span className="text-[9px] font-bold text-brand-orange uppercase tracking-widest">Nutrition data unavailable for this meal</span>
          </div>
        )}
        </div>

        {/* DCI & NIS Indices Card */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-charcoal-border/50">
          <div className="p-5.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-2.5 shadow-md hover:border-brand-emerald/20 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest">Timing Consistency (DCI)</span>
              <span className="px-2 py-0.5 rounded bg-charcoal-dark text-[8px] font-extrabold text-muted-foreground border border-charcoal-border uppercase tracking-widest">{dci_level ?? 'Not Available'}</span>
            </div>
            <span className="text-2xl font-black text-foreground tracking-tight font-mono">
              {dci != null ? <>{`${(dci * 100).toFixed(0)}`} <span className="text-xs text-muted-foreground">/ 100</span></> : 'N/A'}
            </span>
          </div>

          <div className="p-5.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-2.5 shadow-md hover:border-brand-orange/20 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest">Nutrient Imbalance (NIS)</span>
              <span className="px-2 py-0.5 rounded bg-charcoal-dark text-[8px] font-extrabold text-muted-foreground border border-charcoal-border uppercase tracking-widest">{nis_level ?? 'Not Available'}</span>
            </div>
            <span className="text-2xl font-black text-foreground tracking-tight font-mono">{nis != null ? nis.toFixed(2) : 'N/A'}</span>
          </div>
        </div>

        {/* AI Dietitian + chat — rendered only when the backend returned a result */}
        {ai_dietitian != null && (
          <div className="space-y-4 pt-2">
            <AIDietitianCard ai={ai_dietitian} />
            <AIChatPanel mealId={currentAnalysis.meal_id} />
          </div>
        )}

        {/* Redirect buttons to prediction / recommendations */}
        <div className="flex flex-col sm:flex-row items-center justify-end gap-4 mt-8 pt-6 border-t border-charcoal-border/50">
          <button
            type="button"
            onClick={handleDownloadReport}
            disabled={isDownloading}
            aria-label="Download meal report as PDF"
            className="w-full sm:w-auto px-6 py-3.5 bg-charcoal-medium border border-charcoal-border hover:bg-charcoal-light hover:border-brand-blue/40 text-muted-foreground hover:text-foreground text-[10px] font-bold uppercase tracking-widest rounded-xl text-center flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isDownloading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Preparing PDF</span>
              </>
            ) : (
              <>
                <FileDown className="h-4 w-4 text-brand-blue" />
                <span>Download Report</span>
              </>
            )}
          </button>

          <Link href="/predictions" className="w-full sm:w-auto px-6 py-3.5 bg-charcoal-medium border border-charcoal-border hover:bg-charcoal-light hover:border-zinc-700 text-muted-foreground hover:text-foreground text-[10px] font-bold uppercase tracking-widest rounded-xl text-center flex items-center justify-center space-x-2 transition-all cursor-pointer">
            <ShieldAlert className="h-4 w-4 text-brand-red" />
            <span>View Disease Risks</span>
          </Link>
          
          <Link href="/recommendations" className="w-full sm:w-auto px-6 py-3.5 bg-brand-blue hover:bg-brand-blue-hover text-white text-[10px] font-bold uppercase tracking-widest rounded-xl text-center flex items-center justify-center space-x-2 shadow-lg shadow-brand-blue/15 border border-brand-blue/20 transition-all cursor-pointer">
            <Sparkles className="h-4 w-4 text-brand-cyan" />
            <span>Generate ExplainDiet Advice</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </ProtectedRoute>
  );
}
