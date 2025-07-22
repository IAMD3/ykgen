"""Image generation modules for YKGen.

This package contains image generation components including ComfyUI integrations
and group mode image generation functionality.
"""

from .comfyui_image_simple import ComfyUISimpleClient, generate_images_for_scenes
from .comfyui_image_vpred import ComfyUIVPredClient
from .comfyui_image_vpred import generate_illustrious_images_for_scenes
# WAI client removed
from .group_mode_image_generator import (
    generate_images_for_scenes_group_mode,
    generate_images_for_scenes_group_mode_optimized,
    generate_images_for_scenes_all_mode,
    generate_images_for_scenes_adaptive,
    generate_images_for_scenes_adaptive_optimized,
)

__all__ = [
    # ComfyUI Image Generation
    "ComfyUISimpleClient",
    "ComfyUIVPredClient",
    "generate_images_for_scenes",
    # "ComfyUIIllustriousClient", # Renamed to ComfyUIVPredClient
    "generate_illustrious_images_for_scenes",
    # WAI client exports removed
    # Group Mode Image Generation
    "generate_images_for_scenes_group_mode",
    "generate_images_for_scenes_group_mode_optimized",
    "generate_images_for_scenes_all_mode",
    "generate_images_for_scenes_adaptive",
    "generate_images_for_scenes_adaptive_optimized",
]