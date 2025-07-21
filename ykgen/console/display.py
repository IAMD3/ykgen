"""Beautiful console output utilities for YKGen.

This module provides styled console output, progress bars, and status updates
using the rich library for a polished user experience.
"""

import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from rich import box
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.columns import Columns
from rich.padding import Padding


class YKGenConsole:
    """Beautiful console interface for YKGen operations."""

    def __init__(self):
        self.console = Console()
        self.progress = None
        self.current_task = None

    def print_banner(self):
        """Print the YKGen banner with elegant styling."""
        banner_text = Text()
        banner_text.append("YKGen", style="bold bright_cyan")
        banner_text.append(" - ", style="dim white")
        banner_text.append("AI Story & Video Generator", style="bright_white italic")
        banner_text.append("\n")
        banner_text.append("Transform ideas into videos", style="bright_magenta italic")

        banner_panel = Panel(
            Align.center(banner_text),
            border_style="bright_cyan",
            padding=(1, 2),
            box=box.ROUNDED,
        )
        
        self.console.print()
        self.console.print(banner_panel)
        self.console.print()

    def print_section_divider(self, title: str = "", style: str = "bright_blue"):
        """Print an elegant section divider with clean design."""
        if title:
            self.console.print(f"\n[bold {style}]{title}[/bold {style}]")
            self.console.print(Rule(style=f"dim {style}"))
        else:
            self.console.print(Rule(style=f"dim {style}"))
        self.console.print()

    def print_prompt(self, prompt: str):
        """Print the user prompt with elegant styling."""
        display_prompt = prompt if len(prompt) <= 200 else prompt[:197] + "..."
        
        prompt_text = Text()
        prompt_text.append(display_prompt, style="italic bright_white")
        
        prompt_panel = Panel(
            prompt_text,
            title="[bold bright_yellow]Your Creative Vision[/bold bright_yellow]",
            title_align="left",
            border_style="yellow",
            padding=(1, 2),
            box=box.ROUNDED,
        )
        self.console.print(prompt_panel)
        self.console.print()

    def print_section_header(self, title: str, icon: str = ""):
        """Print an elegant section header with clean visual hierarchy."""
        header_text = Text()
        header_text.append(title, style="bold bright_white")
        
        header_panel = Panel(
            Align.center(header_text),
            border_style="bright_cyan",
            padding=(1, 2),
            box=box.ROUNDED,
        )

        self.console.print()
        self.console.print(header_panel)
        self.console.print()

    def print_step_start(self, step_number: int, step_name: str, description: str = ""):
        """Print the start of a processing step with elegant formatting."""
        step_text = Text()
        step_text.append(f"Step {step_number}: ", style="bold bright_cyan")
        step_text.append(f"{step_name}", style="bold bright_white")
        
        if description:
            step_text.append(f"\n{description}", style="dim white")

        step_panel = Panel(
            step_text,
            border_style="cyan",
            padding=(1, 2),
            box=box.MINIMAL,
        )
        self.console.print(step_panel)

    def print_step_complete(self, step_name: str, duration: float = None, result: str = ""):
        """Print step completion with timing and result."""
        complete_text = Text()
        complete_text.append("Complete: ", style="bold bright_green")
        complete_text.append(f"{step_name}", style="bright_green")
        
        if duration:
            complete_text.append(f" ({duration:.1f}s)", style="dim green")
            
        if result:
            complete_text.append(f"\n{result}", style="bright_white")

        self.console.print(complete_text)
        self.console.print()

    def print_story(self, story: str):
        """Print the generated story with beautiful typography."""
        paragraphs = story.split('\n\n')
        story_text = Text()
        
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                if i > 0:
                    story_text.append("\n\n")
                story_text.append(paragraph.strip(), style="white")

        story_panel = Panel(
            story_text,
            title="[bold bright_green]Generated Story[/bold bright_green]",
            title_align="left",
            border_style="green",
            padding=(1, 2),
            box=box.ROUNDED,
        )
        self.console.print(story_panel)
        self.console.print()

    def print_characters(self, characters: List[Dict[str, str]]):
        """Print the generated characters with beautiful table formatting."""
        if not characters:
            self.console.print("  [dim red]No characters generated[/dim red]")
            return

        table = Table(
            title="[bold bright_cyan]Story Characters[/bold bright_cyan]",
            box=box.ROUNDED,
            title_style="bold bright_cyan",
            border_style="cyan",
            header_style="bold bright_white",
            show_lines=True,
            row_styles=["", "dim"]
        )
        table.add_column("Character", style="bold cyan", min_width=15)
        table.add_column("Description", style="white", ratio=3)

        for character in characters:
            name = character.get("name", "Unknown")
            desc = character.get("description", "No description")
            if len(desc) > 80:
                desc = desc[:77] + "..."
            table.add_row(name, desc)

        self.console.print(table)
        self.console.print()

    def print_scenes(self, scenes: List[Dict[str, Any]]):
        """Print the generated scenes with elegant formatting."""
        if not scenes:
            self.console.print("  [dim red]No scenes generated[/dim red]")
            return

        self.print_section_header("Scene Breakdown")

        for i, scene in enumerate(scenes, 1):
            scene_header = Text()
            scene_header.append(f"Scene {i:02d}", style="bold bright_cyan")
            scene_header.append(" - ", style="dim bright_white")
            scene_header.append(
                f"Location: {scene.get('location', 'Unknown location')}", 
                style="bright_yellow"
            )
            scene_header.append(" - ", style="dim bright_white")
            scene_header.append(
                f"Time: {scene.get('time', 'Unknown time')}", 
                style="bright_magenta"
            )

            scene_content = Text()
            
            action = scene.get('action', 'No action described')
            scene_content.append("Action: ", style="bold bright_white")
            scene_content.append(f"{action}\n\n", style="white")
            
            characters = [char.get("name", "Unknown") for char in scene.get("characters", [])]
            scene_content.append("Characters: ", style="bold bright_white")
            if characters:
                scene_content.append(", ".join(characters), style="cyan")
            else:
                scene_content.append("None", style="dim white")

            scene_panel = Panel(
                scene_content,
                title=scene_header,
                border_style="blue",
                padding=(1, 2),
                box=box.ROUNDED,
            )
            self.console.print(scene_panel)

        self.console.print()

    def print_images_summary(self, image_paths: List[str]):
        """Print summary of generated images with elegant formatting."""
        if not image_paths:
            self.console.print("  [dim red]No images were generated[/dim red]")
            return

        output_dir = "/".join(image_paths[0].split("/")[:2]) if image_paths else "unknown"

        summary_text = Text()
        summary_text.append("Generated ", style="white")
        summary_text.append(f"{len(image_paths)}", style="bold bright_green")
        summary_text.append(f" beautiful images\n\n", style="white")
        summary_text.append("Location: ", style="bold white")
        summary_text.append(f"{output_dir}/", style="bright_blue")
        summary_text.append("\nReady for video generation", style="dim bright_green")

        summary_panel = Panel(
            summary_text,
            title="[bold bright_green]Image Generation Complete[/bold bright_green]",
            border_style="green",
            padding=(1, 2),
            box=box.ROUNDED,
        )
        self.console.print(summary_panel)
        self.console.print()

    def print_video_summary(self, video_count: int):
        """Print summary of video generation with beautiful formatting."""
        if video_count <= 0:
            return

        summary_text = Text()
        summary_text.append("Completed video generation for ", style="white")
        summary_text.append(f"{video_count}", style="bold bright_magenta")
        summary_text.append(f" scenes\n\n", style="white")
        
        summary_text.append("Enhanced Features:\n", style="bold white")
        features = [
            "Audio narration with text-to-speech",
            # "Subtitles based on scene content",  # Subtitles currently disabled
            "Combined into single story video",
            "Professional video encoding"
        ]
        
        for feature in features:
            summary_text.append(f"  {feature}\n", style="cyan")

        video_panel = Panel(
            summary_text,
            title="[bold bright_magenta]Video Generation Complete[/bold bright_magenta]",
            border_style="magenta",
            padding=(1, 2),
            box=box.ROUNDED,
        )

        self.console.print(video_panel)
        self.console.print()

    def print_completion_banner(self):
        """Print elegant completion banner with celebration."""
        completion_text = Text()
        completion_text.append("Generation Complete!", style="bold bright_green")
        completion_text.append("\n\n")
        completion_text.append("Your AI-generated story video is ready!", style="bright_white italic")
        completion_text.append("\n")
        completion_text.append("Ready to captivate your audience", style="dim bright_cyan")

        completion_panel = Panel(
            Align.center(completion_text),
            box=box.DOUBLE,
            border_style="bright_green",
            padding=(2, 4),
        )
        self.console.print()
        self.console.print(completion_panel)
        self.console.print()

    def print_error(self, message: str, details: Optional[str] = None):
        """Print an elegant error message with helpful styling."""
        error_content = Text()
        error_content.append("Error: ", style="bold red")
        error_content.append(message, style="red")

        if details:
            error_content.append(f"\n\nDetails:\n{details}", style="dim red")

        error_panel = Panel(
            error_content,
            title="[bold bright_red]Something went wrong[/bold bright_red]",
            title_align="left",
            border_style="red",
            padding=(1, 2),
            box=box.ROUNDED,
        )
        self.console.print()
        self.console.print(error_panel)
        self.console.print()

    def print_warning(self, message: str):
        """Print an elegant warning message."""
        warning_text = Text()
        warning_text.append("Warning: ", style="bold bright_yellow")
        warning_text.append(message, style="yellow")
        
        self.console.print(warning_text)

    def print_success(self, message: str):
        """Print an elegant success message."""
        success_text = Text()
        success_text.append("Success: ", style="bold bright_green")
        success_text.append(message, style="green")
        
        self.console.print(success_text)

    def print_info(self, message: str, icon: str = ""):
        """Print an elegant info message with better visual hierarchy."""
        info_text = Text()
        info_text.append(message, style="blue")
        
        self.console.print(info_text)

    def print_operation_start(self, operation: str, details: str = ""):
        """Print the start of a major operation with elegant formatting."""
        op_text = Text()
        op_text.append(f"Starting {operation}", style="bold bright_white")
        
        if details:
            op_text.append(f"\n{details}", style="dim white")

        op_panel = Panel(
            op_text,
            border_style="cyan",
            padding=(1, 2),
            box=box.MINIMAL,
        )
        self.console.print()
        self.console.print(op_panel)

    def print_key_status_table(self, status_data: Dict[str, Any]):
        """Print key management status in a beautiful table format."""
        table = Table(
            title="[bold bright_blue]API Key Management Status[/bold bright_blue]",
            box=box.ROUNDED,
            title_style="bold bright_blue",
            border_style="blue",
            header_style="bold bright_white",
            show_header=False,
            padding=(0, 1)
        )
        table.add_column("Property", style="bold white", min_width=20)
        table.add_column("Value", style="cyan")

        for key, value in status_data.items():
            if key == "mode":
                table.add_row("Mode", f"[bright_green]{value}[/bright_green]")
            elif key == "total_keys":
                table.add_row("Total Keys", f"[bright_cyan]{value}[/bright_cyan]")
            elif key == "available_keys":
                try:
                    num_value = int(value)
                    color = "bright_green" if num_value > 0 else "bright_red"
                except (ValueError, TypeError):
                    color = "white"
                table.add_row("Available Keys", f"[{color}]{value}[/{color}]")
            elif key == "best_balance":
                table.add_row("Best Key Balance", f"[bright_green]{value}[/bright_green]")
            elif key == "total_balance":
                table.add_row("Total Balance", f"[bright_green]{value}[/bright_green]")
            elif key == "max_videos":
                table.add_row("Max Videos", f"[bright_magenta]{value}[/bright_magenta]")

        self.console.print(table)
        self.console.print()

    def status_update(self, message: str, style: str = "blue"):
        """Print a status update with elegant formatting."""
        self.console.print(f"[{style}]{message}[/{style}]")

    @contextmanager
    def progress_context(self, description: str):
        """Context manager for elegant progress tracking."""
        self.progress = Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40, style="cyan", complete_style="bright_green"),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            expand=True,
        )

        try:
            with self.progress:
                self.current_task = self.progress.add_task(description, total=None)
                yield self.progress, self.current_task
        finally:
            self.progress = None
            self.current_task = None

    @contextmanager
    def step_progress(self, description: str, total: int):
        """Context manager for elegant step-by-step progress tracking."""
        progress = Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40, style="cyan", complete_style="bright_green"),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console,
            expand=True,
        )

        with progress:
            task = progress.add_task(description, total=total)
            yield progress, task

    def update_progress(
        self, task_id, advance: int = 1, description: Optional[str] = None
    ):
        """Update progress for a task."""
        if self.progress and task_id is not None:
            self.progress.update(task_id, advance=advance)
            if description:
                self.progress.update(task_id, description=description)

    def set_progress_total(self, task_id, total: int):
        """Set the total for a progress task."""
        if self.progress and task_id is not None:
            self.progress.update(task_id, total=total)


# Global console instance
console = YKGenConsole()

# Convenience functions for backward compatibility
def print_banner():
    """Print the YKGen banner."""
    console.print_banner()

def print_prompt(prompt: str):
    """Print the user prompt."""
    console.print_prompt(prompt)

def print_section_header(title: str, icon: str = ""):
    """Print a section header."""
    console.print_section_header(title, icon)

def print_story(story: str):
    """Print the generated story."""
    console.print_story(story)

def print_characters(characters: List[Dict[str, str]]):
    """Print the generated characters."""
    console.print_characters(characters)

def print_scenes(scenes: List[Dict[str, Any]]):
    """Print the generated scenes."""
    console.print_scenes(scenes)

def print_images_summary(image_paths: List[str]):
    """Print images summary."""
    console.print_images_summary(image_paths)

def print_video_summary(video_count: int):
    """Print video summary."""
    console.print_video_summary(video_count)

def print_completion_banner():
    """Print completion banner."""
    console.print_completion_banner()

def print_error(message: str, details: Optional[str] = None):
    """Print an error message."""
    console.print_error(message, details)

def print_warning(message: str):
    """Print a warning message."""
    console.print_warning(message)

def print_success(message: str):
    """Print a success message."""
    console.print_success(message)

def print_info(message: str, icon: str = ""):
    """Print an info message."""
    console.print_info(message, icon)

def status_update(message: str, style: str = "blue"):
    """Print a status update."""
    console.status_update(message, style)

def progress_context(description: str):
    """Get progress context manager."""
    return console.progress_context(description)

def step_progress(description: str, total: int):
    """Get step progress context manager."""
    return console.step_progress(description, total)

def print_key_status_elegant(status_lines: List[str]):
    """Print key status in elegant format."""
    if not status_lines:
        return
    
    # Parse status lines into structured data
    status_data = {}
    for line in status_lines:
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()
            status_data[key] = value
    
    console.print_key_status_table(status_data)

def print_generation_steps(agent_type: str, images_per_scene: int = 1):
    """Print the generation steps for the specified agent type."""
    steps_map = {
        "video_agent": [
            "Story Creation - Generate rich narrative from your prompt",
            "Character Extraction - Identify key characters and personalities", 
            "Scene Breakdown - Divide story into visual scenes",
            "Image Generation - Create stunning visuals with ComfyUI",
            "Video Production - Convert images to cinematic videos",
            "Audio Enhancement - Add narration and sound effects",
            "Final Assembly - Combine all elements into complete video"
        ],
        "poetry_agent": [
            "Pinyin Conversion - Convert Chinese characters to pronunciation",
            "Tone Analysis - Analyze poetic meter and rhythm",
            "Visual Interpretation - Create imagery from poetic essence",
            "Audio Production - Generate speech with proper tones",
            "Cultural Context - Add historical and cultural annotations"
        ],
        "poetry_agent_pure_image": [
            "Pinyin Conversion - Convert Chinese characters to pronunciation",
            "Poetry Interpretation - Create visual story from poetic essence",
            "Character Extraction - Identify characters from poetry",
            "Scene Breakdown - Divide poetry into visual scenes",
            "Image Prompt Generation - Create AI prompts for each scene",
            f"Multiple Image Generation - Create {images_per_scene} images per scene with ComfyUI",
            "Video Prompt Recording - Save comprehensive video prompts for manual video generation"
        ],
        "pure_image_agent": [
            "Story Creation - Generate rich narrative from your prompt",
            "Character Extraction - Identify key characters and personalities", 
            "Scene Breakdown - Divide story into visual scenes",
            "Image Prompt Generation - Create AI prompts for each scene",
            f"Multiple Image Generation - Create {images_per_scene} images per scene with ComfyUI",
            "Video Prompt Recording - Save comprehensive video prompts for manual video generation"
        ]
    }
    
    steps = steps_map.get(agent_type, steps_map["video_agent"])
    
    console.print_section_header("Generation Process")
    
    for i, step in enumerate(steps, 1):
        step_text = Text()
        step_text.append(f"{i}. ", style="bold bright_cyan")
        step_text.append(step, style="white")
        console.console.print(step_text)
    
    console.console.print()

def print_proxy_status():
    """Print proxy configuration status."""
    proxy_text = Text()
    proxy_text.append("Proxy Configuration", style="bold bright_green")
    proxy_text.append("\nAll API connections will route through configured proxy", style="dim green")
    proxy_text.append("\nEnhanced privacy and reliability", style="bright_white")
    
    proxy_panel = Panel(
        proxy_text,
        title="[bold bright_green]Network Status[/bold bright_green]",
        border_style="green",
        padding=(1, 2),
        box=box.ROUNDED,
    )
    console.console.print(proxy_panel)
    console.console.print()

def print_welcome_message(agent_type: str = "video"):
    """Print welcome message for the specified agent type."""
    welcome_messages = {
        "video": "Welcome to YKGen Video Agent - Transform your ideas into stunning videos!",
        "poetry": "Welcome to YKGen Poetry Agent - Process and visualize Chinese poetry with AI!"
    }
    
    message = welcome_messages.get(agent_type, welcome_messages["video"])
    console.print_info(message)

def print_processing_summary(operation: str, count: int, duration: float = None):
    """Print processing summary with elegant formatting."""
    summary_text = Text()
    summary_text.append(f"Completed {operation}", style="bold bright_green")
    summary_text.append(f"\nProcessed {count} items", style="white")
    
    if duration:
        summary_text.append(f"\nTotal time: {duration:.1f} seconds", style="dim white")
    
    summary_panel = Panel(
        summary_text,
        title="[bold bright_green]Processing Summary[/bold bright_green]",
        border_style="green",
        padding=(1, 2),
        box=box.ROUNDED,
    )
    console.console.print(summary_panel)
    console.console.print()

def print_separator(style: str = "dim blue"):
    """Print a visual separator."""
    console.console.print(Rule(style=style))

def print_phase_header(phase: str, description: str = ""):
    """Print phase header with description."""
    phase_text = Text()
    phase_text.append(phase, style="bold bright_cyan")
    
    if description:
        phase_text.append(f"\n{description}", style="dim white")
    
    phase_panel = Panel(
        phase_text,
        border_style="cyan",
        padding=(1, 2),
        box=box.ROUNDED,
    )
    console.console.print()
    console.console.print(phase_panel)

def print_step_start(step_number: int, step_name: str, description: str = ""):
    """Print step start."""
    console.print_step_start(step_number, step_name, description)

def print_step_complete(step_name: str, duration: float = None, result: str = ""):
    """Print step completion."""
    console.print_step_complete(step_name, duration, result)

def print_operation_start(operation: str, details: str = ""):
    """Print operation start."""
    console.print_operation_start(operation, details)

def print_welcome(agent_type: str = "video"):
    """Print welcome message."""
    print_welcome_message(agent_type)

def print_phase(phase: str, description: str = ""):
    """Print phase header."""
    print_phase_header(phase, description)
