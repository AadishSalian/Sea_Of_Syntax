import streamlit as st
import sounddevice as sd
import numpy as np
import tempfile
import wave
import os
import time

# Fix OpenMP duplicate lib issue often seen on Windows with faster-whisper/CTranslate2
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from faster_whisper import WhisperModel

@st.cache_resource(show_spinner=False)
def get_whisper_model():
    """
    Load and cache the Whisper model so it only loads once per session.
    Using "base" model on CPU to ensure maximum compatibility and speed.
    """
    return WhisperModel("base", device="cpu", compute_type="int8")

def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """
    Takes raw WAV audio bytes, saves to a temporary file, 
    and uses faster-whisper to transcribe it.
    Returns the transcription as a string. On failure, returns an empty string.
    """
    try:
        model = get_whisper_model()
        
        # Save audio to a temporary file because WhisperModel.transcribe accepts file paths
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_wav_path = temp_wav.name
            temp_wav.write(audio_bytes)
        
        # Transcribe the audio file
        segments, info = model.transcribe(temp_wav_path, beam_size=5)
        
        # Join all text segments
        transcript = " ".join([segment.text for segment in segments])
        
        # Clean up the temporary file
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
            
        return transcript.strip()
        
    except Exception as e:
        print(f"WARNING: Audio transcription failed: {e}")
        return ""
