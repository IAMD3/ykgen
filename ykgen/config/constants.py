"""
Constants and default values for YKGen.

This module centralizes all magic numbers, default values, and configuration
constants used throughout the application for better maintainability.
"""

# Video Generation Constants
class VideoDefaults:
    """Default values for video generation."""
    
    # Model and format defaults
    DEFAULT_MODEL = "Wan-AI/Wan2.1-I2V-14B-720P"
    DEFAULT_SIZE = "1280x720"
    
    # Timing and timeouts
    MAX_WAIT_TIME_SECONDS = 600  # 10 minutes
    CHECK_INTERVAL_SECONDS = 5
    TIMEOUT_MINUTES = 50
    
    # Quality settings
    CRF_VALUE = 23  # Constant Rate Factor for video quality
    AUDIO_BITRATE = "192k"
    
    # Threading
    THREAD_CHECK_INTERVAL = 5
    PROGRESS_UPDATE_INTERVAL = 30
    
    # Retry settings
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 5
    RETRY_EXPONENTIAL_BACKOFF = True


# ComfyUI Workflow Constants
class ComfyUIDefaults:
    """Default values for ComfyUI workflows."""
    
    # Image generation
    IMAGE_WIDTH = 1024
    IMAGE_HEIGHT = 1024
    BATCH_SIZE = 1
    
    # Flux model settings
    FLUX_STEPS = 4
    FLUX_CFG = 1
    FLUX_SAMPLER = "euler"
    FLUX_SCHEDULER = "simple"
    FLUX_DENOISE = 1
    
    # Model files
    FLUX_MODEL = "flux1-schnell-fp8.safetensors"
    
    # Connection settings
    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT = 8188


# Audio Generation Constants
class AudioDefaults:
    """Default values for audio generation."""
    
    # Duration and timing
    DEFAULT_DURATION = 120  # seconds
    DURATION_PER_SCENE = 5  # seconds
    
    # Quality settings
    STEPS = 50
    CFG = 5
    SAMPLER = "euler"
    SCHEDULER = "simple"
    DENOISE = 1
    
    # Model settings
    LYRICS_STRENGTH = 0.99
    SHIFT_VALUE = 5.0
    MULTIPLIER = 1.0
    
    # Model files
    AUDIO_MODEL = "ace_step_v1_3.5b.safetensors"
    
    # Output settings
    AUDIO_QUALITY = "V0"
    OUTPUT_PREFIX = "audio/ComfyUI"
    
    # Lyrics generation
    MIN_WORDS_PER_SECOND = 1.5
    MAX_WORDS_PER_SECOND = 2.5
    MAX_TAGS_COUNT = 15


# File and Directory Constants
class FileDefaults:
    """Default values for file operations."""
    
    # Directory patterns
    OUTPUT_DIR_PATTERN = "output/{timestamp}_images4story_{suffix}"
    TIMESTAMP_FORMAT = "%Y_%m_%d"
    
    # File naming
    SCENE_NAME_PATTERN = "scene_{:03d}"
    IMAGE_NAME_PATTERN = "scene_{:03d}_{:02d}.png"
    VIDEO_NAME_PATTERN = "scene_{:03d}.mp4"
    ENHANCED_VIDEO_PATTERN = "scene_{:03d}_enhanced.mp4"
    
    # File extensions
    IMAGE_EXT = ".png"
    VIDEO_EXT = ".mp4"
    AUDIO_EXT = ".mp3"
    SUBTITLE_EXT = ".srt"
    RECORD_EXT = ".txt"
    
    # File sizes (for progress reporting)
    MB_DIVISOR = 1024 * 1024


# Generation Limits
class GenerationLimits:
    """Limits for various generation operations."""
    
    # Content limits
    DEFAULT_MAX_SCENES = 6
    DEFAULT_MAX_CHARACTERS = 5
    MIN_STORY_LENGTH = 100
    MAX_STORY_LENGTH = 300
    
    # Retry and timeout
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 2
    LLM_RETRY_DELAY_SECONDS = 3
    
    # Fallback limits
    MAX_FALLBACK_CHARACTERS = 2
    MIN_API_KEY_LENGTH = 10


# Network and API Constants
class NetworkDefaults:
    """Network and API related constants."""
    
    # Base URLs
    SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
    
    # API key validation
    SILICONFLOW_KEY_PREFIX = "sk-"
    
    # Request settings
    REQUEST_TIMEOUT = 300  # 5 minutes
    MAX_REQUEST_RETRIES = 3


# ffmpeg Constants
class FFmpegDefaults:
    """Constants for ffmpeg operations."""
    
    # Video encoding
    VIDEO_CODEC = "libx264"
    PIXEL_FORMAT = "yuv420p"
    PROFILE = "high"
    LEVEL = "4.0"
    PRESET = "medium"
    
    # Audio encoding
    AUDIO_CODEC = "aac"
    
    # Transition settings
    DEFAULT_TRANSITION_DURATION = 1.0
    CROSSFADE_OFFSET_BASE = 5  # Base offset for crossfade calculations
    
    # Container settings
    MOVFLAGS = "+faststart"  # Optimize for web playback


# UI and Display Constants
class DisplayDefaults:
    """Constants for UI and console display."""
    
    # Formatting
    SEPARATOR_LENGTH = 50
    RECORD_SEPARATOR = "=" * 80
    SECTION_SEPARATOR = "-" * 40
    SUBSECTION_SEPARATOR = "-" * 60
    
    # Progress reporting
    PROGRESS_BAR_LENGTH = 50
    STATUS_UPDATE_INTERVAL = 5
    
    # File size reporting precision
    FILE_SIZE_PRECISION = 1  # decimal places


# Default Tags and Prompts
class DefaultPrompts:
    """Default prompts and tags for generation."""
    
    # Audio style tags
    DEFAULT_AUDIO_TAGS = (
        "immediate vocals, vocal-driven, soft female vocals, anime, kawaii pop, "
        "j-pop, piano, guitar, synthesizer, fast, happy, cheerful, lighthearted, "
        "voice-first, early vocals"
    )
    
    # Common character names for fallback
    FALLBACK_CHARACTER_NAMES = [
        "hero", "protagonist", "character", "person", "knight", "warrior",
        "mage", "princess", "king", "queen"
    ]
    
    # System messages
    STORY_WRITER_SYSTEM = (
        "You are a writer specializing in writing stories. "
        "You will be provided with a prompt and your goal is to write a story based on that prompt."
    )
    
    SONGWRITER_SYSTEM = (
        "You are a talented songwriter who creates catchy, emotional songs based on stories. "
        "Your songs should capture the essence of the story while being memorable and singable."
    )
    
    MUSIC_PRODUCER_SYSTEM = (
        "You are a music producer who selects appropriate musical styles and instruments "
        "based on story content and mood."
    )