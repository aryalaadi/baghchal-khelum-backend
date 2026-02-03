# Bagchal Khelum Backend - API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## Authentication Endpoints

### Register
**POST** `/auth/register`

Create a new user account.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "token": "string",
  "userId": 1
}
```

### Login
**POST** `/auth/login`

Login to an existing account.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "token": "string",
  "userId": 1
}
```

---

## User Profile Endpoints

### Get All Users
**GET** `/users/all`

Get a list of all users with pagination.

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records (default: 50, max: 100)

**Response:**
```json
[
  {
    "id": 1,
    "username": "player1",
    "elo_rating": 1250.5
  }
]
```

### Get User Profile
**GET** `/users/{user_id}`

Get detailed profile information for a specific user.

**Response:**
```json
{
  "id": 1,
  "username": "player1",
  "elo_rating": 1250.5,
  "created_at": "2026-01-26T10:00:00Z",
  "stats": {
    "games_played": 50,
    "games_won": 30,
    "games_lost": 15,
    "games_drawn": 5,
    "goats_captured_total": 120,
    "win_rate": 60.0
  }
}
```

### Get User Stats
**GET** `/users/{user_id}/stats`

Get game statistics for a specific user.

**Response:**
```json
{
  "games_played": 50,
  "games_won": 30,
  "games_lost": 15,
  "games_drawn": 5,
  "goats_captured_total": 120,
  "win_rate": 60.0
}
```

### Get User Game History
**GET** `/users/{user_id}/games`

Get game log history for a specific user.

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records (default: 20, max: 50)

**Response:**
```json
[
  {
    "id": 1,
    "match_id": "uuid-string",
    "tiger_player_id": 1,
    "goat_player_id": 2,
    "winner_id": 1,
    "result": "tiger_win",
    "goats_captured": 5,
    "total_moves": 45,
    "game_duration_seconds": 1800,
    "tiger_elo_before": 1200.0,
    "tiger_elo_after": 1215.5,
    "goat_elo_before": 1180.0,
    "goat_elo_after": 1164.5,
    "created_at": "2026-01-26T10:00:00Z"
  }
]
```

---

## Friend Management Endpoints

### Add Friend
**POST** `/friends/add` 🔒

Add a user as a friend.

**Request Body:**
```json
{
  "friend_id": 2
}
```

**Response:**
```json
{
  "message": "Friend added successfully"
}
```

### Remove Friend
**DELETE** `/friends/{friend_id}` 🔒

Remove a friend from your friend list.

**Response:**
```json
{
  "message": "Friend removed successfully"
}
```

### Get Friends List
**GET** `/friends/` 🔒

Get list of all your friends.

**Response:**
```json
[
  {
    "id": 2,
    "username": "friend1",
    "elo_rating": 1180.0
  }
]
```

---

## Friend Challenge Endpoints

### Create Challenge
**POST** `/friends/challenge` 🔒

Challenge a friend to a game.

**Request Body:**
```json
{
  "friend_id": 2
}
```

**Response:**
```json
{
  "id": 1,
  "challenger_id": 1,
  "challenged_id": 2,
  "status": "pending",
  "match_id": null,
  "created_at": "2026-01-26T10:00:00Z"
}
```

### Get Challenges
**GET** `/friends/challenges` 🔒

Get all pending challenges (both sent and received).

**Response:**
```json
[
  {
    "id": 1,
    "challenger_id": 1,
    "challenged_id": 2,
    "status": "pending",
    "match_id": null,
    "created_at": "2026-01-26T10:00:00Z"
  }
]
```

### Respond to Challenge
**POST** `/friends/challenge/respond` 🔒

Accept or decline a challenge.

**Request Body:**
```json
{
  "challenge_id": 1,
  "action": "accept"
}
```

**Response (Accept):**
```json
{
  "message": "Challenge accepted",
  "match_id": "uuid-string",
  "action": "accepted"
}
```

**Response (Decline):**
```json
{
  "message": "Challenge declined",
  "action": "declined"
}
```

---

## Leaderboard Endpoint

### Get Leaderboard
**GET** `/community/leaderboard`

Get top 10 players ranked by ELO rating.

**Response:**
```json
{
  "users": [
    {
      "rank": 1,
      "id": 5,
      "user_id": 5,
      "username": "champion",
      "elo": 1450.5,
      "rating": 1450.5,
      "games_played": 100,
      "games_won": 75,
      "win_rate": 75.0
    }
  ]
}
```

---

## Matchmaking Endpoints

### Create Match
**POST** `/matchmaking/create` 🔒

Create a new matchmaking request.

**Response:**
```json
{
  "matchId": "uuid-string"
}
```

### Get Match
**GET** `/matchmaking/match/{match_id}` 🔒

Get match information.

**Response:**
```json
{
  "matchId": "uuid-string",
  "p1": 1,
  "p2": 2,
  "status": "active"
}
```

### Cancel Match
**POST** `/matchmaking/cancel` 🔒

Cancel an active matchmaking request.

**Response:**
```json
{
  "message": "Match cancelled successfully"
}
```

---

## Game WebSocket Endpoint

### Game WebSocket
**WebSocket** `/ws/game?token={jwt_token}&matchId={match_id}`

Real-time game communication via WebSocket.

**Connection Parameters:**
- `token`: JWT authentication token
- `matchId`: Match ID from matchmaking

**Message Types:**
- `start`: Game initialization
- `place`: Place a goat piece
- `move`: Move a piece
- `both_connected`: Both players connected
- `update`: Game state update
- `error`: Error message
- `game_over`: Game ended

---

## Replay Endpoints

### Get Replays
**GET** `/replay/list` 🔒

Get list of saved game replays.

**Response:**
```json
[
  {
    "id": 1,
    "match_id": "uuid-string",
    "game_data": {},
    "created_at": "2026-01-26T10:00:00Z"
  }
]
```

### Get Replay
**GET** `/replay/{replay_id}` 🔒

Get a specific replay by ID.

---

## Community Endpoints

### Get Posts
**GET** `/community/posts`

Get community posts.

### Create Post
**POST** `/community/posts` 🔒

Create a new community post.

---

## Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or invalid
- `403 Forbidden`: Not authorized to perform action
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Notes

🔒 = Requires authentication

All timestamps are in ISO 8601 format (UTC).

ELO ratings start at 1200.0 for new players.

Challenge status can be: `pending`, `accepted`, `declined`, or `expired`.

Game results can be: `tiger_win`, `goat_win`, or `draw`.
