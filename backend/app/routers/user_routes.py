"""
user_routes.py

This module defines routes for user-related operations including registration, login, and logout.

Routes:
    - POST /register: Registers a new user by accepting avatar and optional cover image files.
    - POST /login: Logs in a user by accepting request and response for session management.
    - POST /logout: Logs out a user, with JWT authentication required for access.

Dependencies:
    - veryfy_jwt: A middleware that verifies the JWT token for secure logout.

"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Request, Response, Depends

from app.controllers.user_controller import register_user
from app.controllers.user_controller import login_user
from app.controllers.user_controller import logout_user
from app.middlewares.auth_middlewares import veryfy_jwt


router = APIRouter()

@router.post('/register')
async def register_route(request: Request, avatar: UploadFile = File(...), cover_image: Optional[UploadFile] = File(None)):
    """
    Registers a user with an avatar and optional cover image.
    """
    return await register_user(request, avatar, cover_image)

@router.post('/login')
async def login_route(request: Request, response: Response):
    """
    Authenticates a user and logs them into the system.
    """
    return await login_user(request, response)

# Secure
@router.post('/logout', dependencies=[Depends(veryfy_jwt)])
async def logout_route(request: Request, response: Response):
    """
    Logs a user out (JWT authentication required).
    """
    return await logout_user(request, response)
