"""
Video client factory for YKGen.

This module provides factory functions to create video generation clients
based on the selected provider (SiliconFlow).
"""

from typing import Optional

from ykgen.config.config import config
from ..console import print_error
from .siliconflow_client import VideoGenerationClient

from .base_video_client import BaseVideoClient


def create_video_client(provider: str = "siliconflow", api_key: Optional[str] = None) -> Optional[BaseVideoClient]:
    """
    Create a video generation client based on the provider.
    
    Args:
        provider: The video provider ("siliconflow")
        api_key: Optional API key to use (if not provided, will get from config)
        
    Returns:
        Video client instance or None if configuration is invalid
    """
    provider = provider.lower()
    
    if provider == "siliconflow":
        if api_key is None:
            api_key = config.SILICONFLOW_VIDEO_KEY
        if not api_key:
            print_error("SiliconFlow video API key not available", "Please configure SILICONFLOW_VIDEO_KEY")
            return None
            
        return VideoGenerationClient(api_key)
        

        
    else:
        print_error(f"Unknown video provider: {provider}", "Supported providers: siliconflow")
        return None


def get_video_provider_info(provider: str) -> dict:
    """
    Get information about a video provider.
    
    Args:
        provider: The video provider name
        
    Returns:
        Dictionary with provider information
    """
    provider = provider.lower()
    
    if provider == "siliconflow":
        return {
            "name": "SiliconFlow",
            "model": "Wan2.1 I2V-14B-720P-Turbo",
            "duration": 5,
            "resolution": "720P",
            "max_resolution": "720P",
            "features": ["Fast generation", "Reliable API"],
            "api_key_env": "SILICONFLOW_VIDEO_KEY"
        }

    else:
        return {
            "name": "Unknown",
            "model": "N/A",
            "duration": "N/A",
            "resolution": "N/A",
            "max_resolution": "N/A",
            "features": [],
            "api_key_env": "N/A"
        }


def validate_video_provider_config(provider: str) -> bool:
    """
    Validate that the video provider is properly configured.
    
    Args:
        provider: The video provider name
        
    Returns:
        True if properly configured, False otherwise
    """
    provider = provider.lower()
    
    if provider == "siliconflow":
        return bool(config.SILICONFLOW_VIDEO_KEY)
            

        
    else:
        return False


def get_supported_providers() -> list:
    """
    Get list of supported video providers.
    
    Returns:
        List of supported provider names
    """
    return ["siliconflow"]


def get_configured_providers() -> list:
    """
    Get list of properly configured video providers.
    
    Returns:
        List of configured provider names
    """
    configured = []
    
    for provider in get_supported_providers():
        if validate_video_provider_config(provider):
            configured.append(provider)
            
    return configured