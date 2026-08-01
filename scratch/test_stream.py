import requests
import json

def test_stream():
    url = "http://localhost:8000/api/stream"
    payload = {"transcript": "Please email Sarah to send the design documents by Monday."}
    
    with requests.post(url, json=payload, stream=True) as r:
        for line in r.iter_lines():
            if line:
                print(line.decode('utf-8'))

if __name__ == "__main__":
    test_stream()
