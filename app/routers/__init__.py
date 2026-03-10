"""Auth router."""
from fastapi import APIRouter, HTTPException, Response, status

from app.auth import clear_session_cookie, get_current_user, set_session_cookie, verify_credentials
from app.schemas import LoginRequest, LoginResponse
from fastapi import Depends, Request

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response):
    if not verify_credentials(request.email, request.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    set_session_cookie(response, request.email)
    return LoginResponse(email=request.email)


@router.post("/logout")
async def logout(response: Response):
    clear_session_cookie(response)
    return {"message": "Logged out"}


@router.get("/me")
async def me(request: Request, user: dict = Depends(get_current_user)):
    return {"email": user["email"]}
