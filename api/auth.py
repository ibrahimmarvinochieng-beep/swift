"""JWT authentication, RBAC middleware, and user store.

Users are persisted via the same SQLite backend as events when
PERSISTENCE_BACKEND=sqlite.  On startup the store hydrates from disk
so registered users survive restarts.
"""

import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from utils.security_utils import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from utils.logger import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

ROLE_HIERARCHY = {
    "admin": 3,
    "analyst": 2,
    "viewer": 1,
}

# ── User store (in-memory + optional SQLite write-through) ────────

_users_store: dict = {}
_user_db = None


def _get_user_db():
    """Lazily initialise the SQLite backend for users."""
    global _user_db
    if _user_db is not None:
        return _user_db

    backend = os.environ.get("PERSISTENCE_BACKEND", "sqlite")
    if backend == "sqlite":
        from db.sqlite_store import SQLiteStore
        db_path = os.environ.get("SQLITE_DB_PATH", "")
        _user_db = SQLiteStore(db_path or None)
        return _user_db
    return None


def _hydrate_users():
    """Load users from SQLite into memory on first access."""
    if _users_store:
        return
    store = _get_user_db()
    if store is None:
        return
    loaded = store.load_all_users()
    _users_store.update(loaded)
    if loaded:
        logger.info("users_hydrated_from_sqlite", count=len(loaded))


# ── Public API ────────────────────────────────────────────────────

def register_user(username: str, email: str, password: str, role: str = "viewer") -> dict:
    _hydrate_users()

    if username in _users_store:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = {
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
        "role": role,
        "is_active": True,
    }
    _users_store[username] = user

    store = _get_user_db()
    if store:
        store.put_user(username, user)

    logger.info("user_registered", username=username, role=role)
    return {k: v for k, v in user.items() if k != "password_hash"}


def authenticate_user(username: str, password: str) -> Optional[dict]:
    _hydrate_users()
    user = _users_store.get(username)
    if not user or not user["is_active"]:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    _hydrate_users()
    payload = decode_access_token(token)
    username = payload.get("sub")

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = _users_store.get(username)
    if not user or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


def require_role(minimum_role: str):
    min_level = ROLE_HIERARCHY.get(minimum_role, 0)

    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_level = ROLE_HIERARCHY.get(current_user.get("role", ""), 0)
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires at least '{minimum_role}' role",
            )
        return current_user

    return role_checker


def create_default_admin():
    _hydrate_users()
    if "admin" not in _users_store:
        register_user("admin", "admin@swift.ai", "SwiftAdmin2026!", role="admin")
        logger.info("default_admin_created")
