import React, { useState, useRef } from 'react';
import { Mic, Square, Upload, ArrowRight, Loader2 } from 'lucide-react';

const TranscriptPanel = ({ onStartProcessing, isProcessing, pastedText, setPastedText }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);

  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      try {
        const text = await file.text();
        setPastedText(text);
      } catch (err) {
        alert('Could not read file');
      }
    }
  };

  const handleStartProcessing = () => {
    if (!pastedText.trim()) {
      alert('Please upload a file, record audio, or paste transcript text first.');
      return;
    }
    if (onStartProcessing) onStartProcessing(pastedText);
  };

  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
      return;
    }

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
          const res = await fetch('http://localhost:8000/api/transcribe', {
            method: 'POST',
            body: formData,
          });
          const data = await res.json();
          if (data.transcript?.trim()) {
            const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const newEntry = `${timestamp} ${data.transcript}`;
            setPastedText((prev) => (prev ? prev + '\n\n' + newEntry : newEntry));
          }
        } catch (e) {
          console.error('Transcription error:', e);
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Mic access denied or error:', err);
    }
  };

  return (
    <div className="bg-surface border border-border rounded-lg h-full flex flex-col overflow-hidden">
      <div className="px-5 py-4 border-b border-border flex items-center justify-between shrink-0">
        <h2 className="text-[13px] font-semibold text-ink">Meeting transcript</h2>
        <div className="flex items-center gap-2">
          {isRecording && (
            <span className="flex items-center gap-1.5 text-[11px] font-semibold text-danger bg-danger-soft px-2 py-1 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-danger animate-pulse" />
              Recording
            </span>
          )}
          {isTranscribing && (
            <span className="flex items-center gap-1.5 text-[11px] font-semibold text-accent bg-accent-soft px-2 py-1 rounded-full">
              <Loader2 size={11} className="animate-spin" />
              Transcribing
            </span>
          )}
        </div>
      </div>

      <textarea
        value={pastedText}
        onChange={(e) => setPastedText(e.target.value)}
        placeholder="Paste a transcript, upload a .txt file, or record with the mic below..."
        className="flex-1 min-h-0 w-full bg-transparent px-5 py-4 text-[13px] text-ink placeholder:text-ink-faint resize-none focus:outline-none scrollbar-thin leading-relaxed"
      />

      <div className="px-5 py-3.5 border-t border-border flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".txt"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium rounded-md border border-border text-ink-muted hover:bg-canvas transition-colors"
          >
            <Upload size={13} />
            Upload
          </button>
          <button
            onClick={toggleRecording}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium rounded-md border transition-colors ${
              isRecording
                ? 'border-danger/30 bg-danger-soft text-danger'
                : 'border-border text-ink-muted hover:bg-canvas'
            }`}
          >
            {isRecording ? <Square size={13} /> : <Mic size={13} />}
            {isRecording ? 'Stop' : 'Record'}
          </button>
        </div>

        <button
          onClick={handleStartProcessing}
          disabled={isProcessing}
          className="flex items-center gap-1.5 px-4 py-1.5 text-[12px] font-semibold text-white bg-accent hover:bg-accent-hover rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? <Loader2 size={13} className="animate-spin" /> : <ArrowRight size={13} />}
          {isProcessing ? 'Processing' : 'Process'}
        </button>
      </div>
    </div>
  );
};

export default TranscriptPanel;
