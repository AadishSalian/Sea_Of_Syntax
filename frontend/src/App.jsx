import React, { useState, useEffect } from 'react';
import PipelineTracker from './components/PipelineTracker';
import ActionItemsTable from './components/ActionItemsTable';
import ActionPanel from './components/ActionPanel';
import InsightsPanel from './components/InsightsPanel';
import { Search } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [pastedText, setPastedText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [pipelinePhase, setPipelinePhase] = useState('idle');
  const [actionItems, setActionItems] = useState([]);

  const handleStartProcessing = async (text) => {
    setIsProcessing(true);
    setPipelinePhase('extract');
    setActionItems([]);
    
    try {
      const res = await fetch("http://localhost:8000/api/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript: text })
      });
      
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep the last incomplete line in buffer
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              if (data.type === 'extracted') {
                setPipelinePhase('execute');
                setActionItems(data.items.map(item => ({ item: { ...item, status: 'pending' } })));
              } else if (data.type === 'update') {
                setActionItems(prev => {
                  const newItems = [...prev];
                  const state = data.state;
                  const result = state.result;
                  newItems[data.index] = {
                    item: {
                      ...state.item,
                      status: result ? (result.status === 'success' ? 'completed' : 'failed') : 'processing',
                      owner: state.item.owner || result?.resolved_owner,
                      link: result?.link
                    }
                  };
                  return newItems;
                });
              }
            } catch(e) {}
          }
        }
      }
      setPipelinePhase('done');
    } catch(err) {
      console.error(err);
      setPipelinePhase('idle');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#09090b] text-white relative">
      {/* The main container */}
      <div className="relative z-10 w-full h-full flex overflow-hidden justify-center max-w-7xl mx-auto">
        
        {/* Main Content Area */}
        <main className="flex-1 block pt-10 px-10 pb-10 overflow-y-auto custom-scrollbar w-full">
          {/* Header */}
              <div className="flex items-start justify-between mb-8 shrink-0">
                <div>
                  <h1 className="text-2xl font-semibold text-zinc-100 mb-1">Meeting Workspace</h1>
                  <p className="text-sm text-zinc-400">Ready to process new meeting</p>
                </div>
              </div>
              
              {/* Top Row: Transcript and Insights */}
              <div className="flex flex-col lg:flex-row gap-6 h-64 mb-10 shrink-0">
                 <div className="flex-[0.6]">
                   <ActionPanel 
                     onStartProcessing={handleStartProcessing} 
                     isProcessing={isProcessing} 
                     pastedText={pastedText}
                     setPastedText={setPastedText}
                   />
                 </div>
                 <div className="flex-[0.4]">
                   <InsightsPanel insights={null} />
                 </div>
              </div>
              
              <h2 className="text-lg font-semibold text-zinc-100 mb-6 shrink-0">AI Meeting Pipeline</h2>
              <PipelineTracker phase={pipelinePhase} />
              
              <ActionItemsTable items={actionItems} />
        </main>
      </div>
    </div>
  )
}

export default App;
