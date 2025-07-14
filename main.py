from flask import Flask, render_template_string, request, jsonify, redirect, url_for, flash
import requests
import time
import threading
from datetime import datetime
from typing import List, Dict, Any
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'simple-pinger-key-change-in-production')

# Global storage for active tasks with a lock for thread safety
active_tasks = {}
task_counter = 0
task_lock = threading.Lock()

# Embedded HTML template since PythonAnywhere might have template issues
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple URL Pinger</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        h1, h2 {
            color: #333;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        textarea, input {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        textarea {
            height: 100px;
            resize: vertical;
        }
        .btn {
            background-color: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin-right: 10px;
        }
        .btn:hover {
            background-color: #0056b3;
        }
        .btn-danger {
            background-color: #dc3545;
        }
        .btn-danger:hover {
            background-color: #c82333;
        }
        .alert {
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .alert-success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .alert-error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .task {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
            border-left: 4px solid #007bff;
        }
        .task-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .task-id {
            font-weight: bold;
            color: #007bff;
        }
        .status {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-active {
            background-color: #28a745;
            color: white;
        }
        .result {
            background-color: white;
            padding: 8px;
            margin: 5px 0;
            border-radius: 4px;
            border-left: 3px solid #28a745;
        }
        .result-failed, .result-warning {
            border-left-color: #dc3545;
        }
        .result-error, .result-connection_error {
            border-left-color: #ffc107;
        }
        .result-timeout {
            border-left-color: #fd7e14;
        }
        .no-tasks {
            text-align: center;
            color: #666;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 Simple URL Pinger</h1>
        
        <!-- Flash Messages -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'success' if category == 'success' else 'error' }}">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <!-- New Task Form -->
        <h2>Start New Ping Task</h2>
        <form method="POST" action="/ping">
            <div class="form-group">
                <label for="urls">URLs (one per line):</label>
                <textarea id="urls" name="urls" placeholder="https://example.com&#10;https://another-site.com" required></textarea>
            </div>
            <div class="form-group">
                <label for="interval">Interval (seconds):</label>
                <input type="number" id="interval" name="interval" value="60" min="10" max="3600" required>
            </div>
            <button type="submit" class="btn">Start Pinging</button>
        </form>
    </div>

    <div class="container">
        <h2>Active Tasks (<span id="task-count">{{ active_tasks|length }}</span>)</h2>
        
        <div id="tasks-container">
            {% if active_tasks %}
                {% for task_id, task in active_tasks.items() %}
                    <div class="task">
                        <div class="task-header">
                            <span class="task-id">{{ task_id }} ({{ task.urls|length }} URLs)</span>
                            <span class="status {{ 'status-active' if task.active }}">
                                {{ 'Active' if task.active else 'Stopped' }}
                            </span>
                        </div>
                        <div><strong>Started:</strong> {{ task.started_at }}</div>
                        <div><strong>Interval:</strong> {{ task.interval }} seconds</div>
                        <div><strong>URLs:</strong> {{ task.urls|join(', ') }}</div>
                        
                        {% if task.results %}
                            <div><strong>Recent Results:</strong></div>
                            {% for result in task.results[-3:] %}
                                <div class="result result-{{ result.status }}">
                                    <strong>{{ result.url }}</strong><br>
                                    {{ result.timestamp }} - {{ result.status.upper() }}
                                    {% if result.status_code %} ({{ result.status_code }}){% endif %}
                                    {% if result.message %} - {{ result.message }}{% endif %}
                                </div>
                            {% endfor %}
                        {% endif %}
                        
                        <div style="margin-top: 10px;">
                            <a href="/stop/{{ task_id }}" class="btn btn-danger">Stop Task</a>
                        </div>
                    </div>
                {% endfor %}
            {% else %}
                <div class="no-tasks">No active tasks</div>
            {% endif %}
        </div>
        
        {% if active_tasks %}
            <a href="/stop-all" class="btn btn-danger">Stop All Tasks</a>
        {% endif %}
    </div>

    <script>
        // Simple auto-refresh functionality
        function updateTasks() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('task-count').textContent = data.active_tasks;
                    
                    // Only update if there are changes to avoid flickering
                    if (data.active_tasks > 0) {
                        setTimeout(() => {
                            window.location.reload();
                        }, 30000); // Refresh every 30 seconds
                    }
                })
                .catch(error => {
                    console.error('Error updating tasks:', error);
                });
        }
        
        // Update every 30 seconds
        setInterval(updateTasks, 30000);
        updateTasks(); // Initial load
    </script>
</body>
</html>
'''

def ping_url(url: str) -> Dict[str, Any]:
    """Simple URL ping function with better error handling"""
    try:
        # Add proper headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Use shorter timeout for PythonAnywhere
        response = requests.get(
            url,
            timeout=10,  # Increased timeout
            headers=headers,
            allow_redirects=True,
            verify=True  # Enable SSL verification
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
    except requests.exceptions.SSLError:
        return {
            "url": url,
            "status": "ssl_error",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": "SSL certificate error"
        }
    except requests.exceptions.ConnectionError:
        return {
            "url": url,
            "status": "connection_error",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": "Connection failed"
        }
    except Exception as e:
        return {
            "url": url,
            "status": "error",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
        }

def ping_task(task_id: str, urls: List[str], interval: int):
    """Background task to ping URLs with proper error handling"""
    try:
        while True:
            with task_lock:
                if task_id not in active_tasks or not active_tasks[task_id]["active"]:
                    break
                task_info = active_tasks[task_id]
            
            # Ping each URL
            for url in urls:
                with task_lock:
                    if task_id not in active_tasks or not active_tasks[task_id]["active"]:
                        break
                
                try:
                    result = ping_url(url)
                    with task_lock:
                        if task_id in active_tasks:
                            task_info["results"].append(result)
                            # Keep only last 10 results
                            if len(task_info["results"]) > 10:
                                task_info["results"].pop(0)
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {url} -> {result['status']}: {result['message']}")
                    
                except Exception as e:
                    print(f"Error pinging {url}: {str(e)}")
                    
                # Small delay between URLs
                time.sleep(1)
            
            # Wait for the interval
            for _ in range(interval):
                with task_lock:
                    if task_id not in active_tasks or not active_tasks[task_id]["active"]:
                        break
                time.sleep(1)
                
    except Exception as e:
        print(f"Task {task_id} error: {str(e)}")
    finally:
        # Clean up
        with task_lock:
            if task_id in active_tasks:
                del active_tasks[task_id]
        print(f"Task {task_id} finished")

@app.route('/')
def index():
    """Main page with embedded template"""
    with task_lock:
        tasks = active_tasks.copy()
    return render_template_string(HTML_TEMPLATE, active_tasks=tasks)

@app.route('/ping', methods=['POST'])
def start_ping():
    """Start pinging URLs"""
    global task_counter
    
    try:
        urls_input = request.form.get('urls', '')
        interval = int(request.form.get('interval', 60))
        
        # Validate interval
        if interval < 10:
            interval = 10
        elif interval > 3600:
            interval = 3600
        
        urls = []
        for url in urls_input.split('\n'):
            url = url.strip()
            if url:
                # Add protocol if missing
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                urls.append(url)
        
        if not urls:
            flash('Please enter at least one URL', 'error')
            return redirect(url_for('index'))
        
        # Limit number of URLs for PythonAnywhere
        if len(urls) > 10:
            flash('Maximum 10 URLs allowed', 'error')
            return redirect(url_for('index'))
        
        with task_lock:
            task_counter += 1
            task_id = f"task_{task_counter}"
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
        
    except Exception as e:
        flash(f'Error starting ping task: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/stop/<task_id>')
def stop_task(task_id: str):
    """Stop a specific task"""
    try:
        with task_lock:
            if task_id in active_tasks:
                active_tasks[task_id]["active"] = False
                flash(f'Stopped {task_id}', 'success')
            else:
                flash(f'Task {task_id} not found', 'error')
    except Exception as e:
        flash(f'Error stopping task: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/stop-all')
def stop_all():
    """Stop all tasks"""
    try:
        with task_lock:
            count = 0
            for task_id in list(active_tasks.keys()):
                active_tasks[task_id]["active"] = False
                count += 1
            flash(f'Stopped {count} tasks', 'success')
    except Exception as e:
        flash(f'Error stopping tasks: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/status')
def get_status():
    """Get status as JSON"""
    try:
        with task_lock:
            tasks_data = []
            for task_id, task_info in active_tasks.items():
                tasks_data.append({
                    "task_id": task_id,
                    "urls": task_info["urls"],
                    "interval": task_info["interval"],
                    "active": task_info["active"],
                    "started_at": task_info["started_at"],
                    "results": task_info["results"][-3:]  # Last 3 results
                })
            
            return jsonify({
                "active_tasks": len(active_tasks),
                "tasks": tasks_data
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# Initialize app
if __name__ == "__main__":
    print("Simple URL Pinger - Starting...")
    print("For PythonAnywhere deployment")
    app.run(debug=False, host="0.0.0.0", port=8000)