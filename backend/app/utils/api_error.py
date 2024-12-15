"""
api_error.py

This module defines a custom exception class for handling API-related errors.
"""

import traceback

class ApiError(Exception):
    """
    ApiError: Custom exception class for handling API errors.

    Attributes:
        status_code (int): HTTP status code for the error.
        message (str): Error message.
        success (bool): Indicates whether the operation was successful (always False for errors).
        errors (list): A list of additional error details.
        stack (str): The stack trace of the error, captured automatically if not provided.

    Methods:
        _capture_stack(): Captures the current stack trace if no custom stack is provided.
    """

    def __init__(self, status_code: int, message: str = "Somthing went wrong", errors: list = None, stack: str = ""):

        """
        Initializes the ApiError with the provided status code, message, 
        errors, and optional stack trace.
        """
        if errors is None:
            errors = []
        super().__init__(message)
        self.status_code = status_code
        self.data = None
        self.message = message
        self.success = False
        self.errors = errors

        if stack:
            self.stack = stack
        else:
            self.stack = self._capture_stack()

    def _capture_stack(self) -> str:
        """ Capture the current stack trace if no custom stack is provided. """
        return "\n".join(traceback.format_stack())
