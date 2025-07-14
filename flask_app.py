from flask import Flask, request, jsonify
import requests
import threading
import time
from datetime import datetime
from typing import List, Dict, Any

app = Flask(__name__)

# Global storage for active tasks (same as FastAPI version)
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

@app.route("/")
def root():
    """Root endpoint with service information"""
    return jsonify({
        "message": "URL Pinger Service",
        "description": "A Flask service to ping URLs at regular intervals",
        "author": "Based on script by jashgro (https://bit.ly/jashgro)",
        "endpoints": {
            "POST /ping": "Start pinging URLs",
            "GET /status": "Get status of all active tasks",
            "DELETE /stop/<task_id>": "Stop a specific ping task",
            "DELETE /stop-all": "Stop all active tasks"
        }
    })

@app.route("/ping", methods=["POST"])
def start_ping():
    """Start pinging the provided URLs at specified intervals"""
    global task_counter
    
    data = request.get_json()
    if not data or 'urls' not in data:
        return jsonify({"error": "URLs are required"}), 400
    
    urls = data['urls']
    interval = data.get('interval', 60)  # Default to 60 seconds
    
    task_counter += 1
    task_id = f"task_{task_counter}"
    
    # Store task information
    active_tasks[task_id] = {
        "urls": urls,
        "interval": interval,
        "active": True,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_results": []
    }
    
    # Start the pinging task in a separate thread
    thread = threading.Thread(
        target=ping_urls_continuously,
        args=(task_id, urls, interval)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "message": f"Started pinging {len(urls)} URLs every {interval} seconds",
        "task_id": task_id,
        "urls": urls,
        "interval": interval
    })

@app.route("/status")
def get_status():
    """Get the status of all active ping tasks"""
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

@app.route("/stop/<task_id>", methods=["DELETE"])
def stop_task(task_id: str):
    """Stop a specific ping task"""
    if task_id not in active_tasks:
        return jsonify({"error": "Task not found"}), 404
    
    active_tasks[task_id]["active"] = False
    
    return jsonify({"message": f"Task {task_id} stopped successfully"})

@app.route("/stop-all", methods=["DELETE"])
def stop_all_tasks():
    """Stop all active ping tasks"""
    stopped_count = 0
    
    for task_id in list(active_tasks.keys()):
        active_tasks[task_id]["active"] = False
        stopped_count += 1
    
    return jsonify({"message": f"Stopped {stopped_count} active tasks"})

@app.route("/ping-once")
def ping_once():
    """Ping a single URL once and return the result"""
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400
    
    result = send_request(url)
    return jsonify(result)

if __name__ == "__main__":
    print("Script made by jashgro (https://bit.ly/jashgro)")
    print("Updates on https://github.com/BlackHatDevX/Render-Pinger")
    print("Flask Version - Starting server...")
    
    app.run(host="0.0.0.0", port=8000, debug=True)