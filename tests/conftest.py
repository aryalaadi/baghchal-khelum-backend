import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./_test_bootstrap.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

from main import app
from app.api.deps import get_db as deps_get_db
from app.db.session import Base
from app.db.models.user import User
from app.db.models.community import Post
from app.db.models.friend_challenge import FriendChallenge
from app.db.models.game_log import GameLog
from app.db.models.replay import Replay
from app.db.models.password_reset_code import PasswordResetCode
from app.core.security import get_password_hash, create_access_token


@pytest.fixture()
def db_session():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    db_url = f"sqlite:///{tmp.name}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        os.unlink(tmp.name)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[deps_get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db_session):
    def _make_user(username: str, email: str, password: str = "Password1", elo: float = 1200.0):
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            elo_rating=elo,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make_user


@pytest.fixture()
def auth_header_for():
    def _auth_header_for(user_id: int, username: str):
        token = create_access_token({"sub": str(user_id), "username": username})
        return {"Authorization": f"Bearer {token}"}

    return _auth_header_for
