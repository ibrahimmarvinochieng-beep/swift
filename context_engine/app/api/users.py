"""User context API."""

from fastapi import APIRouter, HTTPException, Request, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.repository import get_user, create_user, update_user
from app.core.cache import invalidate_feed
from app.models.user import UserCreate, UserUpdate, UserResponse
from app.core.security import limiter

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
@limiter.limit("60/minute")
async def create_user_endpoint(request: Request, user: UserCreate, session: AsyncSession = Depends(get_db)):
    existing = await get_user(session, user.user_id)
    if existing:
        raise HTTPException(status_code=409, detail="User exists")
    u = await create_user(
        session, user.user_id, user.locations, user.interests,
        user.profession, user.industries, user.alert_preferences
    )
    return UserResponse(
        user_id=u.user_id, locations=u.locations, interests=u.interests,
        profession=u.profession, industries=u.industries,
        alert_preferences=u.alert_preferences, created_at=u.created_at
    )


@router.get("/{user_id}", response_model=UserResponse)
@limiter.limit("60/minute")
async def get_user_endpoint(request: Request, user_id: str = Path(..., min_length=1, max_length=128), session: AsyncSession = Depends(get_db)):
    u = await get_user(session, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        user_id=u.user_id, locations=u.locations, interests=u.interests,
        profession=u.profession, industries=u.industries,
        alert_preferences=u.alert_preferences, created_at=u.created_at
    )


@router.patch("/{user_id}", response_model=UserResponse)
@limiter.limit("60/minute")
async def update_user_endpoint(request: Request, user_id: str, update: UserUpdate, session: AsyncSession = Depends(get_db)):
    kwargs = {k: v for k, v in update.model_dump(exclude_unset=True).items()}
    u = await update_user(session, user_id, **kwargs)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    await invalidate_feed(user_id)
    return UserResponse(
        user_id=u.user_id, locations=u.locations, interests=u.interests,
        profession=u.profession, industries=u.industries,
        alert_preferences=u.alert_preferences, created_at=u.created_at
    )
