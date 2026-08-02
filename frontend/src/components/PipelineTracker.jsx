import React from 'react';
import { FileText, AlignLeft, CheckCircle2, BarChart2, MessageSquare } from 'lucide-react';

const PipelineTracker = ({ phase = "idle" }) => {
  const steps = [
    { id: 1, label: 'Transcript', icon: FileText, state: phase === 'idle' ? 'pending' : 'completed' },
    { id: 2, label: 'Extract\nAction Items', icon: AlignLeft, state: phase === 'extract' ? 'active' : phase === 'execute' || phase === 'done' ? 'completed' : 'pending' },
    { id: 3, label: 'Execute\nTools', icon: CheckCircle2, state: phase === 'execute' ? 'active' : phase === 'done' ? 'completed' : 'pending' },
    { id: 4, label: 'Finalize', icon: MessageSquare, state: phase === 'done' ? 'completed' : 'pending' },
  ];

  return (
    <div className="relative w-full max-w-4xl mx-auto flex justify-between mb-12 px-4 shrink-0">
      {/* Background Line */}
      <div className="absolute top-6 left-12 right-12 h-[2px] bg-white/[0.05] z-0" />
      
      {/* Active Line */}
      <div 
        className="absolute top-6 left-12 h-[1px] bg-blue-500 z-0 transition-all duration-1000" 
        style={{ width: phase === 'done' ? '100%' : phase === 'execute' ? '66%' : phase === 'extract' ? '33%' : '0%' }}
      />

      {steps.map((step) => {
        const isActive = step.state === 'active';
        const isCompleted = step.state === 'completed';
        
        return (
          <div key={step.id} className="relative z-10 flex flex-col items-center flex-1">
            <div 
              className={`flex items-center justify-center rounded-full transition-all duration-300 relative z-20 ${
                isActive 
                  ? 'w-10 h-10 bg-[#09090b] border-2 border-blue-500 text-blue-500' 
                  : isCompleted
                  ? 'w-8 h-8 bg-blue-500 text-white mt-1'
                  : 'w-8 h-8 bg-[#09090b] border border-zinc-800 text-zinc-500 mt-1'
              }`}
            >
              {isActive ? (
                <span className="font-bold text-lg">{step.id}</span>
              ) : isCompleted ? (
                <step.icon size={18} />
              ) : (
                <span className="text-sm font-medium">{step.id}</span>
              )}
            </div>
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
