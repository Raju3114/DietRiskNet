'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  Upload, ScanLine, Layers, Activity, Gauge, MessageSquareText,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface Stage {
  num: string;
  name: string;
  icon: LucideIcon;
  desc: string;
  feature?: boolean;
}

const STAGES: Stage[] = [
  { num: '01', name: 'Upload', icon: Upload, desc: 'A photo of your meal' },
  { num: '02', name: 'Detect', icon: ScanLine, desc: 'YOLOv8 locates food regions' },
  { num: '03', name: 'Classify', icon: Layers, desc: 'EfficientNet-B3 identifies the dish' },
  {
    num: '04', name: 'Analyze', icon: Activity, desc: 'Nutrition, DCI & NIS indices', feature: true,
  },
  { num: '05', name: 'Predict', icon: Gauge, desc: 'XGBoost disease-risk + fusion' },
  { num: '06', name: 'Explain', icon: MessageSquareText, desc: 'Recommendations & AI guidance' },
];

const container = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
} as const;

const item = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } },
} as const;

export default function PipelineFlow() {
  return (
    <section className="relative z-10 py-10" aria-labelledby="pipeline-title">
      <div className="text-center mb-7">
        <span className="lr-eyebrow inline-flex">Processing Pipeline</span>
        <h2 id="pipeline-title" className="text-2xl md:text-3xl font-extrabold tracking-tight text-foreground mt-4">
          From Image to Dietary Intelligence
        </h2>
        <p className="text-muted-foreground text-sm mt-2 max-w-xl mx-auto">
          Every analysis follows the same deterministic path — from a meal photo
          to explainable dietary insight.
        </p>
      </div>

      <motion.div
        variants={container}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.25 }}
        className="lr-pipeline"
      >
        <div className="lr-rail" aria-hidden="true" />
        <div className="lr-rail-v" aria-hidden="true" />
        {STAGES.map((s) => {
          const Icon = s.icon;
          return (
            <motion.div
              key={s.num}
              variants={item}
              whileHover={{ y: -4 }}
              className={s.feature ? 'lr-stage lr-stage--feature' : 'lr-stage'}
            >
              <span className="lr-stage-node" aria-hidden="true">
                <span className="lr-stage-num">{s.num}</span>
              </span>
              <div className="lr-stage-card">
                <span className="lr-stage-icon">
                  <Icon className="h-4 w-4" aria-hidden="true" />
                </span>
                <h4 className="lr-stage-title">{s.name}</h4>
                <p className="lr-stage-desc">{s.desc}</p>
                {s.feature ? (
                  <div className="lr-stage-badges">
                    <span className="lr-stage-badge lr-stage-badge--gold">DCI</span>
                    <span className="lr-stage-badge lr-stage-badge--emerald">NIS</span>
                    <span className="lr-stage-badge-label">Research indices</span>
                  </div>
                ) : null}
              </div>
            </motion.div>
          );
        })}
      </motion.div>

      <p className="lr-pipeline-note">
        DCI — Dietary Consistency Index&nbsp;&nbsp;·&nbsp;&nbsp;NIS — Nutrient Imbalance Score
      </p>
    </section>
  );
}
