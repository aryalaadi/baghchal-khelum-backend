# Quick Start Guide

## Prerequisites
- Python 3.12+
- PostgreSQL
- Redis

## Setup Steps

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up PostgreSQL
```bash
# Create database
createdb bagchal

# Or using psql:
psql -U postgres
CREATE DATABASE bagchal;
\q
```

### 3. Start Redis
```bash
# On Windows (if installed via MSI):
redis-server

# On Linux/Mac:
redis-server

# Or using Docker:
docker run -d -p 6379:6379 redis:latest
```

### 4. Configure Environment
The `.env` file is already created with default values. Update if needed:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/bagchal
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
```

### 5. Run Database Migrations
```bash
alembic upgrade head
```

### 6. Start the Server
```bash
# Development mode with auto-reload:
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python directly:
python main.py
```

### 7. Open Test UI
Navigate to:
```
http://localhost:8000/tests/static_test_ui.html
```

## Testing the Application

### Test with 2 Players:
1. Open the test UI in two different browser tabs
2. In Tab 1: Register/login as "player1"
3. In Tab 2: Register/login as "player2"
4. In both tabs: Click "Start Matchmaking"
5. Once matched, click "Connect to Game" in both tabs
6. Player 1 (Goat) starts by placing goats on the board
7. Player 2 (Tiger) moves tigers

### API Testing with curl:

**Register:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'
```

**Start Matchmaking:**
```bash
curl -X POST http://localhost:8000/matchmaking/start \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Troubleshooting

### PostgreSQL Connection Issues
- Check if PostgreSQL is running: `pg_isready`
- Verify credentials in `.env`
- Ensure database exists: `psql -l | grep bagchal`

### Redis Connection Issues
- Check if Redis is running: `redis-cli ping`
- Should return "PONG"

### Import Errors
- Ensure you're in the project root directory
- Verify all `__init__.py` files exist
- Check Python version: `python --version`

## API Documentation

Once running, access interactive API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
