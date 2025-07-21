"""
Abstract base class for video generation clients.

This module provides common functionality for video generation clients
to ensure consistent behavior across different providers.
"""

import base64
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import requests

from ..console import (
    print_success,
    print_warning,
)
from ykgen.config.config import config
from ykgen.config.constants import VideoDefaults


class BaseVideoClient(ABC):
    """Abstract base class for video generation clients."""

    def __init__(self, api_key: str, base_url: str):
        """
        Initialize the video generation client.

        Args:
            api_key: API key for the video generation service
            base_url: Base URL for the API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.request_kwargs = self._get_request_kwargs()

    def _get_request_kwargs(self) -> Dict:
        """Get request kwargs."""
        return {}

    def _encode_image_to_base64(self, image_path: str) -> str:
        """Encode an image file to base64 string."""
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded}"

    def _get_api_key_display(self) -> str:
        """Get API key display string for logging."""
        show_full_key = os.getenv("YKGEN_DEBUG_KEYS", "false").lower() == "true"
        if show_full_key:
            return self.api_key if self.api_key else "unknown"
        else:
            return f"*{self.api_key[-8:]}" if self.api_key else "unknown"

    def _is_retryable_error(self, error: str) -> bool:
        """Check if an error is retryable."""
        retryable_keywords = [
            "502", "503", "504", "Bad Gateway", "Service Unavailable", 
            "Gateway Timeout", "Connection", "Network", "Timeout", "RequestException"
        ]
        return any(keyword.lower() in error.lower() for keyword in retryable_keywords)

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff."""
        if VideoDefaults.RETRY_EXPONENTIAL_BACKOFF:
            return VideoDefaults.RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
        else:
            return VideoDefaults.RETRY_DELAY_SECONDS

    @abstractmethod
    def submit_video_generation(
        self,
        image_path: str,
        prompt: str,
        **kwargs
    ) -> Optional[str]:
        """
        Submit a video generation request.

        Args:
            image_path: Path to the input image
            prompt: Text prompt for video generation
            **kwargs: Additional parameters specific to the provider

        Returns:
            Request ID if successful, None otherwise
        """
        pass

    @abstractmethod
    def check_video_status(self, request_id: str) -> Dict[str, Any]:
        """
        Check the status of a video generation request.

        Args:
            request_id: The request ID returned by submit_video_generation

        Returns:
            Status response dictionary
        """
        pass

    @abstractmethod
    def wait_and_download_video(
        self,
        request_id: str,
        output_path: str,
        max_wait_time: int = 600,
        check_interval: int = 5,
        scene_name: str = None,
    ) -> bool:
        """
        Wait for video generation to complete and download the result.

        Args:
            request_id: The request ID to monitor
            output_path: Path where to save the video
            max_wait_time: Maximum time to wait in seconds
            check_interval: Interval between status checks in seconds
            scene_name: Optional scene name for better logging

        Returns:
            True if successful, False otherwise
        """
        pass

    def _download_video_from_url(self, video_url: str, output_path: str) -> bool:
        """
        Download video from URL.

        Args:
            video_url: URL of the video to download
            output_path: Path where to save the video

        Returns:
            True if successful, False otherwise
        """
        try:
            video_response = requests.get(video_url, **self.request_kwargs)
            video_response.raise_for_status()

            # Save the video
            with open(output_path, "wb") as f:
                f.write(video_response.content)

            file_size = len(video_response.content) / (1024 * 1024)  # MB
            key_display = self._get_api_key_display()
            print_success(f"Video downloaded successfully using Key {key_display}")
            print_success(f"   └─ Saved to: {output_path} ({file_size:.1f} MB)")
            return True

        except requests.exceptions.RequestException as e:
            print_warning(f"Error downloading video: {e}")
            return False