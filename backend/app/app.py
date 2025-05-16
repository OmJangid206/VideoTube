"""
app.py

This module initializes the FastAPI app, imports necessary routes, and includes
the user-related routes under the `/api/v1/users` prefix.

Routes:
    - User-related endpoints are included from `user_routes` under the prefix `/api/v1/users`.

Modules:
    - FastAPI: The web framework for creating the application.
    - ApiError: Custom error handling for the application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.utils.api_error import ApiError

from app.routers.user_routes import router as user_router
from app.routers.video_routes import router as video_router

# Initialize FastAPI app
app = FastAPI()

# # custom Exception
# @app.exception_handler(ApiError)
# async def api_error_handler(request: Request, exc: ApiError):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={
#             "success": exc.success,
#             "message": exc.message,
#             "errors": exc.errors,
#             "stack": exc.stack
#         },
#     )

# middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routes declaration
app.include_router(user_router, prefix="/api/v1/users")
app.include_router(video_router, prefix="/api/v1/videos")
