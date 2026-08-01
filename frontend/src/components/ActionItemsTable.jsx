import React from 'react';
import { Eye, Edit2, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ActionItemsTable = ({ items = [] }) => {
  const displayItems = items.map(r => r.item || r);

  const getPriorityStyle = (priority) => {
    switch(priority?.toLowerCase()) {
      case 'high': return 'border-red-400/50 text-red-400 bg-red-400/10 shadow-[0_0_10px_rgba(248,113,113,0.15)]';
      case 'medium': return 'border-amber-400/50 text-amber-400 bg-amber-400/10 shadow-[0_0_10px_rgba(251,191,36,0.15)]';
      case 'low': return 'border-blue-400/50 text-blue-400 bg-blue-400/10 shadow-[0_0_10px_rgba(96,165,250,0.15)]';
      default: return 'border-gray-400/50 text-gray-400 bg-gray-400/10';
    }
  };

  return (
    <div className="glass-panel w-full rounded-2xl overflow-hidden mb-6 relative border-t border-t-purple-500/30">
      <div className="p-5 flex items-center justify-between border-b border-white/[0.05]">
        <h2 className="text-lg font-bold text-white tracking-wide">Action Items & Insights</h2>
        <div className="flex gap-3">
          <button className="px-4 py-2 text-xs font-semibold text-gray-300 border border-white/20 rounded-lg hover:bg-white/5 transition-colors">
            ↓ Export Report
          </button>
          <button className="px-4 py-2 text-xs font-semibold text-white bg-gradient-to-r from-blue-500 to-indigo-500 rounded-lg shadow-[0_0_15px_rgba(59,130,246,0.4)]">
            Assign All Tasks
          </button>
          <button className="px-4 py-2 text-xs font-semibold text-white bg-gradient-to-r from-purple-500 to-violet-500 rounded-lg shadow-[0_0_15px_rgba(168,85,247,0.4)]">
            Mark All
          </button>
        </div>
      </div>
      
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="border-b border-white/[0.05] text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
            <th className="px-6 py-4 w-[20%]">Owner</th>
            <th className="px-6 py-4 w-[30%]">Action Item</th>
            <th className="px-6 py-4 w-[10%]">Deadline</th>
            <th className="px-6 py-4 w-[10%]">Priority</th>
            <th className="px-6 py-4 w-[10%]">Source</th>
            <th className="px-6 py-4 w-[10%]">Status</th>
            <th className="px-6 py-4 w-[10%] text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <AnimatePresence>
            {displayItems.length === 0 ? (
              <motion.tr
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <td colSpan="7" className="py-12 text-center text-gray-500 font-medium bg-white/[0.01]">
                  No action items extracted yet. Run the pipeline to populate.
                </td>
              </motion.tr>
            ) : (
              displayItems.map((item, idx) => (
                <motion.tr 
                  key={idx} 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.1, duration: 0.3 }}
                  className="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors group"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-600/30 to-purple-600/30 flex items-center justify-center border border-purple-500/20 text-purple-300 font-semibold text-xs shadow-inner-light">
                        {item.owner ? item.owner.charAt(0).toUpperCase() : '?'}
                      </div>
                      <span className="text-sm text-gray-200 group-hover:text-purple-300 transition-colors">{item.owner || "Unassigned"}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-300 font-medium">{item.task}</td>
                  <td className="px-6 py-4 text-sm text-gray-400">{item.deadline || "TBD"}</td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-[11px] border font-medium ${getPriorityStyle(item.priority || 'Medium')}`}>
                      {item.priority || 'Medium'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-400 capitalize">{item.tool_type || "email"}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-gray-300 capitalize">{item.status || "Pending"}</span>
                      <div className={`w-8 h-4 rounded-full relative transition-colors ${item.status === 'completed' ? 'bg-purple-500' : 'bg-gray-600'}`}>
                        <div className={`absolute top-0.5 w-3 h-3 rounded-full bg-white transition-transform ${item.status === 'completed' ? 'right-0.5' : 'left-0.5'}`} />
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-3 text-gray-500">
                      <Eye size={16} className="hover:text-gray-300 cursor-pointer transition-colors" />
                      <Edit2 size={16} className="hover:text-gray-300 cursor-pointer transition-colors" />
                      <Trash2 size={16} className="hover:text-gray-300 cursor-pointer transition-colors" />
                    </div>
                  </td>
                </motion.tr>
              ))
            )}
          </AnimatePresence>
        </tbody>
      </table>
    </div>
  );
};

export default ActionItemsTable;
