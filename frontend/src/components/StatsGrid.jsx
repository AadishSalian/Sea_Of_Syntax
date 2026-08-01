import React from 'react';
import { motion } from 'framer-motion';
import { Activity, Clock, CheckCircle2, AlertCircle } from 'lucide-react';

const StatsGrid = ({ items = [] }) => {
  const total = items.length;
  const completed = items.filter(row => row.result?.status === 'success').length;
  const inProgress = items.filter(row => row.result && row.result.status !== 'success' && row.result.status !== 'failed').length;
  const failed = items.filter(row => row.result?.status === 'failed').length;
  const pending = total - (completed + inProgress + failed);
  const needsClarification = failed;
  
  const stats = [
    { label: 'Total Items', value: total, icon: Activity, color: 'text-blue-400', bg: 'bg-blue-500/10' },
    { label: 'Completed', value: completed, icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    { label: 'Pending / Actionable', value: pending, icon: Clock, color: 'text-purple-400', bg: 'bg-purple-500/10' },
    { label: 'Needs Clarification', value: needsClarification, icon: AlertCircle, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
  ];

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemAnim = {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <motion.div 
      variants={container}
      initial="hidden"
      animate="show"
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6"
    >
      {stats.map((stat, idx) => {
        const Icon = stat.icon;
        return (
          <motion.div 
            key={idx} 
            variants={itemAnim}
            className="glass-panel rounded-2xl p-6 group hover:border-purple-500/30 transition-colors"
          >
            <div className="flex items-start justify-between mb-4">
              <div className={`p-3 rounded-xl ${stat.bg} shadow-inner-light`}>
                <Icon size={20} className={stat.color} />
              </div>
              <div className="w-16 h-8 opacity-30 flex items-end gap-1">
                {[40, 70, 30, 85, 50, 90].map((h, i) => (
                  <div key={i} className={`w-1.5 rounded-t-sm ${stat.bg.replace('10', '40')}`} style={{ height: `${h}%` }} />
                ))}
              </div>
            </div>
            <h3 className="text-3xl font-bold text-white tracking-tight mb-1">{stat.value}</h3>
            <p className="text-sm font-medium text-gray-400">{stat.label}</p>
          </motion.div>
        );
      })}
    </motion.div>
  );
};

export default StatsGrid;
