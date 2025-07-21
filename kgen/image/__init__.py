"""Image generation modules for KGen.

This package contains image generation components including ComfyUI integrations
and group mode image generation functionality.
"""

from .comfyui_image_flux import ComfyUIClient4Flux, generate_images_for_scenes
from .comfyui_image_illustrious import ComfyUIIllustriousClient, generate_illustrious_images_for_scenes
from .comfyui_image_wai import ComfyUIWaiClient, generate_wai_images_for_scenes
from .group_mode_image_generator import (
    generate_images_for_scenes_group_mode,
    generate_images_for_scenes_group_mode_optimized,
    generate_images_for_scenes_all_mode,
    generate_images_for_scenes_adaptive,
    generate_images_for_scenes_adaptive_optimized,
)

__all__ = [
    # ComfyUI Image Generation
    "ComfyUIClient4Flux",
    "generate_images_for_scenes",
    "ComfyUIIllustriousClient",
    "generate_illustrious_images_for_scenes",
    "ComfyUIWaiClient",
    "generate_wai_images_for_scenes",
    # Group Mode Image Generation
    "generate_images_for_scenes_group_mode",
    "generate_images_for_scenes_group_mode_optimized",
    "generate_images_for_scenes_all_mode",
    "generate_images_for_scenes_adaptive",
    "generate_images_for_scenes_adaptive_optimized",
]