from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import re
import random
from app.db.models.user import User
from app.db.models.password_reset_code import PasswordResetCode
from app.core.security import get_password_hash, verify_password


def is_valid_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email or ""))


def validate_password_strength(password: str) -> str | None:
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return "Password must include at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return "Password must include at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return "Password must include at least one number"
    return None


def create_user(db: Session, username: str, email: str, password: str) -> User:
    hashed_password = get_password_hash(password)
    user = User(username=username, email=email.lower(), hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_by_id(db: Session, user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> User:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> User:
    normalized_email = (email or "").strip().lower()
    return db.query(User).filter(User.email == normalized_email).first()


def create_password_reset_code(db: Session, user_id: int) -> str:
    db.query(PasswordResetCode).filter(
        PasswordResetCode.user_id == user_id,
        PasswordResetCode.used == False,
    ).update({"used": True}, synchronize_session=False)

    code = f"{random.randint(0, 999999):06d}"
    reset_entry = PasswordResetCode(
        user_id=user_id,
        code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        used=False,
    )
    db.add(reset_entry)
    db.commit()
    return code


def verify_password_reset_code(
    db: Session, user_id: int, code: str
) -> PasswordResetCode | None:
    normalized_code = "".join(ch for ch in (code or "") if ch.isdigit())
    if not normalized_code:
        return None
    if len(normalized_code) <= 6:
        normalized_code = normalized_code.zfill(6)

    reset_entry = (
        db.query(PasswordResetCode)
        .filter(
            PasswordResetCode.user_id == user_id,
            PasswordResetCode.code == normalized_code,
            PasswordResetCode.used == False,
        )
        .order_by(PasswordResetCode.created_at.desc())
        .first()
    )
    if not reset_entry:
        return None

    now = datetime.now(timezone.utc)
    expires_at = reset_entry.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        return None
    return reset_entry


def reset_password_with_code(db: Session, user: User, code: str, new_password: str) -> bool:
    reset_entry = verify_password_reset_code(db, user.id, code)
    if not reset_entry:
        return False
    user.hashed_password = get_password_hash(new_password)
    reset_entry.used = True
    db.commit()
    return True
