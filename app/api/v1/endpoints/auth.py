from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    ForgotPasswordRequest,
    ForgotPasswordVerify,
)
from app.services.auth_service import (
    create_user,
    authenticate_user,
    get_user_by_username,
    get_user_by_email,
    is_valid_email,
    validate_password_strength,
    create_password_reset_code,
    reset_password_with_code,
)
from app.core.security import create_access_token
from app.db.session import get_db
from app.services.email_service import send_reset_code_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    if not is_valid_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid email address",
        )

    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    existing_email = get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    password_error = validate_password_strength(user_data.password)
    if password_error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=password_error)

    user = create_user(db, user_data.username, user_data.email, user_data.password)
    token = create_access_token({"sub": str(user.id), "username": user.username})
    return Token(token=token, userId=user.id)


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    existing_user = get_user_by_username(db, user_data.username)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    user = authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    token = create_access_token({"sub": str(user.id), "username": user.username})
    return Token(token=token, userId=user.id)


@router.post("/forgot-password/request")
def request_forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if not user:
        return {"message": "If the email exists, a reset code has been sent."}

    code = create_password_reset_code(db, user.id)
    try:
        send_reset_code_email(user.email, user.username, code)
    except Exception:
        pass

    return {"message": "If the email exists, a reset code has been sent."}


@router.post("/forgot-password/verify")
def verify_forgot_password(payload: ForgotPasswordVerify, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or code")

    password_error = validate_password_strength(payload.new_password)
    if password_error:
        raise HTTPException(status_code=400, detail=password_error)

    success = reset_password_with_code(db, user, payload.code.strip(), payload.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    return {"message": "Password reset successful"}
