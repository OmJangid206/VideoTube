"""
user_controller.py

This module manages user authentication and profile management, including:
- User registration, login, and logout functionalities
- Password hashing and verification
- User data validation
- File uploads to Cloudinary
- Token generation and cookie management
"""

import os
from typing import Optional
from fastapi import HTTPException, Request, Response, UploadFile, File
from passlib.context import CryptContext
from bson import ObjectId
import httpx

from app.db.mongodb_handler import connect_db
from app.utils.cloudinary import upload_on_cloudinary
from app.utils.api_response import ApiResponse

from app.models.user_models import generate_access_and_refresh_token

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12, deprecated="auto")

def convert_formdata_to_json(form_data):
    """
    Args:
        form_data (FormData): Incoming form data to be converted.

    Returns:
        dict: A dictionary representation of the form data.
    """
    form_data_dict = {}
    for key, value in form_data.items():
        form_data_dict[key] = value
    return form_data_dict


def hash_password(password):
    """
    Args:
        password (str): The plain-text password to be hashed.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def is_password_correct(password, hashed_password):
    """
    Args:
        password (str): The plain-text password to verify.
        hashed_password (str): The previously hashed password to compare against.

    Returns:
        bool: True if passwords match, False otherwise.
    """
    return pwd_context.verify(password, hashed_password)


async def register_user(
        request: Request, 
        avatar: UploadFile = File(...), cover_image: 
        Optional[UploadFile] = File(None, alias="coverImage")) -> ApiResponse:
    """
    Workflow:
    1. Validates all required user fields
    2. Checks for existing users with same username or email
    3. Uploads avatar and optional cover image to Cloudinary
    4. Hashes user password
    5. Creates user record in database
    6. Returns user details (excluding sensitive information)

    Args:
        request (Request): The HTTP request containing user registration details.
        avatar (UploadFile): Required avatar image file for the user.
        cover_image (Optional[UploadFile], optional): Optional cover image for user profile.

    Returns:
        ApiResponse: Response containing registered user details and success message.
    """

    # initialization collection
    client, database = connect_db()
    users_collection = database["users"]

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
    Workflow:
    1. Validates login credentials (username or email)
    2. Verifies user existence
    3. Checks password correctness
    4. Generates access and refresh tokens
    5. Sets HTTP-only, secure cookies
    6. Returns user details and tokens

    Args:
        request (Request): The HTTP request containing login credentials.
        response (Response): HTTP response for setting authentication cookies.

    Returns:
        ApiResponse: Response with user details, access token, and refresh token.
    """

    request = await request.json()

    if not (request.get("username") or request.get("email")):
        raise HTTPException(400, detail="username or email is required")

    client, database = connect_db()
    user_collection = database["users"]

    user = user_collection.find_one({
        "$or":[{"username": request.get("username")}, {"email": request.get("email")}]
    })

    if not user:
        raise HTTPException(404, detail="User does not exist")

    is_validate_password = is_password_correct(request.get("password"), user.get("password"))
    if not is_validate_password:
        raise HTTPException(401, detail="Invalid user credentials")

    access_token, refresh_token = generate_access_and_refresh_token(user.get("_id"))

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
    Workflow:
    1. Removes refresh token from user record
    2. Deletes access and refresh token cookies

    Args:
        request (Request): The HTTP request with logged-in user's context.
        response (Response): HTTP response for deleting authentication cookies.

    Returns:
        ApiResponse: Confirmation of successful logout.
    """
    client, database = connect_db()
    user_collection = database["users"]
    
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
    """
    Workflow:
    1. Validates all password change fields
    2. Ensures new password differs from old password
    3. Verifies current password
    4. Updates password with new hashed password

    Args:
        request (Request): HTTP request containing password change details.

    Returns:
        ApiResponse: Confirmation of successful password update.
    """
    request_body= await request.json()

    if not all([request_body.get("oldPassword"),request_body.get("newPassword"), request_body.get("confirmPassword")]):
        raise HTTPException(status_code=400, detail="All fields are required")

    if request_body.get("newPassword") != request_body.get("confirmPassword"):
        raise HTTPException(status_code=400, detail="New password and confirmation do not match")
        
    if request_body.get("oldPassword") == request_body.get("newPassword"):
        raise HTTPException(status_code=400, detail="New Password cannot be same as old Password")
    
    client, database  = connect_db()
    user_collection = database["users"]

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


async def get_current_user(request: Request) -> ApiResponse:
    """
    Retrieve the current authenticated user's profile information.

    This function extracts key user details from the authenticated request,
    providing a secure way to fetch the current user's profile without 
    exposing sensitive information.

    Args:
        request (Request): HTTP request with user authentication context.
            Contains user information in the request state.

    Returns:
        ApiResponse: A response object containing:
    """
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
    """
    Update the user's account details, including full name and email.

    This function validates and updates the user's account information 
    in the database, ensuring all required fields are present.

    Args:
        request (Request): HTTP request containing updated account details.
            Expected to have a JSON body with 'fullName' and 'email'.

    Returns:
        ApiResponse: A response object containing:
    """
    request_body = await request.json()

    if not all([request_body.get("fullName"),request_body.get("email")]):
        raise HTTPException(status_code=400, detail="All fields are required")

    client, database  = connect_db()
    user_collection = database["users"]

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
    """
    Update the user's profile avatar image.

    Handles avatar image upload process:
    1. Validates avatar file
    2. Saves file to temporary directory
    3. Uploads to Cloudinary
    4. Updates user's avatar in database

    Args:
        request (Request): HTTP request with user authentication context.
        avatar (UploadFile): New avatar image file to be uploaded.
            Defaults to File(...) which requires a file to be present.

    Returns:
        ApiResponse: A response object containing:
    """
    client, database = connect_db()
    user_collection = database["users"]

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
    """
    Update the user's profile cover image.

    Handles cover image upload process:
    1. Validates cover image file
    2. Saves file to temporary directory
    3. Uploads to Cloudinary
    4. Updates user's cover image in database

    Args:
        request (Request): HTTP request with user authentication context.
        cover_image (UploadFile): New cover image file to be uploaded.
            Defaults to File(...) which requires a file to be present.

    Returns:
        ApiResponse: A response object containing:
    """
    if not cover_image:
        raise HTTPException(status_code=401, detail="cover image file is missing")
    
    client, database = connect_db()
    user_collection = database["users"]

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
    """
    Retrieve a user's channel profile with comprehensive subscription information.

    Performs a complex aggregation to fetch user profile details, 
    including subscriber and subscription metrics.

    Args:
        username (str): The username of the channel to retrieve.
        request (Request): HTTP request with user authentication context.

    Returns:
        ApiResponse: A response object containing:
    """
    if not username.strip():
        raise HTTPException(status_code=400, detail="Username is missing")
    
    # Connect to the database
    client, database = connect_db()
    user_collection = database["users"]
    # subscriptions_collection = database["subscriptions"]

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
                        "if": { "$in": [ObjectId(request.state.user["_id"]), "$subscribers.subscriber"] },
                        "then": True,
                        "else": False
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
    channel = list(channel)
    user_id = channel[0].get('_id')
    channel[0]['_id'] = str(user_id)

    if not channel:
        raise HTTPException(status_code=404, detail="Chnannel does not exist")
    
    return ApiResponse(
        status_code=200,
        data=channel,
        message="User channel fetched successfully"
    )


async def get_user_watch_history(request: Request) -> ApiResponse:
    """
    Retrieve the authenticated user's watch history with detailed video information.

    Performs an aggregation to fetch watch history, including:
    - Watched videos
    - Detailed video owner information

    Args:
        request (Request): HTTP request with user authentication context.

    Returns:
        ApiResponse: A response object containing:
    """
    client, database = connect_db()
    user_collection = database["users"]

    user = user_collection.aggregate([
        {
            "$match": {
                "_id": request.state.user["_id"]
            }
        },
        {
            "$lookup": {
                "from": "videos",
                "localField": "watchHistory",
                "foreignField": "_id",
                "as": "watchHistory",
                "pipeline": [
                    {
                        "$lookup": {
                            "from": "users",
                            "localField": "owner",
                            "foreignField": "_id", 
                            "as": "owner",
                            "pipeline": [
                                {
                                    "$project": {
                                        "fullName": 1,
                                        "username": 1,
                                        "avatar": 1
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "$addFields": {
                            "owner": {
                                "$first": "$owner"
                            }
                        }
                    }
                ]
            }
        }
    ])

    user = list(user)
    user_id = user[0].get('_id')
    user[0]['_id'] = str(user_id)

    return ApiResponse(
        status_code=200,
        data=user,
        message="User watchHistory fetched successfully"
    )

GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
#################################################
async def google_login(request: Request, response: Response):
    data = await request.json()
    token = data.get("id_token")  # frontend sends Google ID token here
    print(f"token,: {token}")
    # Verify token with Google
    google_resp = httpx.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}")
    payload = google_resp.json()

    if payload.get("aud") != GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=400, detail="Invalid Google Client ID")

    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email not found in token")

    client, database = connect_db()
    user_collection = database["users"]

    user = user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")

    # generate your tokens for the user (no password check here)
    access_token, refresh_token = generate_access_and_refresh_token(user.get("_id"))


    logged_in_user = user_collection.find_one({"_id": user.get("_id")}, {"password":0, "refreshToken":0})
    logged_in_user["_id"] = str(logged_in_user["_id"])
    
    # set cookies and respond
    response.set_cookie("accessToken", value=access_token, httponly=True, secure=False)
    response.set_cookie("refreshToken", value=refresh_token, httponly=True, secure=False)

    # user["_id"] = str(user["_id"])
    # user.pop("password", None)
    # user.pop("refreshToken", None)

    return ApiResponse(
        200,
        {
            "user": logged_in_user,
            "accessToken": access_token,
            "refreshToken": refresh_token,
        },
        "User logged in via Google successfully"
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

####################################
# Watchhistory
# user collection
# username | _id | watchhistory | 
# om       | 1   | video_1      | 
# om       | 1   | video_2      | 
# om       | 1   | video_3      |

# video_1 = {
#     "ower": "_id",
#     "username" = "username",
#     "name" = "name"
#   "avatar_img": "avatarImg"
# }

# update_password
# get_current_user
# get_user_channel_profile
# update_avatar
# update_cover_image
# update_user_account_details
# get_user_watch_history

# users collection
# | username | _id | other_details |
# | om       | 1   | xyz           |
# | dev      | 2   | abc           |
# | ashok    | 3   | xyz           |

# subscriptions collection
#  | channel   | subscriber  |
#  | 1 (om)    | 2 (dev)     |
#  | 1 (om)    | 3 (ashok)   |
#  | 2 (dev)   | 1 (om)      |
#  | 3 (ashok) | 1 (om)      |
#  | 2 (dev)   | 1 (om)      |
#  | 2 (dev)   | 1 (ashok)   |
####################################