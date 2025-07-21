#!/usr/bin/env python3
"""
Enhanced Console Display Demonstration for KGen.

This script demonstrates the beautiful, clear, and graceful console output
system with improved typography, elegant transitions, and visual hierarchy.
"""

import time
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kgen.console.display import (
    console,
    print_banner,
    print_welcome,
    print_section_header,
    print_prompt,
    print_phase,
    print_step_start,
    print_step_complete,
    print_generation_steps,
    print_story,
    print_characters,
    print_scenes,
    print_images_summary,
    print_video_summary,
    print_completion_banner,
    print_proxy_status,
    print_processing_summary,
    print_separator,
    print_info,
    print_success,
    print_warning,
    print_error,
)


def demonstrate_console_beauty():
    """Demonstrate the beautiful console output system."""
    
    # 1. Banner and Welcome
    print_banner()
    print_welcome("video")
    
    # 2. Proxy Status
    print_proxy_status()
    
    # 3. User Input
    sample_prompt = "A magical forest where ancient trees whisper secrets to a young wanderer seeking the lost city of dreams"
    print_prompt(sample_prompt)
    
    # 4. Generation Pipeline
    print_generation_steps("video_agent")
    
    # 5. Phase Headers and Steps
    print_phase("Story Generation", "Creating your narrative masterpiece")
    
    print_step_start(1, "Story Creation", "Generating rich narrative from your prompt")
    time.sleep(1)
    print_step_complete("Story Creation", 12.3, "Generated 450-word story with 3 acts")
    
    print_step_start(2, "Character Extraction", "Identifying key characters and personalities")
    time.sleep(0.8)
    print_step_complete("Character Extraction", 8.7, "Found 3 main characters with detailed backgrounds")
    
    # 6. Generated Content Display
    sample_story = """In the heart of the Whispering Woods, where moonlight danced through ancient canopies, young Elara stepped carefully along the moss-covered path. The trees seemed alive with secrets, their branches reaching toward her like gentle guardians sharing forgotten wisdom.

As she ventured deeper, the forest revealed its magic. Crystalline streams sang melodies of old, and luminescent flowers guided her way toward the fabled Lost City of Dreams, where legends claimed one's deepest aspirations could become reality."""
    
    print_story(sample_story)
    
    # 7. Characters Table
    sample_characters = [
        {"name": "Elara", "description": "A brave young wanderer with curious eyes and an adventurous spirit, seeking her true destiny"},
        {"name": "The Ancient Oak", "description": "A wise tree spirit, centuries old, guardian of forest secrets and guide to lost souls"},
        {"name": "Lumina", "description": "A mystical firefly who transforms into a glowing fairy, protector of the dream realm"}
    ]
    
    print_characters(sample_characters)
    
    # 8. Scenes Display
    sample_scenes = [
        {
            "location": "Whispering Woods Entrance",
            "time": "Moonlit Evening",
            "action": "Elara begins her mystical journey into the enchanted forest",
            "characters": [{"name": "Elara"}]
        },
        {
            "location": "Crystal Stream Clearing",
            "time": "Deep Night",
            "action": "The Ancient Oak reveals the path to the Lost City through whispered prophecies",
            "characters": [{"name": "Elara"}, {"name": "The Ancient Oak"}]
        },
        {
            "location": "Lost City of Dreams",
            "time": "Dawn's First Light",
            "action": "Lumina guides Elara to the heart of the dream realm where wishes take form",
            "characters": [{"name": "Elara"}, {"name": "Lumina"}]
        }
    ]
    
    print_scenes(sample_scenes)
    
    # 9. Generation Progress
    print_phase("Visual Creation", "Bringing your story to life with stunning imagery")
    
    print_info("Connecting to ComfyUI for image generation...")
    time.sleep(0.5)
    print_success("ComfyUI connection established")
    
    # 10. Processing Summaries
    sample_images = ["output/scene_001.png", "output/scene_002.png", "output/scene_003.png"]
    print_images_summary(sample_images)
    
    print_processing_summary("Image Generation", 3, 45.2)
    
    # 11. Video Generation Phase
    print_phase("Video Production", "Converting images to cinematic videos")
    
    print_info("Starting video generation with SiliconFlow API...")
    print_info("Using API key with proxy configuration...")
    time.sleep(1)
    print_success("All videos generated successfully")
    
    print_video_summary(3)
    
    # 12. Warning and Error Examples
    print_separator()
    print_warning("This is how elegant warnings look in the enhanced console")
    print_error("Enhanced error display with helpful context", 
                "This shows how errors are presented with additional details for better debugging")
    
    # 13. Completion
    print_completion_banner()
    
    # 14. Final Statistics
    print_section_header("Generation Summary")
    
    stats_data = [
        ("Story", "1 narrative (450 words)"),
        ("Characters", "3 detailed personas"),
        ("Scenes", "3 cinematic moments"),
        ("Images", "3 AI-generated artworks"),
        ("Videos", "3 dynamic sequences"),
        ("Total Time", "2m 15s"),
        ("Output", "output/2024_01_15_story_abc123/")
    ]
    
    for label, value in stats_data:
        console.console.print(f"  {label} {value}", style="dim bright_white")
    
    console.console.print()
    
    # 15. Elegant Farewell
    farewell_text = console.console.print(
        "\nThank you for experiencing KGen's enhanced console interface!",
        style="bold bright_cyan",
        justify="center"
    )


def demonstrate_poetry_mode():
    """Demonstrate poetry agent console output."""
    print_separator("bright_magenta")
    console.print_section_header("Poetry Agent Demo")
    
    print_welcome("poetry")
    
    # Poetry-specific steps
    print_generation_steps("poetry_agent")
    
    sample_poetry = """静夜思——李白
床前明月光，疑是地上霜。
举头望明月，低头思故乡。"""
    
    console.print_prompt(sample_poetry)
    
    print_phase("Pinyin Conversion", "Converting classical Chinese to pronunciation guide")
    
    print_step_start(1, "Pinyin Processing", "Analyzing tones and pronunciation")
    time.sleep(0.8)
    print_step_complete("Pinyin Processing", 5.2, "Generated pinyin with tone markers")
    
    print_phase("Visual Interpretation", "Creating imagery from poetic essence")
    
    print_processing_summary("Poetry Visualization", 1, 125.7)


if __name__ == "__main__":
    console.console.print("\nKGen Enhanced Console Display Demonstration\n", style="bold bright_cyan", justify="center")
    console.console.print("Experience the beauty, clarity, and grace of the new interface\n", style="dim bright_white", justify="center")
    
    try:
        # Main video agent demo
        demonstrate_console_beauty()
        
        # Poetry agent demo
        demonstrate_poetry_mode()
        
        console.console.print("\n" + "─" * 60, style="dim bright_blue")
        console.console.print("Console Enhancement Demo Complete!", style="bold bright_green", justify="center")
        console.console.print("The interface is now more beautiful, clear, and graceful than ever!", style="bright_white italic", justify="center")
        console.console.print("─" * 60 + "\n", style="dim bright_blue")
        
    except KeyboardInterrupt:
        console.console.print("\n\nDemo interrupted by user", style="yellow")
    except Exception as e:
        console.console.print(f"\n\nDemo error: {e}", style="red") 