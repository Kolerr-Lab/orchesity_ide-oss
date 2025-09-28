"""
User management router for Orchesity IDE OSS
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
import uuid
from typing import Optional
from ..models import UserSession
from ..config import settings
from ..utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# In-memory session storage (replace with database in production)
_sessions: dict[str, UserSession] = {}


@router.post("/session", response_model=UserSession)
async def create_session(user_id: Optional[str] = None):
    """Create a new user session"""
    try:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"

        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_activity=now,
            preferences={
                "theme": "light",
                "max_concurrent_requests": settings.max_concurrent_requests,
                "routing_strategy": settings.routing_strategy,
            },
        )

        _sessions[session_id] = session
        logger.info(f"Created session: {session_id}")

        return session

    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.get("/session/{session_id}", response_model=UserSession)
async def get_session(session_id: str):
    """Get session information"""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]

    # Update last activity
    session.last_activity = datetime.utcnow().isoformat() + "Z"

    return session


@router.put("/session/{session_id}/preferences")
async def update_preferences(session_id: str, preferences: dict):
    """Update user preferences"""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]

    # Update preferences
    session.preferences.update(preferences)
    session.last_activity = datetime.utcnow().isoformat() + "Z"

    logger.info(f"Updated preferences for session: {session_id}")
    return {"message": "Preferences updated", "preferences": session.preferences}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a user session"""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del _sessions[session_id]
    logger.info(f"Deleted session: {session_id}")

    return {"message": "Session deleted"}


@router.get("/sessions/count")
async def get_sessions_count():
    """Get total number of active sessions"""
    return {"active_sessions": len(_sessions)}


@router.post("/session/{session_id}/heartbeat")
async def session_heartbeat(session_id: str):
    """Update session last activity (heartbeat)"""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    _sessions[session_id].last_activity = datetime.utcnow().isoformat() + "Z"

    return {"message": "Heartbeat received"}
