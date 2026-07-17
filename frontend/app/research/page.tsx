'use client';

import React from 'react';
import ProtectedRoute from '../../components/ProtectedRoute';
import { BookOpen, Brain, Activity, ShieldAlert, CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';

export default function ResearchPage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  } as const;

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 15 } }
  } as const;

  return (
    <ProtectedRoute>
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="max-w-4xl mx-auto space-y-12 animate-fade-in font-sans"
      >
        <motion.div variants={itemVariants}>
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full border border-brand-blue/20 bg-brand-blue/5 text-brand-blue text-[9px] font-bold uppercase tracking-widest mb-3 w-fit glow-blue">
            <BookOpen className="h-3.5 w-3.5 text-brand-blue" />
            <span>Academic Methodology</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center space-x-3">
            <span>Research Publication Overview</span>
          </h1>
          <p className="text-zinc-550 text-[10px] font-extrabold uppercase tracking-wider mt-1">Unified vision-language pipelines, XGBoost clinical matrices, and weighted risk fusion paradigms.</p>
        </motion.div>

        {/* Vision Pipeline Section */}
        <motion.section variants={itemVariants} className="space-y-4">
          <div className="flex items-center space-x-3 border-b border-charcoal-border/50 pb-3">
            <Brain className="h-5 w-5 text-brand-cyan glow-cyan" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">1. Vision-Language Crop Segmentation</h2>
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed font-semibold">
            DietRiskNet implements a dual-stage vision architecture. First, a custom **YOLOv8** model performs multi-class object detection, generating localized bounding box coordinate matrices for food items in a single scan. Each recognized region is then cropped and processed through a fine-tuned **EfficientNet-B0** convolutional neural network, classifying crops into 360 unique food types.
          </p>
          <div className="p-5.5 rounded-2xl bg-charcoal-medium/50 border border-charcoal-border space-y-3.5 shadow-md">
            <span className="text-[9px] font-extrabold text-zinc-400 uppercase tracking-widest block">Model Specifications</span>
            <ul className="text-xs text-zinc-300 space-y-3">
              <li className="flex items-start space-x-3">
                <CheckCircle className="h-4 w-4 text-brand-cyan mt-0.5 shrink-0" />
                <span className="font-semibold text-zinc-305">YOLOv8 Weights: <code className="text-brand-cyan bg-charcoal-light border border-charcoal-border/80 px-2 py-0.5 rounded font-mono text-[9px]">DietRiskNet_FoodDetector_YOLOv8.pt</code> (18 detection classes)</span>
              </li>
              <li className="flex items-start space-x-3">
                <CheckCircle className="h-4 w-4 text-brand-cyan mt-0.5 shrink-0" />
                <span className="font-semibold text-zinc-305">EfficientNet Backbone: Configurable (defaults to B0 with 360 food classification matrices)</span>
              </li>
              <li className="flex items-start space-x-3">
                <CheckCircle className="h-4 w-4 text-brand-cyan mt-0.5 shrink-0" />
                <span className="font-semibold text-zinc-305">Feature Mapper: Interfaced against a library of 1014 Indian dishes with 11 nutritional bounds.</span>
              </li>
            </ul>
          </div>
        </motion.section>

        {/* Prediction Pipeline Section */}
        <motion.section variants={itemVariants} className="space-y-4">
          <div className="flex items-center space-x-3 border-b border-charcoal-border/50 pb-3">
            <Activity className="h-5 w-5 text-brand-blue glow-blue" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">2. XGBoost Clinical Classifiers</h2>
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed font-semibold">
            The diagnostic disease-risk scoring is driven by four independent **XGBoost Classifier** models. These models are trained on distinct clinical datasets, mapping patient parameters, diet consistency scores, and cumulative nutrient imbalances to hazard probabilities.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-5 rounded-xl bg-charcoal-medium/50 border border-charcoal-border space-y-2.5 hover:border-brand-blue/20 transition-all duration-200">
              <div className="flex items-center space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-brand-cyan glow-cyan" />
                <h4 className="text-[10px] font-extrabold text-white uppercase tracking-widest">Diabetes Mellitus Model</h4>
              </div>
              <p className="text-[10px] text-zinc-405 leading-relaxed font-semibold">
                Inputs: Gender, Age, Hypertension history, Heart disease history, Smoking history, BMI, HbA1c levels, and Blood glucose levels.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-charcoal-medium/50 border border-charcoal-border space-y-2.5 hover:border-brand-orange/20 transition-all duration-200">
              <div className="flex items-center space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-brand-orange glow-orange" />
                <h4 className="text-[10px] font-extrabold text-white uppercase tracking-widest">Obesity Index Model</h4>
              </div>
              <p className="text-[10px] text-zinc-405 leading-relaxed font-semibold">
                Inputs: Gender, Age, Height, Weight, Family history of obesity, FAVC (High caloric intake frequency), FCVC (Vegetable consumption frequency), NCP (Meals count), CAEC (Eating between meals), FAF (Physical activity), TUE (Screen time).
              </p>
            </div>

            <div className="p-5 rounded-xl bg-charcoal-medium/50 border border-charcoal-border space-y-2.5 hover:border-brand-red/20 transition-all duration-200">
              <div className="flex items-center space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-brand-red glow-red" />
                <h4 className="text-[10px] font-extrabold text-white uppercase tracking-widest">Hypertension Model</h4>
              </div>
              <p className="text-[10px] text-zinc-405 leading-relaxed font-semibold">
                Inputs: Age, Daily Salt Intake (sodium), Stress Score, Blood Pressure History, Sleep Duration, BMI, Medication history, Family history, Exercise levels, and Smoking status.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-charcoal-medium/50 border border-charcoal-border space-y-2.5 hover:border-brand-emerald/20 transition-all duration-200">
              <div className="flex items-center space-x-2">
                <div className="w-1.5 h-1.5 rounded-full bg-brand-emerald glow-emerald" />
                <h4 className="text-[10px] font-extrabold text-white uppercase tracking-widest">Nutritional Deficiency Model</h4>
              </div>
              <p className="text-[10px] text-zinc-405 leading-relaxed font-semibold">
                Inputs: Age, Gender, BMI, RDA percentages (Vitamin A, Vitamin C, Vitamin D, Vitamin E, Vitamin B12, Folate, Calcium, Iron), Hemoglobin levels, and specific physiological symptoms.
              </p>
            </div>
          </div>
        </motion.section>

        {/* Risk Fusion Section */}
        <motion.section variants={itemVariants} className="space-y-4">
          <div className="flex items-center space-x-3 border-b border-charcoal-border/50 pb-3">
            <ShieldAlert className="h-5 w-5 text-brand-red glow-red" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">3. Fused Diagnostic Probability Matrix</h2>
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed font-semibold">
            Instead of examining metrics in isolation, DietRiskNet uses a weighted risk fusion algorithm configured by <code className="text-brand-blue bg-charcoal-light border border-charcoal-border/80 px-2 py-0.5 rounded font-mono text-[9px]">DietRiskNet_RiskFusion_Config.json</code>. The formula fuses consistency (DCI), imbalances (NIS), and predicted disease probabilities:
          </p>
          <div className="p-6 rounded-xl bg-charcoal-dark border border-charcoal-border/80 text-center font-mono text-[10px] text-brand-blue overflow-x-auto shadow-inner leading-relaxed select-all">
            Fused Score = 0.25 × (1 - DCI) + 0.25 × NIS + 0.20 × Diabetes + 0.15 × Obesity + 0.10 × Hypertension + 0.05 × Deficiency
          </div>
        </motion.section>
      </motion.div>
    </ProtectedRoute>
  );
}
