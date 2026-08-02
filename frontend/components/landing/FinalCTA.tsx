'use client';

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';

export default function FinalCTA() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.4 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className="relative z-10 py-10"
      aria-labelledby="final-cta-title"
    >
      <div className="lr-final-cta">
        <Sparkles className="mx-auto h-7 w-7 text-gold-soft" aria-hidden="true" />
        <h2 id="final-cta-title">
          Your meal contains more information
          <br />
          than you think.
        </h2>
        <p>
          Turn your next meal into actionable dietary insight — food recognition,
          risk analytics, and personalized guidance in one step.
        </p>
        <div className="flex justify-center">
          <Link href="/register" className="lr-cta-primary">
            Analyze a Meal
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </div>
      </div>
    </motion.section>
  );
}
