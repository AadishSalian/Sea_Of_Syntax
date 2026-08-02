import React from 'react';
import { FileText, Sparkles, Zap, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';

const STEPS = [
  { id: 1, key: 'transcript', label: 'Transcript', icon: FileText },
  { id: 2, key: 'extract', label: 'Extracting items', icon: Sparkles },
  { id: 3, key: 'execute', label: 'Executing', icon: Zap },
  { id: 4, key: 'done', label: 'Complete', icon: CheckCircle2 },
];

// phase: idle | extract | execute | done
const stepState = (stepKey, phase) => {
  const order = ['idle', 'extract', 'execute', 'done'];
  const phaseIdx = order.indexOf(phase);
  const stepOrder = { transcript: 0, extract: 1, execute: 2, done: 3 };
  const idx = stepOrder[stepKey];

  if (stepKey === 'transcript') return phase === 'idle' ? 'pending' : 'complete';
  if (idx < phaseIdx) return 'complete';
  if (idx === phaseIdx) return 'active';
  return 'pending';
};

const PipelineTracker = ({ phase = 'idle' }) => {
  const progress = { idle: 8, extract: 38, execute: 68, done: 100 }[phase];

  return (
    <div className="bg-surface border border-border rounded-lg px-6 py-5 shrink-0">
      <div className="relative flex justify-between">
        <div className="absolute top-4 left-4 right-4 h-[2px] bg-border rounded-full" />
        <motion.div
          className="absolute top-4 left-4 h-[2px] bg-accent rounded-full"
          initial={false}
          animate={{ width: `calc(${progress}% - 32px)` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />

        {STEPS.map((step) => {
          const state = stepState(step.key, phase);
          const Icon = step.icon;
          return (
            <div key={step.id} className="relative z-10 flex flex-col items-center gap-2 w-24">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors duration-300 ${
                  state === 'complete'
                    ? 'bg-accent border-accent text-white'
                    : state === 'active'
                    ? 'bg-accent-soft border-accent text-accent'
                    : 'bg-surface border-border text-ink-faint'
                }`}
              >
                {state === 'active' ? (
                  <motion.div
                    animate={{ opacity: [1, 0.4, 1] }}
                    transition={{ duration: 1.4, repeat: Infinity }}
                  >
                    <Icon size={14} />
                  </motion.div>
                ) : (
                  <Icon size={14} />
                )}
              </div>
              <span
                className={`text-[11px] font-medium text-center leading-tight ${
                  state === 'pending' ? 'text-ink-faint' : 'text-ink-muted'
                }`}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PipelineTracker;
