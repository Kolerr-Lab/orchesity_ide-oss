"""
User management router for Orchesity IDE OSS
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import uuid
from typing import Optional, Dict, Any
import logging
from ..models import UserSession
from ..core.container import ServiceContainer

logger = logging.getLogger(__name__)

# In-memory session storage (replace with database in production)
_sessions: Dict[str, UserSession] = {}


def create_router(container: ServiceContainer) -> APIRouter:
    """Create user router with dependency injection"""
    router = APIRouter()

    @router.post("/session", response_model=UserSession)
    async def create_session(
        user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ):
        """Create a new user session"""
        try:
            session_id = str(uuid.uuid4())
            created_at = datetime.utcnow()
            last_activity = created_at

            session = UserSession(
                session_id=session_id,
                user_id=user_id or "anonymous",
                created_at=str(created_at),
                last_activity=str(last_activity),
                preferences=metadata or {},
            )

            _sessions[session_id] = session

            logger.info(f"Created session: {session_id} for user: {session.user_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise HTTPException(
                status_code=500, detail=f"Session creation failed: {str(e)}"
            )

    @router.get("/session/{session_id}", response_model=UserSession)
    async def get_session(session_id: str):
        """Get session information"""
        try:
            if session_id not in _sessions:
                raise HTTPException(status_code=404, detail="Session not found")

            session = _sessions[session_id]

            return session

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Session retrieval failed: {str(e)}"
            )

    @router.delete("/session/{session_id}")
    async def delete_session(session_id: str):
        """Delete/invalidate a session"""
        try:
            if session_id not in _sessions:
                raise HTTPException(status_code=404, detail="Session not found")

            del _sessions[session_id]

            logger.info(f"Deleted session: {session_id}")
            return {"message": "Session deleted successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Session deletion failed: {str(e)}"
            )

    @router.get("/sessions")
    async def list_sessions(active_only: bool = True):
        """List all sessions (admin endpoint)"""
        try:
            sessions = []

            for session in _sessions.values():
                sessions.append(
                    {
                        "session_id": session.session_id,
                        "user_id": session.user_id,
                        "created_at": session.created_at,
                        "last_activity": session.last_activity,
                        "preferences": session.preferences,
                    }
                )

            return {"sessions": sessions, "total": len(sessions)}

        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            raise HTTPException(
                status_code=500, detail=f"Session listing failed: {str(e)}"
            )

    return router
