'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Eye, Brain, MessageCircle, Image as ImageIcon, ScanLine, ChevronRight } from 'lucide-react';

const PANELS = [
  {
    num: '01',
    icon: Eye,
    title: 'Computer Vision',
    tech: 'YOLOv8 + EfficientNet-B3',
    desc: 'Detect and classify foods from meal imagery into 118 recognized dishes.',
    viz: 'vision' as const,
  },
  {
    num: '02',
    icon: Brain,
    title: 'Dietary Intelligence',
    tech: 'Nutrition + DCI + NIS + Risk Fusion',
    desc: 'Transform meal composition into interpretable dietary indicators.',
    viz: 'gauge' as const,
  },
  {
    num: '03',
    icon: MessageCircle,
    title: 'Explainable Guidance',
    tech: 'Rule Recommendations + Local AI Coach',
    desc: 'Translate analysis into understandable dietary guidance — powered by a local LLM (Ollama).',
    viz: 'chat' as const,
  },
] as const;

const container = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12 } },
} as const;

const item = {
  hidden: { opacity: 0, y: 22 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.55, ease: 'easeOut' } },
} as const;

function VisionMini() {
  return (
    <div className="lr-viz-box lr-viz-vision" aria-hidden="true">
      <span className="lr-viz-corner tl" />
      <span className="lr-viz-corner br" />
      <div className="lr-viz-flow">
        <div className="lr-viz-step">
          <span className="lr-viz-step-icon">
            <ImageIcon className="h-3.5 w-3.5" />
          </span>
          <span className="lr-viz-step-label">Meal</span>
        </div>
        <ChevronRight className="lr-viz-flow-arrow" />
        <div className="lr-viz-step">
          <span className="lr-viz-step-icon lr-viz-step-icon--accent">
            <ScanLine className="h-3.5 w-3.5" />
          </span>
          <span className="lr-viz-step-label">Detect</span>
        </div>
        <ChevronRight className="lr-viz-flow-arrow" />
        <div className="lr-viz-step">
          <span className="lr-viz-chip">Idli · 84%</span>
          <span className="lr-viz-step-label">Classify</span>
        </div>
      </div>
    </div>
  );
}

function MiniVisual({ kind }: { kind: 'vision' | 'gauge' | 'chat' }) {
  if (kind === 'vision') {
    return <VisionMini />;
  }
  if (kind === 'gauge') {
    return (
      <div className="h-[84px] flex items-center justify-center gap-4" aria-hidden="true">
        <div className="lr-viz-gauge shrink-0" />
        <div className="flex flex-col gap-1.5 text-[9px] font-bold text-muted-foreground uppercase tracking-widest">
          <span className="flex items-center gap-1.5">
            <i className="w-2 h-2 rounded-full bg-brand-emerald inline-block" />DCI
          </span>
          <span className="flex items-center gap-1.5">
            <i className="w-2 h-2 rounded-full bg-brand-orange inline-block" />NIS
          </span>
          <span className="flex items-center gap-1.5">
            <i className="w-2 h-2 rounded-full bg-brand-primary inline-block" />Risk
          </span>
        </div>
      </div>
    );
  }
  return (
    <div className="h-[84px] flex flex-col justify-center gap-1.5" aria-hidden="true">
      <div className="lr-viz-bubble user self-end">How can I reduce sodium?</div>
      <div className="lr-viz-bubble ai">Try herbs, less salt, potassium-rich foods.</div>
    </div>
  );
}

export default function TechnologyPanel() {
  return (
    <section className="relative z-10 py-10" aria-labelledby="tech-title">
      <div className="text-center mb-7">
        <span className="lr-eyebrow inline-flex">Core Technology</span>
        <h2 id="tech-title" className="text-2xl md:text-3xl font-extrabold tracking-tight text-foreground mt-4">
          How DietRiskNet Thinks
        </h2>
      </div>

      <motion.div
        variants={container}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.25 }}
        className="grid grid-cols-1 lg:grid-cols-3 gap-6"
      >
        {PANELS.map((p) => {
          const Icon = p.icon;
          return (
            <motion.article key={p.num} variants={item} className="lr-tech">
              <span className="lr-tech-num" aria-hidden="true">{p.num}</span>
              <div className="p-3 rounded-xl bg-brand-primary/8 text-brand-primary border border-brand-primary/15 w-fit mb-4">
                <Icon className="h-5 w-5" aria-hidden="true" />
              </div>
              <h3 className="text-sm font-extrabold tracking-wide text-foreground uppercase">
                {p.title}
              </h3>
              <p className="text-[10px] font-bold text-gold mt-1 uppercase tracking-widest">
                {p.tech}
              </p>
              <p className="text-xs text-muted-foreground leading-relaxed mt-3">
                {p.desc}
              </p>

              <div className="mt-5">
                <MiniVisual kind={p.viz} />
              </div>
            </motion.article>
          );
        })}
      </motion.div>
    </section>
  );
}
