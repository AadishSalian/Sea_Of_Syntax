import React from 'react';
import { Home, Calendar, BarChart2, CheckSquare, Video, Settings, ChevronLeft, User, Plus } from 'lucide-react';

const Sidebar = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
  ];

  return (
    <aside className="w-[260px] h-full flex flex-col justify-between p-6 bg-[#09090b] border-r border-zinc-800 relative z-10 shrink-0 overflow-y-auto custom-scrollbar">
      <div>
        {/* Logo Area */}
        <div className="flex items-center justify-between mb-10 pl-2 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-white flex items-center justify-center">
               <span className="text-black font-bold text-lg leading-none">M</span>
            </div>
            <span className="text-xl font-bold text-zinc-100 tracking-tight">MeetingToMotion</span>
          </div>
          <button className="text-zinc-500 hover:text-zinc-300 transition-colors">
            <ChevronLeft size={20} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center justify-between w-full px-3 py-2.5 rounded-md transition-all duration-200 ${
                  isActive 
                    ? 'bg-zinc-800/50 text-zinc-100' 
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/30'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon size={16} className={isActive ? 'text-zinc-100' : 'text-zinc-400'} />
                  <span className="font-medium text-sm">{item.label}</span>
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Profile Area */}
      <div>
        <div className="flex items-center gap-3 px-2 mb-6">
          <div className="w-8 h-8 rounded-full border border-zinc-700 bg-zinc-800 flex items-center justify-center text-zinc-400">
            <User size={16} />
          </div>
          <div className="flex flex-col text-left">
            <span className="text-sm font-semibold text-zinc-200">Current User</span>
            <span className="text-xs text-zinc-500">Workspace Member</span>
          </div>
        </div>

        <button className="w-full py-2.5 rounded-md bg-white text-black font-semibold text-sm flex items-center justify-center gap-2 hover:bg-zinc-200 transition-colors">
          New Meeting
          <Plus size={16} />
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
