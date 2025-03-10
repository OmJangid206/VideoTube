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

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12, deprecated="auto")

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


async def register_user(
        request: Request, 
        avatar: UploadFile = File(...), cover_image: 
        Optional[UploadFile] = File(None, alias="coverImage")) -> ApiResponse:
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


async def change_password(request: Request) -> ApiResponse:

    request_body= await request.json()

    if not all([request_body.get("oldPassword"),request_body.get("newPassword"), request_body.get("confirmPassword")]):
        raise HTTPException(status_code=400, detail="All fields are required")

    if request_body.get("newPassword") != request_body.get("confirmPassword"):
        raise HTTPException(status_code=400, detail="New password and confirmation do not match")
        
    if request_body.get("oldPassword") == request_body.get("newPassword"):
        raise HTTPException(status_code=400, detail="New Password cannot be same as old Password")
    
    client, database, collection  = connect_db()
    user_collection = collection

    user = user_collection.find_one(
        {"_id": ObjectId(request.state.user.get("_id"))}
    )

    is_validate_password = is_password_correct(request_body.get("oldPassword"),user.get("password"))

    if not is_validate_password:
        raise HTTPException(status_code=401, detail="Incorrect old password. Please try again.")

    user_collection.find_one_and_update(
        {"_id": user.get("_id")},
        {"$set": {"password": hash_password(request_body.get("newPassword"))}}
    )

    return ApiResponse(
        200,
        {},
        "password updated successfully."
    )

    # validate Fields
    # check old password exists 
    # compaire new password with old passowrd 
    # passowrd1 and passowrd1 should be same 
    # update password with new password

    # vailidate email
    # find the user by email sotre token for passwrod token with expiration
    # send the email for change the password with token
    # click on email redirect on change-password path find user by token also validate if expire or not
    # find the user by token update the password with new one when submit and also delete token in db one updated password


async def get_current_user(request: Request) -> ApiResponse:

    # find the user in db by username
    # return ApiResponse

    current_user = {
        "username": request.state.user.get("username"),
        "email": request.state.user.get("email"),
        "avatar": request.state.user.get("avatar"),
        "coverImage": request.state.user.get("coverImage"),
    }

    return ApiResponse(
        200,
        current_user,
        "User fetched Successfully."
    )


async def update_account_details(request: Request) -> ApiResponse:
    
    # validate Fields 
    # find by userid and update in db
    # return updated Data 

    request_body = await request.json()

    if not all([request_body.get("fullName"),request_body.get("email")]):
        raise HTTPException(status_code=400, detail="All fields are required")

    client, database, collection  = connect_db()
    user_collection = collection

    user = user_collection.find_one_and_update(
        {"_id": ObjectId(request.state.user.get("_id"))},
        {"$set": {"fullName": request_body.get("fullName"), "email": request_body.get("email")}}
    )
    
    updated_user = {
        "username": user.get("username"),
        "email": user.get("email"),
        "avatar": user.get("avatar"),
        "coverImage": user.get("coverImage"),
    }  

    return ApiResponse(
        200,
        updated_user,
        "Account details updated successfully"
    )


async def update_avatar(request: Request, avatar: UploadFile = File(...)) -> ApiResponse:
    
    client, database, collection  = connect_db()
    user_collection = collection

    if not avatar.filename:
        raise HTTPException(status_code=401, detail="Avatar file is missing")
    
    if not os.path.exists("public/temp"):
        os.mkdir("public/temp")
    avatar_path = f"public/temp{avatar.filename}"
    with open(avatar_path, "wb") as file:
        file.write(await avatar.read())

    avatar_url = upload_on_cloudinary(avatar_path)

    if not avatar_url:
        raise HTTPException(status_code=401,detail="Error while uploading on avatar" )
    
    user = user_collection.find_one_and_update(
        {"_id": ObjectId(request.state.user.get("_id"))},
        {"$set": {"avatar":avatar_url.get('url')}}
    )
    
    updated_user = {
        "username": user.get("username"),
        "email": user.get("email"),
        "avatar": user.get("avatar"),
        "coverImage": user.get("coverImage"),
    }  

    return ApiResponse(
        200,
        updated_user,
        "Avatar image updated successfully"
    )


async def update_cover_image(request: Request, cover_image: UploadFile = File(...)) -> ApiResponse:
    
    # validate Fields
    # find in db 
    # save in folder path 
    # upload in cloudinary
    # return with updated user

    if not cover_image:
        raise HTTPException(status_code=401, detail="cover image file is missing")
    
    client, database, collection = connect_db()
    user_collection = collection

    if not os.path.exists("public/temp"):
        os.mkdir("public/temp")

    cover_image_path  = f"public/temp/{cover_image.filename}"
    with open(cover_image_path, "wb") as file:
        file.write(await cover_image.read())

    cover_image_url = upload_on_cloudinary(cover_image_path)

    if not cover_image_url:
        raise HTTPException(status_code=401, detail="Error while uploading on cover image")

    user = user_collection.find_one_and_update(
        {"_id": ObjectId(request.state.user.get("_id"))},
        {"$set": {"coverImage": cover_image_url.get('url')}}
    )

    updated_user = {
        "username": user.get("username"),
        "email": user.get("email"),
        "avatar": user.get("avatar"),
        "coverImage": user.get("coverImage"),
    }  

    return ApiResponse(
        200,
        updated_user,
        "Cover image updated successfully"
    )


async def get_user_channel_profile(username: str, request: Request) -> ApiResponse:
    # get the param username
    # find by username

    if not username.strip():
        raise HTTPException(status_code=400, detail="Username is missing")
    
    # Connect to the database
    client, database, collection = connect_db()
    user_collection = database["users"]
    subscriptions_collection = database["subscriptions"]

    # Perform aggregation
    channel = user_collection.aggregate([
        {
            "$match": {
                "username": username.lower()
            }
        },
        {
            "$lookup": {
                "from": "subscriptions",
                "localField": "_id",
                "foreignField": "channel",
                "as": "subscribers"
            }
        },
        {
            "$lookup": {
                "from": "subscriptions",
                "localField": "_id",
                "foreignField": "subscriber",
                "as": "subscribedTo"
            }
        },
        {
            "$addFields": {
                "subscribersCount": {
                    "$size": "$subscribers"
                },
                "channelsSubsribedToCount": {
                    "$size": "$subscribedTo",
                },
                "isSubscribed": {
                    "$cond": {
                        "if": {
                            "$in": { [ObjectId(request.state.user["_id"]), "subscribers.subscriber"] 
                            },
                        "then": True,
                        "else": False
                        }
                    }
                }
            }
        },
        {
            "$project": {
                "fullName": 1,
                "username": 1,
                "subscribersCount": 1,
                "channelsSubsribedToCount": 1,
                "avatar": 1,
                "coverImage": 1,
                "email": 1

            }
        }
    ])

    # channel = list(user_collection.aggregate(pipeline))

    if not channel:
        raise HTTPException(status_code=404, detail="Chnannel does not exist")
    
    return ApiResponse(
        status_code=200,
        data=channel,
        message="User channel fetched successfully"
    )


async def get_user_watch_history():
    pass


# update_password
# get_current_user
# get_user_channel_profile
# update_avatar
# update_cover_image
# update_user_account_details
# get_user_watch_history

