"""
user_routes.py

This module defines routes for user-related operations, including registration, login, logout, and account management.

Routes:
    - POST /register: Registers a new user with an avatar and optional cover image.
    - POST /login: Authenticates and logs in a user.
    - POST /logout: Logs out a user (JWT required).
    - POST /change-password: Changes the user's password (JWT required).
    - GET /current-user: Retrieves the current authenticated user (JWT required).
    - PATCH /update-account: Updates user account details (JWT required).
    - PATCH /avatar: Updates user avatar (JWT required).
    - PATCH /cover-image: Updates user cover image (JWT required).
    - GET /c/{username}: Retrieves a user channel profile (JWT required).
    - GET /history: Retrieves user watch history (JWT required).

Dependencies:
    - verify_jwt: Middleware that verifies the JWT token for secure access.
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, Request, Response, Depends

from app.controllers.user_controller import register_user
from app.controllers.user_controller import login_user
from app.controllers.user_controller import logout_user
from app.controllers.user_controller import change_password
from app.controllers.user_controller import get_current_user
from app.controllers.user_controller import update_account_details
from app.controllers.user_controller import update_avatar
from app.controllers.user_controller import update_cover_image
from app.controllers.user_controller import get_user_channel_profile
from app.controllers.user_controller import get_user_watch_history
from app.controllers.user_controller import google_login

from app.middlewares.auth_middlewares import verify_jwt

router = APIRouter()


@router.post("/register")
async def register_route(
    request: Request,
    avatar: UploadFile = File(...),
    cover_image: Optional[UploadFile] = File(None, alias="coverImage"),
):
    """
    Registers a user with an avatar and optional cover image.
    """
    return await register_user(request, avatar, cover_image)


@router.post("/login")
async def login_route(request: Request, response: Response):
    """
    Authenticates a user and logs them into the system.
    """
    return await login_user(request, response)


# Secure
@router.post("/logout", dependencies=[Depends(verify_jwt)])
async def logout_route(request: Request, response: Response):
    """
    Logs a user out (JWT authentication required).
    """
    return await logout_user(request, response)


@router.post("/change-password",dependencies=[Depends(verify_jwt)])
async def change_password_route(request: Request):
    """
    Changes the user password (JWT required).
    """
    return await change_password(request)


@router.get("/current-user", dependencies=[Depends(verify_jwt)])
async def get_current_user_route(request: Request):
    """
    Gets the current authenticated user.
    """
    return await get_current_user(request) 


@router.patch("/update-account", dependencies=[Depends(verify_jwt)])
async def update_account_details_route(request: Request):
    """
    Updates user account details.
    """
    return await update_account_details(request)



@router.patch("/avatar", dependencies=[Depends(verify_jwt)])
async def update_avatar_route(request: Request, avatar: UploadFile = File(...)):
    """
    Updates user avatar.
    """
    return await update_avatar(request, avatar)


@router.patch("/cover-image", dependencies=[Depends(verify_jwt)])
async def update_cover_image_route(
    request: Request,
    cover_image: UploadFile = File(..., alias="coverImage")
):
    """
    Updates user cover image.
    """
    return await update_cover_image(request, cover_image)


@router.get("/c/{username}", dependencies=[Depends(verify_jwt)])
async def get_channel_profile_route(username: str, request: Request):
    """
    Gets user channel profile.
    """
    return await get_user_channel_profile(username, request)

@router.get("/history", dependencies=[Depends(verify_jwt)])
async def get_watch_history_route(request: Request):
    """
    Gets user watch history.
    """
    return await get_user_watch_history(request)

@router.post("/auth/google")
async def google_login_route(requst : Request, response: Response):
    print(f"requst: {requst}or {response}")
    return await google_login(requst, response) 