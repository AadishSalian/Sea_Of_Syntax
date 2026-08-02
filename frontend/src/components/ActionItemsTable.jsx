import React from 'react';
import { Eye, Edit2, Trash2, List, Filter, MoreHorizontal } from 'lucide-react';
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
    <div className="w-full bg-[#18181b] border border-zinc-800 rounded-xl overflow-hidden shrink-0 mt-8">
      <div className="px-6 py-4 border-b border-zinc-800 flex justify-between items-center bg-[#18181b]">
        <h2 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
          <List size={20} className="text-zinc-400" />
          Extracted Action Items
        </h2>
        <div className="flex gap-2">
          <button className="p-1.5 hover:bg-zinc-800 rounded-md text-zinc-400 transition-colors">
            <Filter size={16} />
          </button>
          <button className="p-1.5 hover:bg-zinc-800 rounded-md text-zinc-400 transition-colors">
            <MoreHorizontal size={16} />
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-zinc-800 bg-[#09090b]">
              <th className="px-6 py-3 text-xs font-semibold text-zinc-400 uppercase tracking-wider">Owner</th>
              <th className="px-6 py-3 text-xs font-semibold text-zinc-400 uppercase tracking-wider">Action Item</th>
              <th className="px-6 py-3 text-xs font-semibold text-zinc-400 uppercase tracking-wider">Deadline</th>
              <th className="px-6 py-3 text-xs font-semibold text-zinc-400 uppercase tracking-wider">Priority</th>
              <th className="px-6 py-3 text-xs font-semibold text-zinc-400 uppercase tracking-wider">Source</th>
              <th className="px-6 py-3 text-xs font-semibold text-zinc-400 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-xs font-semibold text-zinc-400 uppercase tracking-wider text-right">Actions</th>
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
                <td colSpan="7" className="py-12 text-center text-zinc-500 font-medium bg-[#18181b]">
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
                  className="border-b border-zinc-800 hover:bg-zinc-800/30 transition-colors group"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-7 h-7 rounded-md bg-zinc-800 flex items-center justify-center border border-zinc-700 text-zinc-300 font-semibold text-xs">
                        {item.owner ? item.owner.charAt(0).toUpperCase() : '?'}
                      </div>
                      <span className="text-sm text-zinc-200 group-hover:text-blue-400 transition-colors">{item.owner || "Unassigned"}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-zinc-300 font-medium">{item.task}</td>
                  <td className="px-6 py-4 text-sm text-zinc-400">{item.deadline || "TBD"}</td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-[11px] border font-medium ${getPriorityStyle(item.priority || 'Medium')}`}>
                      {item.priority || 'Medium'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-zinc-400 capitalize">{item.tool_type || "email"}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-zinc-300 capitalize">{item.status || "Pending"}</span>
                      <div className={`w-8 h-4 rounded-full relative transition-colors ${item.status === 'completed' ? 'bg-purple-500' : 'bg-gray-600'}`}>
                        <div className={`absolute top-0.5 w-3 h-3 rounded-full bg-white transition-transform ${item.status === 'completed' ? 'right-0.5' : 'left-0.5'}`} />
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-3 text-zinc-500 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Eye size={16} className="hover:text-zinc-300 cursor-pointer transition-colors" />
                      <Edit2 size={16} className="hover:text-zinc-300 cursor-pointer transition-colors" />
                      <Trash2 size={16} className="hover:text-zinc-300 cursor-pointer transition-colors" />
                    </div>
                  </td>
                </motion.tr>
              ))
            )}
          </AnimatePresence>
        </tbody>
      </table>
      </div>
    </div>
  );
};

export default ActionItemsTable;
