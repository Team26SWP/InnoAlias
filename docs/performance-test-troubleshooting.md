# Performance Test Troubleshooting Guide

This guide helps resolve common issues when running the InnoAlias performance tests.

## Common Issues and Solutions

### 1. Connection Refused (Cannot connect to host)

**Error**: `Cannot connect to host localhost:80 ssl:default [Multiple exceptions: [Errno 111] Connect call failed]`

**Solution**: The backend server is not running. Start it with:
```bash
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. HTTP 400 Bad Request on Authentication

**Error**: `Authentication failed: HTTP 400`

**Solution**: The login endpoint expects form-encoded data, not JSON. The performance test has been updated to handle this correctly. If you're still getting this error, ensure you're using the latest version of the test script.

### 3. MongoDB Connection Issues

**Error**: `motor.errors.ServerSelectionTimeoutError`

**Solution**: MongoDB is not running. Start it with:
```bash
sudo systemctl start mongodb
```

### 4. Missing Dependencies

**Error**: `ModuleNotFoundError: No module named 'aiohttp'`

**Solution**: Install the required dependency:
```bash
pip install aiohttp
```

### 5. Permission Denied for MongoDB

**Error**: `Failed to start mongod.service: Unit mongod.service not found`

**Solution**: The MongoDB service name might be different. Try:
```bash
# Check available MongoDB services
systemctl list-units --type=service | grep -i mongo

# Start the correct service (common names: mongod, mongodb, mongo)
sudo systemctl start mongodb  # or mongod
```

### 6. Port Already in Use

**Error**: `OSError: [Errno 98] Address already in use`

**Solution**: Another process is using port 8000. Either:
- Stop the existing process: `pkill -f uvicorn`
- Use a different port: `python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8001`

### 7. Environment Variables Missing

**Error**: `decouple.UndefinedValueError: SECRET_KEY not found.`

**Solution**: Ensure the `.env` file exists and contains required variables:
```bash
# Check if .env exists
ls -la .env

# Create .env from example if needed
cp .env.example .env
```

## Quick Diagnostic Commands

```bash
# Check if MongoDB is running
systemctl status mongodb

# Check if backend server is responding
curl -s http://localhost:8000/docs

# Check if dependencies are installed
python -c "import aiohttp; print('aiohttp OK')"

# Check environment variables
cat .env
```

## Using the Automated Script

The easiest way to run performance tests is using the automated script:

```bash
# Run with default settings
./run_performance_test.sh

# Run with custom parameters
./run_performance_test.sh http://localhost:8000 5
```

The script will automatically:
- Check and start MongoDB if needed
- Install missing dependencies
- Start the backend server if not running
- Run the performance test
- Provide cleanup instructions

## Expected Performance Results

When everything is working correctly, you should see results like:

```
AUTHENTICATION:
  Total Tests: 10
  Successful: 10
  Success Rate: 100.0%
  Avg Duration: ~209ms

GAME_CREATION:
  Total Tests: 10
  Successful: 10
  Success Rate: 100.0%
  Avg Duration: ~2.2ms

LEADERBOARD:
  Total Tests: 10
  Successful: 10
  Success Rate: 100.0%
  Avg Duration: ~0.9ms
```

## Getting Help

If you're still experiencing issues:

1. Check the server logs for detailed error messages
2. Ensure all prerequisites are met (MongoDB, dependencies, environment)
3. Try running the automated script which handles most common issues
4. Check the main README.md for updated instructions 