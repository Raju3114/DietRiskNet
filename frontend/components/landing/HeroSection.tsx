'use client';

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';
import IntelligenceCore from './IntelligenceCore';

const container = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
} as const;

const item = {
  hidden: { opacity: 0, y: 18 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
} as const;

export default function HeroSection() {
  return (
    <section className="lr-hero relative z-10">
      {/* Left — copy */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="visible"
      >
        <motion.span variants={item} className="lr-eyebrow">
          <Sparkles className="h-3 w-3" aria-hidden="true" />
          AI-Powered Dietary Intelligence
        </motion.span>

        <motion.h1 variants={item} className="lr-headline">
          Understand Your Meals.
          <br />
          Discover Your <span className="lr-grad">Dietary Risk</span>.
          <br />
          Improve What Comes Next.
        </motion.h1>

        <motion.p variants={item} className="lr-lede">
          DietRiskNet combines computer vision, nutritional analytics, dietary
          consistency modelling, risk prediction and explainable AI guidance to
          transform a meal image into actionable dietary insight.
        </motion.p>

        <motion.div variants={item} className="flex flex-wrap items-center gap-4">
          <Link href="/register" className="lr-cta-primary">
            Analyze Your Meal
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
          <Link href="/about" className="lr-cta-secondary">
            Explore the Methodology
          </Link>
        </motion.div>

        <motion.div variants={item} className="lr-trust">
          <span>YOLOv8</span>
          <span>EfficientNet-B3</span>
          <span>XGBoost</span>
          <span>DCI</span>
          <span>NIS</span>
          <span>Local AI</span>
        </motion.div>
      </motion.div>

      {/* Right — 3D intelligence visual */}
      <IntelligenceCore />
    </section>
  );
}
