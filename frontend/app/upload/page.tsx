'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '../../lib/store';
import { api } from '../../services/api';
import ProtectedRoute from '../../components/ProtectedRoute';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Sparkles, Activity, FileImage } from 'lucide-react';

export default function UploadPage() {
  const router = useRouter();
  const setCurrentAnalysis = useAppStore((state) => state.setCurrentAnalysis);
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  const steps = [
    'Uploading meal image assets to clinical server...',
    'Initializing spatial object detectors...',
    'Running YOLOv8 Food Crop Localization...',
    'Compiling bounding box coordinates matrix...',
    'Cropping food item region matrices...',
    'Running EfficientNet Deep Classifier...',
    'Classifying items into 118 nutritional bounds...',
    'Mapping to Indian food composition table database...',
    'Calculating cumulative NIS imbalance values...',
    'Generating Timing and Portion Consistency Index (DCI)...',
    'Executing XGBoost Diabetes Mellitus diagnostics...',
    'Executing XGBoost Obesity Index diagnostics...',
    'Executing XGBoost Hypertension diagnostics...',
    'Evaluating RDA Nutritional Deficiency parameters...',
    'Calculating Fused Risk Score probabilities...',
    'Compiling ExplainDiet personalized recommendations...',
    'Committing diagnostic record to database...',
  ];

  // Rotate steps animation while loading
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | undefined;
    let timer: ReturnType<typeof setTimeout> | undefined;
    if (loading) {
      interval = setInterval(() => {
        setStepIndex((prev) => (prev + 1) % steps.length);
      }, 1500);
    } else {
      timer = setTimeout(() => {
        setStepIndex(0);
      }, 0);
    }
    return () => {
      if (interval) clearInterval(interval);
      if (timer) clearTimeout(timer);
    };
  }, [loading, steps.length]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setLoading(true);
    try {
      const res = await api.analyzeMeal(selectedFile, notes);
      setCurrentAnalysis(res);
      router.push('/analysis');
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      alert(error.message || 'Analysis failed. Make sure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="max-w-2xl mx-auto space-y-8 animate-fade-in font-sans">
        <div>
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full border border-brand-cyan/20 bg-brand-cyan/5 text-brand-cyan text-[9px] font-bold uppercase tracking-widest mb-3 w-fit glow-cyan">
            <Activity className="h-3.5 w-3.5 text-brand-cyan animate-pulse" />
            <span>Computer Vision Ingestion</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center space-x-3">
            <span>AI Food Scanner</span>
          </h1>
          <p className="text-zinc-550 text-[10px] font-extrabold uppercase tracking-wider mt-1">Upload meal photo for YOLOv8 crop localization &amp; EfficientNet diagnostics analysis.</p>
        </div>

        <AnimatePresence mode="wait">
          {loading ? (
            /* Loading Status Dashboard */
            <motion.div 
              key="loading"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="p-10 rounded-2xl bg-charcoal-medium/50 border border-brand-blue/20 text-center flex flex-col items-center justify-center space-y-6 min-h-[400px] shadow-2xl glow-blue"
            >
              <div className="relative">
                <div className="h-16 w-16 border-4 border-brand-blue border-t-transparent rounded-full animate-spin" />
                <Activity className="absolute inset-0 m-auto h-6 w-6 text-brand-cyan animate-pulse" />
              </div>
              
              <div className="space-y-3.5 max-w-md">
                <h3 className="text-[10px] font-extrabold uppercase tracking-widest text-zinc-400">Running Vision &amp; Clinical Pipeline</h3>
                <p className="text-xs text-brand-cyan font-bold animate-pulse h-12 flex items-center justify-center leading-relaxed">
                  {steps[stepIndex]}
                </p>
              </div>

              <div className="w-full max-w-xs bg-charcoal-light rounded-full h-1.5 overflow-hidden border border-charcoal-border/55">
                <div 
                  className="bg-gradient-to-r from-brand-blue via-brand-cyan to-brand-emerald h-full rounded-full transition-all duration-350" 
                  style={{ width: `${((stepIndex + 1) / steps.length) * 100}%` }}
                />
              </div>
              
              <span className="text-[9px] font-extrabold text-zinc-500 uppercase tracking-widest">
                Pipeline Stage {stepIndex + 1} of {steps.length}
              </span>
            </motion.div>
          ) : (
            /* Upload Form */
            <motion.form 
              key="form"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              onSubmit={handleSubmit} 
              className="space-y-6"
            >
              {/* Drag Drop Area */}
              <div 
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                className={`
                  border-2 border-dashed rounded-3xl p-12 text-center flex flex-col items-center justify-center space-y-4 cursor-pointer transition-all duration-300 relative overflow-hidden group
                  ${previewUrl 
                    ? 'border-charcoal-border bg-charcoal-medium/20 hover:border-brand-blue/30' 
                    : 'border-charcoal-border bg-charcoal-medium/40 hover:border-brand-blue/40 hover:bg-charcoal-medium/60 hover:shadow-lg hover:shadow-brand-blue/5'}
                `}
                onClick={() => document.getElementById('meal-file')?.click()}
              >
                <input 
                  id="meal-file"
                  type="file" 
                  accept="image/*"
                  className="hidden"
                  onChange={handleFileChange}
                />

                {previewUrl ? (
                  /* Preview Image */
                  <div className="relative w-full max-h-[300px] rounded-2xl overflow-hidden flex justify-center">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img 
                      src={previewUrl} 
                      alt="Meal preview" 
                      className="object-cover max-h-[300px] rounded-xl shadow-lg border border-charcoal-border/50 group-hover:scale-[1.01] transition-transform duration-300"
                    />
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity duration-200">
                      <div className="flex items-center space-x-2 bg-charcoal-dark border border-charcoal-border px-4 py-2 rounded-xl text-[10px] font-bold uppercase tracking-widest text-brand-blue shadow-lg">
                        <FileImage className="h-4 w-4" />
                        <span>Change Photo</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Helper Prompt */
                  <>
                    <div className="p-4 rounded-xl bg-charcoal-dark border border-charcoal-border text-zinc-500 group-hover:text-brand-blue group-hover:border-brand-blue/20 transition-all glow-blue">
                      <Upload className="h-6 w-6" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-white uppercase tracking-wider">Drag and drop your food photo</h4>
                      <p className="text-[9px] text-zinc-500 font-bold uppercase tracking-widest mt-1">Supports PNG, JPG, or JPEG up to 10MB</p>
                    </div>
                  </>
                )}
              </div>

              {/* Meal Notes */}
              <div className="space-y-2">
                <label className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Optional Clinical Metadata (Meal Notes)</label>
                <textarea 
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g., Breakfast post-workout, default portion sizes, minimal added salt"
                  rows={3}
                  className="w-full bg-charcoal-medium/55 border border-charcoal-border rounded-2xl p-4 text-xs font-semibold text-white focus:outline-none focus:border-brand-blue/50 focus:ring-1 focus:ring-brand-blue/20 transition-all resize-none placeholder:text-zinc-600 shadow-inner"
                />
              </div>

              {/* Submit Trigger */}
              <button 
                type="submit" 
                disabled={!selectedFile}
                className="w-full py-4 bg-brand-blue hover:bg-brand-blue-hover text-white font-extrabold rounded-xl text-[10px] uppercase tracking-widest flex items-center justify-center space-x-2 shadow-lg shadow-brand-blue/15 border border-brand-blue/20 cursor-pointer disabled:bg-charcoal-medium/50 disabled:text-zinc-600 disabled:border-charcoal-border disabled:cursor-not-allowed transition-all duration-300"
              >
                <Sparkles className="h-4 w-4" />
                <span>Execute Diagnostic Analysis</span>
              </button>
            </motion.form>
          )}
        </AnimatePresence>
      </div>
    </ProtectedRoute>
  );
}
