import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
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
    <div className="flex h-screen w-screen overflow-hidden bg-[#07070A] text-white relative">
      {/* Abstract Background Orbs */}
      <div className="absolute top-[10%] left-[10%] w-[45vw] h-[45vw] rounded-full bg-violet-600/15 blur-[120px] mix-blend-screen pointer-events-none" />
      <div className="absolute bottom-[10%] right-[10%] w-[45vw] h-[45vw] rounded-full bg-blue-600/15 blur-[120px] mix-blend-screen pointer-events-none" />
      
      {/* The ONE massive glass panel container covering the whole page */}
      <div className="relative z-10 w-full h-full flex overflow-hidden !backdrop-blur-[60px] !bg-white/[0.03]">
        
        {/* Left Sidebar */}
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        
        {/* Main Content Area */}
        <main className="flex-1 block pt-10 px-10 pb-10 overflow-y-auto custom-scrollbar">
          {activeTab === 'dashboard' ? (
            <>
              {/* Header */}
              <div className="flex items-start justify-between mb-8 shrink-0">
                <div>
                  <h1 className="text-2xl font-bold text-white tracking-tight mb-2">Meeting Workspace</h1>
                  <p className="text-sm text-gray-400 font-medium tracking-wide">Ready to process new meeting</p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.05] border border-white/10 text-xs font-medium text-gray-300">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
                    Ongoing
                  </div>
                  <div className="relative">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input 
                      type="text" 
                      placeholder="Search" 
                      className="bg-white/[0.03] border border-white/10 rounded-full py-1.5 pl-9 pr-4 text-sm text-gray-300 focus:outline-none focus:border-purple-500/50 w-48 shadow-inner-light transition-colors hover:bg-white/[0.05]" 
                    />
                  </div>
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
              
              <h2 className="text-lg font-bold text-white mb-6 tracking-wide shrink-0">AI Meeting Pipeline</h2>
              <PipelineTracker phase={pipelinePhase} />
              
              <ActionItemsTable items={actionItems} />
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full min-h-[600px]">
              <div className="w-20 h-20 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mb-6 shadow-inner-light">
                <span className="text-3xl capitalize text-purple-400 font-bold tracking-wider">{activeTab.charAt(0)}</span>
              </div>
              <h2 className="text-3xl font-bold text-white capitalize mb-3 tracking-wide">{activeTab}</h2>
              <p className="text-gray-400 text-sm max-w-md text-center leading-relaxed">
                The <strong className="text-white capitalize">{activeTab}</strong> module is currently under development. Check back later for updates.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App;
