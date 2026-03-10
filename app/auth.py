"""Session-based auth using itsdangerous signed cookies."""
from fastapi import Cookie, HTTPException, Request, Response, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import (
    APP_LOGIN_EMAIL,
    APP_LOGIN_PASSWORD,
    SECRET_KEY,
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE,
)

_serializer = URLSafeTimedSerializer(SECRET_KEY)


def verify_credentials(email: str, password: str) -> bool:
    """Check email+password against env-configured credentials."""
    return email == APP_LOGIN_EMAIL and password == APP_LOGIN_PASSWORD


def create_session_token(email: str) -> str:
    return _serializer.dumps({"email": email})


def decode_session_token(token: str) -> dict:
    try:
        return _serializer.loads(token, max_age=SESSION_MAX_AGE)
    except SignatureExpired:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    except BadSignature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")


def set_session_cookie(response: Response, email: str) -> None:
    token = create_session_token(email)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME)


def get_current_user(request: Request) -> dict:
    """FastAPI dependency: return session payload or raise 401."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return decode_session_token(token)


def get_current_user_optional(request: Request) -> dict | None:
    """Returns None instead of raising when not authenticated."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    try:
        return decode_session_token(token)
    except HTTPException:
        return None
