"""
Custom exceptions for KGen.

This module defines specific exception types for better error handling
and debugging throughout the application.
"""


class KGenError(Exception):
    """Base exception class for KGen-related errors."""
    
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class ConfigurationError(KGenError):
    """Raised when there are configuration issues."""
    pass


class APIKeyError(ConfigurationError):
    """Raised when API key is missing or invalid."""
    pass


class ComfyUIError(KGenError):
    """Raised when ComfyUI operations fail."""
    pass


class ComfyUIConnectionError(ComfyUIError):
    """Raised when unable to connect to ComfyUI server."""
    pass


class ComfyUIWorkflowError(ComfyUIError):
    """Raised when ComfyUI workflow execution fails."""
    pass


class VideoGenerationError(KGenError):
    """Raised when video generation fails."""
    pass


class VideoAPIError(VideoGenerationError):
    """Raised when video API requests fail."""
    pass


class VideoTimeoutError(VideoGenerationError):
    """Raised when video generation times out."""
    pass


class AudioGenerationError(KGenError):
    """Raised when audio generation fails."""
    pass


class AudioWorkflowError(AudioGenerationError):
    """Raised when audio workflow execution fails."""
    pass


class StoryGenerationError(KGenError):
    """Raised when story generation fails."""
    pass


class LLMError(StoryGenerationError):
    """Raised when LLM operations fail."""
    pass


class FileOperationError(KGenError):
    """Raised when file operations fail."""
    pass


class WorkflowError(KGenError):
    """Raised when workflow execution fails."""
    pass


class ValidationError(KGenError):
    """Raised when input validation fails."""
    pass


class RetryExhaustedError(KGenError):
    """Raised when retry attempts are exhausted."""
    
    def __init__(self, operation: str, max_retries: int, last_error: Exception = None):
        self.operation = operation
        self.max_retries = max_retries
        self.last_error = last_error
        message = f"Operation '{operation}' failed after {max_retries} retries"
        if last_error:
            message += f". Last error: {last_error}"
        super().__init__(message) 