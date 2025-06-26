import requests
import json

url = "http://localhost:8000/schedule"

payload = {
    "steps": [
        {
            "tool": "shell",
            "command": "echo \"Hello from my first task!\" > output.txt"
        },
        {
            "tool": "python",
            "code": "import os; print(f\"The current directory contains: {os.listdir('.')}\" )"
        }
    ]
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, data=json.dumps(payload))

print("Status Code:", response.status_code)
print("Response JSON:", response.json())