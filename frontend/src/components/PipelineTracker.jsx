import React from 'react';
import { FileText, AlignLeft, CheckCircle2, BarChart2, MessageSquare } from 'lucide-react';
import { motion } from 'framer-motion';

const PipelineTracker = ({ phase = "idle" }) => {
  const steps = [
    { id: 1, label: 'Transcript', icon: FileText, state: phase === 'idle' ? 'pending' : 'completed' },
    { id: 2, label: 'Summary', icon: AlignLeft, state: (phase === 'extract' || phase === 'execute' || phase === 'done') ? 'completed' : 'pending' },
    { id: 3, label: 'Generating\nAction Items', icon: CheckCircle2, state: phase === 'extract' ? 'active' : phase === 'execute' || phase === 'done' ? 'completed' : 'pending' },
    { id: 4, label: 'Analysis', icon: BarChart2, state: phase === 'execute' ? 'active' : phase === 'done' ? 'completed' : 'pending' },
    { id: 5, label: 'Follow-ups', icon: MessageSquare, state: phase === 'done' ? 'completed' : 'pending' },
  ];

  return (
    <div className="relative w-full max-w-4xl mx-auto flex justify-between mb-12 px-4 shrink-0">
      {/* Background Line */}
      <div className="absolute top-6 left-12 right-12 h-[2px] bg-white/[0.05] z-0" />
      
      {/* Active Line */}
      <div 
        className="absolute top-6 left-12 h-[2px] bg-gradient-to-r from-purple-500 to-blue-500 z-0 transition-all duration-1000 shadow-[0_0_15px_rgba(168,85,247,0.5)]" 
        style={{ width: phase === 'done' ? '100%' : phase === 'execute' ? '75%' : phase === 'extract' ? '50%' : '25%' }}
      />

      {steps.map((step) => {
        const isActive = step.state === 'active';
        const isCompleted = step.state === 'completed';
        
        return (
          <div key={step.id} className="relative z-10 flex flex-col items-center flex-1">
            <motion.div 
              initial={false}
              animate={isActive ? { scale: [1, 1.1, 1] } : { scale: 1 }}
              transition={{ duration: 2, repeat: isActive ? Infinity : 0 }}
              className={`flex items-center justify-center rounded-full transition-all duration-500 relative z-20 ${
                isActive 
                  ? 'w-12 h-12 bg-blue-500/20 border border-blue-400 shadow-[0_0_30px_rgba(59,130,246,0.6)] text-blue-300 backdrop-blur-md' 
                  : isCompleted
                  ? 'w-10 h-10 bg-purple-500 border-none shadow-[0_0_15px_rgba(168,85,247,0.5)] text-white'
                  : 'w-10 h-10 bg-[#07070A] border border-white/20 text-gray-500'
              }`}
            >
              {isActive ? (
                <span className="font-bold text-lg">{step.id}</span>
              ) : isCompleted ? (
                <step.icon size={18} />
              ) : (
                <span className="text-sm font-medium">{step.id}</span>
              )}
            </motion.div>
            <div className="mt-3 text-center w-28 h-8">
              <span className={`text-[10px] font-medium uppercase tracking-widest whitespace-pre-line leading-tight block ${
                isActive ? 'text-white font-bold' : isCompleted ? 'text-gray-400' : 'text-gray-600'
              }`}>
                {step.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default PipelineTracker;
