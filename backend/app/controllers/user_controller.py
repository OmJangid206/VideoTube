"""
user_controller.py

This module handles user registration, login, and logout functionality, including password hashing, 
user validation, file uploads to Cloudinary, token generation, and cookie management.
"""

import os
from typing import Optional
from fastapi import HTTPException, Request, Response, UploadFile, File
from passlib.context import CryptContext
from bson import ObjectId

from app.db.mongodb_handler import connect_db
from app.utils.cloudinary import upload_on_cloudinary
from app.utils.api_response import ApiResponse

from app.models.user_models import generate_access_and_refresh_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def convert_formdata_to_json(form_data):
    """
    Converts form data to a dictionary.
    """
    form_data_dict = {}
    for key, value in form_data.items():
        form_data_dict[key] = value
    return form_data_dict

def hash_password(password):
    """
    Hashes the provided password using bcrypt.
    """
    return pwd_context.hash(password)

def is_password_correct(password, hashed_password):
    """
    Verifies if the provided password matches the hashed password.
    """
    return pwd_context.verify(password, hashed_password)

async def register_user(request: Request, avatar: UploadFile = File(...), cover_image: Optional[UploadFile] = File(None)) -> ApiResponse:
    """
    Registers a new user, validates input, checks for existing users, uploads files to Cloudinary,
    and saves the user to the database.

    Args:
        request (Request): The request object containing user details.
        avatar (UploadFile): The avatar image file.
        cover_image (Optional[UploadFile]): The cover image file.

    Returns:
        ApiResponse: Response object with user data and success message.
    """
    # get user details from frontend
    # validation - not empty
    # check if user already exists: username, email
    # check for images, check for avatar
    # upload them to cloudinary
    # create user object - create entry in db
    # remove password and refresh token field from response
    # check for user creation
    # return response

    # initialization collection
    client, database, collection = connect_db()
    users_collection = collection

    form_data = await request.form()
    request = convert_formdata_to_json(form_data)

    # validation
    if not all([request.get('fullName'), request.get('email'), request.get('username'), request.get('password')]):
        raise HTTPException(status_code=400, detail="All fields are required")

    # check if user already exists
    existed_user = users_collection.find_one({"$or": [{"username": request.get('username')}, {"email": request.get('email')}]})
    if existed_user:
        raise HTTPException(status_code=409, detail="User with email or username already exists")

    # File upload
    if not os.path.exists("public/temp"):
        os.mkdir("public/temp")
    avatar_path  = f"public/temp/{avatar.filename}"
    with open(avatar_path, "wb") as file:
        file.write(await avatar.read())

    if cover_image:
        cover_image_path = f"public/temp/{cover_image.filename}"
        with open(cover_image_path, "wb") as file:
            file.write(await cover_image.read())

    if not avatar_path:
        raise HTTPException(status_code=400, detail="Avatar file is required")

    avatar_url = upload_on_cloudinary(avatar_path)
    cover_image_url = upload_on_cloudinary(cover_image_path) if cover_image else ""

    if not request.get('avatar'):
        raise HTTPException(status_code=400, detail="Avatar file is required")

    # Create user
    user = {
        "fullName": request.get('fullName'),
        "email":request.get('email'),
        "username": request.get('username'),
        "password": hash_password(request.get('password')),
        "avatar": avatar_url.get('url'),
        "coverImage": cover_image_url.get('url') if cover_image_url else None,
    }

    insterd_result = users_collection.insert_one(user)

    created_user = users_collection.find_one({"_id": insterd_result.inserted_id}, {"password": 0, "refreshToken":0})

    if not created_user:
        raise HTTPException(status_code=500, detail="Something went wrong while registering the user")

    # Convert MongoDB ObjectId to string for response
    created_user["_id"] = str(created_user["_id"])

    return ApiResponse(
        status_code = 201,
        data = created_user,
        message="User registered successfully"
    )

async def login_user(request: Request, response: Response) -> ApiResponse:
    """
    Authenticates a user using their username or email and password, and returns access and refresh tokens.

    Args:
        request (Request): The request object containing login credentials.
        response (Response): The response object to set cookies for access and refresh tokens.

    Returns:
        ApiResponse: Response object with user data, access token, and refresh token.
    """
    # validate email username pasword
    # check username or email in db
    # validate password match or not
    # logIn the user and send response

    request = await request.json()

    if not (request.get("username") or request.get("email")):
        raise HTTPException(400, detail="username or email is required")

    client, database, collection = connect_db()
    user_collection = collection

    user = user_collection.find_one({
        "$or":[{"username": request.get("username")}, {"email": request.get("email")}]
    })

    if not user:
        raise HTTPException(404, detail="User does not exist")

    is_validate_password = is_password_correct(request.get("password"), user.get("password"))
    if not is_validate_password:
        raise HTTPException(401, detail="Invalid user credentials")

    access_token, refresh_token= generate_access_and_refresh_token(user.get("_id"))

    logged_in_user = user_collection.find_one({"_id": user.get("_id")}, {"password":0, "refreshToken":0})
    logged_in_user["_id"] = str(logged_in_user["_id"])

    response.set_cookie("accessToken", value=access_token, httponly=True, secure=True)
    response.set_cookie("refreshToken", value=refresh_token, httponly=True, secure=True)

    return ApiResponse(
        200,
        {
            "user": logged_in_user, 
            "accessToken":access_token, 
            "refreshToken":refresh_token,
        },
        "User logged In Successfully"
    )

async def logout_user(request: Request, response: Response) -> ApiResponse:
    """
    Logs out the user by deleting the refresh and access tokens from cookies.

    Args:
        request (Request): The request object containing the logged-in user's data.
        response (Response): The response object to remove cookies.

    Returns:
        ApiResponse: Response object with a success message for logout.
    """
    client, database, collection = connect_db()
    user_collection = collection
    try:
        user_collection.find_one_and_update(
            {"_id": ObjectId(request.state.user.get("_id"))},
            {"$unset": {"refreshToken": ""}}
        )

        response.delete_cookie(key="accessToken")
        response.delete_cookie(key="refreshToken")

        return ApiResponse(
            200,
            {},
            "User logged Out Successfully"
        )

    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error while logout user: {err}") from err
