import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import TranscriptPanel from './components/TranscriptPanel';
import PipelineTracker from './components/PipelineTracker';
import ActionItemsTable from './components/ActionItemsTable';

const PHASE_LABEL = {
  idle: 'Ready',
  extract: 'Extracting action items',
  execute: 'Executing',
  done: 'Complete',
};

function App() {
  const [pastedText, setPastedText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [pipelinePhase, setPipelinePhase] = useState('idle');
  const [actionItems, setActionItems] = useState([]);

  const handleStartProcessing = async (text) => {
    setIsProcessing(true);
    setPipelinePhase('extract');
    setActionItems([]);

    try {
      const res = await fetch('http://localhost:8000/api/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript: text }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              if (data.type === 'extracted') {
                setPipelinePhase('execute');
                setActionItems(data.items.map((item) => ({ item: { ...item, status: 'pending' } })));
              } else if (data.type === 'update') {
                setActionItems((prev) => {
                  const newItems = [...prev];
                  const state = data.state;
                  const result = state.result;
                  newItems[data.index] = {
                    item: {
                      ...state.item,
                      status: result ? (result.status === 'success' ? 'completed' : 'failed') : 'processing',
                      owner: state.item.owner || result?.resolved_owner,
                      link: result?.link,
                      error: result?.error,
                    },
                  };
                  return newItems;
                });
              }
            } catch (e) {
              /* ignore malformed SSE chunk */
            }
          }
        }
      }
      setPipelinePhase('done');
    } catch (err) {
      console.error(err);
      setPipelinePhase('idle');
    } finally {
      setIsProcessing(false);
    }
  };

  const completedCount = actionItems.filter((r) => r.item.status === 'completed').length;

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-canvas text-ink">
      <Sidebar />

      <div className="flex-1 h-full flex flex-col min-w-0">
        {/* Topbar */}
        <header className="h-16 shrink-0 border-b border-border bg-surface flex items-center justify-between px-8">
          <div>
            <h1 className="text-[15px] font-semibold text-ink leading-tight">Meeting workspace</h1>
            <p className="text-[12px] text-ink-faint">Turn a transcript into executed actions</p>
          </div>
          <div className="flex items-center gap-3">
            {actionItems.length > 0 && (
              <span className="text-[12px] font-medium text-ink-muted">
                {completedCount}/{actionItems.length} complete
              </span>
            )}
            <span
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] font-semibold ${
                pipelinePhase === 'idle'
                  ? 'bg-gray-100 text-ink-muted'
                  : pipelinePhase === 'done'
                  ? 'bg-success-soft text-success'
                  : 'bg-accent-soft text-accent'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  pipelinePhase === 'idle'
                    ? 'bg-gray-400'
                    : pipelinePhase === 'done'
                    ? 'bg-success'
                    : 'bg-accent animate-pulse'
                }`}
              />
              {PHASE_LABEL[pipelinePhase]}
            </span>
          </div>
        </header>

        {/* Body — fixed to viewport, only inner panels scroll */}
        <main className="flex-1 min-h-0 grid grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] gap-6 p-6">
          <TranscriptPanel
            onStartProcessing={handleStartProcessing}
            isProcessing={isProcessing}
            pastedText={pastedText}
            setPastedText={setPastedText}
          />

          <div className="min-h-0 flex flex-col gap-6">
            <PipelineTracker phase={pipelinePhase} />
            <ActionItemsTable items={actionItems} />
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
