from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    email: str
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
    email: str | None = None
    elo_rating: float
    games_played: int = 0
    games_won: int = 0

    class Config:
        from_attributes = True


class ForgotPasswordRequest(BaseModel):
    email: str


class ForgotPasswordVerify(BaseModel):
    email: str
    code: str
    new_password: str
