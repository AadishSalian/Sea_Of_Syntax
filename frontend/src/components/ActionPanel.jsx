import React, { useState, useRef } from 'react';
import { Mic, Square, Upload } from 'lucide-react';

const ActionPanel = ({ onStartProcessing, isProcessing, pastedText, setPastedText }) => {
  const [activeTab, setActiveTab] = useState('paste');
  const [selectedFileName, setSelectedFileName] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFileName(file.name);
      try {
        const text = await file.text();
        setPastedText(text);
      } catch (err) {
        alert("Could not read file");
      }
    }
  };

  const handleStartProcessing = async () => {
    if (!pastedText.trim()) {
      alert("Please upload a file, record audio, or paste transcript text first.");
      return;
    }
    
    if (onStartProcessing) {
      onStartProcessing(pastedText);
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunksRef.current.push(e.data);
        };

        mediaRecorder.onstop = async () => {
          setIsTranscribing(true);
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const formData = new FormData();
          formData.append('audio', audioBlob, 'recording.webm');
          
          try {
            const res = await fetch("http://localhost:8000/api/transcribe", {
              method: "POST",
              body: formData
            });
            const data = await res.json();
            if (data.transcript !== undefined) {
              if (data.transcript.trim() !== "") {
                const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const newEntry = `${timestamp} ${data.transcript}`;
                setPastedText(prev => (prev ? prev + "\n\n" + newEntry : newEntry));
                setActiveTab('paste');
              }
            }
          } catch (e) {
            console.error("Transcription error:", e);
          } finally {
            setIsTranscribing(false);
          }
        };

        mediaRecorder.start();
        setIsRecording(true);
      } catch (err) {
        console.error("Mic access denied or error:", err);
      }
    }
  };

  return (
    <div className="glass-panel h-full rounded-2xl p-6 flex flex-col relative overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-white tracking-wide">Meeting Transcript</h2>
        <div className="flex gap-2">
          {isRecording && (
            <div className="flex items-center gap-2 text-xs font-semibold text-red-400 bg-red-400/10 px-3 py-1.5 rounded-lg border border-red-400/20 animate-pulse">
              <span className="w-2 h-2 rounded-full bg-red-400" />
              Recording...
            </div>
          )}
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            accept=".txt" 
            className="hidden" 
          />
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="px-3 py-1.5 text-xs font-semibold rounded-lg border bg-white/5 text-gray-300 border-white/10 hover:bg-white/10 hover:text-white transition-all flex items-center"
          >
            <Upload size={14} className="mr-1.5" />
            Upload
          </button>
          <button 
            onClick={toggleRecording}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all flex items-center ${
              isRecording 
                ? 'bg-white/10 text-white border-white/20' 
                : 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10 hover:text-white'
            }`}
          >
            {isRecording ? <Square size={14} className="mr-1.5" /> : <Mic size={14} className="mr-1.5" />}
            {isRecording ? 'Stop' : 'Live Mic'}
          </button>
          <button 
            onClick={handleStartProcessing}
            disabled={isProcessing}
            className="px-4 py-1.5 text-xs font-bold text-white bg-gradient-to-r from-purple-500 to-indigo-500 rounded-lg hover:shadow-[0_0_15px_rgba(168,85,247,0.4)] transition-all border border-purple-400/30 disabled:opacity-50 flex items-center"
          >
            {isProcessing ? (
               <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin mr-1.5" />
            ) : null}
            {isProcessing ? 'Processing...' : 'Process'}
          </button>
        </div>
      </div>
      
      <div className="flex-1 border border-white/[0.05] rounded-xl overflow-hidden bg-[#05050A]/50 focus-within:border-purple-500/30 transition-colors shadow-inner-light">
        <textarea 
          value={pastedText}
          onChange={(e) => setPastedText(e.target.value)}
          placeholder="Paste text, upload a .txt file, or use Live Mic to begin..."
          className="w-full h-full bg-transparent p-5 text-[13px] text-gray-300 placeholder:text-gray-600 resize-none focus:outline-none custom-scrollbar leading-relaxed"
        />
      </div>
    </div>
  );
};

export default ActionPanel;
