"""
Configuration module for KGen.

This module handles all configuration settings, environment variables,
and default values used throughout the application.
"""

import os
import requests
import functools
from typing import Optional, Dict, List, Any, TypeVar, Callable
from dataclasses import dataclass
from datetime import datetime

from dotenv import load_dotenv

from kgen.config.constants import (
    AudioDefaults,
    ComfyUIDefaults,
    GenerationLimits,
    NetworkDefaults,
    VideoDefaults,
)

# Load environment variables from .env file
load_dotenv()

# Type variable for generic function
T = TypeVar('T')


def cached_property(func):
    """
    Decorator to cache property values.
    
    Similar to @property but caches the result after first access.
    """
    attr_name = f"_{func.__name__}"
    
    @property
    @functools.wraps(func)
    def wrapper(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)
    
    return wrapper


def method_cache(ttl_seconds: int = 300):
    """
    Decorator to cache method results for a specified time period.
    
    Args:
        ttl_seconds: Time to live for cached results in seconds.
    """
    def decorator(func):
        cache_attr = f"_{func.__name__}_cache"
        timestamp_attr = f"_{func.__name__}_timestamp"
        
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            now = datetime.now()
            
            # Create cache key from args and kwargs
            key = str(args) + str(sorted(kwargs.items()))
            
            # Initialize cache if not exists
            if not hasattr(self, cache_attr):
                setattr(self, cache_attr, {})
                setattr(self, timestamp_attr, {})
            
            cache = getattr(self, cache_attr)
            timestamps = getattr(self, timestamp_attr)
            
            # Check if cache valid
            if (key in cache and key in timestamps and
                (now - timestamps[key]).total_seconds() < ttl_seconds):
                return cache[key]
            
            # Calculate and cache result
            result = func(self, *args, **kwargs)
            cache[key] = result
            timestamps[key] = now
            
            return result
        
        return wrapper
    
    return decorator


@dataclass
class APIKeyInfo:
    """Information about an API key from the key management service."""
    key: str
    balance: float
    added: str
    last_updated: str


class Config:
    """Configuration class that centralizes all settings."""

    # Cache for agent-fetched keys
    _cached_keys: Optional[List[APIKeyInfo]] = None
    _key_cache_timestamp: Optional[datetime] = None
    _cache_duration_minutes: int = 5  # Cache keys for 5 minutes
    
    # Environment variable cache
    _env_cache: Dict[str, Any] = {}
    
    def __init__(self):
        """Initialize the configuration with empty caches."""
        self._env_cache = {}
    
    def _get_env(self, key: str, default: Any = None) -> Any:
        """
        Get environment variable with caching.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Environment variable value or default
        """
        if key not in self._env_cache:
            self._env_cache[key] = os.getenv(key, default)
        return self._env_cache[key]
    


    @cached_property
    def LLM_API_KEY(self) -> str:
        """Get the LLM API key."""
        return self._get_env("LLM_API_KEY", "")
        
    @cached_property
    def LLM_BASE_URL(self) -> str:
        """Get the LLM base URL."""
        return self._get_env("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
        
    @cached_property
    def LLM_MODEL(self) -> str:
        """Get the LLM model name."""
        return self._get_env("LLM_MODEL", "deepseek-ai/DeepSeek-V3")
        
    @cached_property
    def SILICONFLOW_VIDEO_KEY(self) -> str:
        """Get the SiliconFlow video API key."""
        return self._get_env("SILICONFLOW_VIDEO_KEY", "")

    # Proxy Configuration
    @cached_property
    def NO_PROXY(self) -> str:
        """Get the NO_PROXY configuration."""
        return self._get_env("NO_PROXY", "")

    @cached_property
    def COMFYUI_HOST(self) -> str:
        """Get the ComfyUI host."""
        return self._get_env("COMFYUI_HOST", ComfyUIDefaults.DEFAULT_HOST)
        
    @cached_property
    def COMFYUI_PORT(self) -> int:
        """Get the ComfyUI port."""
        return int(self._get_env("COMFYUI_PORT", str(ComfyUIDefaults.DEFAULT_PORT)))

    @cached_property
    def comfyui_address(self) -> str:
        """Get the full ComfyUI server address."""
        return f"{self.COMFYUI_HOST}:{self.COMFYUI_PORT}"

    @cached_property
    def DEFAULT_VIDEO_MODEL(self) -> str:
        """Get the default video model."""
        return self._get_env("DEFAULT_VIDEO_MODEL", VideoDefaults.DEFAULT_MODEL)
        
    @cached_property
    def DEFAULT_VIDEO_SIZE(self) -> str:
        """Get the default video size."""
        return self._get_env("DEFAULT_VIDEO_SIZE", VideoDefaults.DEFAULT_SIZE)

    @cached_property
    def DEFAULT_OUTPUT_DIR(self) -> str:
        """Get the default output directory."""
        return self._get_env("DEFAULT_OUTPUT_DIR", "output")
        
    @cached_property
    def MAX_SCENES(self) -> int:
        """Get the maximum number of scenes."""
        return int(self._get_env("MAX_SCENES", str(GenerationLimits.DEFAULT_MAX_SCENES)))
        
    @cached_property
    def MAX_CHARACTERS(self) -> int:
        """Get the maximum number of characters."""
        return int(self._get_env("MAX_CHARACTERS", str(GenerationLimits.DEFAULT_MAX_CHARACTERS)))

    @cached_property
    def VIDEO_TIMEOUT_MINUTES(self) -> int:
        """Get the video generation timeout in minutes."""
        return int(self._get_env("VIDEO_TIMEOUT_MINUTES", str(VideoDefaults.TIMEOUT_MINUTES)))
        
    @cached_property
    def AUDIO_DURATION_PER_SCENE(self) -> int:
        """Get the audio duration per scene."""
        return int(self._get_env("AUDIO_DURATION_PER_SCENE", str(AudioDefaults.DURATION_PER_SCENE)))
        
    @cached_property
    def TRANSITION_DURATION(self) -> float:
        """Get the transition duration."""
        return float(self._get_env("TRANSITION_DURATION", "1.0"))

    @cached_property
    def MAX_GENERATION_RETRIES(self) -> int:
        """Get the maximum retry count for story/character/scene generation."""
        return int(self._get_env("MAX_GENERATION_RETRIES", "5"))






    

    

    
    @method_cache(ttl_seconds=60)  # Cache for 1 minute
    def get_multiple_keys(self, count: int) -> List[str]:
        """
        Get multiple API keys for video generation tasks.
        
        Args:
            count: Number of keys needed
            
        Returns:
            List of API key strings (same key repeated for normal mode)
        """
        key = self.SILICONFLOW_VIDEO_KEY
        return [key] * count if key else []
    
    @method_cache(ttl_seconds=60)  # Cache for 1 minute
    def allocate_keys_for_videos(self, video_count: int) -> Dict[int, str]:
        """
        Allocate API keys for video generation tasks.
        
        Args:
            video_count: Number of videos to generate
            
        Returns:
            Dictionary mapping video index to API key
        """
        key = self.SILICONFLOW_VIDEO_KEY
        if key:
            return {i: key for i in range(video_count)}
        return {}





    @method_cache(ttl_seconds=30)  # Cache for 30 seconds
    def validate_required_keys(self) -> list[str]:
        """
        Validate that required API keys are present.

        Returns:
            List of missing required keys
        """
        missing_keys = []

        if not self.LLM_API_KEY:
            missing_keys.append("LLM_API_KEY")
            
        if not self.SILICONFLOW_VIDEO_KEY:
            missing_keys.append("SILICONFLOW_VIDEO_KEY")

        return missing_keys

    @method_cache(ttl_seconds=300)  # Cache for 5 minutes
    def validate_api_key_format(self, key: str, provider: str) -> bool:
        """
        Validate API key format for security.
        
        Args:
            key: The API key to validate
            provider: The provider name for context
            
        Returns:
            True if format is valid, False otherwise
        """
        if not key:
            return False
            
        # Basic validation - API keys should be reasonable length and format
        if provider.lower() == "siliconflow" and not key.startswith(NetworkDefaults.SILICONFLOW_KEY_PREFIX):
            return False
            
        if len(key) < GenerationLimits.MIN_API_KEY_LENGTH:
            return False
            
        return True

    @method_cache(ttl_seconds=60)  # Cache for 1 minute
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific provider.

        Args:
            provider: The provider name (llm, siliconflow_video)

        Returns:
            API key if available, None otherwise
        """
        if provider.lower() == "siliconflow_video":
            return self.SILICONFLOW_VIDEO_KEY
        elif provider.lower() == "llm":
            return self.LLM_API_KEY
        
        return None

    @method_cache(ttl_seconds=30)  # Cache for 30 seconds
    def show_key_status(self) -> str:
        """
        Show the status of available API keys.
        
        Returns:
            Status string showing key information
        """
        return "Mode: normal - Using static keys from environment"


# Global config instance
config = Config()
