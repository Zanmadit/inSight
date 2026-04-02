from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import RegisterRequest, TokenResponse, UserPublic
from app.services.auth_service import authenticate_user, create_access_token, register_user

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        user = await register_user(db, data.email, data.password, data.role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    token = create_access_token(user)
    return TokenResponse(
        access_token=token,
        user=UserPublic.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    db: Annotated[AsyncSession, Depends(get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(user)
    return TokenResponse(
        access_token=token,
        user=UserPublic.model_validate(user),
    )


@router.get("/me", response_model=UserPublic)
async def me(current: Annotated[User, Depends(get_current_user)]):
    return UserPublic.model_validate(current)
