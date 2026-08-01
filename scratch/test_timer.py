import sys
from audio_input import record_and_transcribe

def mock_callback(secs_left):
    print(f"Callback fired: {secs_left} seconds left.")
    sys.stdout.flush()

if __name__ == "__main__":
    print("Starting 3s transcription test...")
    res = record_and_transcribe(3, progress_callback=mock_callback)
    print(f"Final Transcript: '{res}'")
