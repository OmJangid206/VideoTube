"""
auth_middlewares.py

This module provides JWT authentication middleware for verifying access tokens in 
requests. It decodes the token from cookies or the Authorization header, validates it, 
and retrieves the corresponding user from MongoDB.

The `verify_jwt` method is used to authenticate requests.
"""

import os
import jwt

from dotenv import load_dotenv
from bson import ObjectId

from fastapi import Request, HTTPException
from app.db.mongodb_handler import connect_db

ACCESS_TOKEN_SECRET = os.environ['ACCESS_TOKEN_SECRET']
client, database, user_collection = connect_db()
load_dotenv()

def veryfy_jwt(request: Request) -> None:
    """
    Verifies the access token in the request's cookies or Authorization header. 
    Decodes and validates the token, retrieves the corresponding user from the database, 
    and adds the user to the request state. 

    Args:
        request (Request): The FastAPI request containing the JWT.

    Returns:
        None: Sets the user in `request.state.user` if the token is valid.
    """
    try:
        token = request.cookies.get("accessToken") or request.headers.get("Authorization")

        # print(f"token: {token}")
        if token.startswith("Bearer "):
            token = token.replace("Bearer ", "")

        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized request")

        decoded_token = jwt.decode(token, ACCESS_TOKEN_SECRET, algorithms=["HS256"])
        # print(f"decoded_token: {decoded_token}")

        user_id = decoded_token.get("_id")
        # print(f"user_id: {user_id}")

        user = user_collection.find_one({"_id": ObjectId(user_id)}, {"password": 0, "refreshToken": 0})
        # print(f"üser: {user}")

        if not user:
            raise HTTPException(status_code=401, detail="Invalid access token")

        request.state.user = user

    except Exception as err:
        raise HTTPException(status_code=401, detail=f"Invalid access token: {err}") from err
