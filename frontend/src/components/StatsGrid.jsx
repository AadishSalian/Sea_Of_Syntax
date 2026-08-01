import React from 'react';
import { Users, CheckCircle2, RefreshCw, Clock, TrendingUp, Timer } from 'lucide-react';

const StatsGrid = ({ items = [] }) => {
  const total = items.length;
  const completed = items.filter(row => row.result?.status === 'success').length;
  const inProgress = items.filter(row => row.result && row.result.status !== 'success' && row.result.status !== 'failed').length;
  const failed = items.filter(row => row.result?.status === 'failed').length;
  const pending = total - (completed + inProgress + failed);
  
  const avgConfidence = total > 0 
    ? (items.reduce((acc, row) => acc + (row.item?.confidence || 0), 0) / total).toFixed(2)
    : "0.00";

  const stats = [
    { label: "Total Action Items", value: total.toString(), icon: Users, subtext: "Extracted", color: "text-purple-400", bg: "bg-purple-500/10" },
    { label: "Completed", value: completed.toString(), icon: CheckCircle2, subtext: "Success", color: "text-green-500", bg: "bg-green-500/10" },
    { label: "In Progress", value: inProgress.toString(), icon: RefreshCw, subtext: "Working", color: "text-blue-500", bg: "bg-blue-500/10" },
    { label: "Pending", value: pending.toString(), icon: Clock, subtext: "Queued", color: "text-yellow-500", bg: "bg-yellow-500/10" },
    { label: "Avg Confidence", value: avgConfidence, icon: TrendingUp, subtext: "Score", color: "text-indigo-400", bg: "bg-indigo-500/10" },
    { label: "Failed", value: failed.toString(), icon: Timer, subtext: "Errors", color: "text-red-400", bg: "bg-red-500/10" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {stats.map((stat, i) => {
        const Icon = stat.icon;
        return (
          <div key={i} className="bg-card rounded-2xl p-4 border border-white/5 hover:border-white/10 transition-colors flex flex-col justify-between h-32">
            <div className="flex items-start justify-between">
              <span className="text-xs font-semibold text-gray-400 max-w-[80%] leading-tight">{stat.label}</span>
              <div className={`w-7 h-7 rounded-lg ${stat.bg} ${stat.color} flex items-center justify-center shrink-0`}>
                <Icon size={14} />
              </div>
            </div>
            
            <div>
              <div className="text-2xl font-bold text-white mb-1">{stat.value}</div>
              <div className="text-[10px] text-gray-500 font-medium">{stat.subtext}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default StatsGrid;
