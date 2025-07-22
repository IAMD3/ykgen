"""
Group mode image generation for YKGen.

This module handles image generation for group mode where LoRAs are dynamically
selected per image based on scene content using LLM intelligence.
"""

from typing import List, Dict, Any, Optional

# ComfyUIWaiClient removed
from ykgen.lora.lora_selector import select_loras_for_scenes, select_loras_for_all_scenes_optimized
from ..providers import get_llm
from ..console import status_update, print_success, print_warning
from ..config.model_types import is_vpred_model, get_model_display_name
from .comfyui_image_simple import ComfyUISimpleClient
from .comfyui_image_vpred import ComfyUIVPredClient


def generate_images_for_scenes_group_mode_optimized(
    scenes: List[Dict[str, Any]], 
    group_config: Dict[str, Any],
    output_dir: Optional[str] = None,
    llm_provider = None,
    model_name: Optional[str] = None
) -> List[str]:
    """
    Generate images for scenes using optimized group mode with story-wide LoRA selection.
    
    This optimized approach selects LoRAs once for the entire story instead of per scene,
    ensuring visual consistency and reducing LLM API calls.
    
    Args:
        scenes: List of scene dictionaries with prompts and scene data
        group_config: Group mode configuration with required and optional LoRAs
        output_dir: Optional custom output directory path
        llm_provider: Deprecated parameter, kept for compatibility
        
    Returns:
        List of paths to generated image files
    """
    if group_config.get("mode") != "group":
        raise ValueError("This function is only for group mode")
    
    status_update("Starting optimized group mode image generation with story-wide LoRA selection...", "bright_cyan")
    
    # Get the model type from the group config
    model_type = group_config.get("model_type", "flux-schnell")
    
    # Step 1: Select LoRAs once for all scenes using optimized approach
    # This happens only once after all scenes and prompts are generated
    story_lora_config = select_loras_for_all_scenes_optimized(scenes, group_config)
    
    # Step 2: Generate images for each scene with the same selected LoRAs
    image_paths = []
    
    # Log the story-wide LoRA selection
    if story_lora_config:
        if story_lora_config.get("is_multiple"):
            lora_names = [lora["name"] for lora in story_lora_config.get("loras", [])]
            print_success(f"Story-wide LoRAs: {', '.join(lora_names)}")
        else:
            print_success(f"Story-wide LoRA: {story_lora_config.get('name', 'Unknown')}")
        
        # Show the reasoning
        if story_lora_config.get("selection_reasoning"):
            print_success(f"Selection reasoning: {story_lora_config['selection_reasoning']}")
    else:
        print_warning("No LoRAs selected for story")
    
    for i, scene in enumerate(scenes):
        scene_name = f"scene_{i+1:03d}"
        
        # Create single-scene list for generation
        single_scene = [scene]
        
        # Generate image for this scene with the story-wide selected LoRAs
        try:
            if is_vpred_model(model_type):
                # Use vPred workflow
                client = ComfyUIVPredClient(lora_config=story_lora_config, model_name=model_name)
                scene_image_paths = client.generate_scene_images(single_scene, output_dir)
            else:
                # Use simple workflow
                client = ComfyUISimpleClient(lora_config=story_lora_config, model_name=model_name)
                scene_image_paths = client.generate_scene_images(single_scene, output_dir)
            
            image_paths.extend(scene_image_paths)
            print_success(f"{scene_name}: Generated {len(scene_image_paths)} images")
            
        except Exception as e:
            print_warning(f"{scene_name}: Error generating images: {str(e)}")
            continue
    
    print_success(f"Optimized group mode image generation completed: {len(image_paths)} images generated")
    return image_paths


def generate_images_for_scenes_group_mode(
    scenes: List[Dict[str, Any]], 
    group_config: Dict[str, Any],
    output_dir: Optional[str] = None,
    llm_provider = None,
    model_name: Optional[str] = None
) -> List[str]:
    """
    Generate images for scenes using group mode with dynamic LoRA selection.
    
    Args:
        scenes: List of scene dictionaries with prompts and scene data
        group_config: Group mode configuration with required and optional LoRAs
        output_dir: Optional custom output directory path
        llm_provider: Deprecated parameter, kept for compatibility
        
    Returns:
        List of paths to generated image files
    """
    if group_config.get("mode") != "group":
        raise ValueError("This function is only for group mode")
    
    status_update("Starting group mode image generation with dynamic LoRA selection...", "bright_cyan")
    
    # Get the model type from the group config
    model_type = group_config.get("model_type", "flux-schnell")
    
    # Step 1: Select LoRAs for each scene using LLM
    scene_lora_configs = select_loras_for_scenes(scenes, group_config)
    
    # Step 2: Generate images for each scene with its selected LoRAs
    image_paths = []
    
    for i, (scene, lora_config) in enumerate(zip(scenes, scene_lora_configs)):
        scene_name = f"scene_{i+1:03d}"
        
        # Create single-scene list for generation
        single_scene = [scene]
        
        # Log the LoRA selection for this scene
        if lora_config:
            if lora_config.get("is_multiple"):
                lora_names = [lora["name"] for lora in lora_config.get("loras", [])]
                print_success(f"{scene_name}: Using LoRAs: {', '.join(lora_names)}")
            else:
                print_success(f"{scene_name}: Using LoRA: {lora_config.get('name', 'Unknown')}")
            
            # Show the reasoning
            if lora_config.get("selection_reasoning"):
                print_success(f"{scene_name}: Selection reasoning: {lora_config['selection_reasoning']}")
        else:
            print_warning(f"{scene_name}: No LoRAs selected")
        
        # Generate image for this scene with the selected LoRAs
        try:
            if is_vpred_model(model_type):
                # Use vPred workflow
                client = ComfyUIVPredClient(lora_config=lora_config, model_name=model_name)
                scene_image_paths = client.generate_scene_images(single_scene, output_dir)
            else:
                # Use simple workflow
                client = ComfyUISimpleClient(lora_config=lora_config, model_name=model_name)
                scene_image_paths = client.generate_scene_images(single_scene, output_dir)
            
            image_paths.extend(scene_image_paths)
            print_success(f"{scene_name}: Generated {len(scene_image_paths)} images")
            
        except Exception as e:
            print_warning(f"{scene_name}: Error generating images: {str(e)}")
            continue
    
    print_success(f"Group mode image generation completed: {len(image_paths)} images generated")
    return image_paths


def generate_images_for_scenes_all_mode(
    scenes: List[Dict[str, Any]], 
    lora_config: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
    model_name: Optional[str] = None
) -> List[str]:
    """
    Generate images for scenes using all mode (traditional behavior).
    
    Args:
        scenes: List of scene dictionaries with prompts and scene data
        lora_config: LoRA configuration to use for all images
        output_dir: Optional custom output directory path
        
    Returns:
        List of paths to generated image files
    """
    status_update("Starting all mode image generation with consistent LoRA usage...", "bright_cyan")
    
    # Get the model type from the lora_config
    model_type = lora_config.get("model_type", "flux-schnell") if lora_config else "flux-schnell"
    
    # Generate images using the traditional method
    try:
        if is_vpred_model(model_type):
            # Use vPred workflow
            client = ComfyUIVPredClient(lora_config=lora_config, model_name=model_name)
            image_paths = client.generate_scene_images(scenes, output_dir)
        else:
            # Use simple workflow
            client = ComfyUISimpleClient(lora_config=lora_config, model_name=model_name)
            image_paths = client.generate_scene_images(scenes, output_dir)
        
        print_success(f"All mode image generation completed: {len(image_paths)} images generated")
        return image_paths
        
    except Exception as e:
        print_warning(f"Error in all mode image generation: {str(e)}")
        return []


def generate_images_for_scenes_adaptive(
    scenes: List[Dict[str, Any]], 
    lora_config: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
    llm_provider = None,
    model_name: Optional[str] = None
) -> List[str]:
    """
    Generate images for scenes with adaptive mode selection.
    
    Automatically detects whether to use group mode or all mode based on the
    lora_config structure.
    
    Args:
        scenes: List of scene dictionaries with prompts and scene data
        lora_config: LoRA configuration (can be group mode or all mode)
        output_dir: Optional custom output directory path
        llm_provider: Deprecated parameter, kept for compatibility
        
    Returns:
        List of paths to generated image files
    """
    if not lora_config:
        # No LoRA config, use all mode with no LoRAs
        return generate_images_for_scenes_all_mode(scenes, None, output_dir, model_name)
    
    # Check if this is group mode
    if lora_config.get("mode") == "group":
        status_update("Detected group mode configuration", "bright_magenta")
        return generate_images_for_scenes_group_mode(
            scenes=scenes,
            group_config=lora_config,
            output_dir=output_dir,
            llm_provider=llm_provider,
            model_name=model_name
        )
    elif lora_config.get("mode") == "none":
        status_update("Detected none mode configuration - using base model only", "bright_cyan")
        return generate_images_for_scenes_all_mode(scenes, lora_config, output_dir, model_name)
    else:
        status_update("Detected all mode configuration", "bright_green")
        return generate_images_for_scenes_all_mode(scenes, lora_config, output_dir, model_name)


def generate_images_for_scenes_adaptive_optimized(
    scenes: List[Dict[str, Any]], 
    lora_config: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
    llm_provider = None,
    model_name: Optional[str] = None
) -> List[str]:
    """
    Generate images for scenes with adaptive mode selection using optimized approach.
    
    This version uses the optimized story-wide LoRA selection for group mode,
    ensuring visual consistency and reducing LLM API calls.
    
    Args:
        scenes: List of scene dictionaries with prompts and scene data
        lora_config: LoRA configuration (can be group mode or all mode)
        output_dir: Optional custom output directory path
        llm_provider: Deprecated parameter, kept for compatibility
        
    Returns:
        List of paths to generated image files
    """
    if not lora_config:
        # No LoRA config, use all mode with no LoRAs
        return generate_images_for_scenes_all_mode(scenes, None, output_dir)
    
    # Check if this is group mode
    if lora_config.get("mode") == "group":
        status_update("Detected group mode configuration - using optimized story-wide LoRA selection", "bright_magenta")
        return generate_images_for_scenes_group_mode_optimized(
            scenes=scenes,
            group_config=lora_config,
            output_dir=output_dir,
            llm_provider=llm_provider,
            model_name=model_name
        )
    elif lora_config.get("mode") == "none":
        status_update("Detected none mode configuration - using base model only", "bright_cyan")
        return generate_images_for_scenes_all_mode(scenes, lora_config, output_dir, model_name)
    else:
        status_update("Detected all mode configuration", "bright_green")
        return generate_images_for_scenes_all_mode(scenes, lora_config, output_dir, model_name)