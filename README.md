# BaghChal Multiplayer Backend

A real-time multiplayer backend implementation for the traditional Nepalese board game BaghChal (Tigers and Goats). Built with FastAPI, PostgreSQL, Redis, and WebSocket support.

## 📚 Documentation

**For detailed API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)**

## Features

- Real-time multiplayer gameplay via WebSocket
- ELO rating system for competitive matchmaking
- User authentication and authorization
- **User profiles with comprehensive game statistics**
- **Friend system with challenge functionality**
- **Game history and logs tracking**
- **Top 10 leaderboard with detailed stats**
- Game replay system
- Community features (posts and leaderboard)
- Docker containerization for easy deployment

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache/Queue**: Redis
- **Real-time**: WebSocket
- **Migrations**: Alembic
- **Containerization**: Docker & Docker Compose

## Project Structure

```
bagchal-khelum-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── auth.py
│   │           ├── game.py
│   │           ├── matchmaking.py
│   │           ├── replay.py
│   │           └── community.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── redis.py
│   ├── db/
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── replay.py
│   │   │   └── community.py
│   │   └── session.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── game.py
│   │   └── community.py
│   └── services/
│       ├── auth_service.py
│       ├── elo_service.py
│       ├── matchmaking_service.py
│       ├── replay_service.py
│       └── game/
│           ├── game_service.py
│           ├── manager.py
│           └── connection_manager.py
├── alembic/
├── tests/
│   └── static_test_ui.html
├── docker-compose.yml
├── Dockerfile
├── main.py
└── requirements.txt
```

## Installation

### Using Docker (Recommended)

1. Clone the repository
```bash
git clone <repository-url>
cd bagchal-khelum-backend
```

2. Start the services
```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

### Manual Installation

1. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up PostgreSQL and Redis
- Install PostgreSQL and create a database
- Install Redis

4. Configure environment variables
Create a `.env` file with:
```env
DATABASE_URL=postgresql://user:password@localhost/bagchal
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
```

5. Run database migrations
```bash
alembic upgrade head
```

**Note:** The latest migration (002) adds:
- User game statistics tracking
- Friends relationship table
- Game logs for detailed match history
- Friend challenges system

6. Start the server
```bash
uvicorn main:app --reload
```

## Quick API Overview

For complete API documentation with request/response examples, see **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)**

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get access token

### User Profiles & Stats (NEW)
- `GET /users/all` - Get all users with pagination
- `GET /users/{user_id}` - Get detailed user profile with stats
- `GET /users/{user_id}/stats` - Get user game statistics
- `GET /users/{user_id}/games` - Get user's game history

### Friends & Challenges (NEW)
- `POST /friends/add` - Add a friend
- `DELETE /friends/{friend_id}` - Remove a friend
- `GET /friends/` - Get friends list
- `POST /friends/challenge` - Challenge a friend to a game
- `GET /friends/challenges` - Get pending challenges
- `POST /friends/challenge/respond` - Accept or decline a challenge

### Matchmaking
- `POST /matchmaking/start` - Start matchmaking
- `GET /matchmaking/status` - Check matchmaking status
- `POST /matchmaking/cancel` - Cancel matchmaking

### Game
- `WS /ws/game` - WebSocket connection for real-time gameplay

### Replay
- `GET /replay/{match_id}` - Get game replay data
- `GET /replay/user/{user_id}` - Get user's game history

### Community
- `POST /community/post` - Create a community post
- `GET /community/feed` - Get community feed
- `GET /community/leaderboard` - Get top 10 players with stats (UPDATED)

## Game Rules

BaghChal is a traditional Nepalese board game played on a 5x5 grid.

### Players
- **Goat Player**: Controls 20 goats
- **Tiger Player**: Controls 4 tigers (placed at corners)

### Phases

**Phase 1: Placement**
- Goat player places goats one by one on empty intersections
- Tiger player can move tigers after each goat placement
- Continues until all 20 goats are placed

**Phase 2: Movement**
- Both players can move their pieces to adjacent intersections
- Tigers can capture goats by jumping over them

### Winning Conditions
- **Tigers win**: Capture 5 goats
- **Goats win**: Block all tigers (no legal moves)

## Development

### Running Tests
```bash
pytest
```

### Test UI
Access the test UI at `http://localhost:8000/tests/static_test_ui.html` to test the gameplay and ELO system.

### Database Migrations
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
