"""User and interaction repository."""

from datetime import datetime
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserModel, InteractionModel


async def get_user(session: AsyncSession, user_id: str) -> UserModel | None:
    r = await session.execute(select(UserModel).where(UserModel.user_id == user_id))
    return r.scalars().first()


async def create_user(session: AsyncSession, user_id: str, locations: list, interests: list, profession: str, industries: list, alert_preferences: dict) -> UserModel:
    u = UserModel(user_id=user_id, locations=locations, interests=interests, profession=profession, industries=industries, alert_preferences=alert_preferences)
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return u


VALID_USER_UPDATE = {"locations", "interests", "profession", "industries", "alert_preferences"}


async def update_user(session: AsyncSession, user_id: str, **kwargs) -> UserModel | None:
    filtered = {k: v for k, v in kwargs.items() if k in VALID_USER_UPDATE}
    if not filtered:
        return await get_user(session, user_id)
    await session.execute(update(UserModel).where(UserModel.user_id == user_id).values(**filtered))
    await session.commit()
    return await get_user(session, user_id)


async def record_interaction(session: AsyncSession, user_id: str, event_id: str, interaction_type: str, metadata: dict | None = None) -> InteractionModel:
    i = InteractionModel(user_id=user_id, event_id=event_id, interaction_type=interaction_type, metadata_json=metadata)
    session.add(i)
    await session.commit()
    await session.refresh(i)
    return i


async def get_user_interaction_counts(session: AsyncSession, user_id: str) -> dict[str, int]:
    r = await session.execute(
        select(InteractionModel.event_id, InteractionModel.interaction_type, func.count())
        .where(InteractionModel.user_id == user_id)
        .group_by(InteractionModel.event_id, InteractionModel.interaction_type)
    )
    return {f"{row[0]}:{row[1]}": row[2] for row in r}


async def get_users_by_ids(session: AsyncSession, user_ids: list[str]) -> list[UserModel]:
    r = await session.execute(select(UserModel).where(UserModel.user_id.in_(user_ids)))
    return list(r.scalars().all())
