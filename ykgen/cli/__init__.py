"""
Command Line Interface package for YKGen.

This package contains all command-line interface components for the YKGen application.
"""

from .cli import main
from .menu import (
    AgentSelectionMenu,
    VideoProviderMenu,
    ModelSelectionMenu,
    LoRAModeMenu
)
from .input_handlers import (
    get_user_prompt,
    get_images_per_scene,
    get_audio_preference_and_language
)
from .display import (
    display_generation_info,
    display_results,
    display_completion
)

__all__ = [
    "main",
    # Menus
    "AgentSelectionMenu",
    "VideoProviderMenu",
    "ModelSelectionMenu",
    "LoRAModeMenu",
    # Input handlers
    "get_user_prompt",
    "get_images_per_scene",
    "get_audio_preference_and_language",
    # Display functions
    "display_generation_info",
    "display_results",
    "display_completion"
]