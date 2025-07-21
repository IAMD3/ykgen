"""
Menu handling classes for the KGen CLI.

This module provides classes for displaying and handling user input for various menus.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any, Union
from rich.panel import Panel
from rich.text import Text
from rich import box

from kgen.console.display import console
from kgen.config import config


class Menu(ABC):
    """Base abstract class for all menu implementations."""
    
    @abstractmethod
    def display(self) -> None:
        """Display the menu to the user."""
        pass
    
    @abstractmethod
    def get_user_choice(self) -> Any:
        """Get and validate the user's choice from the menu."""
        pass
    
    def create_panel(self, content: Text, title: str, border_style: str) -> Panel:
        """Create a styled panel with the given content."""
        return Panel(
            content,
            title=f"[bold {border_style}]{title}[/bold {border_style}]",
            border_style=border_style,
            box=box.ROUNDED,
            padding=(1, 2),
        )
    
    def display_panel(self, panel: Panel) -> None:
        """Display the panel to the console."""
        console.console.print(panel)
        print()


class AgentSelectionMenu(Menu):
    """Menu for selecting the agent type."""
    
    def display(self) -> None:
        """Display the agent selection menu."""
        menu_text = Text()
        menu_text.append("Available Agents:\n\n", style="bold bright_white")
        menu_text.append("  1. ", style="bold bright_cyan")
        menu_text.append("VideoAgent", style="bright_cyan")
        menu_text.append("    - Create original stories from text prompts\n", style="white")
        menu_text.append("  2. ", style="bold bright_magenta") 
        menu_text.append("PoetryAgent", style="bright_magenta")
        menu_text.append("   - Transform Chinese poetry into visual experiences\n", style="white")
        menu_text.append("  3. ", style="bold bright_green")
        menu_text.append("PureImageAgent", style="bright_green")
        menu_text.append(" - Generate images only with customizable count per scene", style="white")
        menu_text.append("  4. ", style="bold bright_yellow")
        menu_text.append("PoetryAgent (Pure Image)", style="bright_yellow")
        menu_text.append(" - Generate poetry images only, no videos", style="white")
        
        panel = self.create_panel(
            menu_text, 
            "Agent Selection", 
            "bright_blue"
        )
        self.display_panel(panel)
    
    def get_user_choice(self) -> str:
        """Get and validate the user's agent choice."""
        import sys
        from kgen.console import print_info
        
        while True:
            try:
                choice = input("  Please choose an agent (1, 2, 3, or 4): ").strip()
                
                if choice == "1":
                    from kgen.console import print_info
                    print_info("Selected: VideoAgent for story generation")
                    return "video_agent"
                elif choice == "2":
                    from kgen.console import print_info
                    print_info("Selected: PoetryAgent for Chinese poetry processing")
                    return "poetry_agent"
                elif choice == "3":
                    from kgen.console import print_info
                    print_info("Selected: PureImageAgent for image-only generation")
                    return "pure_image_agent"
                elif choice == "4":
                    from kgen.console import print_info
                    print_info("Selected: PoetryAgent (Pure Image Mode) for poetry image generation")
                    return "poetry_agent_pure_image"
                else:
                    print("  Invalid choice. Please enter 1, 2, 3, or 4.")
                    continue
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                sys.exit(0)
            except EOFError:
                print("\n\nGoodbye!")
                sys.exit(0)


class VideoProviderMenu(Menu):
    """Menu for selecting the video provider."""
    
    def display(self) -> None:
        """Display the video provider selection menu."""
        provider_text = Text()
        provider_text.append("Choose video generation provider:\n\n", style="bold bright_yellow")
        provider_text.append("Available Providers:\n", style="bold white")
        provider_text.append("  1. ", style="bright_green")
        provider_text.append("SiliconFlow", style="green")
        provider_text.append(" (default) - Wan2.1 I2V model, 5-second clips, 720P\n", style="white")


        provider_text.append("\nProvider Details:\n", style="bold white")
        provider_text.append("  • SiliconFlow: ", style="bright_green")
        provider_text.append("Fast, reliable, 5-second videos, 720P resolution\n", style="white")

        provider_text.append("High quality, flexible duration, up to 1080P, movement control\n", style="white")
        
        panel = self.create_panel(
            provider_text,
            "Video Provider Selection",
            "bright_yellow"
        )
        self.display_panel(panel)
    
    def get_user_choice(self) -> str:
        """Get and validate the user's video provider choice."""
        import sys
        from kgen.console import print_error, print_info
        
        while True:
            try:
                choice = input("  Select video provider (1 or 2): ").strip()
                
                if choice == "1" or choice == "":
                    # Check if SiliconFlow API key is available
                    if not config.SILICONFLOW_VIDEO_KEY:
                        print_error("SiliconFlow video API key not configured", "Please set SILICONFLOW_VIDEO_KEY in your .env file")
                        continue
                    
                    print_info("Selected: SiliconFlow for video generation")
                    return "siliconflow"

                else:
                    print("  Invalid choice. Please enter 1 or 2.")
                    continue
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                sys.exit(0)
            except EOFError:
                print("\n\nGoodbye!")
                sys.exit(0)


class ModelSelectionMenu(Menu):
    """Menu for selecting the image generation model."""
    
    def display(self) -> None:
        """Display the model selection menu."""
        model_text = Text()
        model_text.append("Choose an image generation model:\n\n", style="bold bright_cyan")
        model_text.append("Available Models:\n", style="bold white")
        model_text.append("  1. ", style="bright_yellow")
        model_text.append("Flux-Schnell", style="yellow")
        model_text.append(" (default) - Ultra-fast 4-step generation with multiple LoRA options\n", style="white")
        model_text.append("  2. ", style="bright_yellow")
        model_text.append("Illustrious-vPred", style="yellow")
        model_text.append(" - High-quality anime/manga style with Elena Kimberlite character LoRA\n", style="white")
        model_text.append("  3. ", style="bright_yellow")
        model_text.append("Wai NSFW Illustrious", style="yellow")
        model_text.append(" - NSFW-capable illustrative style with 26-step generation\n", style="white")
        model_text.append("\nModel Characteristics:\n", style="bold white")
        model_text.append("  • Flux-Schnell: ", style="bright_blue")
        model_text.append("Fast generation, versatile styles, 8 LoRA options\n", style="white")
        model_text.append("  • Illustrious-vPred: ", style="bright_magenta")
        model_text.append("Anime/manga focus, character consistency, v-prediction model\n", style="white")
        model_text.append("  • Wai NSFW Illustrious: ", style="bright_green")
        model_text.append("Advanced illustrative generation with NSFW capabilities and custom steps\n", style="white")
        
        panel = self.create_panel(
            model_text,
            "Model Selection",
            "bright_cyan"
        )
        self.display_panel(panel)
    
    def get_user_choice(self) -> str:
        """Get and validate the user's model choice."""
        import sys
        from kgen.console import print_info
        
        while True:
            try:
                choice = input("  Select model (1, 2 or 3): ").strip()
                
                if choice == "1" or choice == "":
                    print_info("Selected: Flux-Schnell for fast, versatile image generation")
                    return "flux-schnell"
                elif choice == "2":
                    print_info("Selected: Illustrious-vPred for anime/manga style generation")
                    return "illustrious-vpred"
                elif choice == "3":
                    print_info("Selected: Wai NSFW Illustrious for advanced illustrative generation")
                    return "wai-illustrious"
                else:
                    print("  Invalid choice. Please enter 1, 2 or 3.")
                    continue
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                sys.exit(0)
            except EOFError:
                print("\n\nGoodbye!")
                sys.exit(0)


class LoRAModeMenu(Menu):
    """Menu for selecting the LoRA mode."""
    
    def display(self) -> None:
        """Display the LoRA mode selection menu."""
        mode_text = Text()
        mode_text.append("LoRA Usage Mode Selection:\n\n", style="bold bright_magenta")
        mode_text.append("Available modes:\n", style="bold white")
        mode_text.append("  1. all - Use all selected LoRAs for every image (default)\n", style="white")
        mode_text.append("     • Consistent style across all images\n", style="dim white")
        mode_text.append("     • All LoRAs applied to every scene\n", style="dim white")
        mode_text.append("  2. group - Dynamic LoRA selection per image\n", style="white")
        mode_text.append("     • Choose required LoRAs (always used)\n", style="dim white")
        mode_text.append("     • Choose optional LoRAs (LLM decides per image)\n", style="dim white")
        mode_text.append("     • More variety and scene-appropriate styling\n", style="dim white")
        mode_text.append("\nTIP: ", style="bold bright_blue")
        mode_text.append("'all' mode is simpler and gives consistent results.\n", style="blue")
        mode_text.append("      'group' mode is more advanced and gives varied, scene-appropriate results.", style="blue")
        
        panel = self.create_panel(
            mode_text,
            "LoRA Mode Selection",
            "bright_magenta"
        )
        self.display_panel(panel)
    
    def get_user_choice(self) -> str:
        """Get and validate the user's LoRA mode choice."""
        import sys
        
        while True:
            try:
                choice = input("  Select LoRA mode (1-2, default 1): ").strip()
                
                if not choice:
                    choice = "1"
                    
                if choice == "1":
                    # Elegant confirmation
                    confirm_text = Text()
                    confirm_text.append("Selected: ", style="bold white")
                    confirm_text.append("all", style="italic bright_green")
                    confirm_text.append(" - All selected LoRAs will be used for every image", style="white")
                    
                    confirm_panel = self.create_panel(
                        confirm_text,
                        "Mode Confirmation",
                        "white"
                    )
                    self.display_panel(confirm_panel)
                    return "all"
                    
                elif choice == "2":
                    # Elegant confirmation
                    confirm_text = Text()
                    confirm_text.append("Selected: ", style="bold white")
                    confirm_text.append("group", style="italic bright_yellow")
                    confirm_text.append(" - Dynamic LoRA selection per image\n", style="white")
                    confirm_text.append("  • You'll select required LoRAs (always used)\n", style="dim white")
                    confirm_text.append("  • You'll select optional LoRAs (LLM decides per image)\n", style="dim white")
                    confirm_text.append("  • Each image may use different LoRA combinations", style="dim white")
                    
                    confirm_panel = self.create_panel(
                        confirm_text,
                        "Mode Confirmation",
                        "white"
                    )
                    self.display_panel(confirm_panel)
                    return "group"
                    
                else:
                    print("  Please enter 1 or 2.")
                    continue
                    
            except (KeyboardInterrupt, EOFError):
                print("\n\nGoodbye!")
                sys.exit(0)