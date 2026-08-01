import React, { useState } from 'react'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import ActionPanel from './components/ActionPanel'
import PipelineTracker from './components/PipelineTracker'
import ActionItemsTable from './components/ActionItemsTable'
import StatsGrid from './components/StatsGrid'
import RightPanel from './components/RightPanel'

function App() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [actionItems, setActionItems] = useState([]);
  const [pipelinePhase, setPipelinePhase] = useState("idle"); // idle, extract, execute, done
  const [activeTab, setActiveTab] = useState("Dashboard");

  const handleStartProcessing = async (transcriptToSend) => {
    setIsProcessing(true);
    setActionItems([]);
    setPipelinePhase("extract");

    try {
      const response = await fetch("http://localhost:8000/api/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript: transcriptToSend })
      });
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            if (!dataStr) continue;
            try {
              const event = JSON.parse(dataStr);
              if (event.type === 'extracted') {
                // Initialize items in state with pending status
                setActionItems(event.items.map(item => ({ item, result: null, was_clarified: false })));
                setPipelinePhase("execute");
              } else if (event.type === 'update') {
                // Update specific item with its result
                setActionItems(prev => {
                  const newItems = [...prev];
                  newItems[event.index] = {
                    item: event.state.item,
                    result: event.state.result,
                    was_clarified: event.state.was_clarified
                  };
                  return newItems;
                });
              } else if (event.type === 'error') {
                console.error("Pipeline error on item", event.index, event.error);
              }
            } catch (e) {
              console.error("Parse error", e, dataStr);
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
      alert("Error starting pipeline. Is the FastAPI backend running?");
    } finally {
      setIsProcessing(false);
      setPipelinePhase("done");
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      
      <div className="flex-1 flex flex-col h-screen overflow-hidden relative">
        {/* Ambient background glow */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-[120px] pointer-events-none" />
        
        <Header />
        
        <div className="flex flex-1 overflow-hidden">
          <main className="flex-1 overflow-y-auto p-8 custom-scrollbar">
            <div className="max-w-6xl mx-auto">
              {activeTab === "Dashboard" && (
                <>
                  <ActionPanel 
                    onStartProcessing={handleStartProcessing} 
                    isProcessing={isProcessing} 
                  />
                  <PipelineTracker phase={pipelinePhase} />
                  <ActionItemsTable items={actionItems} />
                  <StatsGrid items={actionItems} />
                </>
              )}

              {activeTab === "Action Items" && (
                <div className="mt-4">
                  <h2 className="text-2xl font-bold text-white mb-6">Action Items</h2>
                  <ActionItemsTable items={actionItems} />
                </div>
              )}

              {activeTab === "Analytics" && (
                <div className="mt-4">
                  <h2 className="text-2xl font-bold text-white mb-6">Analytics</h2>
                  <StatsGrid items={actionItems} />
                </div>
              )}

              {activeTab === "AI Processing" && (
                <div className="mt-4">
                  <h2 className="text-2xl font-bold text-white mb-6">Pipeline Live View</h2>
                  <PipelineTracker phase={pipelinePhase} />
                </div>
              )}

              {!["Dashboard", "Action Items", "Analytics", "AI Processing"].includes(activeTab) && (
                <div className="flex flex-col items-center justify-center h-[60vh] text-center">
                  <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
                    <span className="text-gray-500 font-bold text-xl">{activeTab.charAt(0)}</span>
                  </div>
                  <h2 className="text-xl font-bold text-gray-300 mb-2">{activeTab}</h2>
                  <p className="text-gray-500">This module is currently under construction.</p>
                </div>
              )}
            </div>
          </main>
          
          <RightPanel />
        </div>
      </div>
    </div>
  )
}

export default App
