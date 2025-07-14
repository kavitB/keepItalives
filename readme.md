# FastAPI URL Pinger

A FastAPI service that pings URLs at regular intervals. This project wraps the original URL pinger script into a modern web API.

## Features

- 🌐 **Web API**: Easy-to-use REST API endpoints
- 📊 **Multiple URLs**: Ping multiple URLs simultaneously
- ⏰ **Configurable Intervals**: Set custom ping intervals
- 📱 **Real-time Status**: Monitor active ping tasks
- 🔧 **Task Management**: Start, stop, and manage ping tasks
- 📚 **Auto Documentation**: Built-in Swagger UI documentation

## Quick Start

### Option 1: Using the Local Runner (Recommended)

1. **Download all files** to a directory
2. **Run the setup script**:
   ```bash
   python run_local.py
   ```

This will automatically install dependencies and start the server.

### Option 2: Manual Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server**:
   ```bash
   python main.py
   ```

### Option 3: Using Poetry (If you have Poetry installed)

1. **Install dependencies**:
   ```bash
   poetry install
   ```

2. **Run the server**:
   ```bash
   poetry run python main.py
   ```

### Option 4: Using Docker

1. **Build the Docker image**:
   ```bash
   docker build -t fastapi-pinger .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 fastapi-pinger
   ```

## Usage

Once the server is running, you can access:

- **API Server**: http://localhost:8000
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

### API Endpoints

#### 1. Start Pinging URLs
```http
POST /ping
```

**Request Body:**
```json
{
  "urls": [
    "https://quikeyfy.onrender.com/",
    "https://chotu-ly.onrender.com/",
    "https://upi-payment-gateway-demo.onrender.com/"
  ],
  "interval": 60
}
```

**Response:**
```json
{
  "message": "Started pinging 3 URLs every 60 seconds",
  "task_id": "task_1",
  "urls": ["https://quikeyfy.onrender.com/", "..."],
  "interval": 60
}
```

#### 2. Get Status of All Tasks
```http
GET /status
```

**Response:**
```json
{
  "active_tasks": 1,
  "tasks": [
    {
      "task_id": "task_1",
      "urls": ["https://quikeyfy.onrender.com/"],
      "interval": 60,
      "active": true,
      "started_at": "2024-01-15 10:30:00",
      "last_results": [...]
    }
  ]
}
```

#### 3. Stop a Specific Task
```http
DELETE /stop/{task_id}
```

#### 4. Stop All Tasks
```http
DELETE /stop-all
```

#### 5. Ping Once
```http
GET /ping-once?url=https://example.com
```

## Example Usage with curl

```bash
# Start pinging URLs
curl -X POST "http://localhost:8000/ping" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://quikeyfy.onrender.com/", "https://chotu-ly.onrender.com/"],
    "interval": 30
  }'

# Check status
curl http://localhost:8000/status

# Stop all tasks
curl -X DELETE http://localhost:8000/stop-all
```

## Configuration

The server runs on `0.0.0.0:8000` by default. You can modify the host and port in the `main.py` file:

```python
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Project Structure

```
fastapi-url-pinger/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── pyproject.toml      # Poetry configuration
├── Dockerfile          # Docker configuration
├── run_local.py        # Local setup script
└── README.md           # This file
```

## Original Script

This project is based on the original URL pinger script by [jashgro](https://bit.ly/jashgro).
Updates and more info: https://github.com/BlackHatDevX/Render-Pinger

## License

This project maintains the same spirit as the original script - free to use and modify.