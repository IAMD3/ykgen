"""
Display module for the KGen CLI.

This module provides functions for displaying generation information,
results, and completion messages to the user.
"""

from typing import Dict, List, Any
from rich.panel import Panel
from rich.text import Text
from rich import box

from kgen.console.display import console
from kgen.console import (
    print_prompt, print_story, print_characters,
    print_scenes, print_images_summary, print_video_summary,
    print_completion_banner, print_info, print_generation_steps
)


def _create_panel(content: Text, title: str, border_style: str) -> Panel:
    """Create a styled panel with the given content."""
    return Panel(
        content,
        title=f"[bold {border_style}]{title}[/bold {border_style}]",
        border_style=border_style,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _display_panel(panel: Panel) -> None:
    """Display the panel to the console."""
    console.console.print(panel)
    print()


def display_generation_info(agent_type: str, images_per_scene: int = 1) -> None:
    """
    Show beautiful generation process information.
    
    Args:
        agent_type: The type of agent being used.
        images_per_scene: Number of images to generate per scene.
    """
    if agent_type in ["pure_image_agent", "poetry_agent_pure_image"]:
        print_generation_steps(agent_type, images_per_scene)
    else:
        print_generation_steps(agent_type)


def display_results(result: Dict[str, Any], agent_type: str, images_per_scene: int = 1, enable_audio: bool = False, language: str = "english") -> None:
    """
    Display the generation results with beautiful formatting.
    
    Args:
        result: The generation result dictionary.
        agent_type: The type of agent being used.
        images_per_scene: Number of images per scene.
        enable_audio: Whether audio generation was enabled.
        language: The language used for audio generation.
    """
    # Display story, characters, scenes, and images
    print_story(result['story_full'].content)
    print_characters(result['characters_full'])
    print_scenes(result['scenes'])
    print_images_summary(result['image_paths'])
    
    # Show pinyin conversion for poetry
    if agent_type in ["poetry_agent", "poetry_agent_pure_image"] and 'pinyin_lyrics' in result:
        print_info("Pinyin Conversion:")
        print(f"   {result['pinyin_lyrics']}")
        print()
    
    # Pure image agent specific information
    if agent_type in ["pure_image_agent", "poetry_agent_pure_image"]:
        agent_name = "Poetry Pure Image Agent" if agent_type == "poetry_agent_pure_image" else "Pure Image Agent"
        image_info_text = Text()
        image_info_text.append(f"{agent_name} Generation Complete!\n\n", style="bold bright_green")
        image_info_text.append("Images Generated: ", style="bold white")
        image_info_text.append(f"{len(result['image_paths'])}", style="bright_green")
        image_info_text.append(" images total\n", style="white")
        image_info_text.append("Images per scene: ", style="bold white")
        image_info_text.append(f"{images_per_scene}", style="bright_blue")
        image_info_text.append(" images\n", style="white")
        image_info_text.append("Scenes processed: ", style="bold white")
        image_info_text.append(f"{len(result['scenes'])}", style="bright_cyan")
        image_info_text.append(" scenes\n\n", style="white")
        
        record_file = "poetry_generation_record.txt" if agent_type == "poetry_agent_pure_image" else "story_generation_record.txt"
        image_info_text.append("Video prompts saved to: ", style="bold white")
        image_info_text.append(record_file, style="bright_yellow")
        
        image_info_panel = _create_panel(
            image_info_text,
            f"{agent_name} Summary",
            "green"
        )
        _display_panel(image_info_panel)
    
    # Video generation summary
    video_count = len(result.get('video_tasks', []))
    if video_count > 0:
        print_video_summary(video_count)
    
    # Audio information with elegant formatting
    if result.get('audio_path'):
        # Determine audio type based on agent
        if agent_type == "poetry_agent":
            audio_type = "Poetry audio"
        elif agent_type == "poetry_agent_pure_image":
            audio_type = "Poetry audio"
        elif agent_type == "pure_image_agent":
            audio_type = f"Story audio ({language})"
        else:
            audio_type = "Background music"
        
        audio_text = Text()
        audio_text.append(f"{audio_type} generated successfully\n\n", style="white")
        audio_text.append("Location: ", style="bold white")
        audio_text.append(result['audio_path'], style="bright_blue")
        
        # Show language info for PureImageAgent
        if agent_type == "pure_image_agent":
            audio_text.append(f"\nLanguage: ", style="bold white")
            audio_text.append(f"{language}", style="bright_green")
            if language == "chinese":
                audio_text.append(f"\nFeatures: Pinyin conversion + traditional instruments", style="dim cyan")
            else:
                audio_text.append(f"\nFeatures: English lyrics + Western musical style", style="dim cyan")
        
        audio_panel = _create_panel(
            audio_text,
            "Audio Generation Complete",
            "bright_yellow"
        )
        _display_panel(audio_panel)


def display_completion(result: Dict[str, Any]) -> None:
    """
    Display the completion information.
    
    Args:
        result: The generation result dictionary.
    """
    # Final completion banner
    print_completion_banner()
    
    # Show output directory with elegant formatting
    if result.get('image_paths'):
        import os
        output_dir = os.path.dirname(result['image_paths'][0])
        final_text = Text()
        final_text.append("All generated content has been saved to:\n\n", style="white")
        final_text.append(f"{output_dir}", style="bold bright_blue")
        
        final_panel = _create_panel(
            final_text,
            "Output Location",
            "bright_blue"
        )
        _display_panel(final_panel) 