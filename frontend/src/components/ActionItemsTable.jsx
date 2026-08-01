import React from 'react';
import { Search, Filter, ExternalLink, KanbanSquare, Mail, BookOpen } from 'lucide-react';

const ActionItemsTable = ({ items = [] }) => {
  const getStatusColor = (status) => {
    switch(status?.toLowerCase()) {
      case 'success':
      case 'completed': return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'in progress': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'pending': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'failed': return 'bg-red-500/20 text-red-400 border-red-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <div className="bg-card rounded-2xl border border-white/5 shadow-lg overflow-hidden mb-6">
      {/* Table Header */}
      <div className="p-5 border-b border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-cardLight/50">
        <h3 className="text-lg font-semibold text-white">Action Items</h3>
        
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input 
              type="text" 
              placeholder="Search action items..." 
              className="bg-background border border-white/10 rounded-lg pl-9 pr-4 py-1.5 text-sm text-white focus:outline-none focus:border-purple-500/50 w-full sm:w-64 placeholder:text-gray-600 transition-colors"
            />
          </div>
          
          <div className="hidden sm:flex items-center gap-2">
            <select className="bg-background border border-white/10 rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-purple-500/50 appearance-none">
              <option>All Tools</option>
              <option>Jira</option>
              <option>Gmail</option>
              <option>Notion</option>
            </select>
            
            <select className="bg-background border border-white/10 rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-purple-500/50 appearance-none">
              <option>All Status</option>
              <option>Completed</option>
              <option>In Progress</option>
              <option>Pending</option>
            </select>
          </div>
          
          <button className="flex items-center gap-2 px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-sm font-medium text-gray-300 hover:bg-white/10 transition-colors">
            <Filter size={16} />
            <span className="hidden sm:inline">Filters</span>
          </button>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-background/50 border-b border-white/5 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <th className="p-4 pl-6 font-medium">#</th>
              <th className="p-4 font-medium">Task</th>
              <th className="p-4 font-medium">Owner</th>
              <th className="p-4 font-medium">Tool</th>
              <th className="p-4 font-medium">Confidence</th>
              <th className="p-4 font-medium">Due Date</th>
              <th className="p-4 font-medium">Ambiguous</th>
              <th className="p-4 font-medium">Status</th>
              <th className="p-4 pr-6 font-medium text-right">Execution Link</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-sm">
            {items.length === 0 ? (
              <tr>
                <td colSpan="9" className="p-8 text-center text-gray-500 font-medium">
                  No action items found.
                </td>
              </tr>
            ) : (
              items.map((row, idx) => {
                const item = row.item || {};
                const res = row.result || {};
                
                const ToolIcon = item.tool_type === 'jira' ? KanbanSquare : item.tool_type === 'email' ? Mail : BookOpen;
                const status = res.status || (row.was_clarified ? 'pending' : 'pending');
                const confidence = item.confidence || 0.9;
                
                return (
                  <tr key={idx} className="hover:bg-white/[0.02] transition-colors group">
                    <td className="p-4 pl-6 text-gray-500">{idx + 1}</td>
                    <td className="p-4 font-medium text-gray-200">{item.task || 'Unknown Task'}</td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center text-xs font-bold">
                          {(item.owner || '?').charAt(0)}
                        </div>
                        <span className="text-gray-300">{item.owner || 'Unassigned'}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2 text-gray-400">
                        <ToolIcon size={16} className={item.tool_type === 'jira' ? 'text-blue-400' : item.tool_type === 'email' ? 'text-red-400' : 'text-gray-200'} />
                        <span className="capitalize">{item.tool_type}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <div className="relative w-6 h-6 flex items-center justify-center">
                          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                            <path className="text-white/10" strokeWidth="3" stroke="currentColor" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                            <path className={confidence > 0.9 ? "text-green-500" : confidence > 0.8 ? "text-blue-500" : "text-yellow-500"} strokeDasharray={`${confidence * 100}, 100`} strokeWidth="3" stroke="currentColor" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                          </svg>
                        </div>
                        <span className="text-gray-300 font-medium">{confidence.toFixed(2)}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <span className={item.due_hint ? 'text-red-400 font-medium' : 'text-gray-400'}>{item.due_hint || 'N/A'}</span>
                    </td>
                    <td className="p-4">
                      <span className={item.ambiguous ? 'text-yellow-400 font-medium' : 'text-gray-500'}>{item.ambiguous ? 'Yes' : 'No'}</span>
                    </td>
                    <td className="p-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border capitalize ${getStatusColor(status)}`}>
                        {status}
                      </span>
                    </td>
                    <td className="p-4 pr-6 text-right">
                      {res.link ? (
                        <a href={res.link} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 text-xs font-medium transition-colors border border-transparent hover:border-white/10">
                          View
                          <ExternalLink size={12} className="text-gray-500" />
                        </a>
                      ) : (
                        <span className="text-gray-500 text-xs">-</span>
                      )}
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ActionItemsTable;
