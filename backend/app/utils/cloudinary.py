"""
cloudinary_upload.py

This module provides a function to upload files to Cloudinary 
and remove local files after successful upload.
"""

import os
import cloudinary
import cloudinary.uploader

from dotenv import load_dotenv

load_dotenv()

# Configuration
cloudinary.config(
    cloud_name = os.environ['CLOUD_NAME'],
    api_key = os.environ['CLOUDINARY_API_KEY'],
    api_secret = os.environ['CLOUDINARY_API_SECRET'],
    secure=True
)

def upload_on_cloudinary(local_file_path: str) -> dict:
    """
    Uploads a file to Cloudinary and deletes the local file if successful.

    Args:
        local_file_path (str): The local file path to upload.

    Returns:
        dict: A response dictionary from Cloudinary containing details 
            about the uploaded file, or None if an error occurred.
    """
    try:
        if not local_file_path:
            return None

        response = cloudinary.uploader.upload(local_file_path, public_id="auto")

        # print(f"file is uploaded on cloudinary: {response["secure_url"]}")
        # Remove the local file after upload, except for '.gitkeep' files
        if not local_file_path.endswith('.gitkeep'):
            os.remove(local_file_path)

        return response

    except Exception as error:
        print(f"Error uploading file: {error}")

        if os.path.exists(local_file_path) and not local_file_path.endswith('.gitkeep'):
            os.remove(local_file_path)
        return None
