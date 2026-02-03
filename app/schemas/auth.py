from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    token: str
    userId: int


class UserProfile(BaseModel):
    id: int
    username: str
    elo_rating: float
    games_played: int = 0
    games_won: int = 0

    class Config:
        from_attributes = True
