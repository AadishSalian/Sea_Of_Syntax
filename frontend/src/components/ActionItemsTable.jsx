import React from 'react';
import { Ticket, Mail, FileText, ExternalLink, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const TOOL_META = {
  jira: { label: 'Jira', icon: Ticket },
  email: { label: 'Gmail', icon: Mail },
  notion: { label: 'Notion', icon: FileText },
};

const StatusBadge = ({ status, link, error }) => {
  if (status === 'completed') {
    return link ? (
      <a
        href={link}
        target="_blank"
        rel="noreferrer"
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-success-soft text-success hover:underline"
      >
        Done <ExternalLink size={11} />
      </a>
    ) : (
      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-success-soft text-success">
        Done
      </span>
    );
  }
  if (status === 'failed') {
    return (
      <span
        title={error || 'Execution failed'}
        className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-danger-soft text-danger cursor-help"
      >
        Failed
      </span>
    );
  }
  if (status === 'processing') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-accent-soft text-accent">
        <Loader2 size={11} className="animate-spin" /> Processing
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-gray-100 text-ink-muted">
      Pending
    </span>
  );
};

const ActionItemsTable = ({ items = [] }) => {
  const rows = items.map((r) => r.item || r);

  return (
    <div className="bg-surface border border-border rounded-lg flex-1 min-h-0 flex flex-col overflow-hidden">
      <div className="px-5 py-4 border-b border-border flex items-center justify-between shrink-0">
        <h2 className="text-[13px] font-semibold text-ink">Action items</h2>
        <span className="text-[11px] font-medium text-ink-faint">
          {rows.length ? `${rows.length} extracted` : 'None yet'}
        </span>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin">
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 bg-surface z-10">
            <tr className="border-b border-border text-[11px] font-semibold text-ink-faint uppercase tracking-wider">
              <th className="px-5 py-2.5 w-[20%]">Owner</th>
              <th className="px-5 py-2.5 w-[34%]">Task</th>
              <th className="px-5 py-2.5 w-[14%]">Tool</th>
              <th className="px-5 py-2.5 w-[12%]">Confidence</th>
              <th className="px-5 py-2.5 w-[10%]">Due</th>
              <th className="px-5 py-2.5 w-[10%]">Status</th>
            </tr>
          </thead>
          <tbody>
            <AnimatePresence>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center text-[13px] text-ink-faint">
                    Paste or record a transcript, then run it to see extracted action items here.
                  </td>
                </tr>
              ) : (
                rows.map((item, idx) => {
                  const tool = TOOL_META[item.tool_type] || TOOL_META.email;
                  const ToolIcon = tool.icon;
                  return (
                    <motion.tr
                      key={idx}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.25 }}
                      className="border-b border-border last:border-b-0 hover:bg-canvas/60 transition-colors"
                    >
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-6 h-6 rounded-full bg-accent-soft flex items-center justify-center text-accent font-semibold text-[11px] shrink-0">
                            {item.owner ? item.owner.charAt(0).toUpperCase() : '?'}
                          </div>
                          <span className="text-[13px] text-ink font-medium truncate">
                            {item.owner || 'Unassigned'}
                          </span>
                        </div>
                      </td>
                      <td
                        className="px-5 py-3 text-[13px] text-ink-muted"
                        title={item.raw_context}
                      >
                        {item.task}
                      </td>
                      <td className="px-5 py-3">
                        <span className="inline-flex items-center gap-1.5 text-[12px] text-ink-muted font-medium">
                          <ToolIcon size={13} className="text-ink-faint" />
                          {tool.label}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        <span className="text-[12px] font-mono text-ink-muted">
                          {typeof item.confidence === 'number'
                            ? `${Math.round(item.confidence * 100)}%`
                            : '—'}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-[12px] text-ink-muted">
                        {item.due_hint || '—'}
                      </td>
                      <td className="px-5 py-3">
                        <StatusBadge status={item.status} link={item.link} error={item.error} />
                      </td>
                    </motion.tr>
                  );
                })
              )}
            </AnimatePresence>
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ActionItemsTable;
