from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any
import requests
import time
import asyncio
from datetime import datetime
import threading

app = FastAPI(
    title="URL Pinger Service",
    description="A FastAPI service to ping URLs at regular intervals",
    version="1.0.0"
)

# Pydantic models for request/response
class PingRequest(BaseModel):
    urls: List[HttpUrl]
    interval: int = 60  # Default to 60 seconds

class PingResponse(BaseModel):
    message: str
    task_id: str
    urls: List[str]
    interval: int

class StatusResponse(BaseModel):
    active_tasks: int
    tasks: List[Dict[str, Any]]

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

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "message": "URL Pinger Service",
        "description": "A FastAPI service to ping URLs at regular intervals",
        "author": "Based on script by jashgro (https://bit.ly/jashgro)",
        "endpoints": {
            "POST /ping": "Start pinging URLs",
            "GET /status": "Get status of all active tasks",
            "DELETE /stop/{task_id}": "Stop a specific ping task",
            "DELETE /stop-all": "Stop all active tasks"
        }
    }

@app.post("/ping", response_model=PingResponse)
async def start_ping(request: PingRequest):
    """Start pinging the provided URLs at specified intervals"""
    global task_counter
    
    task_counter += 1
    task_id = f"task_{task_counter}"
    
    # Convert HttpUrl objects to strings
    urls_str = [str(url) for url in request.urls]
    
    # Store task information
    active_tasks[task_id] = {
        "urls": urls_str,
        "interval": request.interval,
        "active": True,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_results": []
    }
    
    # Start the pinging task in a separate thread
    thread = threading.Thread(
        target=ping_urls_continuously,
        args=(task_id, urls_str, request.interval)
    )
    thread.daemon = True
    thread.start()
    
    return PingResponse(
        message=f"Started pinging {len(urls_str)} URLs every {request.interval} seconds",
        task_id=task_id,
        urls=urls_str,
        interval=request.interval
    )

@app.get("/status", response_model=StatusResponse)
async def get_status():
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
    
    return StatusResponse(
        active_tasks=len(active_tasks),
        tasks=tasks_info
    )

@app.delete("/stop/{task_id}")
async def stop_task(task_id: str):
    """Stop a specific ping task"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    active_tasks[task_id]["active"] = False
    
    return {"message": f"Task {task_id} stopped successfully"}

@app.delete("/stop-all")
async def stop_all_tasks():
    """Stop all active ping tasks"""
    stopped_count = 0
    
    for task_id in list(active_tasks.keys()):
        active_tasks[task_id]["active"] = False
        stopped_count += 1
    
    return {"message": f"Stopped {stopped_count} active tasks"}

@app.get("/ping-once")
async def ping_once(url: HttpUrl):
    """Ping a single URL once and return the result"""
    result = send_request(str(url))
    return result

if __name__ == "__main__":
    import uvicorn
    print("Script made by jashgro (https://bit.ly/jashgro)")
    print("Updates on https://github.com/BlackHatDevX/Render-Pinger")
    print("FastAPI Version - Starting server...")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)