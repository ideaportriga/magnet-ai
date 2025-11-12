# Logging with Grafana Loki

This guide explains how to set up centralized logging using Grafana Loki for local development.

## Overview

Grafana Loki is a log aggregation system that allows you to:
- Collect structured logs from your application
- Search and filter logs by any field (level, filename, function, etc.)
- View logs in a beautiful web interface
- No changes to application logic required

## Quick Start

### 1. Start Loki and Grafana

```bash
# From project root
docker-compose -f docker-compose-logging.yml up -d
```

This will start:
- **Loki** on port 3100 (log storage)
- **Grafana** on port 3000 (web UI)

### 2. Configure Your Application

Add to your `.env` file:

```bash
# Enable Loki logging
LOKI_URL=http://localhost:3100/loki/api/v1/push
```

### 3. Install Dependencies

```bash
cd api
poetry install
```

### 4. Run Your Application

```bash
# Run your app normally
python run.py
```

All logs will now be sent to Loki automatically!

### 5. View Logs in Grafana

1. Open http://localhost:3000
2. Login with: `admin` / `admin`
3. Go to **Explore** (compass icon in left sidebar)
4. Select **Loki** data source
5. Use **Log browser** to explore your logs

## Grafana Query Examples

### Basic Queries

```logql
# All logs from your application
{application="magnet-ai"}

# Only ERROR level logs
{application="magnet-ai"} |= "level" |= "error"

# Logs from specific file
{application="magnet-ai"} | json | filename="app.py"

# Logs from specific function
{application="magnet-ai"} | json | func_name="get_answer"

# SQL queries
{application="magnet-ai"} |= "SELECT" |= "FROM"

# HTTP requests
{application="magnet-ai"} | json | event="HTTP"
```

### Advanced Filtering

```logql
# Errors in the last 5 minutes
{application="magnet-ai"} 
  | json 
  | level="error" 
  [5m]

# Count errors by file
sum by (filename) (count_over_time({application="magnet-ai"} | json | level="error" [1h]))

# OpenAI API calls
{application="magnet-ai"} | json | logger_name=~"openai.*"
```

## Useful Grafana Features

### 1. **Live Tail**
- Real-time log streaming
- Click "Live" button in top right

### 2. **Log Context**
- Click on any log line
- See surrounding logs
- View full JSON data

### 3. **Time Range**
- Select time range in top right
- Last 5m, 15m, 1h, etc.

### 4. **Labels**
- Automatically extracted from structlog:
  - `level` - log level (debug, info, warning, error)
  - `filename` - source file
  - `func_name` - function name
  - `lineno` - line number
  - `logger` - logger name
  - `event`/`message` - log message

## Stopping Loki

```bash
# Stop but keep data
docker-compose -f docker-compose-logging.yml stop

# Stop and remove (clears logs)
docker-compose -f docker-compose-logging.yml down -v
```

## Troubleshooting

### Logs not appearing?

1. Check Loki is running:
   ```bash
   docker ps | grep loki
   ```

2. Check app can reach Loki:
   ```bash
   curl http://localhost:3100/ready
   ```
   Should return: `ready`

3. Check application logs for errors:
   ```bash
   # Should see logs in console AND sending to Loki
   python run.py
   ```

### Connection refused?

If running app in Docker:
- Use `LOKI_URL=http://host.docker.internal:3100/loki/api/v1/push` (Mac/Windows)
- Or use `LOKI_URL=http://172.17.0.1:3100/loki/api/v1/push` (Linux)

### Want to disable Loki?

Just remove or comment out `LOKI_URL` from `.env`:
```bash
# LOKI_URL=http://localhost:3100/loki/api/v1/push
```

The app will work normally without sending logs to Loki.

## Production Deployment

For production, you might want to:

1. **Secure Grafana**: Change default password
2. **Add authentication**: Configure Loki auth
3. **Set retention**: Configure log retention period
4. **Use external storage**: S3/GCS for long-term storage
5. **Add alerting**: Configure alerts for errors

See [Loki Documentation](https://grafana.com/docs/loki/latest/) for details.

## Benefits

✅ **Zero application changes** - just set environment variable  
✅ **Structured logs** - all fields from structlog available  
✅ **Fast search** - indexed by labels  
✅ **Easy filtering** - by level, file, function, etc.  
✅ **Beautiful UI** - Grafana interface  
✅ **Live tail** - real-time log streaming  
✅ **Separate from app** - doesn't affect app performance  
✅ **Optional** - can disable anytime  
