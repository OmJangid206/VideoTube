"""
user_modles.py

This module provides functionality for generating and refreshing access and refresh tokens
for user authentication in a FastAPI application.
"""

import os

from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, Request, Response

from app.db.mongodb_handler import connect_db
from app.utils.api_response import ApiResponse


load_dotenv()

client, database, user_collection = connect_db()

ACCESS_TOKEN_SECRET = os.environ['ACCESS_TOKEN_SECRET']
ACCESS_TOKEN_EXPIRY = os.environ['ACCESS_TOKEN_EXPIRY_DAY']
REFRESH_TOKEN_SECRET = os.environ['REFRESH_TOKEN_SECRET']
REFRESH_TOKEN_EXPIRY = os.environ['REFRESH_TOKEN_EXPIRY_DAY']

def generate_access_token(user: dict) -> str:
    """
    Generates an access token for the user.

    Args:
        user (dict): The user data containing the user's ID, username, email, and full name.

    Returns:
        str: The generated access token in JWT format.

    Raises:
        HTTPException: If there is an error while generating the token.
    """
    try:
        payload = {
            "_id": str(user.get("_id")),
            "username": user.get("username"),
            "email": user.get("email"),
            "fullName": user.get("fullName"),
            "exp": int((datetime.now(timezone.utc)+timedelta(days=int(ACCESS_TOKEN_EXPIRY))).timestamp())
        }

        access_token = jwt.encode(payload, ACCESS_TOKEN_SECRET, algorithm="HS256")
        return access_token
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Ërror while generating access token: {err}") from err

def generate_refresh_token(user: dict) -> str:
    """
    Generates a refresh token for the user.

    Args:
        user (dict): The user data containing the user's ID.

    Returns:
        str: The generated refresh token in JWT format.

    Raises:
        HTTPException: If there is an error while generating the token.
    """
    try:
        payload = {
            "_id": str(user.get("_id")),
            "exp": int((datetime.now(timezone.utc)+timedelta(days=int(REFRESH_TOKEN_EXPIRY))).timestamp())
        }
        refresh_token = jwt.encode(payload, REFRESH_TOKEN_SECRET, algorithm="HS256")

        return refresh_token
    except Exception as err:
        raise HTTPException(status_code=500,detail=f"Error while generating refresh token: {err}" ) from err

def generate_access_and_refresh_token(user_id: str) -> tuple:
    """
    Generates both access and refresh tokens for a user.

    Args:
        user_id (str): The user's unique ID.

    Returns:
        tuple: A tuple containing the generated access token and refresh token.

    Raises:
        HTTPException: If there is an error while generating the tokens.
    """
    try:
        user = user_collection.find_one({"_id":user_id})
        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)

        return access_token, refresh_token

    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Something went wrong while generating refresh and access token{err}") from err

def refresh_access_token(request: Request, response: Response) -> ApiResponse:
    """
    Refreshes the access token using the provided refresh token.

    Args:
        request (Request): The request object containing the user's refresh token.
        response (Response): The response object to set new cookies for the access and refresh tokens.

    Returns:
        Api_Response: An API response object containing the new access and refresh tokens.

    Raises:
        HTTPException: If the refresh token is invalid, expired, or missing.
    """
    incoming_refresh_token = request.cookies.get("refreshToken") or request.body.get("refreshToken")
    
    if not incoming_refresh_token:
        raise HTTPException(status_code=401, detail="unauthorized request")

    try:
        decoded_token = jwt.decode(incoming_refresh_token, REFRESH_TOKEN_SECRET, algorithms="HS256")

        user = user_collection.find_one({"_id": decoded_token.get("_id")})

        if not user:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if incoming_refresh_token!= user.get("refreshToken"):
            raise HTTPException(status_code=401, detail="Refresh token is expired or used")

        access_token, refresh_token = generate_access_and_refresh_token(user)

        response.set_cookie("accessToken", value=access_token, httponly=True, secure=True)
        response.set_cookie("refreshToken", value=refresh_token, httponly=True, secure=True)
        return ApiResponse(
            200,
            {
                "accessToken":access_token, "refreshToken": refresh_token
            },
            "Access token refreshed"
        )

    except Exception as err:
        raise HTTPException(status_code=401, detail=f"Invalid refresh token {err}") from err
