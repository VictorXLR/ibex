from flask import Flask, request, jsonify
import json
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
log_file = Path(__file__).parent / 'telemetry.log'

class TelemetryClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        
    def log_event(self, event_type: str, data: dict):
        try:
            import requests
            payload = {
                "type": event_type,
                "data": data
            }
            requests.post(f"{self.base_url}/log", json=payload, timeout=1)
        except Exception as e:
            print(f"Telemetry error: {e}")

@app.route('/log', methods=['POST'])
def log_event():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    event = {
        'timestamp': datetime.now().isoformat(),
        'event': data
    }
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event) + '\n')
    
    return jsonify({"status": "success"}), 200

@app.route('/events', methods=['GET'])
def get_events():
    if not log_file.exists():
        return jsonify({"events": []})
    
    with open(log_file, 'r', encoding='utf-8') as f:
        events = [json.loads(line) for line in f]
    
    return jsonify({"events": events})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
