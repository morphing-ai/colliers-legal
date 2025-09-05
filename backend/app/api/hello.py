# backend/app/api/hello.py
from fastapi import APIRouter, Depends
from typing import Dict

from app.api.auth import get_current_user, User

router = APIRouter()

@router.get("/hello", response_model=Dict)
async def hello_world(current_user: User = Depends(get_current_user)):
    """
    Simple hello world endpoint that requires authentication.
    """
    return {
        "message": "Hello, I work!",
        "user": current_user.email
    }
