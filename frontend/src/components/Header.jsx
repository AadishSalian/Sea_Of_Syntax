import React from 'react';
import { Globe, Moon, ChevronDown, CheckCircle2 } from 'lucide-react';

const Header = () => {
  return (
    <header className="flex items-center justify-between px-8 py-5 border-b border-white/5 bg-card/50 backdrop-blur-md sticky top-0 z-20">
      <div>
        <h2 className="text-2xl font-bold text-white mb-1 tracking-tight">Dashboard</h2>
        <p className="text-sm text-gray-400 font-medium">AI Meeting Assistant that turns conversations into actions</p>
      </div>

      <div className="flex items-center gap-4">
        {/* System Status Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 shadow-sm">
          <Globe size={14} className="text-gray-400" />
          <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
          <span className="text-xs font-semibold text-gray-300">All Systems Operational</span>
        </div>

        {/* Connected APIs Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 shadow-sm">
          <span className="text-xs font-semibold text-gray-400 mr-1">APIs</span>
          <div className="flex gap-1.5">
            <div className="w-4 h-4 rounded-full bg-blue-500/20 flex items-center justify-center border border-blue-500/30" title="Gemini">
              <span className="text-[8px]">G</span>
            </div>
            <div className="w-4 h-4 rounded-full bg-blue-600/20 flex items-center justify-center border border-blue-600/30" title="Jira">
              <span className="text-[8px]">J</span>
            </div>
            <div className="w-4 h-4 rounded-full bg-red-500/20 flex items-center justify-center border border-red-500/30" title="Gmail">
              <span className="text-[8px]">M</span>
            </div>
            <div className="w-4 h-4 rounded-full bg-gray-200/20 flex items-center justify-center border border-gray-200/30" title="Notion">
              <span className="text-[8px]">N</span>
            </div>
            <div className="w-4 h-4 rounded-full bg-green-500/20 flex items-center justify-center border border-green-500/30" title="Slack">
              <span className="text-[8px]">S</span>
            </div>
          </div>
        </div>

        <button className="w-9 h-9 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-gray-400 hover:text-white transition-colors">
          <Moon size={16} />
        </button>

        <div className="h-6 w-px bg-white/10 mx-1" />

        <button className="flex items-center gap-3 hover:bg-white/5 p-1.5 pr-2 rounded-full transition-colors">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-600 to-purple-500 flex items-center justify-center text-sm font-bold shadow-[0_0_10px_rgba(124,58,237,0.3)]">
            HD
          </div>
          <div className="text-left hidden sm:block">
            <div className="text-sm font-semibold text-white leading-tight">Hardik</div>
            <div className="text-xs text-purple-400 font-medium">Admin</div>
          </div>
          <ChevronDown size={14} className="text-gray-500" />
        </button>
      </div>
    </header>
  );
};

export default Header;
