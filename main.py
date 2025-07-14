from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import requests
import time
import threading
from datetime import datetime
from typing import List, Dict, Any
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Global storage for active tasks
active_tasks = {}
task_counter = 0

def send_request(url: str) -> Dict[str, Any]:
    """Send a request to the URL and return status"""
    try:
        response = requests.get(url, timeout=30)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if response.status_code == 200:
            result = {
                "url": url,
                "status": "success",
                "status_code": response.status_code,
                "timestamp": timestamp,
                "response_time": response.elapsed.total_seconds()
            }
            print(f"✅ Pinged {url} at {timestamp} - Status: {response.status_code}")
        else:
            result = {
                "url": url,
                "status": "failed",
                "status_code": response.status_code,
                "timestamp": timestamp,
                "response_time": response.elapsed.total_seconds()
            }
            print(f"❌ Failed to ping {url} at {timestamp} - Status: {response.status_code}")
        
        return result
        
    except requests.RequestException as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = {
            "url": url,
            "status": "error",
            "error": str(e),
            "timestamp": timestamp
        }
        print(f"🔥 Error pinging {url} at {timestamp}: {e}")
        return result

def ping_urls_continuously(task_id: str, urls: List[str], interval: int):
    """Continuously ping URLs at specified intervals"""
    task_info = active_tasks[task_id]
    
    while task_info["active"]:
        for url in urls:
            if not task_info["active"]:
                break
                
            result = send_request(url)
            task_info["last_results"].append(result)
            
            # Keep only last 10 results per task
            if len(task_info["last_results"]) > 10:
                task_info["last_results"].pop(0)
        
        # Sleep for the specified interval
        for _ in range(interval):
            if not task_info["active"]:
                break
            time.sleep(1)
    
    # Clean up when task is stopped
    if task_id in active_tasks:
        del active_tasks[task_id]

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html', active_tasks=active_tasks)

@app.route('/ping', methods=['POST'])
def start_ping():
    """Start pinging URLs"""
    global task_counter
    
    urls_input = request.form.get('urls', '')
    interval = int(request.form.get('interval', 60))
    
    # Parse URLs from textarea (one per line)
    urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
    
    if not urls:
        flash('Please enter at least one URL', 'error')
        return redirect(url_for('index'))
    
    # Validate URLs
    valid_urls = []
    for url in urls:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        valid_urls.append(url)
    
    task_counter += 1
    task_id = f"task_{task_counter}"
    
    # Store task information
    active_tasks[task_id] = {
        "urls": valid_urls,
        "interval": interval,
        "active": True,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_results": []
    }
    
    # Start the pinging task in a separate thread
    thread = threading.Thread(
        target=ping_urls_continuously,
        args=(task_id, valid_urls, interval)
    )
    thread.daemon = True
    thread.start()
    
    flash(f'Started pinging {len(valid_urls)} URLs every {interval} seconds', 'success')
    return redirect(url_for('index'))

@app.route('/stop/<task_id>')
def stop_task(task_id: str):
    """Stop a specific ping task"""
    if task_id not in active_tasks:
        flash('Task not found', 'error')
    else:
        active_tasks[task_id]["active"] = False
        flash(f'Task {task_id} stopped successfully', 'success')
    
    return redirect(url_for('index'))

@app.route('/stop-all')
def stop_all_tasks():
    """Stop all active ping tasks"""
    stopped_count = 0
    
    for task_id in list(active_tasks.keys()):
        active_tasks[task_id]["active"] = False
        stopped_count += 1
    
    flash(f'Stopped {stopped_count} active tasks', 'success')
    return redirect(url_for('index'))

@app.route('/status')
def get_status():
    """Get status as JSON (API endpoint)"""
    tasks_info = []
    
    for task_id, task_info in active_tasks.items():
        tasks_info.append({
            "task_id": task_id,
            "urls": task_info["urls"],
            "interval": task_info["interval"],
            "active": task_info["active"],
            "started_at": task_info["started_at"],
            "last_results": task_info["last_results"][-3:]  # Show last 3 results
        })
    
    return jsonify({
        "active_tasks": len(active_tasks),
        "tasks": tasks_info
    })

@app.route('/ping-once')
def ping_once():
    """Ping a single URL once and return the result"""
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    result = send_request(url)
    return jsonify(result)

if __name__ == "__main__":
    print("Script based on jashgro's work (https://bit.ly/jashgro)")
    print("Flask Web Interface Version - Starting server...")
    app.run(debug=True, host="0.0.0.0", port=8000)