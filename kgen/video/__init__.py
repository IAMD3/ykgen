"""
Video generation modules for KGen.

This package contains video generation, processing, and management components.
"""

from .siliconflow_client import (
    VideoGenerationClient,
    VideoGenerationTask,
    generate_videos_from_images,
    wait_for_all_videos,
    combine_videos,
    combine_videos_with_transitions,
    combine_scene_videos,
)

from .base_video_client import BaseVideoClient
from .client_factory import (
    create_video_client,
    get_video_provider_info,
    validate_video_provider_config,
    get_supported_providers,
    get_configured_providers,
)
from .video_manager import VideoTaskMonitor, VideoResultProcessor, VideoQualityManager


__all__ = [
    # SiliconFlow API
    "VideoGenerationClient",
    "VideoGenerationTask", 
    "generate_videos_from_images",
    "wait_for_all_videos",
    "combine_videos",
    "combine_videos_with_transitions",
    "combine_scene_videos",
    
    # Base Video Client
    "BaseVideoClient",
    # Video Client Factory
    "create_video_client",
    "get_video_provider_info",
    "validate_video_provider_config",
    "get_supported_providers",
    "get_configured_providers",
    # Video Management
    "VideoTaskMonitor",
    "VideoResultProcessor",
    "VideoQualityManager",

]