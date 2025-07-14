from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import requests
import asyncio
import time
import logging
from datetime import datetime
import threading
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="URL Pinger Service", version="1.0.0")

# Data models
class PingRequest(BaseModel):
    urls: List[HttpUrl]
    interval: int = 60  # seconds

class PingStatus(BaseModel):
    url: str
    last_ping: Optional[str] = None
    status: str = "Not started"
    status_code: Optional[int] = None
    error: Optional[str] = None

@dataclass
class PingJob:
    urls: List[str]
    interval: int
    active: bool = True
    thread: Optional[threading.Thread] = None

# Global storage for ping jobs
ping_jobs = {}
ping_statuses = {}

def send_request(url: str) -> tuple[bool, int, str]:
    """Send a request to the URL and return success status, status code, and error message."""
    try:
        response = requests.get(url, timeout=10)
        success = 200 <= response.status_code < 300
        return success, response.status_code, None
    except requests.RequestException as e:
        logger.error(f"Error pinging {url}: {e}")
        return False, 0, str(e)

def ping_worker(job_id: str, urls: List[str], interval: int):
    """Background worker that pings URLs at specified intervals."""
    logger.info(f"Starting ping worker for job {job_id}")
    
    while job_id in ping_jobs and ping_jobs[job_id].active:
        for url in urls:
            if job_id not in ping_jobs or not ping_jobs[job_id].active:
                break
                
            success, status_code, error = send_request(url)
            
            # Update status
            ping_statuses[url] = PingStatus(
                url=url,
                last_ping=datetime.now().strftime("%H:%M:%S"),
                status="Success" if success else "Failed",
                status_code=status_code if status_code > 0 else None,
                error=error
            )
            
            if success:
                logger.info(f"Pinged {url} at {time.strftime('%H:%M:%S')}")
            else:
                logger.error(f"Failed to ping {url}. Status code: {status_code}, Error: {error}")
        
        # Wait for the specified interval
        time.sleep(interval)
    
    logger.info(f"Ping worker for job {job_id} stopped")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with HTML interface."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>URL Pinger Service</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea { width: 100%; padding: 8px; margin-bottom: 10px; }
            button { padding: 10px 20px; background-color: #007bff; color: white; border: none; cursor: pointer; }
            button:hover { background-color: #0056b3; }
            .status { margin-top: 30px; }
            .success { color: green; }
            .error { color: red; }
            .info { color: blue; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>URL Pinger Service</h1>
            <p>This service pings URLs at specified intervals to keep them active.</p>
            
            <div class="form-group">
                <label for="urls">URLs (one per line):</label>
                <textarea id="urls" rows="5" placeholder="https://example1.com&#10;https://example2.com"></textarea>
            </div>
            
            <div class="form-group">
                <label for="interval">Ping Interval (seconds):</label>
                <input type="number" id="interval" value="60" min="10">
            </div>
            
            <button onclick="startPinging()">Start Pinging</button>
            <button onclick="stopPinging()">Stop Pinging</button>
            <button onclick="getStatus()">Get Status</button>
            
            <div id="result" class="status"></div>
        </div>
        
        <script>
            async function startPinging() {
                const urls = document.getElementById('urls').value.split('\\n').filter(url => url.trim());
                const interval = parseInt(document.getElementById('interval').value);
                
                if (urls.length === 0) {
                    alert('Please enter at least one URL');
                    return;
                }
                
                try {
                    const response = await fetch('/start-ping', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ urls, interval })
                    });
                    
                    const result = await response.json();
                    document.getElementById('result').innerHTML = 
                        `<div class="success">Started pinging job: ${result.job_id}</div>`;
                } catch (error) {
                    document.getElementById('result').innerHTML = 
                        `<div class="error">Error: ${error.message}</div>`;
                }
            }
            
            async function stopPinging() {
                try {
                    const response = await fetch('/stop-ping', { method: 'POST' });
                    const result = await response.json();
                    document.getElementById('result').innerHTML = 
                        `<div class="info">${result.message}</div>`;
                } catch (error) {
                    document.getElementById('result').innerHTML = 
                        `<div class="error">Error: ${error.message}</div>`;
                }
            }
            
            async function getStatus() {
                try {
                    const response = await fetch('/status');
                    const result = await response.json();
                    
                    let html = '<h3>Current Status:</h3>';
                    if (result.length === 0) {
                        html += '<p>No URLs are being pinged currently.</p>';
                    } else {
                        html += '<table border="1" style="width:100%; border-collapse: collapse;">';
                        html += '<tr><th>URL</th><th>Last Ping</th><th>Status</th><th>Status Code</th><th>Error</th></tr>';
                        result.forEach(status => {
                            html += `<tr>
                                <td>${status.url}</td>
                                <td>${status.last_ping || 'Never'}</td>
                                <td class="${status.status === 'Success' ? 'success' : 'error'}">${status.status}</td>
                                <td>${status.status_code || 'N/A'}</td>
                                <td>${status.error || 'None'}</td>
                            </tr>`;
                        });
                        html += '</table>';
                    }
                    
                    document.getElementById('result').innerHTML = html;
                } catch (error) {
                    document.getElementById('result').innerHTML = 
                        `<div class="error">Error: ${error.message}</div>`;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/start-ping")
async def start_ping(request: PingRequest):
    """Start pinging the specified URLs."""
    # Stop any existing ping job
    await stop_ping()
    
    # Convert URLs to strings
    urls = [str(url) for url in request.urls]
    
    # Create new job
    job_id = f"ping_job_{int(time.time())}"
    
    # Initialize statuses
    for url in urls:
        ping_statuses[url] = PingStatus(url=url, status="Starting...")
    
    # Create and start the ping job
    job = PingJob(urls=urls, interval=request.interval, active=True)
    job.thread = threading.Thread(target=ping_worker, args=(job_id, urls, request.interval))
    job.thread.daemon = True
    job.thread.start()
    
    ping_jobs[job_id] = job
    
    logger.info(f"Started ping job {job_id} for {len(urls)} URLs with {request.interval}s interval")
    
    return {"message": "Ping job started", "job_id": job_id, "urls": urls, "interval": request.interval}

@app.post("/stop-ping")
async def stop_ping():
    """Stop all active ping jobs."""
    stopped_jobs = []
    
    for job_id, job in list(ping_jobs.items()):
        job.active = False
        stopped_jobs.append(job_id)
        del ping_jobs[job_id]
    
    # Clear statuses
    ping_statuses.clear()
    
    logger.info(f"Stopped {len(stopped_jobs)} ping jobs")
    
    return {"message": f"Stopped {len(stopped_jobs)} ping jobs", "stopped_jobs": stopped_jobs}

@app.get("/status")
async def get_status():
    """Get the current status of all pinged URLs."""
    return list(ping_statuses.values())

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "active_jobs": len(ping_jobs)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
