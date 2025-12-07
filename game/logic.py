from typing import List, Tuple, Optional, Set
import hashlib
import json

# Board constants
EMPTY = 0
GOAT = 1
TIGER = 2

# Complete adjacency graph for 5x5 BaghChal board
# Index mapping:
#  0  1  2  3  4
#  5  6  7  8  9
# 10 11 12 13 14
# 15 16 17 18 19
# 20 21 22 23 24

# Correct adjacency graph for BaghChal board
ADJACENCY = {
    # Row 0
    0: [1, 5, 6],
    1: [0, 2, 6],
    2: [1, 3, 6, 7, 8],
    3: [2, 4, 8],
    4: [3, 8, 9],
    
    # Row 1
    5: [0, 6, 10],
    6: [0, 1, 2, 5, 7, 10, 11, 12],
    7: [2, 6, 8, 12],
    8: [2, 3, 4, 7, 9, 12, 13, 14],
    9: [4, 8, 14],
    
    # Row 2
    10: [5, 6, 11, 15, 16],
    11: [6, 10, 12, 16],
    12: [6, 7, 8, 11, 13, 16, 17, 18],
    13: [8, 12, 14, 18],
    14: [8, 9, 13, 18, 19],
    
    # Row 3
    15: [10, 16, 20],
    16: [10, 11, 12, 15, 17, 20, 21, 22],
    17: [12, 16, 18, 22],
    18: [12, 13, 14, 17, 19, 22, 23, 24],
    19: [14, 18, 24],
    
    # Row 4
    20: [15, 16, 21],
    21: [16, 20, 22],
    22: [16, 17, 18, 21, 23],
    23: [18, 22, 24],
    24: [18, 19, 23]
}

class BaghChalGame:
    def __init__(self):
        self.board = [EMPTY] * 25
        # Initial tiger positions at corners
        self.board[0] = TIGER
        self.board[4] = TIGER
        self.board[20] = TIGER
        self.board[24] = TIGER
        
        self.turn = "goat"  # goat places first
        self.goats_placed = 0
        self.goats_captured = 0
        self.phase = 1  # 1 = placing goats, 2 = moving goats
        self.history: Set[str] = set()
        self.total_goats = 20
        
    def get_board_hash(self) -> str:
        """Get unique hash of current board state."""
        board_str = json.dumps(self.board)
        return hashlib.md5(board_str.encode()).hexdigest()
    
    def is_valid_position(self, pos: int) -> bool:
        """Check if position is within board bounds."""
        return 0 <= pos < 25
    
    def place_goat(self, position: int) -> Tuple[bool, str]:
        """Place a goat on the board (phase 1)."""
        if self.phase != 1:
            return False, "Not in placement phase"
        
        if self.turn != "goat":
            return False, "Not goat's turn"
        
        if not self.is_valid_position(position):
            return False, "Invalid position"
        
        if self.board[position] != EMPTY:
            return False, "Position already occupied"
        
        # Place goat
        self.board[position] = GOAT
        self.goats_placed += 1
        
        # Check if all goats placed
        if self.goats_placed >= self.total_goats:
            self.phase = 2
        
        # Switch turn
        self.turn = "tiger"
        
        return True, "Goat placed successfully"
    
    def get_adjacent_positions(self, pos: int) -> List[int]:
        """Get adjacent positions for a given position."""
        return ADJACENCY.get(pos, [])
    
    def is_in_line(self, pos1: int, pos2: int, pos3: int) -> bool:
        """Check if three positions are in a straight line."""
        # Check if pos2 is between pos1 and pos3
        row1, col1 = pos1 // 5, pos1 % 5
        row2, col2 = pos2 // 5, pos2 % 5
        row3, col3 = pos3 // 5, pos3 % 5
        
        # Check horizontal line
        if row1 == row2 == row3:
            return sorted([col1, col2, col3]) == [col1, col2, col3] or sorted([col1, col2, col3]) == [col3, col2, col1]
        
        # Check vertical line
        if col1 == col2 == col3:
            return sorted([row1, row2, row3]) == [row1, row2, row3] or sorted([row1, row2, row3]) == [row3, row2, row1]
        
        # Check diagonal lines
        # Main diagonals
        if abs(row1 - row2) == abs(col1 - col2) and abs(row2 - row3) == abs(col2 - col3):
            # Check if they're collinear
            if (row2 - row1) * (col3 - col1) == (row3 - row1) * (col2 - col1):
                # Check if pos2 is between pos1 and pos3
                if min(row1, row3) <= row2 <= max(row1, row3) and min(col1, col3) <= col2 <= max(col1, col3):
                    return True
        
        return False
    
    def can_tiger_capture(self, from_pos: int, to_pos: int) -> Tuple[bool, int]:
        """Check if tiger can capture a goat by jumping."""
        if self.board[from_pos] != TIGER:
            return False, -1
        
        if not self.is_valid_position(to_pos):
            return False, -1
        
        if self.board[to_pos] != EMPTY:
            return False, -1
        
        # Check all adjacent positions for potential captures
        for adj_pos in self.get_adjacent_positions(from_pos):
            if self.board[adj_pos] == GOAT:
                # Check if to_pos is in line and adjacent to adj_pos on the opposite side
                if adj_pos in self.get_adjacent_positions(to_pos):
                    if self.is_in_line(from_pos, adj_pos, to_pos):
                        return True, adj_pos
        
        return False, -1
    
    def move_tiger(self, from_pos: int, to_pos: int) -> Tuple[bool, str, Optional[int]]:
        """Move a tiger."""
        if self.turn != "tiger":
            return False, "Not tiger's turn", None
        
        if not self.is_valid_position(from_pos) or not self.is_valid_position(to_pos):
            return False, "Invalid position", None
        
        if self.board[from_pos] != TIGER:
            return False, "No tiger at source position", None
        
        if self.board[to_pos] != EMPTY:
            return False, "Destination not empty", None
        
        # Check if it's a capture move
        can_capture, goat_pos = self.can_tiger_capture(from_pos, to_pos)
        
        if can_capture:
            # Capture move
            self.board[goat_pos] = EMPTY
            self.board[from_pos] = EMPTY
            self.board[to_pos] = TIGER
            self.goats_captured += 1
            self.turn = "goat"
            return True, "Tiger captured goat", goat_pos
        else:
            # Regular move (must be adjacent)
            if to_pos not in self.get_adjacent_positions(from_pos):
                return False, "Tigers can only move to adjacent positions or capture", None
            
            self.board[from_pos] = EMPTY
            self.board[to_pos] = TIGER
            self.turn = "goat"
            return True, "Tiger moved", None
    
    def move_goat(self, from_pos: int, to_pos: int) -> Tuple[bool, str]:
        """Move a goat (phase 2 only)."""
        if self.phase != 2:
            return False, "Cannot move goats in placement phase"
        
        if self.turn != "goat":
            return False, "Not goat's turn"
        
        if not self.is_valid_position(from_pos) or not self.is_valid_position(to_pos):
            return False, "Invalid position"
        
        if self.board[from_pos] != GOAT:
            return False, "No goat at source position"
        
        if self.board[to_pos] != EMPTY:
            return False, "Destination not empty"
        
        # Goats can only move to adjacent positions
        if to_pos not in self.get_adjacent_positions(from_pos):
            return False, "Goats can only move to adjacent positions"
        
        # Apply move temporarily to check for repetition
        self.board[from_pos] = EMPTY
        self.board[to_pos] = GOAT
        
        # Check for repetition
        board_hash = self.get_board_hash()
        if board_hash in self.history:
            # Revert move
            self.board[from_pos] = GOAT
            self.board[to_pos] = EMPTY
            return False, "Move would repeat a previous board state"
        
        # Add to history
        self.history.add(board_hash)
        
        # Switch turn
        self.turn = "tiger"
        
        return True, "Goat moved"
    
    def get_tiger_legal_moves(self, tiger_pos: int) -> List[int]:
        """Get all legal moves for a tiger at given position."""
        if self.board[tiger_pos] != TIGER:
            return []
        
        legal_moves = []
        
        # Check adjacent moves
        for adj_pos in self.get_adjacent_positions(tiger_pos):
            if self.board[adj_pos] == EMPTY:
                legal_moves.append(adj_pos)
        
        # Check capture moves
        for adj_pos in self.get_adjacent_positions(tiger_pos):
            if self.board[adj_pos] == GOAT:
                # Check if we can jump over this goat
                for next_pos in self.get_adjacent_positions(adj_pos):
                    if next_pos != tiger_pos and self.board[next_pos] == EMPTY:
                        if self.is_in_line(tiger_pos, adj_pos, next_pos):
                            legal_moves.append(next_pos)
        
        return legal_moves
    
    def has_tiger_legal_moves(self) -> bool:
        """Check if any tiger has legal moves."""
        for i in range(25):
            if self.board[i] == TIGER:
                if len(self.get_tiger_legal_moves(i)) > 0:
                    return True
        return False
    
    def check_winner(self) -> Optional[str]:
        """Check if there's a winner."""
        # Tiger wins if 5 goats captured
        if self.goats_captured >= 5:
            return "tiger"
        
        # Goat wins if in phase 2 and all tigers blocked
        if self.phase == 2:
            if not self.has_tiger_legal_moves():
                return "goat"
        
        return None
    
    def to_dict(self) -> dict:
        """Convert game state to dictionary."""
        return {
            "board": self.board,
            "turn": self.turn,
            "goats_placed": self.goats_placed,
            "goats_captured": self.goats_captured,
            "phase": self.phase,
            "history": list(self.history)
        }
    
    def from_dict(self, data: dict):
        """Load game state from dictionary."""
        self.board = data.get("board", self.board)
        self.turn = data.get("turn", self.turn)
        self.goats_placed = data.get("goats_placed", self.goats_placed)
        self.goats_captured = data.get("goats_captured", self.goats_captured)
        self.phase = data.get("phase", self.phase)
        self.history = set(data.get("history", []))
