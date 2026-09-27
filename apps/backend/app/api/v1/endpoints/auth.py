from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    return await service.register(user_in)


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate and receive a JWT access token"
)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    return await service.authenticate(credentials)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get profile of the currently authenticated user"
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.get(
    "/admin-only",
    summary="Example route restricted exclusively to ADMIN users"
)
async def admin_protected_route(
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    return {
        "message": f"Hello Administrator {current_user.email}. Role verified.",
        "role": current_user.role.value
    }
