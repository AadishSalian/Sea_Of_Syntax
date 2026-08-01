import React from 'react';
import { Calendar, Bot } from 'lucide-react';

const RightPanel = () => {
  return (
    <div className="w-72 h-full glass-panel rounded-3xl p-6 flex flex-col gap-6 flex-shrink-0 relative z-10 overflow-y-auto custom-scrollbar">
      <div>
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Calendar size={16} className="text-purple-400" />
          Upcoming Syncs
        </h3>
        <div className="space-y-3">
          <div className="p-4 rounded-xl bg-cardLight border border-cardBorder shadow-inner-light group hover:border-purple-500/30 transition-colors cursor-pointer">
            <h4 className="text-sm font-medium text-gray-200 mb-1 group-hover:text-white transition-colors">Product Sync</h4>
            <span className="text-xs text-purple-400">10:00 AM - 11:30 AM</span>
          </div>
          <div className="p-4 rounded-xl bg-cardLight border border-cardBorder shadow-inner-light group hover:border-purple-500/30 transition-colors cursor-pointer">
            <h4 className="text-sm font-medium text-gray-200 mb-1 group-hover:text-white transition-colors">Design Review</h4>
            <span className="text-xs text-purple-400">2:00 PM - 3:00 PM</span>
          </div>
        </div>
      </div>
      
      <div className="flex-1 bg-gradient-to-b from-purple-500/5 to-transparent rounded-2xl border border-cardBorder p-5 flex flex-col items-center justify-center text-center mt-4 shadow-inner-light">
        <div className="w-12 h-12 bg-cardLight rounded-full flex items-center justify-center mb-4 border border-cardBorder shadow-glass">
          <Bot size={20} className="text-gray-400" />
        </div>
        <h4 className="text-sm font-semibold text-gray-300 mb-1">AI Assistant Ready</h4>
        <p className="text-xs text-gray-500 leading-relaxed">
          Upload a transcript or paste meeting notes to begin extraction.
        </p>
      </div>
    </div>
  );
};

export default RightPanel;
