import React, { useState, useRef } from 'react';
import { Upload, FileText, Play, Mic, FileTerminal } from 'lucide-react';

const ActionPanel = ({ onStartProcessing, isProcessing }) => {
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' or 'paste'
  const [pastedText, setPastedText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleStartProcessing = async () => {
    if (!selectedFile && !pastedText.trim()) {
      alert("Please upload a file or paste transcript text first.");
      return;
    }
    
    let transcriptToSend = pastedText;
    if (activeTab === 'upload' && selectedFile) {
      transcriptToSend = await selectedFile.text();
    }
    
    if (onStartProcessing) {
      onStartProcessing(transcriptToSend);
    }
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 mb-6">
      {/* Upload/Input Section */}
      <div className="flex-1 bg-card rounded-2xl p-6 border border-white/5 shadow-lg relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/5 rounded-full blur-[80px] -mr-32 -mt-32 transition-opacity group-hover:opacity-100 opacity-50" />
        
        <h2 className="text-xl font-semibold text-white mb-6">New Meeting</h2>
        
        <div className="flex gap-4 mb-6">
          <button 
            onClick={() => setActiveTab('upload')}
            className={`flex-1 py-3 rounded-xl flex items-center justify-center gap-2 font-medium transition-colors ${
              activeTab === 'upload' 
                ? 'bg-purple-600/20 text-purple-400 border border-purple-500/30' 
                : 'bg-white/5 text-gray-300 border border-white/10 hover:bg-white/10'
            }`}
          >
            <Upload size={18} />
            Upload TXT
          </button>
          <button 
            onClick={() => setActiveTab('paste')}
            className={`flex-1 py-3 rounded-xl flex items-center justify-center gap-2 font-medium transition-colors ${
              activeTab === 'paste' 
                ? 'bg-purple-600/20 text-purple-400 border border-purple-500/30' 
                : 'bg-white/5 text-gray-300 border border-white/10 hover:bg-white/10'
            }`}
          >
            <FileTerminal size={18} />
            Paste Text
          </button>
          <button className="flex-[0.5] py-3 rounded-xl bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10 flex items-center justify-center transition-colors">
            <Mic size={18} />
          </button>
        </div>

        {activeTab === 'upload' ? (
          <div 
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-white/10 rounded-xl p-8 flex flex-col items-center justify-center text-center hover:border-purple-500/50 hover:bg-purple-500/5 transition-all cursor-pointer"
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              accept=".txt" 
              className="hidden" 
            />
            <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center mb-3">
              <Upload size={24} className="text-purple-400" />
            </div>
            {selectedFile ? (
              <p className="text-gray-300 font-medium">{selectedFile.name}</p>
            ) : (
              <>
                <p className="text-gray-300 font-medium mb-1">Drag & drop your transcript here</p>
                <p className="text-xs text-gray-500">Supports .txt files up to 10MB</p>
              </>
            )}
          </div>
        ) : (
          <div className="h-40 border border-white/10 rounded-xl overflow-hidden focus-within:border-purple-500/50 transition-colors bg-black/20">
            <textarea 
              value={pastedText}
              onChange={(e) => setPastedText(e.target.value)}
              placeholder="Paste your meeting transcript here..."
              className="w-full h-full bg-transparent p-4 text-sm text-gray-200 placeholder:text-gray-600 resize-none focus:outline-none custom-scrollbar"
            />
          </div>
        )}

        <button 
          onClick={handleStartProcessing}
          disabled={isProcessing}
          className="w-full mt-6 py-4 rounded-xl bg-gradient-to-r from-purple-600 to-violet-500 text-white font-semibold flex items-center justify-center gap-2 hover:opacity-90 transition-opacity shadow-[0_0_20px_rgba(124,58,237,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? (
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <Play size={20} fill="currentColor" />
          )}
          {isProcessing ? 'Processing...' : 'Start Processing Engine'}
        </button>
      </div>

      {/* Recent Transcripts */}
      <div className="w-full lg:w-80 bg-card rounded-2xl p-6 border border-white/5 shadow-lg flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Recent</h3>
          <button className="text-xs text-purple-400 hover:text-purple-300 font-medium transition-colors">View All</button>
        </div>
        
        <div className="flex flex-col gap-3 flex-1 justify-center">
          {/* Placeholder for when no transcripts exist */}
          <div className="flex flex-col items-center justify-center h-full text-center py-4">
            <FileText size={24} className="text-gray-600 mb-2" />
            <p className="text-sm text-gray-500 font-medium">No recent transcripts</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ActionPanel;
