import json
from typing import Dict, Set
from fastapi import WebSocket
from app.services.game.game_service import BaghChalGame
from app.core.redis import get_redis


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.games: Dict[str, BaghChalGame] = {}
        self.connection_info: Dict[WebSocket, tuple] = {}

    async def connect(self, websocket: WebSocket, match_id: str, user_id: int):
        """Connect a websocket to a match room."""
        if match_id not in self.active_connections:
            self.active_connections[match_id] = set()
        self.active_connections[match_id].add(websocket)
        self.connection_info[websocket] = (match_id, user_id)
        if match_id not in self.games:
            await self.load_game(match_id)

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a websocket."""
        if websocket in self.connection_info:
            match_id, user_id = self.connection_info[websocket]
            if match_id in self.active_connections:
                self.active_connections[match_id].discard(websocket)
                if len(self.active_connections[match_id]) == 0:
                    del self.active_connections[match_id]
                    if match_id in self.games:
                        await self.save_game(match_id)
                        del self.games[match_id]
            del self.connection_info[websocket]

    async def load_game(self, match_id: str):
        """Load game state from Redis or create new game."""
        redis = await get_redis()
        game_data = await redis.hgetall(f"game:{match_id}")
        game = BaghChalGame()
        has_data = game_data and (b"board" in game_data or "board" in game_data)
        if has_data:

            def get_value(key):
                val = game_data.get(
                    key.encode() if isinstance(key, str) else key
                ) or game_data.get(key)
                return val.decode() if isinstance(val, bytes) else val

            goats_placed_data = get_value("goats_placed") or "0"
            if int(goats_placed_data) > 0:
                board_data = get_value("board")
                turn_data = get_value("turn") or "goat"
                goats_captured_data = get_value("goats_captured") or "0"
                phase_data = get_value("phase") or "1"
                history_data = get_value("history") or "[]"
                state = {
                    "board": json.loads(board_data),
                    "turn": turn_data,
                    "goats_placed": int(goats_placed_data),
                    "goats_captured": int(goats_captured_data),
                    "phase": int(phase_data),
                    "history": json.loads(history_data),
                }
                game.from_dict(state)
        self.games[match_id] = game

    async def save_game(self, match_id: str):
        """Save game state to Redis."""
        if match_id not in self.games:
            return
        game = self.games[match_id]
        redis = await get_redis()
        game_state = game.to_dict()
        await redis.hset(
            f"game:{match_id}",
            mapping={
                "board": json.dumps(game_state["board"]),
                "turn": game_state["turn"],
                "goats_placed": game_state["goats_placed"],
                "goats_captured": game_state["goats_captured"],
                "phase": game_state["phase"],
                "history": json.dumps(game_state["history"]),
            },
        )

    async def broadcast_to_match(self, match_id: str, message: dict):
        """Broadcast message to all connections in a match."""
        if match_id in self.active_connections:
            connections = list(self.active_connections[match_id])
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting to connection: {e}")

    async def send_to_connection(self, websocket: WebSocket, message: dict):
        """Send message to specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending to connection: {e}")

    def get_game(self, match_id: str) -> BaghChalGame:
        """Get game instance for a match."""
        return self.games.get(match_id)

    async def get_user_role(self, match_id: str, user_id: int) -> str:
        """Get user role (goat or tiger) in the match."""
        redis = await get_redis()
        match_data = await redis.hgetall(f"match:{match_id}")
        if not match_data:
            return None
        p1 = match_data.get(b"p1") or match_data.get("p1")
        p2 = match_data.get(b"p2") or match_data.get("p2")
        p1 = p1.decode() if isinstance(p1, bytes) else p1
        p2 = p2.decode() if isinstance(p2, bytes) else p2
        if str(user_id) == p1:
            return "goat"
        elif str(user_id) == p2:
            return "tiger"
        return None


manager = ConnectionManager()
