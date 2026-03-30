import sys
import base64
import requests
from pathlib import Path

filepath = sys.argv[1]

with open(filepath, "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

resp = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "moondream:latest",
        "messages": [
            {
                "role": "user",
                "content": "Describe this image in detail.",
                "images": [image_data]
            }
        ],
        "stream": False
    },
    timeout=300
)
resp.raise_for_status()
print(resp.json()["message"]["content"])
