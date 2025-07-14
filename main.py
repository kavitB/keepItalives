from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import requests
import time
import threading
from datetime import datetime
from typing import List, Dict, Any

app = Flask(__name__)
app.secret_key = 'simple-pinger-key'

# Global storage for active tasks
active_tasks = {}
task_counter = 0

def ping_url(url: str) -> Dict[str, Any]:
    """Simple URL ping function with better error handling"""
    try:
        # More robust request with headers and shorter timeout
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(
            url, 
            timeout=5,  # Shorter timeout
            headers=headers,
            allow_redirects=True,
            verify=False  # Skip SSL verification for problematic sites
        )
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if response.status_code == 200:
            return {
                "url": url,
                "status": "success",
                "status_code": response.status_code,
                "timestamp": timestamp,
                "message": "OK"
            }
        else:
            return {
                "url": url,
                "status": "warning",
                "status_code": response.status_code,
                "timestamp": timestamp,
                "message": f"HTTP {response.status_code}"
            }
        
    except requests.exceptions.Timeout:
        return {
            "url": url,
            "status": "timeout",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": "Request timed out"
        }
    except requests.exceptions.ConnectionError:
        return {
            "url": url,
            "status": "connection_error",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": "Connection failed (proxy/network issue)"
        }
    except Exception as e:
        return {
            "url": url,
            "status": "error",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
        }

def ping_task(task_id: str, urls: List[str], interval: int):
    """Background task to ping URLs"""
    task_info = active_tasks[task_id]
    
    while task_info["active"]:
        for url in urls:
            if not task_info["active"]:
                break
            
            result = ping_url(url)
            task_info["results"].append(result)
            
            # Keep only last 5 results
            if len(task_info["results"]) > 5:
                task_info["results"].pop(0)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {url} -> {result['status']}: {result['message']}")
        
        # Simple sleep
        time.sleep(interval)
    
    # Cleanup
    if task_id in active_tasks:
        del active_tasks[task_id]

@app.route('/')
def index():
    """Main page"""
    return render_template('simple_index.html', active_tasks=active_tasks)

@app.route('/ping', methods=['POST'])
def start_ping():
    """Start pinging URLs"""
    global task_counter
    
    urls_input = request.form.get('urls', '')
    interval = int(request.form.get('interval', 60))
    
    # Parse URLs
    urls = []
    for url in urls_input.split('\n'):
        url = url.strip()
        if url:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            urls.append(url)
    
    if not urls:
        flash('Please enter at least one URL', 'error')
        return redirect(url_for('index'))
    
    task_counter += 1
    task_id = f"task_{task_counter}"
    
    # Store task info
    active_tasks[task_id] = {
        "urls": urls,
        "interval": interval,
        "active": True,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": []
    }
    
    # Start background thread
    thread = threading.Thread(target=ping_task, args=(task_id, urls, interval))
    thread.daemon = True
    thread.start()
    
    flash(f'Started pinging {len(urls)} URLs every {interval} seconds', 'success')
    return redirect(url_for('index'))

@app.route('/stop/<task_id>')
def stop_task(task_id: str):
    """Stop a specific task"""
    if task_id in active_tasks:
        active_tasks[task_id]["active"] = False
        flash(f'Stopped {task_id}', 'success')
    return redirect(url_for('index'))

@app.route('/stop-all')
def stop_all():
    """Stop all tasks"""
    count = 0
    for task_id in list(active_tasks.keys()):
        active_tasks[task_id]["active"] = False
        count += 1
    flash(f'Stopped {count} tasks', 'success')
    return redirect(url_for('index'))

@app.route('/status')
def get_status():
    """Get status as JSON"""
    return jsonify({
        "active_tasks": len(active_tasks),
        "tasks": list(active_tasks.values())
    })

if __name__ == "__main__":
    print("Simple URL Pinger - Starting...")
    app.run(debug=True, host="0.0.0.0", port=8000)