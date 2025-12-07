from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
from game.manager import manager
from core.security import decode_access_token
from core.database import get_db
from auth.service import get_user_by_id
from elo.service import update_elo_ratings
from replay.service import save_replay
import json

router = APIRouter()

async def verify_websocket_token(token: str, db: Session) -> int:
    """Verify JWT token and return user_id."""
    payload = decode_access_token(token)
    if payload is None:
        return None
    
    user_id = int(payload.get("sub"))
    user = get_user_by_id(db, user_id)
    if user is None:
        return None
    
    return user_id

@router.websocket("/ws/game")
async def game_websocket(websocket: WebSocket, token: str = Query(...), matchId: str = Query(...)):
    """WebSocket endpoint for game communication with robust error handling."""
    db = next(get_db())
    user_id = None
    role = None
    connected = False
    
    try:
        # Accept connection first
        await websocket.accept()
        connected = True
        
        # Authenticate
        user_id = await verify_websocket_token(token, db)
        if user_id is None:
            await websocket.send_json({"type": "error", "message": "Invalid token"})
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Verify match exists
        from core.redis_client import get_redis
        from matchmaking.service import get_match_info, decode_redis_value
        
        redis = await get_redis()
        match_data = await get_match_info(matchId)
        
        if not match_data:
            await websocket.send_json({"type": "error", "message": "Match not found"})
            await websocket.close(code=1008, reason="Match not found")
            return
        
        # Get user role
        role = await manager.get_user_role(matchId, user_id)
        if role is None:
            await websocket.send_json({"type": "error", "message": "User not in match"})
            await websocket.close(code=1008, reason="User not in match")
            return
        
        # Mark user as connected
        await redis.set(f"ws_conn:{matchId}:{user_id}", "connected", ex=3600)
        
        # Connect to match
        await manager.connect(websocket, matchId, user_id)
        
        # Get or create game
        game = manager.get_game(matchId)
        
        # Get player IDs from match
        p1_id = int(decode_redis_value(match_data.get("p1")))
        p2_id = int(decode_redis_value(match_data.get("p2")))
        
        # Check if both players are connected
        p1_connected = await redis.get(f"ws_conn:{matchId}:{p1_id}")
        p2_connected = await redis.get(f"ws_conn:{matchId}:{p2_id}")
        both_connected = p1_connected and p2_connected
        
        # Send initial game state
        await manager.send_to_connection(websocket, {
            "type": "start",
            "board": game.board,
            "turn": game.turn,
            "phase": game.phase,
            "role": role,
            "goats_placed": game.goats_placed,
            "goats_captured": game.goats_captured,
            "both_players_connected": both_connected
        })
        
        # If both players are now connected, notify everyone
        if both_connected:
            await manager.broadcast_to_match(matchId, {
                "type": "both_connected",
                "message": "Both players connected. Game can begin!"
            })
        
        # Game loop with message processing
        while True:
            try:
                # Receive message with timeout
                data = await websocket.receive_text()
                message = json.loads(data)
                
                move_type = message.get("type")
                
                # Verify it's the player's turn
                if game.turn != role:
                    await manager.send_to_connection(websocket, {
                        "type": "error",
                        "message": "Not your turn"
                    })
                    continue
                
                success = False
                error_msg = ""
                move_info = {}
                captured_goat = None
                
                # Handle different move types
                if move_type == "place":
                    position = message.get("position")
                    if position is not None:
                        success, error_msg = game.place_goat(position)
                        move_info = {"type": "place", "position": position}
                    else:
                        error_msg = "Position required"
                    
                elif move_type == "move":
                    from_pos = message.get("from")
                    to_pos = message.get("to")
                    
                    if from_pos is not None and to_pos is not None:
                        if role == "tiger":
                            success, error_msg, captured_goat = game.move_tiger(from_pos, to_pos)
                            move_info = {
                                "type": "move",
                                "from": from_pos,
                                "to": to_pos,
                                "captured": captured_goat
                            }
                        elif role == "goat":
                            success, error_msg = game.move_goat(from_pos, to_pos)
                            move_info = {
                                "type": "move",
                                "from": from_pos,
                                "to": to_pos
                            }
                    else:
                        error_msg = "From and to positions required"
                
                if not success:
                    await manager.send_to_connection(websocket, {
                        "type": "error",
                        "message": error_msg
                    })
                    continue
                
                # Save game state to Redis
                await manager.save_game(matchId)
                
                # Check for winner
                winner = game.check_winner()
                
                if winner:
                    reason = "tigers_captured_5_goats" if winner == "tiger" else "tigers_blocked"
                    
                    # Broadcast game over
                    await manager.broadcast_to_match(matchId, {
                        "type": "game_over",
                        "winner": winner,
                        "reason": reason,
                        "final_board": game.board
                    })
                    
                    # Update ELO and save replay
                    p1_id = int(decode_redis_value(match_data.get("p1")))
                    p2_id = int(decode_redis_value(match_data.get("p2")))
                    
                    winner_id = p1_id if winner == "goat" else p2_id
                    loser_id = p2_id if winner == "goat" else p1_id
                    
                    await update_elo_ratings(db, winner_id, loser_id)
                    
                    moves = []  # Track moves in production
                    await save_replay(db, matchId, p1_id, p2_id, winner_id, moves)
                    
                    # Clean up match data
                    from matchmaking.service import cleanup_match
                    await cleanup_match(matchId)
                    
                    break
                else:
                    # Broadcast update
                    await manager.broadcast_to_match(matchId, {
                        "type": "update",
                        "board": game.board,
                        "turn": game.turn,
                        "phase": game.phase,
                        "move": move_info,
                        "goats_placed": game.goats_placed,
                        "goats_captured": game.goats_captured
                    })
            
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await manager.send_to_connection(websocket, {
                    "type": "error",
                    "message": "Invalid JSON"
                })
            except Exception as e:
                print(f"Message processing error: {e}")
                await manager.send_to_connection(websocket, {
                    "type": "error",
                    "message": "Internal server error"
                })
    
    except WebSocketDisconnect:
        # Notify other player about disconnection
        if matchId and role:
            try:
                await manager.broadcast_to_match(matchId, {
                    "type": "player_disconnected",
                    "message": f"{role.capitalize()} player disconnected"
                })
            except:
                pass
    except Exception as e:
        print(f"WebSocket connection error: {e}")
    finally:
        # Clean up on disconnect
        if connected:
            await manager.disconnect(websocket)
        
        if user_id and matchId:
            try:
                redis = await get_redis()
                await redis.delete(f"ws_conn:{matchId}:{user_id}")
                
                # Check if both players have disconnected
                match_data = await get_match_info(matchId)
                if match_data:
                    p1_id = int(decode_redis_value(match_data.get("p1")))
                    p2_id = int(decode_redis_value(match_data.get("p2")))
                    
                    p1_connected = await redis.get(f"ws_conn:{matchId}:{p1_id}")
                    p2_connected = await redis.get(f"ws_conn:{matchId}:{p2_id}")
                    
                    # If both disconnected, clean up the match after a delay
                    if not p1_connected and not p2_connected:
                        # Set expiry for match cleanup (5 minutes)
                        await redis.expire(f"match:{matchId}", 300)
                        await redis.expire(f"game:{matchId}", 300)
            except:
                pass
        
        try:
            db.close()
        except:
            pass
