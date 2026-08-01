import json
import asyncio
import os
import tempfile
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

from orchestrator import stream_pipeline_async

app = FastAPI(title="MeetingToMotion API")

# Allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from faster_whisper import WhisperModel

# Global model instance
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
    return whisper_model

class ProcessRequest(BaseModel):
    transcript: str

@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Receives an audio file from the browser, transcribes it locally using faster-whisper,
    and returns the text.
    """
    try:
        model = get_whisper_model()
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_audio:
            temp_path = temp_audio.name
            temp_audio.write(await audio.read())
            
        # Transcribe
        segments, info = model.transcribe(temp_path, beam_size=5)
        transcript = " ".join([segment.text for segment in segments])
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return {"transcript": transcript.strip()}
    except Exception as e:
        return {"error": str(e)}
    transcript: str

@app.post("/api/stream")
async def stream_pipeline_endpoint(req: ProcessRequest):
    """
    Streams pipeline execution updates back to the client using Server-Sent Events.
    """
    async def event_generator():
        try:
            # We call the async version of stream_pipeline from orchestrator
            async for event in stream_pipeline_async(req.transcript):
                yield {
                    "data": json.dumps(event)
                }
        except Exception as e:
            yield {
                "data": json.dumps({"type": "error", "error": str(e)})
            }

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
