"""
YKGen - AI-powered story and video generation.

A simple and modern Python library for generating stories, characters, and scenes
from text prompts using LangChain and LangGraph.
"""

__version__ = "0.1.0"
__author__ = "YKGen Team"

# Core modules (staying in root)
from ykgen.config.config import Config, config
from ykgen.model.models import Character, Characters, Scene, SceneList, VisionState
from ykgen.config.constants import (
    AudioDefaults,
    ComfyUIDefaults,
    DefaultPrompts,
    DisplayDefaults,
    FFmpegDefaults,
    FileDefaults,
    GenerationLimits,
    NetworkDefaults,
    VideoDefaults,
)
from .utils import (
    retry_with_backoff,
    validate_file_exists,
    validate_directory_exists,
    generate_output_directory,
    calculate_file_size_mb,
    format_duration,
)
from ykgen.config.exceptions import (
    YKGenError,
    ConfigurationError,
    APIKeyError,
    ComfyUIError,
    VideoGenerationError,
    AudioGenerationError,
    StoryGenerationError,
    FileOperationError,
    ValidationError,
    RetryExhaustedError,
)

# Organized packages
from .agents import VideoAgent, PoetryAgent, PureImageAgent
from .audio import ComfyUIAudioClient, generate_story_audio, generate_song_lyrics, generate_music_tags
from .video import (
    VideoGenerationClient,
    VideoGenerationTask,
    generate_videos_from_images,
    wait_for_all_videos,
    combine_videos,
    combine_videos_with_transitions,
    combine_scene_videos,
    VideoTaskMonitor,
    VideoResultProcessor,
    VideoQualityManager,
)
from .image import ComfyUIClient4Flux, ComfyUISimpleClient, ComfyUIVPredClient, generate_images_for_scenes
from .providers import get_llm
from ykgen.lora.lora_selector import LoRASelector, select_loras_for_scenes, select_loras_for_all_scenes_optimized
from .console import (
    console,
    print_banner,
    print_characters,
    print_completion_banner,
    print_error,
    print_images_summary,
    print_info,
    print_prompt,
    print_scenes,
    print_story,
    print_success,
    print_video_summary,
    print_warning,
    progress_context,
    status_update,
    step_progress,
)

__all__ = [
    # Core classes
    "VideoAgent",
    "PureImageAgent",
    "Character",
    "Characters",
    "Scene",
    "SceneList",
    "VisionState",

    "get_llm",
    # Configuration
    "config",
    "Config",
    # Constants
    "AudioDefaults",
    "ComfyUIDefaults",
    "DefaultPrompts",
    "DisplayDefaults",
    "FFmpegDefaults",
    "FileDefaults",
    "GenerationLimits",
    "NetworkDefaults",
    "VideoDefaults",
    # Video generation and processing
    "VideoGenerationClient",
    "VideoGenerationTask",
    "generate_videos_from_images",
    "wait_for_all_videos",
    "combine_videos",
    "combine_videos_with_transitions",
    "combine_scene_videos",
    # Video management
    "VideoTaskMonitor",
    "VideoResultProcessor", 
    "VideoQualityManager",
    # ComfyUI integration
    "ComfyUIClient4Flux",
    "ComfyUISimpleClient",
    "ComfyUIVPredClient",
    "generate_images_for_scenes",
    # Audio generation
    "ComfyUIAudioClient",
    "generate_story_audio",
    "generate_song_lyrics",
    "generate_music_tags",
    # Console utilities
    "console",
    "print_banner",
    "print_prompt",
    "print_story",
    "print_characters",
    "print_scenes",
    "print_images_summary",
    "print_video_summary",
    "print_completion_banner",
    "print_error",
    "print_warning",
    "print_success",
    "print_info",
    "status_update",
    "progress_context",
    "step_progress",
    # Utilities
    "retry_with_backoff",
    "validate_file_exists",
    "validate_directory_exists",
    "generate_output_directory",
    "calculate_file_size_mb",
    "format_duration",
    # Exceptions
    "YKGenError",
    "ConfigurationError",
    "APIKeyError",
    "ComfyUIError",
    "VideoGenerationError",
    "AudioGenerationError",
    "StoryGenerationError",
    "FileOperationError",
    "ValidationError",
    "RetryExhaustedError",
    "PoetryAgent",
    # LoRA Selector
    "LoRASelector",
    "select_loras_for_scenes",
    "select_loras_for_all_scenes_optimized",
]
