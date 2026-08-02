import React from 'react';
import { Ticket, Mail, FileText } from 'lucide-react';

// Reflects the tools this pipeline actually integrates with (see jira_notion.py,
// gmail_slack.py) rather than decorative nav links to screens that don't exist.
const TOOLS = [
  { id: 'jira', label: 'Jira', icon: Ticket },
  { id: 'notion', label: 'Notion', icon: FileText },
  { id: 'gmail', label: 'Gmail', icon: Mail },
];

const Sidebar = () => {
  return (
    <aside className="w-60 h-full shrink-0 flex flex-col bg-rail text-white">
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-5 h-16 border-b border-rail-border shrink-0">
        <div className="w-7 h-7 rounded-md bg-accent flex items-center justify-center shrink-0">
          <svg width="14" height="14" viewBox="0 0 32 32" fill="none">
            <path d="M9 11L15.5 16L9 21" stroke="white" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M16.5 21H23" stroke="white" strokeWidth="2.6" strokeLinecap="round"/>
          </svg>
        </div>
        <span className="font-semibold text-[15px] tracking-tight">MeetingToMotion</span>
      </div>

      {/* Connected tools */}
      <div className="px-5 pt-6">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-rail-muted mb-3">
          Connected tools
        </p>
        <div className="flex flex-col gap-1">
          {TOOLS.map((tool) => {
            const Icon = tool.icon;
            return (
              <div
                key={tool.id}
                className="flex items-center justify-between px-2.5 py-2 rounded-md hover:bg-rail-hover transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <Icon size={15} className="text-rail-muted" />
                  <span className="text-[13px] font-medium text-gray-200">{tool.label}</span>
                </div>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex-1" />

      {/* Team credit */}
      <div className="px-5 py-4 border-t border-rail-border">
        <p className="text-[11px] text-rail-muted leading-relaxed">
          Team Sea of Syntax<br />Code Kudla 2026
        </p>
      </div>
    </aside>
  );
};

export default Sidebar;
