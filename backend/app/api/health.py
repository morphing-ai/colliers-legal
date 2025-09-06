# backend/app/api/health.py
from fastapi import APIRouter, Depends
from typing import Dict
import os

from app.config import settings
from app.api.auth import get_current_user, User

router = APIRouter()

@router.get("/health", response_model=Dict)
async def health_check():
    """
    Basic health check endpoint.
    """
    return {
        "status": "ok", 
        "api_version": "1.2",
        "debug_mode": settings.DEBUG,
        "dev_mode": settings.DEV_MODE,
        "auth_type": "PEM key" if settings.CLERK_PEM_PUBLIC_KEY or os.path.exists(settings.CLERK_PEM_PUBLIC_KEY_PATH) else "API"
    }

@router.get("/health/auth", response_model=Dict)
async def auth_check(current_user: User = Depends(get_current_user)):
    """
    Health check that also verifies authentication.
    """
    return {
        "status": "ok", 
        "api_version": "1.2",
        "user_id": current_user.id,
        "email": current_user.email,
        "authenticated": True
    }