"""
Custom exceptions for YKGen.

This module defines specific exception types for better error handling
and debugging throughout the application.
"""


class YKGenError(Exception):
    """Base exception class for YKGen-related errors."""
    
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class ConfigurationError(YKGenError):
    """Raised when there are configuration issues."""
    pass


class APIKeyError(ConfigurationError):
    """Raised when API key is missing or invalid."""
    pass


class ComfyUIError(YKGenError):
    """Raised when ComfyUI operations fail."""
    pass


class ComfyUIConnectionError(ComfyUIError):
    """Raised when unable to connect to ComfyUI server."""
    pass


class ComfyUIWorkflowError(ComfyUIError):
    """Raised when ComfyUI workflow execution fails."""
    pass


class VideoGenerationError(YKGenError):
    """Raised when video generation fails."""
    pass


class VideoAPIError(VideoGenerationError):
    """Raised when video API requests fail."""
    pass


class VideoTimeoutError(VideoGenerationError):
    """Raised when video generation times out."""
    pass


class AudioGenerationError(YKGenError):
    """Raised when audio generation fails."""
    pass


class AudioWorkflowError(AudioGenerationError):
    """Raised when audio workflow execution fails."""
    pass


class StoryGenerationError(YKGenError):
    """Raised when story generation fails."""
    pass


class LLMError(StoryGenerationError):
    """Raised when LLM operations fail."""
    pass


class FileOperationError(YKGenError):
    """Raised when file operations fail."""
    pass


class WorkflowError(YKGenError):
    """Raised when workflow execution fails."""
    pass


class ValidationError(YKGenError):
    """Raised when input validation fails."""
    pass


class RetryExhaustedError(YKGenError):
    """Raised when retry attempts are exhausted."""
    
    def __init__(self, operation: str, max_retries: int, last_error: Exception = None):
        self.operation = operation
        self.max_retries = max_retries
        self.last_error = last_error
        message = f"Operation '{operation}' failed after {max_retries} retries"
        if last_error:
            message += f". Last error: {last_error}"
        super().__init__(message)