"""
Input handlers for the YKGen CLI.

This module provides functions for getting user input with elegant formatting.
"""

import sys
from typing import Tuple, Any, Optional
from rich.panel import Panel
from rich.text import Text
from rich import box

from ykgen.console.display import console
from ykgen.console import print_info


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


def get_user_prompt(agent_type: str) -> str:
    """
    Get user input prompt with elegant formatting and examples.
    
    Args:
        agent_type: The type of agent being used.
        
    Returns:
        str: The user's prompt.
    """
    if agent_type == "poetry_agent":
        input_text = Text()
        input_text.append("Please enter your Chinese poetry:\n\n", style="bold bright_yellow")
        input_text.append("Example: ", style="bold white")
        input_text.append("观沧海——曹操：东临碣石，以观沧海。水何澹澹，山岛竦峙...\n\n", style="dim yellow")
        input_text.append("TIP: ", style="bold bright_blue")
        input_text.append("You can input classical Chinese poetry, and the system will\n", style="blue")
        input_text.append("      create a visual story with pinyin audio and traditional aesthetics.", style="blue")
        title = "Poetry Input"
        prompt_label = "Enter Chinese poetry: "
    elif agent_type == "poetry_agent_pure_image":
        input_text = Text()
        input_text.append("Please enter your Chinese poetry:\n\n", style="bold bright_yellow")
        input_text.append("Example: ", style="bold white")
        input_text.append("观沧海——曹操：东临碣石，以观沧海。水何澹澹，山岛竦峙...\n\n", style="dim yellow")
        input_text.append("TIP: ", style="bold bright_blue")
        input_text.append("The Poetry Pure Image Agent generates only images (no videos).\n", style="blue")
        input_text.append("      You can specify multiple images per scene and video prompts\n", style="blue")
        input_text.append("      will be saved to a text file for future reference.", style="blue")
        title = "Poetry Pure Image Input"
        prompt_label = "Enter Chinese poetry: "
    elif agent_type == "pure_image_agent":
        input_text = Text()
        input_text.append("Please enter your story prompt:\n\n", style="bold bright_green")
        input_text.append("Example: ", style="bold white")
        input_text.append("A magical forest where animals can speak\n", style="dim green")
        input_text.append("Style Example: ", style="bold white")
        input_text.append("A watercolor painting of a mystical underwater city\n\n", style="dim green")
        input_text.append("TIP: ", style="bold bright_blue")
        input_text.append("The Pure Image Agent generates only images (no videos).\n", style="blue")
        input_text.append("      You can specify multiple images per scene and video prompts\n", style="blue")
        input_text.append("      will be saved to a text file for future reference.", style="blue")
        title = "Pure Image Story Input"
        prompt_label = "Enter story prompt: "
    else:
        input_text = Text()
        input_text.append("Please enter your story prompt:\n\n", style="bold bright_green")
        input_text.append("Example: ", style="bold white")
        input_text.append("A brave knight's quest to save a magical kingdom\n", style="dim green")
        input_text.append("Style Example: ", style="bold white")
        input_text.append("A watercolor painting of a brave knight's quest\n\n", style="dim green")
        input_text.append("TIP: ", style="bold bright_blue")
        input_text.append("Be creative! Describe characters, settings, or adventures.\n", style="blue")
        input_text.append("      You can include visual style in your prompt if desired\n", style="blue")
        input_text.append("      (e.g., 'A cyberpunk story about...', 'An anime-style adventure...').", style="blue")
        title = "Story Input"
        prompt_label = "Enter story prompt: "
    
    input_panel = _create_panel(
        input_text,
        title,
        "bright_blue"
    )
    _display_panel(input_panel)
    
    while True:
        try:
            prompt = input(f"  {prompt_label}").strip()
            
            if not prompt:
                print("  Prompt cannot be empty. Please try again.")
                continue
                
            # Elegant confirmation
            confirm_text = Text()
            confirm_text.append("You entered: ", style="bold white")
            confirm_text.append(f'"{prompt}"', style="italic bright_yellow")
            
            confirm_panel = _create_panel(
                confirm_text,
                "Confirmation",
                "white"
            )
            _display_panel(confirm_panel)
            
            confirm = input("  Proceed with this prompt? (y/n): ").strip().lower()
            if confirm in ['y', 'yes', '']:
                return prompt
            elif confirm in ['n', 'no']:
                print("  Let's try again...")
                print()
                continue
            else:
                print("  Please enter 'y' for yes or 'n' for no.")
                continue
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            sys.exit(0)
        except EOFError:
            print("\n\nGoodbye!")
            sys.exit(0)


def get_images_per_scene() -> int:
    """
    Get user input for number of images per scene for PureImageAgent.
    
    Returns:
        int: The number of images per scene.
    """
    input_text = Text()
    input_text.append("How many images per scene?\n\n", style="bold bright_green")
    input_text.append("Options:\n", style="bold white")
    input_text.append("  • 1 image per scene (default, like VideoAgent)\n", style="white")
    input_text.append("  • 2-5 images per scene (multiple variations)\n", style="white")
    input_text.append("  • Higher numbers for more creative exploration\n\n", style="white")
    input_text.append("TIP: ", style="bold bright_blue")
    input_text.append("More images per scene give you more creative variations\n", style="blue")
    input_text.append("      but take longer to generate. Recommended: 2-3 images per scene.", style="blue")
    
    input_panel = _create_panel(
        input_text,
        "Images Per Scene",
        "bright_green"
    )
    _display_panel(input_panel)
    
    while True:
        try:
            choice = input("  Number of images per scene (1-10, default 1): ").strip()
            
            if not choice:
                choice = "1"
                
            images_per_scene = int(choice)
            
            if images_per_scene < 1 or images_per_scene > 10:
                print("  Please enter a number between 1 and 10.")
                continue
                
            # Elegant confirmation
            confirm_text = Text()
            confirm_text.append("You chose: ", style="bold white")
            confirm_text.append(f"{images_per_scene} images per scene", style="italic bright_green")
            if images_per_scene > 3:
                confirm_text.append(f"\n\nNote: Generating {images_per_scene} images per scene may take longer.", style="dim yellow")
            
            confirm_panel = _create_panel(
                confirm_text,
                "Confirmation",
                "white"
            )
            _display_panel(confirm_panel)
            
            if images_per_scene <= 3:
                return images_per_scene
            else:
                confirm = input("  Proceed with this setting? (y/n): ").strip().lower()
                if confirm in ['y', 'yes', '']:
                    return images_per_scene
                elif confirm in ['n', 'no']:
                    print("  Let's try again...")
                    print()
                    continue
                else:
                    print("  Please enter 'y' for yes or 'n' for no.")
                    continue
                
        except ValueError:
            print("  Please enter a valid number.")
            continue
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            sys.exit(0)
        except EOFError:
            print("\n\nGoodbye!")
            sys.exit(0)


def get_audio_preference_and_language() -> Tuple[bool, str]:
    """
    Get user input for audio preference and language selection for PureImageAgent.
    
    Returns:
        Tuple[bool, str]: A tuple containing the audio preference (True/False) and language (english/chinese).
    """
    # First, ask if they want audio
    audio_text = Text()
    audio_text.append("Enable audio generation?\n\n", style="bold bright_yellow")
    audio_text.append("Options:\n", style="bold white")
    audio_text.append("  • n - No audio generation (default, pure images only)\n", style="white")
    audio_text.append("  • y - Enable audio generation with language selection\n", style="white")
    audio_text.append("\nTIP: ", style="bold bright_blue")
    audio_text.append("Audio generation creates background music based on the story.\n", style="blue")
    audio_text.append("      You can choose between English and Chinese audio styles.", style="blue")
    
    audio_panel = _create_panel(
        audio_text,
        "Audio Generation",
        "bright_yellow"
    )
    _display_panel(audio_panel)
    
    while True:
        try:
            choice = input("  Enable audio generation? (y/n, default n): ").strip().lower()
            
            if not choice:
                choice = "n"
                
            if choice in ['n', 'no']:
                return False, "english"  # Audio disabled, language doesn't matter
            elif choice in ['y', 'yes']:
                # Ask for language selection
                print()
                language_text = Text()
                language_text.append("Audio Language Selection:\n\n", style="bold bright_cyan")
                language_text.append("Available languages:\n", style="bold white")
                language_text.append("  • english - English lyrics with Western musical style (default)\n", style="white")
                language_text.append("  • chinese - Chinese lyrics with traditional instruments and pinyin conversion\n", style="white")
                language_text.append("\nTIP: ", style="bold bright_blue")
                language_text.append("Chinese audio uses traditional instruments (guqin, erhu, bamboo flute)\n", style="blue")
                language_text.append("      and converts Chinese lyrics to pinyin for singing.", style="blue")
                
                language_panel = _create_panel(
                    language_text,
                    "Language Selection",
                    "bright_cyan"
                )
                _display_panel(language_panel)
                
                while True:
                    try:
                        lang_choice = input("  Select audio language (english/chinese, default english): ").strip().lower()
                        
                        if not lang_choice:
                            lang_choice = "english"
                            
                        if lang_choice in ['english', 'en']:
                            return True, "english"
                        elif lang_choice in ['chinese', 'zh', 'cn']:
                            return True, "chinese"
                        else:
                            print("  Please enter 'english' or 'chinese'.")
                            continue
                            
                    except (KeyboardInterrupt, EOFError):
                        print("\n\nGoodbye!")
                        sys.exit(0)
            else:
                print("  Please enter 'y' for yes or 'n' for no.")
                continue
                
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye!")
            sys.exit(0)