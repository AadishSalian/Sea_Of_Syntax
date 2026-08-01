import React from 'react';
import { 
  FileText, ScanText, BrainCircuit, Tags, 
  BarChart, Database, Network, PlaySquare, 
  HelpCircle, FastForward, CheckCircle2 
} from 'lucide-react';

const PipelineTracker = ({ phase = "idle" }) => {
  const getStatus = (stepName) => {
    if (phase === "idle") return 'pending';
    if (phase === "extract") {
      if (['Transcript', 'Extract'].includes(stepName)) return 'active';
      return 'pending';
    }
    if (phase === "execute") {
      if (['Transcript', 'Extract', 'Understand', 'Classify'].includes(stepName)) return 'completed';
      if (['Confidence', 'Memory', 'Routing', 'Execute'].includes(stepName)) return 'active';
      return 'pending';
    }
    if (phase === "done") {
      return 'completed';
    }
    return 'pending';
  };

  const steps = [
    { label: 'Transcript', icon: FileText, status: getStatus('Transcript') },
    { label: 'Extract', icon: ScanText, status: getStatus('Extract') },
    { label: 'Understand', icon: BrainCircuit, status: getStatus('Understand') },
    { label: 'Classify', icon: Tags, status: getStatus('Classify') },
    { label: 'Confidence', icon: BarChart, status: getStatus('Confidence') },
    { label: 'Memory', icon: Database, status: getStatus('Memory') },
    { label: 'Routing', icon: Network, status: getStatus('Routing') },
    { label: 'Execute', icon: PlaySquare, status: getStatus('Execute') },
    { label: 'Clarify', icon: HelpCircle, status: getStatus('Clarify') },
    { label: 'Completed', icon: CheckCircle2, status: getStatus('Completed') },
  ];

  return (
    <div className="bg-cardLight rounded-2xl p-6 border border-white/5 shadow-lg mb-8">
      <div className="flex items-center justify-between mb-8">
        <h3 className="text-lg font-semibold text-white">Live AI Pipeline</h3>
        <span className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30 text-xs font-semibold flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500"></span>
          </span>
          Processing...
        </span>
      </div>

      <div className="relative">
        {/* Connecting Line */}
        <div className="absolute top-6 left-6 right-6 h-[2px] bg-white/10" />
        <div className="absolute top-6 left-6 h-[2px] bg-gradient-to-r from-green-500 to-blue-500 transition-all duration-1000" style={{ width: '35%' }} />

        <div className="flex justify-between relative z-10">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            let nodeClass = "";
            let iconClass = "";
            let labelClass = "";

            if (step.status === 'completed') {
              nodeClass = "bg-green-500/20 border-green-500 text-green-400";
              iconClass = "text-green-400";
              labelClass = "text-gray-300";
            } else if (step.status === 'active') {
              nodeClass = "bg-blue-600 border-blue-400 text-white shadow-[0_0_20px_rgba(59,130,246,0.6)] scale-110";
              iconClass = "text-white";
              labelClass = "text-blue-400 font-semibold";
            } else {
              nodeClass = "bg-background border-white/20 text-gray-500";
              iconClass = "text-gray-500";
              labelClass = "text-gray-600";
            }

            return (
              <div key={step.label} className="flex flex-col items-center w-20 group">
                <div className={`w-12 h-12 rounded-full border-2 flex items-center justify-center mb-3 bg-card transition-all duration-300 ${nodeClass}`}>
                  {step.status === 'completed' ? (
                    <CheckCircle2 size={20} className={iconClass} />
                  ) : (
                    <Icon size={20} className={iconClass} />
                  )}
                </div>
                <span className={`text-[11px] text-center tracking-wide ${labelClass} group-hover:text-gray-200 transition-colors`}>
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default PipelineTracker;
