import React from 'react';
import { 
  LayoutDashboard, FileText, Cpu, CheckSquare, 
  KanbanSquare, Mail, BookOpen, MessageSquare, 
  Database, History, BarChart2, FileTerminal, 
  Settings 
} from 'lucide-react';

const Sidebar = ({ activeTab, onTabChange }) => {

  const navItems = [
    { name: 'Dashboard', icon: LayoutDashboard },
    { name: 'Transcript', icon: FileText },
    { name: 'AI Processing', icon: Cpu },
    { name: 'Action Items', icon: CheckSquare },
    { name: 'Jira', icon: KanbanSquare },
    { name: 'Gmail', icon: Mail },
    { name: 'Notion', icon: BookOpen },
    { name: 'Slack Clarifications', icon: MessageSquare },
    { name: 'Memory', icon: Database },
    { name: 'Execution History', icon: History },
    { name: 'Analytics', icon: BarChart2 },
    { name: 'Logs', icon: FileTerminal },
    { name: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-[230px] h-screen bg-cardLight border-r border-white/10 flex flex-col justify-between p-4 flex-shrink-0">
      <div>
        <div className="flex items-center gap-2 mb-8 px-2">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-violet-600 to-purple-500 transform rotate-45 flex items-center justify-center shrink-0">
            <div className="w-3 h-3 bg-white transform -rotate-45" />
          </div>
          <h1 className="text-lg font-bold tracking-tight">
            <span className="text-white">MeetingTo</span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-purple-400">Motion</span>
          </h1>
        </div>

        <nav className="flex flex-col gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.name}
                onClick={() => onTabChange(item.name)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 text-sm font-medium ${
                  activeTab === item.name 
                    ? 'bg-gradient-to-r from-violet-600/20 to-purple-500/20 text-purple-400 shadow-[0_0_15px_rgba(124,58,237,0.15)] border border-purple-500/30' 
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'
                }`}
              >
                <Icon size={18} className={activeTab === item.name ? "text-purple-400" : "text-gray-400"} />
                <span className="truncate">{item.name}</span>
              </button>
            )
          })}
        </nav>
      </div>

      <div className="mt-4 p-4 rounded-xl bg-background border border-white/5 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-16 h-16 bg-purple-500/10 blur-xl rounded-full" />
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-gray-300">Processing Engine</span>
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
          </div>
        </div>
        
        <div className="h-8 flex items-end gap-1 opacity-70 mb-3">
          {/* Empty state for processing bars */}
          {[0, 0, 0, 0, 0, 0, 0, 0].map((h, i) => (
            <div key={i} className="w-1.5 bg-gradient-to-t from-purple-600 to-violet-400 rounded-t-sm" style={{ height: `${h}%` }} />
          ))}
        </div>
        
        <div className="flex items-center justify-between text-[10px] text-gray-500 font-medium">
          <span>AI Engine Active</span>
          <span className="px-1.5 py-0.5 rounded-md bg-white/5 flex items-center gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
            v1.0.0
          </span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
