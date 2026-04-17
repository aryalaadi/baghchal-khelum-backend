from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from app.services.game.game_service import ADJACENCY, EMPTY, GOAT, TIGER

try:
    import torch
except Exception:
    torch = None


MODEL_WEIGHTS_PATH = Path(__file__).resolve().parents[3] / "artifacts_model" / "weights.pth"


@dataclass
class AIState:
    board: List[int]
    turn: str
    phase: int
    goats_placed: int
    goats_captured: int


class HybridAIService:
    def __init__(self):
        self.device = "cpu"
        self.model = None
        self.model_loaded = False
        self.model_load_error = None
        self._load_model_if_configured()

    def _load_model_if_configured(self):
        model_path = str(MODEL_WEIGHTS_PATH)
        if torch is None:
            self.model_load_error = "PyTorch not available"
            return
        if not MODEL_WEIGHTS_PATH.exists():
            self.model_load_error = f"Model file not found: {model_path}"
            return

        try:
            loaded = torch.jit.load(model_path, map_location=self.device)
            loaded.eval()
            self.model = loaded
            self.model_loaded = True
        except Exception as exc:
            self.model_load_error = str(exc)

    def _is_in_line(self, pos1: int, pos2: int, pos3: int) -> bool:
        row1, col1 = pos1 // 5, pos1 % 5
        row2, col2 = pos2 // 5, pos2 % 5
        row3, col3 = pos3 // 5, pos3 % 5

        if row1 == row2 == row3:
            return min(col1, col3) <= col2 <= max(col1, col3)
        if col1 == col2 == col3:
            return min(row1, row3) <= row2 <= max(row1, row3)
        if abs(row1 - row2) == abs(col1 - col2) and abs(row2 - row3) == abs(col2 - col3):
            return (row2 - row1) * (col3 - col1) == (row3 - row1) * (col2 - col1)
        return False

    def _tiger_capture_goat(self, board: List[int], from_pos: int, to_pos: int) -> Optional[int]:
        if board[from_pos] != TIGER or board[to_pos] != EMPTY:
            return None
        for adj in ADJACENCY.get(from_pos, []):
            if board[adj] != GOAT:
                continue
            if to_pos in ADJACENCY.get(adj, []) and self._is_in_line(from_pos, adj, to_pos):
                return adj
        return None

    def _tiger_legal_moves_from_board(self, board: List[int], tiger_pos: int) -> List[int]:
        if board[tiger_pos] != TIGER:
            return []

        legal_moves: List[int] = []
        for adj in ADJACENCY.get(tiger_pos, []):
            if board[adj] == EMPTY:
                legal_moves.append(adj)

        for to_pos in range(25):
            if board[to_pos] != EMPTY or to_pos == tiger_pos:
                continue
            captured = self._tiger_capture_goat(board, tiger_pos, to_pos)
            if captured is not None:
                legal_moves.append(to_pos)

        return legal_moves

    def _legal_moves(self, state: AIState, role: str) -> List[Dict]:
        board = state.board
        moves: List[Dict] = []

        if role == "goat" and state.phase == 1:
            for position in range(25):
                if board[position] == EMPTY:
                    moves.append({"type": "place", "position": position})
            return moves

        for from_pos in range(25):
            if role == "goat" and board[from_pos] != GOAT:
                continue
            if role == "tiger" and board[from_pos] != TIGER:
                continue

            for to_pos in ADJACENCY.get(from_pos, []):
                if board[to_pos] == EMPTY:
                    moves.append({"type": "move", "from": from_pos, "to": to_pos})

            if role == "tiger":
                for to_pos in range(25):
                    if to_pos == from_pos or board[to_pos] != EMPTY:
                        continue
                    captured = self._tiger_capture_goat(board, from_pos, to_pos)
                    if captured is not None:
                        moves.append(
                            {
                                "type": "move",
                                "from": from_pos,
                                "to": to_pos,
                                "captured": captured,
                            }
                        )
        return moves

    def _apply_move(self, state: AIState, move: Dict, role: str) -> AIState:
        board = list(state.board)
        goats_placed = state.goats_placed
        goats_captured = state.goats_captured
        phase = state.phase

        if move["type"] == "place":
            position = int(move["position"])
            board[position] = GOAT
            goats_placed += 1
            if goats_placed >= 20:
                phase = 2
        else:
            from_pos = int(move["from"])
            to_pos = int(move["to"])
            piece = GOAT if role == "goat" else TIGER
            board[from_pos] = EMPTY
            board[to_pos] = piece
            if role == "tiger":
                captured = move.get("captured")
                if captured is None:
                    captured = self._tiger_capture_goat(state.board, from_pos, to_pos)
                if captured is not None:
                    board[int(captured)] = EMPTY
                    goats_captured += 1

        next_turn = "goat" if role == "tiger" else "tiger"
        return AIState(
            board=board,
            turn=next_turn,
            phase=phase,
            goats_placed=goats_placed,
            goats_captured=goats_captured,
        )

    def _winner(self, state: AIState) -> Optional[str]:
        if state.goats_captured >= 5:
            return "tiger"
        if state.phase == 2:
            tiger_has_moves = any(
                len(self._tiger_legal_moves_from_board(state.board, i)) > 0
                for i, piece in enumerate(state.board)
                if piece == TIGER
            )
            if not tiger_has_moves:
                return "goat"
        return None

    def _count_mobility(self, board: List[int], role: str) -> int:
        mobility = 0
        for position in range(25):
            piece = board[position]
            if role == "goat" and piece != GOAT:
                continue
            if role == "tiger" and piece != TIGER:
                continue
            if role == "goat":
                mobility += sum(1 for nxt in ADJACENCY.get(position, []) if board[nxt] == EMPTY)
            else:
                mobility += len(self._tiger_legal_moves_from_board(board, position))
        return mobility

    def _heuristic_value(self, state: AIState, perspective_role: str) -> float:
        winner = self._winner(state)
        if winner == perspective_role:
            return 10000.0
        if winner is not None and winner != perspective_role:
            return -10000.0

        tiger_mobility = self._count_mobility(state.board, "tiger")
        goat_mobility = self._count_mobility(state.board, "goat")
        tiger_positions = [i for i, piece in enumerate(state.board) if piece == TIGER]
        trapped_tigers = sum(
            1 for pos in tiger_positions if len(self._tiger_legal_moves_from_board(state.board, pos)) == 0
        )

        center_bonus = 0.0
        for pos in tiger_positions:
            row, col = divmod(pos, 5)
            center_bonus += 4.0 - abs(row - 2) - abs(col - 2)

        tiger_score = (
            state.goats_captured * 50.0
            + tiger_mobility * 2.0
            - goat_mobility * 0.5
            - trapped_tigers * 15.0
            + center_bonus * 0.3
        )

        return tiger_score if perspective_role == "tiger" else -tiger_score

    def _model_value(self, state: AIState, perspective_role: str) -> float:
        if not self.model_loaded or torch is None or self.model is None:
            return 0.0

        flat = [float(x) for x in state.board]
        flat.extend(
            [
                float(state.goats_placed) / 20.0,
                float(state.goats_captured) / 5.0,
                1.0 if state.turn == "tiger" else 0.0,
                1.0 if state.phase == 2 else 0.0,
            ]
        )

        try:
            x = torch.tensor([flat], dtype=torch.float32, device=self.device)
            with torch.no_grad():
                out = self.model(x)

            if isinstance(out, (tuple, list)) and len(out) > 1:
                value = out[-1]
            else:
                value = out

            if hasattr(value, "shape") and len(value.shape) > 1:
                model_value = float(value.reshape(-1)[0].item())
            else:
                model_value = float(value.item())

            if perspective_role == "goat":
                model_value = -model_value
            return model_value
        except Exception:
            return 0.0

    def choose_move(
        self,
        board: List[int],
        turn: str,
        phase: int,
        goats_placed: int,
        goats_captured: int,
        ai_role: Optional[str],
        mode: str = "hybrid",
        top_k: int = 3,
    ) -> Tuple[Optional[Dict], str, float]:
        state = AIState(
            board=list(board),
            turn=turn,
            phase=phase,
            goats_placed=goats_placed,
            goats_captured=goats_captured,
        )
        role = ai_role or turn

        if role != turn:
            return None, mode, 0.0

        moves = self._legal_moves(state, role)
        if not moves:
            return None, mode, -9999.0

        mode_normalized = (mode or "hybrid").strip().lower()
        scored: List[Tuple[float, Dict]] = []
        for move in moves:
            next_state = self._apply_move(state, move, role)
            score = self._heuristic_value(next_state, role)

            if mode_normalized in {"model", "hybrid"}:
                model_bonus = self._model_value(next_state, role)
                if mode_normalized == "model":
                    score = model_bonus * 100.0
                else:
                    score += model_bonus * 40.0

            if role == "tiger" and move.get("captured") is not None:
                score += 10.0

            scored.append((score, move))

        scored.sort(key=lambda item: item[0], reverse=True)
        k = max(1, min(top_k, len(scored)))
        best_score, best_move = scored[0]

        if mode_normalized == "hybrid" and k > 1:
            top_candidates = scored[:k]
            top_candidates.sort(key=lambda item: item[0], reverse=True)
            best_score, best_move = top_candidates[0]

        mode_used = mode_normalized
        if mode_normalized in {"model", "hybrid"} and not self.model_loaded:
            mode_used = "heuristic"

        return best_move, mode_used, float(best_score)


hybrid_ai_service = HybridAIService()
