import React from 'react';
import { Home, Calendar, BarChart2, CheckSquare, Video, Settings, ChevronLeft, User, Plus } from 'lucide-react';

const Sidebar = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'meetings', label: 'Meetings', icon: Calendar },
    { id: 'analytics', label: 'Analytics', icon: BarChart2 },
    { id: 'actions', label: 'Actions', icon: CheckSquare },
    { id: 'recordings', label: 'Recordings', icon: Video },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-[260px] h-full flex flex-col justify-between p-6 bg-transparent border-r border-white/[0.02] relative z-10 shrink-0 overflow-y-auto custom-scrollbar">
      <div>
        {/* Logo Area */}
        <div className="flex items-center justify-between mb-10 pl-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 shadow-[0_0_20px_rgba(168,85,247,0.5)]" />
          <button className="text-gray-500 hover:text-gray-300">
            <ChevronLeft size={20} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center justify-between w-full px-4 py-3 rounded-xl transition-all duration-300 ${
                  isActive 
                    ? 'bg-white/[0.05] text-white shadow-inner-light' 
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/[0.02]'
                }`}
              >
                <div className="flex items-center gap-4">
                  <Icon size={18} className={isActive ? 'text-purple-400' : ''} />
                  <span className="font-medium text-sm tracking-wide">{item.label}</span>
                </div>
                {isActive && (
                  <div className="w-1.5 h-1.5 rounded-full bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.8)]" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Profile Area */}
      <div>
        <div className="flex items-center gap-3 px-2 mb-6">
          <div className="w-10 h-10 rounded-full border border-white/10 bg-white/5 flex items-center justify-center text-gray-400">
            <User size={20} />
          </div>
          <div className="flex flex-col text-left">
            <span className="text-sm font-semibold text-white">Current User</span>
            <span className="text-xs text-gray-500">Workspace Member</span>
          </div>
        </div>

        <button className="w-full py-3.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-500 text-white font-semibold text-sm flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(168,85,247,0.4)] hover:shadow-[0_0_30px_rgba(168,85,247,0.6)] transition-all">
          New Meeting
          <Plus size={16} />
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
