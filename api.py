import json
import asyncio
from fastapi import FastAPI, Request
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

class ProcessRequest(BaseModel):
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
