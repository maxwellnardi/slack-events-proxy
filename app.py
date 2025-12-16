"""Slack Events Proxy Server

This simple server:
1. Handles Slack's URL verification challenge
2. Forwards app_mention events to your Tasklet webhook

Deploy this on Railway, Render, or Replit (all have free tiers).
"""

import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Set this environment variable to your Tasklet webhook URL
TASKLET_WEBHOOK_URL = os.environ.get('TASKLET_WEBHOOK_URL')

@app.route('/slack/events', methods=['POST'])
def slack_events():
    data = request.json
    
    # Handle Slack URL verification challenge
    if data.get('type') == 'url_verification':
        return jsonify({'challenge': data.get('challenge')})
    
    # Handle actual events
    if data.get('type') == 'event_callback':
        event = data.get('event', {})
        
        # Only process app_mention events
        if event.get('type') == 'app_mention':
            # Forward to Tasklet webhook
            payload = {
                'channel': event.get('channel'),
                'user': event.get('user'),
                'text': event.get('text'),
                'ts': event.get('ts'),
                'thread_ts': event.get('thread_ts')
            }
            
            if TASKLET_WEBHOOK_URL:
                try:
                    requests.post(TASKLET_WEBHOOK_URL, json=payload, timeout=5)
                except Exception as e:
                    print(f'Error forwarding to Tasklet: {e}')
            else:
                print('Warning: TASKLET_WEBHOOK_URL not set')
    
    # Always return 200 OK to Slack quickly
    return jsonify({'ok': True})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
