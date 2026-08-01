import React from 'react';
import { Zap, Activity, KanbanSquare, Mail, BookOpen, MessageSquare } from 'lucide-react';

const RightPanel = () => {
  const events = [];

  return (
    <aside className="w-[280px] h-[calc(100vh-80px)] border-l border-white/5 bg-cardLight/30 flex flex-col flex-shrink-0">
      {/* Activity Feed */}
      <div className="flex-1 overflow-y-auto p-5 custom-scrollbar">
        <div className="flex items-center gap-2 mb-6">
          <Zap size={18} className="text-purple-400" />
          <h3 className="text-sm font-semibold text-white">Live Activity</h3>
        </div>
        
        <div className="relative border-l-2 border-white/5 ml-3 space-y-6">
          {events.length === 0 ? (
            <div className="pl-4 text-xs text-gray-500 italic">No activity yet.</div>
          ) : (
            events.map((event, i) => (
              <div key={i} className="relative pl-6 group">
                <div className={`absolute -left-[9px] top-1 w-4 h-4 rounded-full border-2 ${event.bg} ${event.border} ${event.color} bg-background group-hover:scale-125 transition-transform`} />
                <div className="flex flex-col">
                  <span className="text-[10px] font-mono text-gray-500 mb-0.5">{event.time}</span>
                  <span className="text-xs font-semibold text-gray-200 mb-0.5">{event.title}</span>
                  <span className="text-[11px] text-gray-500 leading-tight">{event.desc}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* API Health */}
      <div className="p-5 border-t border-white/5 bg-cardLight/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity size={16} className="text-gray-400" />
            <h3 className="text-sm font-semibold text-white">API Health</h3>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-500/10 text-gray-400 border border-gray-500/20">
            Pending
          </span>
        </div>
        
        <div className="space-y-3">
          {[
            { name: "Gemini", icon: Zap, latency: "--", status: "pending" },
            { name: "Jira", icon: KanbanSquare, latency: "--", status: "pending" },
            { name: "Gmail", icon: Mail, latency: "--", status: "pending" },
            { name: "Notion", icon: BookOpen, latency: "--", status: "pending" },
            { name: "Slack", icon: MessageSquare, latency: "--", status: "pending" },
          ].map((api) => {
            const Icon = api.icon;
            return (
              <div key={api.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <Icon size={14} className="text-gray-500" />
                  <span className="text-xs font-medium text-gray-300">{api.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-gray-500">{api.latency}</span>
                  <div className="w-1.5 h-1.5 rounded-full bg-gray-500" />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
};

export default RightPanel;
