from typing import Optional
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime


class VideoSchema(BaseModel):

    video_file: HttpUrl = Field(..., alias="videoFile")
    thumbnail: HttpUrl
    title: str
    description: str
    duration: int = 0
    views: int = 0
    like: int = 0
    dislike: int = 0 
    is_published: bool = Field(default=True, alias="isPublished")
    owner: Optional[str]
    created_at: datetime = Field(default_factory=datetime.now(), frozen=True)
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}











###########################
# Without Pydantic with Pure logic

# from typing import Optional
# from datetime import datetime
# import re

# class Video:
#     def __init__(
#         self,
#         video_file: str,
#         thumbnail: str,
#         title: str,
#         description: str,
#         duration: int = 0,
#         views: int = 0,
#         like: int = 0,
#         dislike: int = 0,
#         is_published: bool = True,
#         owner: Optional[str] = None,
#         created_at: Optional[datetime] = None,
#         updated_at: Optional[datetime] = None,
#     ):
#         # Validate URL fields
#         if not self.is_valid_url(video_file):
#             raise ValueError("Invalid video file URL")
#         if not self.is_valid_url(thumbnail):
#             raise ValueError("Invalid thumbnail URL")

#         # Validate integer fields
#         if not isinstance(duration, int) or duration < 0:
#             raise ValueError("Duration must be a positive integer")
#         if not isinstance(views, int) or views < 0:
#             raise ValueError("Views must be a positive integer")
#         if not isinstance(like, int) or like < 0:
#             raise ValueError("Likes must be a positive integer")
#         if not isinstance(dislike, int) or dislike < 0:
#             raise ValueError("Dislikes must be a positive integer")

#         # Assign attributes
#         self.video_file = video_file
#         self.thumbnail = thumbnail
#         self.title = title
#         self.description = description
#         self.duration = duration
#         self.views = views
#         self.like = like
#         self.dislike = dislike
#         self.is_published = is_published
#         self.owner = owner
#         self.created_at = created_at or datetime.utcnow()
#         self.updated_at = updated_at or datetime.utcnow()

#     @staticmethod
#     def is_valid_url(url: str) -> bool:
#         """Basic URL validation"""
#         url_pattern = re.compile(r'^(https?|ftp):\/\/[^\s/$.?#].[^\s]*$', re.IGNORECASE)
#         return bool(url_pattern.match(url))

#     def to_dict(self):
#         """Convert instance to dictionary for MongoDB insertion"""
#         return {
#             "videoFile": self.video_file,
#             "thumbnail": self.thumbnail,
#             "title": self.title,
#             "description": self.description,
#             "duration": self.duration,
#             "views": self.views,
#             "like": self.like,
#             "dislike": self.dislike,
#             "isPublished": self.is_published,
#             "owner": self.owner,
#             "created_at": self.created_at,
#             "updated_at": self.updated_at,
#         }
