# BaghChal Multiplayer Backend

A complete production-quality multiplayer BaghChal game backend built with FastAPI, WebSockets, Redis, and PostgreSQL.

## 🎯 Features

- **JWT Authentication**: Secure user registration and login
- **Real-time Gameplay**: WebSocket-based multiplayer game rooms
- **Matchmaking System**: Redis-powered queue-based matchmaking
- **ELO Rating System**: K=32 factor ELO ratings for competitive play
- **Complete Game Logic**: Full BaghChal rules implementation with all win conditions
- **Game Replays**: Store and retrieve game history
- **Community Features**: Social posts and feed
- **Test UI**: Complete HTML test interface for development

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.12)
- **WebSockets**: FastAPI WebSocket endpoints
- **Game State**: Redis (in-memory state management)
- **Database**: PostgreSQL + SQLAlchemy + Alembic
- **Authentication**: JWT Bearer tokens
- **ELO System**: Standard 32-K factor algorithm

## 📦 Installation

1. **Clone the repository**
```bash
cd bagchal-khelum-backend
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your database and Redis credentials
```

4. **Start PostgreSQL and Redis**
```bash
# Make sure PostgreSQL is running on localhost:5432
# Make sure Redis is running on localhost:6379
```

5. **Run database migrations**
```bash
alembic upgrade head
```

6. **Start the server**
```bash
python main.py
# Or use uvicorn:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🎮 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user

### Matchmaking
- `POST /matchmaking/start` - Start matchmaking
- `POST /matchmaking/cancel` - Cancel matchmaking

### Game
- `WS /ws/game?token=<JWT>&matchId=<ID>` - WebSocket game connection

### Replay
- `GET /replay/{game_id}` - Get game replay
- `GET /replay/user/{user_id}` - Get user's replays

### Community
- `POST /community/post` - Create post
- `GET /community/feed` - Get community feed

## 🧪 Testing

Open the test UI in your browser:
```
http://localhost:8000/tests/static_test_ui.html
```

### Test Flow:
1. Register or login with a username/password
2. Click "Start Matchmaking" (open in 2 browser tabs for two players)
3. Once matched, click "Connect to Game"
4. Play by clicking on the board cells
5. Watch the game state update in real-time

## 🎲 Game Rules

### BaghChal (Tigers and Goats)

**Objective:**
- **Tigers**: Capture 5 goats to win
- **Goats**: Block all tigers from moving to win

**Gameplay:**
- **Phase 1**: Goats place pieces on empty points (20 goats total)
- **Phase 2**: After all goats placed, goats can move
- Tigers can move to adjacent points or capture by jumping over goats
- Goats can only move to adjacent points (cannot capture)
- Anti-repetition rule: No repeating board states in Phase 2

### Board Layout
```
 0  -  1  -  2  -  3  -  4
 |  \\ | / \\ | / \\ | /  |
 5  -  6  -  7  -  8  -  9
 |  / | \\ / | \\ / | \\  |
10 - 11 - 12 - 13 - 14
 |  \\ | / \\ | / \\ | /  |
15 - 16 - 17 - 18 - 19
 |  / | \\ / | \\ / | \\  |
20 - 21 - 22 - 23 - 24
```

Initial tiger positions: 0, 4, 20, 24

## 🔧 Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── core/
│   ├── config.py          # Configuration settings
│   ├── security.py        # JWT and password hashing
│   ├── database.py        # Database connection
│   └── redis_client.py    # Redis connection
├── auth/
│   ├── router.py          # Auth endpoints
│   ├── models.py          # User model
│   ├── schemas.py         # Pydantic schemas
│   └── service.py         # Auth business logic
├── matchmaking/
│   ├── router.py          # Matchmaking endpoints
│   └── service.py         # Queue management
├── game/
│   ├── router_ws.py       # WebSocket endpoint
│   ├── logic.py           # Complete game rules
│   ├── manager.py         # WebSocket connection manager
│   └── schemas.py         # Game message schemas
├── elo/
│   └── service.py         # ELO rating calculations
├── replay/
│   ├── router.py          # Replay endpoints
│   ├── models.py          # Replay model
│   └── service.py         # Replay storage
├── community/
│   ├── router.py          # Community endpoints
│   ├── models.py          # Post model
│   └── schemas.py         # Post schemas
├── alembic/                # Database migrations
└── tests/
    └── static_test_ui.html # Test interface
```

## 🔒 Security

- Passwords hashed with bcrypt
- JWT tokens with configurable expiration
- WebSocket authentication via query parameter tokens
- CORS enabled for development (configure for production)

## 📊 Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `hashed_password`: Bcrypt hashed password
- `elo_rating`: Float (default 1200.0)
- `created_at`: Timestamp

### Replays Table
- `id`: Primary key
- `game_id`: Unique game identifier
- `player1_id`, `player2_id`: Player IDs
- `winner_id`: Winner's user ID
- `moves`: JSON array of moves
- `created_at`: Timestamp

### Posts Table
- `id`: Primary key
- `user_id`: Author ID
- `title`, `content`: Post data
- `created_at`: Timestamp

## 🚀 Production Deployment

1. Update `.env` with production credentials
2. Set strong `SECRET_KEY`
3. Configure CORS for your frontend domain
4. Use a production WSGI server (e.g., Gunicorn)
5. Set up PostgreSQL and Redis with authentication
6. Enable SSL/TLS for WebSocket connections
7. Implement rate limiting and request validation

## 📝 WebSocket Protocol

### Client → Server

**Place Goat (Phase 1):**
```json
{
  "type": "place",
  "position": 12
}
```

**Move Piece:**
```json
{
  "type": "move",
  "from": 3,
  "to": 8
}
```

### Server → Client

**Game Start:**
```json
{
  "type": "start",
  "board": [2,0,0,0,2,...],
  "turn": "goat",
  "phase": 1,
  "role": "goat",
  "goats_placed": 0,
  "goats_captured": 0
}
```

**Board Update:**
```json
{
  "type": "update",
  "board": [...],
  "turn": "tiger",
  "phase": 1,
  "move": {...},
  "goats_placed": 5,
  "goats_captured": 0
}
```

**Game Over:**
```json
{
  "type": "game_over",
  "winner": "tiger",
  "reason": "tigers_captured_5_goats",
  "final_board": [...]
}
```

**Error:**
```json
{
  "type": "error",
  "message": "Illegal move"
}
```

## 🐛 Troubleshooting

**Cannot connect to PostgreSQL:**
- Ensure PostgreSQL is running
- Check credentials in `.env`
- Create database: `createdb bagchal`

**Cannot connect to Redis:**
- Ensure Redis is running: `redis-server`
- Check Redis URL in `.env`

**WebSocket connection fails:**
- Check that token is valid
- Ensure matchId exists
- Check CORS settings

## 📄 License

MIT License - See LICENSE file for details

## 👥 Contributing

Contributions welcome! Please open an issue or submit a pull request.
