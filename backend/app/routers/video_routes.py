from fastapi import APIRouter

from app.controllers.video_controller import publish_video
from app.controllers.video_controller import get_all_videos
from app.controllers.video_controller import get_video_by_id
from app.controllers.video_controller import delete_video
from app.controllers.video_controller import update_video
from app.controllers.video_controller import toggle_publish_status


router = APIRouter()

@router.post("/")
async def publish_video_route():
    return await publish_video()


@router.get("/")
async def get_all_videos_route():
    return await get_all_videos()


@router.get("/{videoId}")
async def get_video_by_id_route():
    return await get_video_by_id()


@router.delete("/{videoId}")
async def delete_video_route():
    return await delete_video()


@router.patch("/{videoId}")
async def update_video_route():
    return await update_video()


@router.patch("/toggle/publish/{videoId}")
async def toggle_publish_status_route():
    return await toggle_publish_status()

# videotube.com/api/v1/videos POST method
# videotube.com/api/v1/videos GET method
# videotube.com/api/v1/videos/video=video_id GET method
# videotube.com/api/v1/videos/video=video_id PATCH method
# videotube.com/api/v1/videos/video=video_id PATCH method
