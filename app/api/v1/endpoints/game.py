from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.game.connection_manager import manager
from app.core.security import decode_access_token
from app.db.session import get_db
from app.api.deps import get_current_user_id
from app.schemas.game import AIMoveRequest, AIMoveResponse
from app.services.game.ai_service import hybrid_ai_service
from app.services.auth_service import get_user_by_id
from app.services.elo_service import update_elo_ratings
from app.services.replay_service import save_replay
from app.services.game_log_service import log_game
from app.db.models.user import User
import json

router = APIRouter()


@router.post("/game/ai/move", response_model=AIMoveResponse)
async def get_ai_move(
    payload: AIMoveRequest, _user_id: int = Depends(get_current_user_id)
):
    if len(payload.board) != 25:
        raise HTTPException(status_code=400, detail="Board must have exactly 25 cells")
    if payload.turn not in {"goat", "tiger"}:
        raise HTTPException(status_code=400, detail="Invalid turn value")
    if payload.phase not in {1, 2}:
        raise HTTPException(status_code=400, detail="Invalid phase value")

    move, mode_used, score = hybrid_ai_service.choose_move(
        board=payload.board,
        turn=payload.turn,
        phase=payload.phase,
        goats_placed=payload.goats_placed,
        goats_captured=payload.goats_captured,
        ai_role=payload.ai_role,
        mode=payload.mode,
        top_k=payload.top_k,
    )
    if move is None:
        raise HTTPException(status_code=400, detail="No legal AI move available")

    move_type = move["type"]
    return AIMoveResponse(
        move_type=move_type,
        role=payload.ai_role or payload.turn,
        position=move.get("position"),
        from_pos=move.get("from"),
        to_pos=move.get("to"),
        mode_used=mode_used,
        score=score,
    )


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
async def game_websocket(
    websocket: WebSocket, token: str = Query(...), matchId: str = Query(...)
):
    """WebSocket endpoint for game communication with robust error handling."""
    db = next(get_db())
    user_id = None
    role = None
    connected = False
    game = None

    async def handle_player_forfeit(
        current_match_data, leaving_user_id: int, leaving_role: str, current_game
    ):
        if not current_match_data or leaving_user_id is None or leaving_role is None:
            return

        p1_id = int(decode_redis_value(current_match_data.get("p1")))
        p2_id = int(decode_redis_value(current_match_data.get("p2")))
        opponent_role = "goat" if leaving_role == "tiger" else "tiger"
        winner_id = p2_id if leaving_user_id == p1_id else p1_id
        loser_id = leaving_user_id

        final_board = current_game.board if current_game else []
        goats_captured = current_game.goats_captured if current_game else 0
        total_moves = (
            len(current_game.move_history)
            if current_game and hasattr(current_game, "move_history")
            else 0
        )
        moves_history = (
            {"moves": current_game.move_history}
            if current_game and hasattr(current_game, "move_history")
            else None
        )

        await manager.broadcast_to_match(
            matchId,
            {
                "type": "game_over",
                "winner": opponent_role,
                "reason": "opponent_left",
                "message": f"{leaving_role.capitalize()} player left the game",
                "final_board": final_board,
            },
        )

        tiger_player_id = p2_id
        goat_player_id = p1_id

        tiger = db.query(User).filter(User.id == tiger_player_id).first()
        goat = db.query(User).filter(User.id == goat_player_id).first()
        tiger_elo_before = tiger.elo_rating if tiger else 1200.0
        goat_elo_before = goat.elo_rating if goat else 1200.0

        await update_elo_ratings(db, winner_id, loser_id)

        if tiger:
            db.refresh(tiger)
        if goat:
            db.refresh(goat)
        tiger_elo_after = tiger.elo_rating if tiger else tiger_elo_before
        goat_elo_after = goat.elo_rating if goat else goat_elo_before

        result = "tiger_win" if opponent_role == "tiger" else "goat_win"

        log_game(
            db=db,
            match_id=matchId,
            tiger_player_id=tiger_player_id,
            goat_player_id=goat_player_id,
            winner_id=winner_id,
            result=result,
            goats_captured=goats_captured,
            total_moves=total_moves,
            game_duration_seconds=None,
            tiger_elo_before=tiger_elo_before,
            tiger_elo_after=tiger_elo_after,
            goat_elo_before=goat_elo_before,
            goat_elo_after=goat_elo_after,
            moves_history=moves_history,
        )

        await save_replay(db, matchId, p1_id, p2_id, winner_id, [])
        from app.services.matchmaking_service import cleanup_match

        await cleanup_match(matchId)

    try:
        await websocket.accept()
        connected = True
        user_id = await verify_websocket_token(token, db)
        if user_id is None:
            await websocket.send_json({"type": "error", "message": "Invalid token"})
            await websocket.close(code=1008, reason="Invalid token")
            return
        from app.core.redis import get_redis
        from app.services.matchmaking_service import get_match_info, decode_redis_value

        redis = await get_redis()
        match_data = await get_match_info(matchId)
        if not match_data:
            await websocket.send_json({"type": "error", "message": "Match not found"})
            await websocket.close(code=1008, reason="Match not found")
            return
        role = await manager.get_user_role(matchId, user_id)
        if role is None:
            await websocket.send_json({"type": "error", "message": "User not in match"})
            await websocket.close(code=1008, reason="User not in match")
            return
        await redis.set(f"ws_conn:{matchId}:{user_id}", "connected", ex=3600)
        await manager.connect(websocket, matchId, user_id)
        game = manager.get_game(matchId)
        p1_id = int(decode_redis_value(match_data.get("p1")))
        p2_id = int(decode_redis_value(match_data.get("p2")))
        p1_connected = await redis.get(f"ws_conn:{matchId}:{p1_id}")
        p2_connected = await redis.get(f"ws_conn:{matchId}:{p2_id}")
        both_connected = p1_connected and p2_connected
        p1_user = db.query(User).filter(User.id == p1_id).first()
        p2_user = db.query(User).filter(User.id == p2_id).first()
        opponent_id = p2_id if user_id == p1_id else p1_id
        current_user_db = p1_user if user_id == p1_id else p2_user
        opponent_user_db = p2_user if user_id == p1_id else p1_user
        await manager.send_to_connection(
            websocket,
            {
                "type": "start",
                "match_id": matchId,
                "board": game.board,
                "turn": game.turn,
                "phase": game.phase,
                "role": role,
                "goats_placed": game.goats_placed,
                "goats_captured": game.goats_captured,
                "player": {
                    "id": user_id,
                    "username": current_user_db.username if current_user_db else f"Player {user_id}",
                    "elo_rating": current_user_db.elo_rating if current_user_db else 1200.0,
                },
                "opponent": {
                    "id": opponent_id,
                    "username": opponent_user_db.username if opponent_user_db else f"Player {opponent_id}",
                    "elo_rating": opponent_user_db.elo_rating if opponent_user_db else 1200.0,
                },
                "both_players_connected": both_connected,
            },
        )
        if both_connected:
            await manager.broadcast_to_match(
                matchId,
                {
                    "type": "both_connected",
                    "message": "Both players connected. Game can begin!",
                },
            )
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                move_type = message.get("type")

                await manager.load_game(matchId)
                game = manager.get_game(matchId)

                if move_type == "ping":
                    await manager.send_to_connection(websocket, {"type": "pong"})
                    continue
                if move_type == "leave":
                    await handle_player_forfeit(match_data, user_id, role, game)
                    break
                if game.turn != role:
                    await manager.send_to_connection(
                        websocket, {"type": "error", "message": "Not your turn"}
                    )
                    continue
                success = False
                error_msg = ""
                move_info = {}
                captured_goat = None
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
                            success, error_msg, captured_goat = game.move_tiger(
                                from_pos, to_pos
                            )
                            move_info = {
                                "type": "move",
                                "from": from_pos,
                                "to": to_pos,
                                "captured": captured_goat,
                            }
                        elif role == "goat":
                            success, error_msg = game.move_goat(from_pos, to_pos)
                            move_info = {"type": "move", "from": from_pos, "to": to_pos}
                    else:
                        error_msg = "From and to positions required"
                if not success:
                    await manager.send_to_connection(
                        websocket, {"type": "error", "message": error_msg}
                    )
                    continue
                await manager.save_game(matchId)
                winner = game.check_winner()
                if winner:
                    reason = (
                        "tigers_captured_5_goats"
                        if winner == "tiger"
                        else "tigers_blocked"
                    )
                    await manager.broadcast_to_match(
                        matchId,
                        {
                            "type": "game_over",
                            "winner": winner,
                            "reason": reason,
                            "final_board": game.board,
                        },
                    )
                    p1_id = int(decode_redis_value(match_data.get("p1")))
                    p2_id = int(decode_redis_value(match_data.get("p2")))
                    
                    # Determine tiger and goat players
                    tiger_player_id = p2_id  # p2 is tiger
                    goat_player_id = p1_id   # p1 is goat
                    
                    winner_id = p1_id if winner == "goat" else p2_id
                    loser_id = p2_id if winner == "goat" else p1_id
                    
                    # Get ELO ratings before update
                    tiger = db.query(User).filter(User.id == tiger_player_id).first()
                    goat = db.query(User).filter(User.id == goat_player_id).first()
                    tiger_elo_before = tiger.elo_rating if tiger else 1200.0
                    goat_elo_before = goat.elo_rating if goat else 1200.0
                    
                    # Update ELO ratings
                    elo_result = await update_elo_ratings(db, winner_id, loser_id)
                    
                    # Get ELO ratings after update
                    db.refresh(tiger)
                    db.refresh(goat)
                    tiger_elo_after = tiger.elo_rating
                    goat_elo_after = goat.elo_rating
                    
                    # Determine result string
                    result = "tiger_win" if winner == "tiger" else "goat_win"
                    
                    # Log the game
                    log_game(
                        db=db,
                        match_id=matchId,
                        tiger_player_id=tiger_player_id,
                        goat_player_id=goat_player_id,
                        winner_id=winner_id,
                        result=result,
                        goats_captured=game.goats_captured,
                        total_moves=len(game.move_history) if hasattr(game, 'move_history') else 0,
                        game_duration_seconds=None,  # Can be calculated if needed
                        tiger_elo_before=tiger_elo_before,
                        tiger_elo_after=tiger_elo_after,
                        goat_elo_before=goat_elo_before,
                        goat_elo_after=goat_elo_after,
                        moves_history={"moves": game.move_history} if hasattr(game, 'move_history') else None
                    )
                    
                    moves = []  # Track moves in production
                    await save_replay(db, matchId, p1_id, p2_id, winner_id, moves)
                    from app.services.matchmaking_service import cleanup_match

                    await cleanup_match(matchId)
                    break
                else:
                    await manager.broadcast_to_match(
                        matchId,
                        {
                            "type": "update",
                            "board": game.board,
                            "turn": game.turn,
                            "phase": game.phase,
                            "move": move_info,
                            "goats_placed": game.goats_placed,
                            "goats_captured": game.goats_captured,
                        },
                    )
            except WebSocketDisconnect:
                try:
                    current_match_data = await get_match_info(matchId)
                    if current_match_data and user_id and role:
                        await handle_player_forfeit(
                            current_match_data, user_id, role, manager.get_game(matchId)
                        )
                except Exception:
                    pass
                break
            except json.JSONDecodeError:
                await manager.send_to_connection(
                    websocket, {"type": "error", "message": "Invalid JSON"}
                )
            except Exception as e:
                print(f"Message processing error: {e}")
                await manager.send_to_connection(
                    websocket, {"type": "error", "message": "Internal server error"}
                )
    except WebSocketDisconnect:
        if matchId and role and user_id:
            try:
                current_match_data = await get_match_info(matchId)
                if current_match_data:
                    await handle_player_forfeit(
                        current_match_data, user_id, role, manager.get_game(matchId)
                    )
            except:
                pass
    except Exception as e:
        print(f"WebSocket connection error: {e}")
    finally:
        if connected:
            await manager.disconnect(websocket)
        if user_id and matchId:
            try:
                redis = await get_redis()
                await redis.delete(f"ws_conn:{matchId}:{user_id}")
                match_data = await get_match_info(matchId)
                if match_data:
                    p1_id = int(decode_redis_value(match_data.get("p1")))
                    p2_id = int(decode_redis_value(match_data.get("p2")))
                    p1_connected = await redis.get(f"ws_conn:{matchId}:{p1_id}")
                    p2_connected = await redis.get(f"ws_conn:{matchId}:{p2_id}")
                    if not p1_connected and not p2_connected:
                        await redis.expire(f"match:{matchId}", 300)
                        await redis.expire(f"game:{matchId}", 300)
            except:
                pass
        try:
            db.close()
        except:
            pass
