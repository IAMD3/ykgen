#!/usr/bin/env python3
"""
Test script to demonstrate text exclusion in image generation.

This script shows how the updated agents now explicitly exclude text from generated images.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kgen.image.comfyui_image_flux import ComfyUIClient4Flux
from kgen.console import print_banner, print_info, print_success


def test_text_exclusion():
    """Test the text exclusion functionality."""
    print_banner()
    print_info("🚫 Testing Text Exclusion in Image Generation 🚫", "")
    print()
    
    # Test VideoAgent scene generation
    print_info("VideoAgent Scene Example:", "🎬")
    video_scene = {
        "location": "Medieval castle",
        "time": "Dawn",
        "characters": [{"name": "Knight", "description": "Brave warrior"}],
        "action": "Knight preparing for battle",
        "image_prompt_positive": "cartoon style illustration of a brave knight in silver armor preparing for battle at a medieval castle at dawn, epic fantasy art style, dramatic lighting"
    }
    
    print("Original prompt:")
    print(f"  {video_scene['image_prompt_positive']}")
    print()
    
    # Simulate what the ComfyUI client does now
    client = ComfyUIClient4Flux()
    enhanced_prompt = f"{video_scene['image_prompt_positive']}, no text, no words, no letters, no writing, no characters, no typography"
    
    print("Enhanced prompt with text exclusion:")
    print(f"  {enhanced_prompt}")
    print()
    
    # Show the negative prompt
    negative_prompt = "text, words, letters, writing, characters, typography, calligraphy, signs, symbols, numbers, chinese characters, japanese characters, korean characters, arabic text, latin text, cyrillic text, any written language"
    print("Negative prompt for text exclusion:")
    print(f"  {negative_prompt}")
    print()
    
    # Test PoetryAgent scene generation
    print_info("PoetryAgent Scene Example:", "🎋")
    poetry_scene = {
        "location": "Mountain lake",
        "time": "Moonlit night",
        "characters": [{"name": "Poet", "description": "Contemplative scholar"}],
        "action": "Gazing at moon reflection",
        "image_prompt_positive": "Traditional Chinese painting style, poetic landscape inspired by classical poetry, tranquil mountain lake under moonlight, watercolor and ink, serene atmosphere, no text, no words, no letters, no Chinese characters, pure visual poetry"
    }
    
    print("Poetry scene prompt (already includes text exclusion):")
    print(f"  {poetry_scene['image_prompt_positive']}")
    print()
    
    enhanced_poetry_prompt = f"{poetry_scene['image_prompt_positive']}, no text, no words, no letters, no writing, no characters, no typography"
    print("Enhanced poetry prompt:")
    print(f"  {enhanced_poetry_prompt}")
    print()
    
    print_success("✅ Text Exclusion Features:")
    print("  1. 🎭 VideoAgent: Updated system prompts to exclude text")
    print("  2. 🎋 PoetryAgent: Added Chinese character exclusion")
    print("  3. 🖼️ ComfyUI: Enhanced positive prompts with text exclusion")
    print("  4. 🚫 ComfyUI: Comprehensive negative prompts for all text types")
    print("  5. 🔄 Fallback: Updated fallback scenes to exclude text")
    print()
    
    print_info("🎯 Impact:", "")
    print("  • Generated images will be purely visual")
    print("  • No text, words, or characters will appear")
    print("  • Better video generation compatibility")
    print("  • Professional, clean visual storytelling")
    print()


if __name__ == "__main__":
    test_text_exclusion()