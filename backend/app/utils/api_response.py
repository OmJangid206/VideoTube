"""
api_response.py

This module defines a class for handling API responses.
"""

class ApiResponse:
    """
    ApiResponse: Represents an API response.

    Attributes:
        status_code (int): HTTP status code of the response.
        data (any): Data returned in the response.
        message (str): Message describing the response (default is "Success").
        success (bool): True if the status code is less than 400.

    Methods:
        __init__(self, status_code, data, message="Success"):
            Initializes the ApiResponse instance.
    """

    def __init__(self, status_code: int, data: any, message: str = "Success"):
        """
        Initializes the ApiResponse with status code, data, and message.
        """
        self.status_code = status_code
        self.data = data
        self.message = message
        self.success = status_code < 400
