"""
Utility functions for KGen.

This module contains common utility functions used throughout the application,
including retry logic, validation helpers, and file operations.
"""

import functools
import os
import time
import uuid
from datetime import datetime
from typing import Any, Callable, List, Optional, TypeVar

from kgen.config.constants import FileDefaults, GenerationLimits
from kgen.config.exceptions import FileOperationError, RetryExhaustedError, ValidationError

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = GenerationLimits.MAX_RETRIES,
    delay: float = GenerationLimits.RETRY_DELAY_SECONDS,
    exponential: bool = False,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator for retrying functions with configurable backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        exponential: Whether to use exponential backoff
        exceptions: Tuple of exceptions to catch and retry on
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        break
                        
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    
                    if exponential:
                        current_delay *= 2
                        
            raise RetryExhaustedError(
                operation=func.__name__,
                max_retries=max_retries,
                last_error=last_exception
            )
            
        return wrapper
    return decorator


def validate_file_exists(file_path: str, description: str = "File") -> None:
    """
    Validate that a file exists.
    
    Args:
        file_path: Path to the file
        description: Description of the file for error messages
        
    Raises:
        ValidationError: If file doesn't exist
    """
    if not os.path.exists(file_path):
        raise ValidationError(f"{description} not found: {file_path}")


def validate_directory_exists(dir_path: str, create: bool = False) -> str:
    """
    Validate that a directory exists, optionally creating it.
    
    Args:
        dir_path: Path to the directory
        create: Whether to create the directory if it doesn't exist
        
    Returns:
        The validated directory path
        
    Raises:
        ValidationError: If directory doesn't exist and create=False
    """
    if not os.path.exists(dir_path):
        if create:
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"Created directory: {dir_path}")
            except OSError as e:
                raise FileOperationError(f"Failed to create directory {dir_path}: {e}")
        else:
            raise ValidationError(f"Directory not found: {dir_path}")
    
    return dir_path


def generate_output_directory(base_dir: str = "output") -> str:
    """
    Generate a unique output directory name with timestamp.
    
    Args:
        base_dir: Base directory for output
        
    Returns:
        Path to the generated directory
    """
    timestamp = datetime.now().strftime(FileDefaults.TIMESTAMP_FORMAT)
    unique_suffix = str(uuid.uuid4())[:8]
    
    output_dir = f"{base_dir}/{timestamp}_images4story_{unique_suffix}"
    return validate_directory_exists(output_dir, create=True)


def safe_file_operation(operation: Callable[[], T], description: str) -> T:
    """
    Safely execute a file operation with proper error handling.
    
    Args:
        operation: Function to execute
        description: Description of the operation for error messages
        
    Returns:
        Result of the operation
        
    Raises:
        FileOperationError: If the operation fails
    """
    try:
        return operation()
    except (OSError, IOError) as e:
        raise FileOperationError(f"Failed to {description}: {e}")


def calculate_file_size_mb(file_path: str) -> float:
    """
    Calculate file size in megabytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in MB rounded to 1 decimal place
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / FileDefaults.MB_DIVISOR, 1)
    except OSError:
        return 0.0


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "2m 30s")
    """
    if seconds < 60:
        return f"{seconds}s"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s" if remaining_seconds > 0 else f"{minutes}m"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    parts = [f"{hours}h"]
    if remaining_minutes > 0:
        parts.append(f"{remaining_minutes}m")
    if remaining_seconds > 0:
        parts.append(f"{remaining_seconds}s")
    
    return " ".join(parts)


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length with optional suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def validate_positive_integer(value: Any, name: str, minimum: int = 1) -> int:
    """
    Validate that a value is a positive integer.
    
    Args:
        value: Value to validate
        name: Name of the parameter for error messages
        minimum: Minimum allowed value
        
    Returns:
        Validated integer value
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        int_value = int(value)
        if int_value < minimum:
            raise ValidationError(f"{name} must be at least {minimum}, got {int_value}")
        return int_value
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be an integer, got {type(value).__name__}")


def batch_process(
    items: List[T],
    processor: Callable[[T], Any],
    batch_size: int = 5,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[Any]:
    """
    Process items in batches with optional progress reporting.
    
    Args:
        items: List of items to process
        processor: Function to process each item
        batch_size: Number of items to process at once
        progress_callback: Optional callback for progress updates
        
    Returns:
        List of processed results
    """
    results = []
    total_items = len(items)
    
    for i in range(0, total_items, batch_size):
        batch = items[i:i + batch_size]
        
        for item in batch:
            try:
                result = processor(item)
                results.append(result)
            except Exception as e:
                print(f"Error processing item: {e}")
                results.append(None)
        
        if progress_callback:
            completed = min(i + batch_size, total_items)
            progress_callback(completed, total_items)
    
    return results


def clean_filename(filename: str) -> str:
    """
    Clean a filename by removing or replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename safe for filesystem use
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    cleaned = filename
    
    for char in invalid_chars:
        cleaned = cleaned.replace(char, '_')
    
    # Remove extra spaces and dots
    cleaned = ' '.join(cleaned.split())  # Normalize whitespace
    cleaned = cleaned.strip('. ')  # Remove leading/trailing dots and spaces
    
    return cleaned or "untitled"


def ensure_file_extension(filename: str, extension: str) -> str:
    """
    Ensure a filename has the correct extension.
    
    Args:
        filename: Original filename
        extension: Desired extension (with or without leading dot)
        
    Returns:
        Filename with correct extension
    """
    if not extension.startswith('.'):
        extension = '.' + extension
    
    if not filename.lower().endswith(extension.lower()):
        return filename + extension
    
    return filename 