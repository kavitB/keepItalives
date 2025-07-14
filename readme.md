# FastAPI URL Pinger

A web service that pings URLs at specified intervals to keep them active. Perfect for keeping Render.com or other free hosting services from going to sleep.

## Features

- Web interface for easy management
- REST API endpoints
- Background URL pinging
- Real-time status monitoring
- Multiple URL support
- Configurable ping intervals

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

3. Visit `http://localhost:8000` in your browser

### PythonAnywhere Deployment

1. Upload all files to your PythonAnywhere account
2. Install requirements in the PythonAnywhere console:
```bash
pip3.10 install --user -r requirements.txt
```

3. Configure the Web App:
   - Go to the "Web" tab in your PythonAnywhere dashboard
   - Click "Add a new web app"
   - Choose "Manual configuration" and Python 3.10
   - Set the source code directory to `/home/yourusername/mysite`
   - Set the working directory to `/home/yourusername/mysite`
   - Edit the WSGI file to point to your `wsgi.py`

4. Update `wsgi.py`:
   - Change `yourusername` to your actual PythonAnywhere username
   - Make sure the path points to your project directory

5. Reload your web app

## API Endpoints

### Web Interface
- `GET /` - HTML interface for managing pings

### REST API
- `POST /start-ping` - Start pinging URLs
- `POST /stop-ping` - Stop all ping jobs
- `GET /status` - Get current status of all URLs
- `GET /health` - Health check

## Usage Examples

### Start Pinging (API)
```bash
curl -X POST "http://your-domain.com/start-ping" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example1.com", "https://example2.com"],
    "interval": 60
  }'
```

### Get Status
```bash
curl "http://your-domain.com/status"
```

### Stop Pinging
```bash
curl -X POST "http://your-domain.com/stop-ping"
```

## Default URLs to Ping

Based on your original script, here are the URLs you were pinging:
- https://quikeyfy.onrender.com/
- https://chotu-ly.onrender.com/
- https://upi-payment-gateway-demo.onrender.com/
- https://authsystems.onrender.com/

## Configuration

- **Ping Interval**: Minimum 10 seconds (configurable via API or web interface)
- **Request Timeout**: 10 seconds per request
- **Concurrent Pinging**: All URLs are pinged in sequence

## Logging

The application logs all ping attempts and their results. Check the PythonAnywhere error log for detailed information.

## Error Handling

- Network errors are caught and logged
- Failed requests are retried on the next interval
- Status codes outside 200-299 range are considered failures

## Security Notes

- No authentication is implemented - consider adding it for production use
- URLs are validated using Pydantic's HttpUrl validator
- Request timeouts prevent hanging requests

## Troubleshooting

1. **Import errors**: Make sure all requirements are installed
2. **WSGI errors**: Check that the path in `wsgi.py` is correct
3. **Ping failures**: Check the status endpoint for error details
4. **Memory issues**: Consider reducing ping frequency for many URLs

## Credits

Original script by jashgro (https://bit.ly/jashgro)
Updates on https://github.com/BlackHatDevX/Render-Pinger
