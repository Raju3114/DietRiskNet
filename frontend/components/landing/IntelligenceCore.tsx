'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

/**
 * Pseudo-3D "Dietary Intelligence Core" — a pure CSS/React visual.
 * Lightweight: no WebGL, no external assets.
 *
 * Cards show demo/illustrative values only (labelled "Illustrative").
 */

interface CoreState {
  x: number;
  y: number;
}

export default function IntelligenceCore() {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [parallax, setParallax] = useState<CoreState>({ x: 0, y: 0 });
  const enabledRef = useRef(true);

  // Respect reduced motion + disable on small screens.
  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const narrow = window.matchMedia('(max-width: 1023px)').matches;
    enabledRef.current = !reduce && !narrow;
  }, []);

  const onMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!enabledRef.current) return;
    const rect = wrapRef.current?.getBoundingClientRect();
    if (!rect) return;
    // Normalized -0.5..0.5, scaled to a few degrees.
    const nx = (e.clientX - rect.left) / rect.width - 0.5;
    const ny = (e.clientY - rect.top) / rect.height - 0.5;
    setParallax({ x: nx * 8, y: ny * 8 });
  }, []);

  const onLeave = useCallback(() => setParallax({ x: 0, y: 0 }), []);

  const cards = [
    { label: 'Food Detected', value: 'Idli', sub: '84% confidence', cls: 'lr-fc-gold', style: { top: '10%', left: '2%', zIndex: 20 } },
    { label: 'Nutrition', value: '82 kcal', sub: 'per serving', cls: '', style: { top: '58%', left: '0%', zIndex: 30 } },
    { label: 'DCI', value: '0.71', sub: 'consistency', cls: '', style: { top: '6%', right: '8%', zIndex: 18 } },
    { label: 'NIS', value: '0.96', sub: 'imbalance', cls: '', style: { top: '46%', right: '0%', zIndex: 22 } },
    { label: 'Risk', value: 'Moderate', sub: 'fused score', cls: '', style: { bottom: '6%', left: '16%', zIndex: 24 } },
    { label: 'AI Coach', value: 'Guidance', sub: 'local LLM', cls: 'lr-fc-gold', style: { top: '14%', right: '26%', zIndex: 26 } },
  ];

  return (
    <div
      ref={wrapRef}
      className="lr-core-wrap"
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      aria-hidden="true"
    >
      <motion.div
        className="lr-core-scene"
        style={{ transform: `rotateX(${10 - parallax.y}deg) rotateY(${parallax.x}deg)` }}
        initial={{ opacity: 0, scale: 0.92 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.9, ease: 'easeOut' }}
      >
        {/* atmosphere glow + rings */}
        <div className="lr-core-glow" />
        <div className="lr-orbit" />
        <div className="lr-orbit-inner" />
        <svg className="lr-tick-ring" viewBox="0 0 100 100" fill="none" aria-hidden="true">
          <circle cx="50" cy="50" r="47" strokeWidth="1.4" strokeDasharray="1 6" style={{ stroke: 'var(--gold)' }} />
        </svg>
        <div className="lr-pulse-ring" />

        {/* scanning arc + central sphere + ECG line */}
        <svg className="lr-core-arc" viewBox="0 0 100 100" fill="none" aria-hidden="true">
          <circle cx="50" cy="50" r="45" strokeWidth="1.6" strokeLinecap="round" strokeDasharray="34 100" opacity="0.5" style={{ stroke: 'var(--gold)' }} />
        </svg>
        <div className="lr-core-sphere">
          <svg viewBox="0 0 120 60" fill="none" preserveAspectRatio="xMidYMid meet">
            <path
              d="M0 30 H34 L44 30 L52 14 L64 48 L72 30 H120"
              stroke="#ffffff"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeDasharray="600"
              style={{ strokeDashoffset: 600, animation: 'lr-ecg 7s linear infinite' }}
            />
            <circle cx="60" cy="30" r="2.4" style={{ fill: 'var(--gold)' }} />
          </svg>
        </div>

        {/* faint data particles */}
        <span className="lr-data-dot" style={{ top: '16%', left: '30%', animationDelay: '0s' }} />
        <span className="lr-data-dot" style={{ top: '28%', right: '18%', animationDelay: '1.2s' }} />
        <span className="lr-data-dot" style={{ bottom: '22%', left: '22%', animationDelay: '2.4s' }} />

        {/* floating demo cards */}
        {cards.map((c) => (
          <div key={c.label} className={`lr-float-card ${c.cls}`} style={c.style}>
            <span className="lr-fc-label">{c.label}</span>
            <span className="lr-fc-value">{c.value}</span>
            <span className="lr-fc-sub">{c.sub}</span>
          </div>
        ))}
      </motion.div>

      <span className="lr-core-label">Illustrative analysis</span>
    </div>
  );
}
