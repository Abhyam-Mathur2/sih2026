from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserCreate, UserRead, UserUpdate
from app.schemas.common import StatusResponse
from app.services import auth_service

router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=201, summary="Register an initial user")
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    return await auth_service.create_user(db, payload)


@router.post("/login", response_model=TokenResponse, summary="Login and get JWT token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    return await auth_service.authenticate_user(db, form_data.username, form_data.password)


@router.get("/me", response_model=UserRead, summary="Get current user profile")
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/users", response_model=UserRead, status_code=201, summary="Create a new user (Admin only)")
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> User:
    return await auth_service.create_user(db, payload)


@router.get("/users", response_model=list[UserRead], summary="List all users (Admin only)")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[User]:
    return await auth_service.list_users(db, skip=skip, limit=limit)


@router.patch("/users/{user_id}", response_model=UserRead, summary="Update user (Admin only)")
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> User:
    return await auth_service.update_user(db, user_id, payload)
