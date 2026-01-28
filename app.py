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
@app.route('/', methods=['POST'])
def slack_events():
    data = request.json
    
    # Handle Slack URL verification challenge
    if data.get('type') == 'url_verification':
        return jsonify({'challenge': data.get('challenge')})
    
    # Handle actual events
    if data.get('type') == 'event_callback':
        event = data.get('event', {})
        event_type = event.get('type')
        
        payload = None
        
        # Process app_mention events
        if event_type == 'app_mention':
            payload = {
                'type': 'app_mention',
                'channel': event.get('channel'),
                'user': event.get('user'),
                'text': event.get('text'),
                'ts': event.get('ts'),
                'thread_ts': event.get('thread_ts')
            }
        
        # Process reaction_added events (📧 emoji)
        elif event_type == 'reaction_added':
            reaction = event.get('reaction', '')
            # Check for email emoji (📧)
            if reaction in ['email', 'e-mail', 'envelope']:
                item = event.get('item', {})
                payload = {
                    'type': 'reaction_added',
                    'reaction': reaction,
                    'user': event.get('user'),
                    'item': {
                        'channel': item.get('channel'),
                        'ts': item.get('ts')
                    }
                }
        
        # Process thread replies (for sequence selection responses)
        elif event_type == 'message':
            # Only forward if it's a thread reply (has thread_ts)
            # Exclude bot messages, message_changed, etc.
            subtype = event.get('subtype')
            thread_ts = event.get('thread_ts')
            
            if thread_ts and not subtype:
                payload = {
                    'type': 'thread_reply',
                    'channel': event.get('channel'),
                    'user': event.get('user'),
                    'text': event.get('text'),
                    'ts': event.get('ts'),
                    'thread_ts': thread_ts
                }
        
        # Forward payload to Tasklet if we have one
        if payload and TASKLET_WEBHOOK_URL:
            try:
                requests.post(TASKLET_WEBHOOK_URL, json=payload, timeout=5)
            except Exception as e:
                print(f'Error forwarding to Tasklet: {e}')
        elif not TASKLET_WEBHOOK_URL:
            print('Warning: TASKLET_WEBHOOK_URL not set')
    
    # Always return 200 OK to Slack quickly
    return jsonify({'ok': True})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
