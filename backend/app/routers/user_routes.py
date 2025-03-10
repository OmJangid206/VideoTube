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
from app.controllers.user_controller import change_password
from app.controllers.user_controller import get_current_user
from app.controllers.user_controller import update_account_details
from app.controllers.user_controller import update_avatar
from app.controllers.user_controller import update_cover_image
from app.controllers.user_controller import get_user_channel_profile

from app.middlewares.auth_middlewares import veryfy_jwt


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
@router.post("/logout", dependencies=[Depends(veryfy_jwt)])
async def logout_route(request: Request, response: Response):
    """
    Logs a user out (JWT authentication required).
    """
    return await logout_user(request, response)


@router.post("/change-password",dependencies=[Depends(veryfy_jwt)])
async def change_password_route(request: Request):
    """change the password"""
    return await change_password(request)


@router.get("/current-user", dependencies=[Depends(veryfy_jwt)])
async def get_current_user_route(request: Request):
    return await get_current_user(request) 


@router.patch("/update-account", dependencies=[Depends(veryfy_jwt)])
async def update_account_details_route(request: Request):
    return await update_account_details(request)



@router.patch("/avatar", dependencies=[Depends(veryfy_jwt)])
async def update_avatar_route(request: Request, avatar: UploadFile = File(...)):
    """update avatart image"""
    return await update_avatar(request, avatar)


@router.patch("/cover-image", dependencies=[Depends(veryfy_jwt)])
async def update_cover_image_route(
    request: Request,
    cover_image: UploadFile = File(..., alias="coverImage")
):
    """update cover image"""
    return await update_cover_image(request, cover_image)


@router.get("/c/{username}", dependencies=[Depends(veryfy_jwt)])
async def get_channel_profile_route(username: str, request: Request):
    """get user channel profile"""
    return await get_user_channel_profile(username, request)
