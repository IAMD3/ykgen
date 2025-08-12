"""
Poetry agent for processing Chinese poetry and generating videos.

This module contains the PoetryAgent that:
1. Accepts Chinese poetry as input
2. Converts it to pinyin format for audio generation
3. Generates story, characters, and scenes based on the poetry
4. Creates videos with poetry-inspired visuals and audio
"""

import os
import time
from typing import Optional

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import END
from langgraph.graph import StateGraph

from .base_agent import BaseAgent
from ..video import wait_for_all_videos
from ykgen.config.config import config
from ..config.model_types import get_model_display_name
from ..console import (
    print_info,
    print_success,
    print_warning,
    status_update,
)
from ykgen.model.models import Characters, SceneList, VisionState
from ..providers import get_llm


class PoetryAgent(BaseAgent):
    """Agent for processing Chinese poetry and generating videos."""

    def __init__(
        self,

        enable_audio: bool = True,
        style: str = "",
        lora_config: Optional[dict] = None,
        video_provider: str = "siliconflow",
        pure_image_mode: bool = False,  # New parameter for pure image mode
        images_per_scene: int = 1,  # New parameter for multiple images per scene
    ):
        """Initialize the poetry agent."""
        super().__init__(enable_audio, style, lora_config)
        self.video_provider = video_provider
        self.pure_image_mode = pure_image_mode
        self.images_per_scene = images_per_scene

    def convert_poetry_to_pinyin(self, state: VisionState) -> VisionState:
        """Convert Chinese poetry to pinyin format for audio generation."""
        status_update("Converting poetry to pinyin format...", "bright_yellow")

        system_message = (
            "You are an expert in Chinese poetry and pinyin conversion. "
            "Your task is to convert Chinese poetry into pinyin format suitable for singing."
        )

        poetry_prompt = f"""Convert the following Chinese poetry into pinyin format for audio generation.

Poetry:
{state['prompt'].content}

Requirements:
1. Convert each Chinese character to its pinyin with tone numbers (1-4)
2. Group the pinyin by verses, maintaining the original structure
3. Format as shown in the example:
   [verse]
   [zh]pinyin1 pinyin2 pinyin3...
   
4. Each line should start with [zh] followed by pinyin separated by spaces
5. Separate verses with [verse] markers
6. Maintain the poetic rhythm and structure

Output ONLY the formatted pinyin, no explanations."""

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_message), ("user", poetry_prompt)]
        )

        def try_convert():
            chain = prompt | self.llm
            output = chain.invoke({})
            
            if not output or not output.content.strip():
                raise ValueError("Empty pinyin conversion")
            
            # Store the pinyin version in state for audio generation
            state["pinyin_lyrics"] = output.content.strip()
            print_success("Poetry to pinyin conversion completed")
            return state

        def fallback():
            # Basic fallback - just use the original text
            print_warning("Pinyin conversion failed, using original text")
            state["pinyin_lyrics"] = state['prompt'].content
            return state

        return self._retry_with_fallback("Pinyin conversion", try_convert, fallback)

    def generate_poetry_story(self, state: VisionState) -> VisionState:
        """Generate a visual story based on the poetry."""
        status_update("Creating visual story from poetry...", "bright_green")

        system_message = (
            "You are a poet and storyteller who creates vivid visual narratives from classical Chinese poetry. "
            "Your task is to interpret the poetry and create a descriptive story that captures its essence, "
            "imagery, and emotions in a way suitable for visual representation."
        )

        story_prompt = f"""Create a visual story based on this Chinese poetry:

{state['prompt'].content}

Requirements:
1. Capture the mood, imagery, and emotions of the poetry
2. Create a narrative that can be visualized in scenes
3. Include descriptions of landscapes, characters, and actions mentioned or implied in the poetry
4. Maintain the poetic and artistic essence
5. The story should be 100-300 words
6. Write in English for scene generation

Focus on visual elements that can be rendered as images."""

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_message), ("user", story_prompt)]
        )

        def try_generate():
            chain = prompt | self.llm
            output = chain.invoke({})
            
            if not output or not output.content.strip():
                raise ValueError("Empty story generated")
            
            result = VisionState(
                prompt=state["prompt"], 
                story_full=output,
                pinyin_lyrics=state.get("pinyin_lyrics", "")
            )
            print_success("Poetry story generation completed")
            return result

        def fallback():
            # Create a basic fallback story from the poetry
            fallback_story_content = f"A visual interpretation of the classical Chinese poetry: {state['prompt'].content}. The scene unfolds with poetic imagery and deep emotions."
            fallback_story = AIMessage(content=fallback_story_content)
            return VisionState(
                prompt=state["prompt"], 
                story_full=fallback_story,
                pinyin_lyrics=state.get("pinyin_lyrics", "")
            )

        return self._retry_with_fallback("Poetry story generation", try_generate, fallback)

    def generate_poetry_characters(self, state: VisionState) -> VisionState:
        """Extract or create characters from the poetry interpretation with LoRA-aware character descriptions."""
        status_update("Identifying characters from poetry with LoRA optimization...", "bright_blue")

        # Build LoRA context for character generation
        lora_context = self._build_lora_context_for_characters()
        
        system_message = (
            "You are an expert in Chinese poetry analysis. "
            "Identify or create characters based on the poetry and its visual story. "
            "When creating character descriptions, focus on visual details that will help with consistent image generation."
        )

        character_prompt = f"""Based on this poetry and its visual interpretation, identify or create characters:

Original Poetry:
{state['prompt'].content}

Visual Story:
{state['story_full'].content}

{lora_context}

Generate characters (maximum: {config.MAX_CHARACTERS}) that represent:
1. The poet or narrator (if implied)
2. Any people mentioned in the poetry
3. Personifications of natural elements if no humans are mentioned
4. Characters that embody the poetry's emotions or themes

Requirements for character descriptions:
1. Include detailed physical appearance (hair color/style, eye color, facial features, body type)
2. Specify clothing style and distinctive accessories
3. Mention any unique visual characteristics or markings
4. Keep descriptions consistent with the poetry's setting and tone
5. If LoRA information is provided above, consider incorporating relevant style elements
6. Make the characters suitable for visual representation in a poetic, cartoon style"""

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_message), ("user", character_prompt)]
        )

        model_with_tools = get_llm().bind_tools([Characters])
        chain = prompt | model_with_tools

        def try_generate():
            output = chain.invoke({})

            if not hasattr(output, "tool_calls") or not output.tool_calls:
                raise ValueError("No tool calls found in output")

            characters = output.tool_calls[0]["args"]["characters"]

            if not isinstance(characters, list):
                raise ValueError("Characters is not a list")

            result = VisionState(
                prompt=state["prompt"],
                story_full=state["story_full"],
                characters_full=characters,
                pinyin_lyrics=state.get("pinyin_lyrics", "")
            )
            print_success(f"Character extraction completed - {len(characters)} characters identified")
            return result

        def fallback():
            # Create a default character representing the poet/observer
            fallback_characters = [
                {
                    "name": "The Poet",
                    "description": "A contemplative figure observing the scene described in the poetry, dressed in traditional Chinese robes"
                }
            ]
            return VisionState(
                prompt=state["prompt"],
                story_full=state["story_full"],
                characters_full=fallback_characters,
                pinyin_lyrics=state.get("pinyin_lyrics", "")
            )

        return self._retry_with_fallback("Poetry character generation", try_generate, fallback)



    def generate_poetry_scenes(self, state: VisionState) -> VisionState:
        """Generate visual scenes based on the poetry (without image prompts)."""
        status_update("Creating visual scenes from poetry...", "bright_magenta")

        # Format characters for the prompt
        formatted_characters = []
        for character in state["characters_full"]:
            formatted_character = (
                f'name={character["name"]},description={character["description"]}'
            )
            formatted_characters.append(formatted_character)

        character_str = "| ".join(formatted_characters)

        # Get the style from state or use default
        style = state.get("style", self.style)

        system_message = (
            "You are a visual artist specializing in creating scene descriptions from poetry and visual stories. "
            "You create scene breakdowns that capture the essence, mood, and imagery of poetry "
            "focusing on narrative elements rather than image generation prompts. "
            "Focus on the poetic elements: location, time, characters, and actions."
            "the scene is the stroyboard for small video, each scene should be around 5 seconds long"
        )

        # Build the prompt based on whether style is provided
        if style and style.strip():
            scene_prompt = f"""Generate visual scenes based below:

Original Poetry:
{state['prompt'].content}

Visual Story:
{state['story_full'].content}

Characters: {character_str}
Visual Style: {style}

Create {config.MAX_SCENES} scenes focusing on:
1. Location - Where the poetic scene takes place
2. Time - The temporal setting or mood of the poetry
3. Characters - Which characters or elements are present
4. Action - What is happening or being contemplated

The scenes should capture the poetry's essence through narrative elements, maintaining consistency
between scenes in terms of characters and the poetic environment described."""
        else:
            scene_prompt = f"""Generate visual scenes based below:

Original Poetry:
{state['prompt'].content}

Visual Story:
{state['story_full'].content}

Characters: {character_str}

Create {config.MAX_SCENES} scenes focusing on:
1. Location - Where the poetic scene takes place
2. Time - The temporal setting or mood of the poetry
3. Characters - Which characters or elements are present
4. Action - What is happening or being contemplated

The scenes should capture the poetry's essence through narrative elements, maintaining consistency
between scenes in terms of characters and the poetic environment described."""

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_message), ("user", scene_prompt)]
        )

        model_with_tools = get_llm().bind_tools([SceneList])
        chain = prompt | model_with_tools

        def try_generate():
            output = chain.invoke({})

            if not hasattr(output, "tool_calls") or not output.tool_calls:
                raise ValueError("No tool calls found in output")

            scenes = output.tool_calls[0]["args"]["scenes"]

            if not isinstance(scenes, list) or len(scenes) == 0:
                raise ValueError("Invalid scenes generated")

            # Add placeholder prompts that will be filled by generate_prompts node
            processed_scenes = []
            for scene in scenes:
                processed_scene = {
                    "location": scene.get("location", "Unknown location"),
                    "time": scene.get("time", "Unknown time"),
                    "characters": scene.get("characters", []),
                    "action": scene.get("action", "Unknown action"),
                    "image_prompt_positive": None,  # Will be filled by generate_prompts
                    "image_prompt_negative": None   # Will be filled by generate_prompts
                }
                processed_scenes.append(processed_scene)

            result = VisionState(
                prompt=state["prompt"],
                story_full=state["story_full"],
                characters_full=state["characters_full"],
                scenes=processed_scenes,
                pinyin_lyrics=state.get("pinyin_lyrics", ""),
                style=style,
            )
            print_success(f"Scene generation completed - {len(processed_scenes)} scenes created")
            return result

        def fallback():
            # Create basic scenes from the poetry without image prompts
            fallback_scenes = [
                {
                    "location": "Poetry landscape",
                    "time": "Timeless moment",
                    "characters": state["characters_full"],
                    "action": "Contemplating the scene",
                    "image_prompt_positive": None,  # Will be filled by generate_prompts
                    "image_prompt_negative": None,  # Will be filled by generate_prompts
                }
            ]
            return VisionState(
                prompt=state["prompt"],
                story_full=state["story_full"],
                characters_full=state["characters_full"],
                scenes=fallback_scenes,
                pinyin_lyrics=state.get("pinyin_lyrics", ""),
                style=style,
            )

        return self._retry_with_fallback("Poetry scene generation", try_generate, fallback)

    def generate_poetry_audio(self, state: VisionState) -> VisionState:
        """Generate audio using the pinyin lyrics."""
        if not state.get("pinyin_lyrics"):
            print_warning("No pinyin lyrics available for audio generation")
            return state

        # Get the output directory from image paths or create one
        if state.get("image_paths"):
            output_dir = os.path.dirname(state["image_paths"][0])
        else:
            import uuid
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y_%m_%d")
            unique_suffix = str(uuid.uuid4())[:8]
            output_dir = (
                f"{config.DEFAULT_OUTPUT_DIR}/{timestamp}_poetry_{unique_suffix}"
            )
            os.makedirs(output_dir, exist_ok=True)

        status_update("Generating poetry audio...", "bright_yellow")

        try:
            # Use ComfyUI audio client directly with pinyin lyrics
            from ..audio.comfyui_audio import ComfyUIAudioClient

            client = ComfyUIAudioClient()
            audio_path = os.path.join(output_dir, "poetry_song.mp3")

            # Calculate duration based on poetry length
            duration_seconds = max(30, len(state["pinyin_lyrics"]) // 10)  # Rough estimate
            duration_seconds = min(duration_seconds, 120)  # Cap at 2 minutes

            # Generate with poetry-specific tags
            poetry_tags = "chinese traditional, guqin, erhu, bamboo flute, peaceful, meditative, classical chinese, poetic, vocal-driven, immediate vocals"
            
            success = client.generate_audio(
                lyrics=state["pinyin_lyrics"],
                output_path=audio_path,
                tags=poetry_tags,
                duration_seconds=duration_seconds,
            )

            if success:
                state["audio_path"] = audio_path
                print_success(f"Poetry audio generation completed: {audio_path}")
            else:
                print_warning("Poetry audio generation failed")
                state["audio_path"] = None

            return state

        except Exception as e:
            print_warning(f"Error in poetry audio generation: {str(e)}")
            state["audio_path"] = None
            return state

    # Inherit common methods from VideoAgent
    def generate_images(self, state: VisionState) -> VisionState:
        """Generate images for the scenes using ComfyUI and selected model with adaptive LoRA mode."""
        # Get the lora_config_key from lora_config, which is used to determine the model
        lora_key = self.lora_config.get("model_type")
        
        # Convert lora_config_key to actual model name for display and model lookup
        from ykgen.config.image_model_loader import find_model_by_name, get_all_model_names
        
        # Find the model that uses this lora_config_key
        model_name = None
        for name in get_all_model_names():
            model_config = find_model_by_name(name)
            if model_config and model_config.get("lora_config_key") == lora_key:
                model_name = name
                break
        
        # Fallback to a default model if no match found
        if not model_name:
           raise EnvironmentError # Default fallback
        
        # Check if we're in group mode or all mode
        lora_mode = getattr(self, 'lora_mode', 'all')
        
        if lora_mode == 'group':
            status_update(
                f"Generating images for {len(state['scenes'])} poetry scenes using {model_name} (Group Mode - Dynamic LoRA selection)...",
                "bright_cyan",
            )
        elif lora_mode == 'none':
            status_update(
                f"Generating images for {len(state['scenes'])} poetry scenes using {model_name} (None Mode - Base model only)...",
                "bright_cyan",
            )
        else:
            status_update(
                f"Generating images for {len(state['scenes'])} poetry scenes using {model_name} (All Mode - Consistent LoRA usage)...",
                "bright_cyan",
            )

        try:
            # Use the optimized adaptive image generation function
            from ..image.group_mode_image_generator import generate_images_for_scenes_adaptive_optimized
            
            image_paths = generate_images_for_scenes_adaptive_optimized(
                scenes=state["scenes"],
                lora_config=self.lora_config,
                model_name=model_name
            )
                
            print_success(f"Successfully generated {len(image_paths)} images with {model_name}")

            # Preserve pinyin_lyrics and style in state
            return VisionState(
                prompt=state["prompt"],
                story_full=state["story_full"],
                characters_full=state["characters_full"],
                scenes=state["scenes"],
                image_paths=image_paths,
                pinyin_lyrics=state.get("pinyin_lyrics", ""),
                style=state.get("style", self.style),
            )
        except Exception as e:
            print_warning(f"Error generating images: {str(e)}")
            return VisionState(
                prompt=state["prompt"],
                story_full=state["story_full"],
                characters_full=state["characters_full"],
                scenes=state["scenes"],
                image_paths=[],
                pinyin_lyrics=state.get("pinyin_lyrics", ""),
                style=state.get("style", self.style),
            )

    def generate_videos(self, state: VisionState) -> VisionState:
        """Generate videos from the generated images."""
        if not state.get("image_paths"):
            print_warning("No images available for video generation")
            return state

        status_update(
            f"Starting video generation for {len(state['image_paths'])} images...",
            "bright_magenta",
        )

        try:
            # Generate videos using the new task system with selected provider
            video_tasks = generate_videos_from_images(
                image_paths=state["image_paths"],
                scenes=state["scenes"],
                video_provider=self.video_provider,
            )

            state["video_tasks"] = video_tasks
            print_success(f"Started {len(video_tasks)} video generation tasks")

            return state

        except Exception as e:
            print_warning(f"Error starting video generation: {str(e)}")
            return state

    def wait_for_videos(self, state: VisionState) -> VisionState:
        """Wait for all videos to complete generation."""
        video_tasks = state.get("video_tasks", [])

        if not video_tasks:
            print_info("No video tasks to wait for")
            return state

        status_update(
            f"Waiting for {len(video_tasks)} videos to complete...", "bright_blue"
        )

        audio_path = state.get("audio_path")

        success = wait_for_all_videos(
            video_tasks,
            max_wait_minutes=config.VIDEO_TIMEOUT_MINUTES,
            enhance_with_audio=self.enable_audio,
            audio_path=audio_path,
        )

        if success:
            print_success("All videos generated successfully!")
        else:
            print_warning(
                f"Some videos may not have completed within the {config.VIDEO_TIMEOUT_MINUTES} minute timeout"
            )

        return state

    def generate_multiple_images(self, state: VisionState) -> VisionState:
        """Generate multiple images per scene for pure image mode using ComfyUI and selected model with adaptive LoRA mode."""
        # Get the lora_config_key from lora_config, which is used to determine the model
        lora_key = self.lora_config.get("model_type")
        
        # Convert lora_config_key to actual model name for display and model lookup
        from ykgen.config.image_model_loader import find_model_by_name, get_all_model_names
        
        # Find the model that uses this lora_config_key
        model_name = None
        for name in get_all_model_names():
            model_config = find_model_by_name(name)
            if model_config and model_config.get("lora_config_key") == lora_key:
                model_name = name
                break
        
        # Fallback to a default model if no match found
        if not model_name:
            raise EnvironmentError("model config error")  # Default fallback
        
        # Check if we're in group mode or all mode
        lora_mode = getattr(self, 'lora_mode', 'all')
        
        total_images = len(state['scenes']) * self.images_per_scene
        
        if lora_mode == 'group':
            status_update(
                f"Generating {total_images} images ({self.images_per_scene} per scene) for {len(state['scenes'])} poetry scenes using {model_name} (Group Mode - Dynamic LoRA selection)...",
                "bright_cyan",
            )
        elif lora_mode == 'none':
            status_update(
                f"Generating {total_images} images ({self.images_per_scene} per scene) for {len(state['scenes'])} poetry scenes using {model_name} (None Mode - Base model only)...",
                "bright_cyan",
            )
        else:
            status_update(
                f"Generating {total_images} images ({self.images_per_scene} per scene) for {len(state['scenes'])} poetry scenes using {model_name} (All Mode - Consistent LoRA usage)...",
                "bright_cyan",
            )

        try:
            # Create output directory
            import uuid
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y_%m_%d")
            unique_suffix = str(uuid.uuid4())[:8]
            output_dir = f"{config.DEFAULT_OUTPUT_DIR}/{timestamp}_poetry_images_{unique_suffix}"
            os.makedirs(output_dir, exist_ok=True)

            all_image_paths = []
            
            # Generate multiple images for each scene
            for scene_index, scene in enumerate(state["scenes"]):
                scene_image_paths = []
                
                for image_index in range(self.images_per_scene):
                    status_update(
                        f"Generating image {image_index + 1}/{self.images_per_scene} for poetry scene {scene_index + 1}/{len(state['scenes'])}...",
                        "bright_blue",
                    )
                    
                    # Create a single-scene list for the adaptive generation function
                    single_scene = [scene]
                    
                    # Use the optimized adaptive image generation function
                    from ..image.group_mode_image_generator import generate_images_for_scenes_adaptive_optimized
                    
                    image_paths = generate_images_for_scenes_adaptive_optimized(
                        scenes=single_scene,
                        lora_config=self.lora_config,
                        output_dir=output_dir,
                        model_name=model_name
                    )
                    
                    # Add the generated image path
                    if image_paths:
                        # Rename the image to include scene and image indices
                        old_path = image_paths[0]
                        new_filename = f"poetry_scene_{scene_index + 1:03d}_image_{image_index + 1:02d}.png"
                        new_path = os.path.join(output_dir, new_filename)
                        
                        # Rename the file
                        if os.path.exists(old_path):
                            os.rename(old_path, new_path)
                            scene_image_paths.append(new_path)
                        else:
                            scene_image_paths.append(old_path)
                    
                    # Small delay between images to avoid overwhelming the system
                    time.sleep(0.5)
                
                all_image_paths.extend(scene_image_paths)
                
                print_success(f"Generated {len(scene_image_paths)} images for poetry scene {scene_index + 1}")
                
            # Save video prompts to file
            self._save_video_prompts(state, output_dir)
            
            print_success(f"Successfully generated {len(all_image_paths)} poetry images with {model_name}")

            return VisionState(
                prompt=state["prompt"],
                story_full=state["story_full"],
                characters_full=state["characters_full"],
                scenes=state["scenes"],
                image_paths=all_image_paths,
                pinyin_lyrics=state.get("pinyin_lyrics", ""),
                style=state.get("style", self.style),
            )
        except Exception as e:
            print_warning(f"Error generating poetry images: {str(e)}")
            # Return state with empty image paths if generation fails
            return VisionState(
                prompt=state["prompt"],
                story_full=state["story_full"],
                characters_full=state["characters_full"],
                scenes=state["scenes"],
                image_paths=[],
                pinyin_lyrics=state.get("pinyin_lyrics", ""),
                style=state.get("style", self.style),
            )

    def _save_video_prompts(self, state: VisionState, output_dir: str):
        """Save comprehensive video prompts to poetry_generation_record.txt file for manual video generation."""
        status_update("Saving comprehensive video prompts for manual poetry video generation...", "bright_yellow")
        
        record_file = os.path.join(output_dir, "poetry_generation_record.txt")
        
        try:
            with open(record_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("POETRY GENERATION RECORD - PURE IMAGE MODE\n")
                f.write("COMPREHENSIVE VIDEO PROMPTS FOR MANUAL VIDEO GENERATION\n")
                f.write("=" * 80 + "\n\n")
                
                # Write instructions for manual video generation
                f.write("HOW TO USE THESE VIDEO PROMPTS:\n")
                f.write("-" * 40 + "\n")
                f.write("1. Use the generated images as input for video generation tools\n")
                f.write("2. Apply the video prompts below to each corresponding image\n")
                f.write("3. Recommended video settings:\n")
                f.write("   - Duration: 4-8 seconds per clip\n")
                f.write("   - Resolution: 720P or higher\n")
                f.write("   - Frame rate: 24-30 fps\n")
                f.write("4. Suggested video generation tools:\n")
                f.write("   - Runway ML Gen-3\n")
                f.write("   - Pika Labs\n")
                f.write("   - Stable Video Diffusion\n")

                f.write("   - SiliconFlow (Wan2.1 I2V)\n\n")
                
                # Write original poetry
                f.write("ORIGINAL POETRY:\n")
                f.write("-" * 20 + "\n")
                f.write(f"{state['prompt'].content}\n\n")
                
                # Write pinyin lyrics
                if state.get("pinyin_lyrics"):
                    f.write("PINYIN LYRICS:\n")
                    f.write("-" * 20 + "\n")
                    f.write(f"{state['pinyin_lyrics']}\n\n")
                
                # Write generated story
                f.write("GENERATED STORY:\n")
                f.write("-" * 20 + "\n")
                f.write(f"{state['story_full'].content}\n\n")
                
                # Write characters
                f.write("CHARACTERS:\n")
                f.write("-" * 20 + "\n")
                for i, character in enumerate(state["characters_full"], 1):
                    f.write(f"{i}. {character['name']}: {character['description']}\n")
                f.write("\n")
                
                # Write comprehensive video prompts for each scene
                f.write("DETAILED VIDEO GENERATION PROMPTS:\n")
                f.write("-" * 50 + "\n")
                f.write(f"Total scenes: {len(state['scenes'])}\n")
                f.write(f"Images per scene: {self.images_per_scene}\n")
                f.write(f"Total images generated: {len(state['scenes']) * self.images_per_scene}\n\n")
                
                for i, scene in enumerate(state["scenes"], 1):
                    f.write("=" * 60 + "\n")
                    f.write(f"POETRY SCENE {i} - VIDEO GENERATION GUIDE\n")
                    f.write("=" * 60 + "\n")
                    
                    # Scene details
                    f.write(f"Location: {scene.get('location', 'Unknown location')}\n")
                    f.write(f"Time: {scene.get('time', 'Unknown time')}\n")
                    f.write(f"Action: {scene.get('action', 'Unknown action')}\n")
                    f.write(f"Characters: {', '.join([c.get('name', 'Unknown') for c in scene.get('characters', [])])}\n\n")
                    
                    # Generated images for this scene
                    f.write(f"GENERATED IMAGES FOR SCENE {i}:\n")
                    for j in range(self.images_per_scene):
                        f.write(f"  - poetry_scene_{i:03d}_image_{j+1:02d}.png\n")
                    f.write("\n")
                    
                    # Comprehensive video prompts
                    f.write("VIDEO GENERATION PROMPTS:\n")
                    f.write("-" * 30 + "\n")
                    
                    # Primary video prompt (optimized for movement and cinematography)
                    video_prompt_parts = []
                    if scene.get('location'):
                        video_prompt_parts.append(f"camera movement through {scene['location']}")
                    if scene.get('time'):
                        video_prompt_parts.append(f"atmospheric lighting for {scene['time']}")
                    if scene.get('action'):
                        # Make action more video-friendly
                        action = scene['action']
                        video_prompt_parts.append(f"smooth motion: {action}")
                    
                    # Add cinematic elements with poetry-specific aesthetics
                    video_prompt_parts.extend([
                        "cinematic camera movement",
                        "professional film quality",
                        "smooth transitions",
                        "dynamic composition",
                        "depth of field effects",
                        "natural lighting progression",
                        "poetic atmosphere",
                        "classical chinese aesthetics",
                        "elegant camera work"
                    ])
                    
                    primary_prompt = ", ".join(video_prompt_parts)
                    f.write(f"Primary Prompt: {primary_prompt}\n\n")
                    
                    # Alternative prompts for different styles
                    f.write("Alternative Prompts:\n")
                    f.write("1. Slow, meditative camera movement with classical Chinese music\n")
                    f.write("2. Gentle panning shot with soft, natural lighting\n")
                    f.write("3. Poetic zoom effect with atmospheric fog or mist\n")
                    f.write("4. Elegant tracking shot with traditional Chinese elements\n\n")
                    
                    # Audio suggestions
                    f.write("AUDIO SUGGESTIONS:\n")
                    f.write("-" * 20 + "\n")
                    f.write("Use the generated pinyin lyrics with traditional Chinese instruments:\n")
                    f.write("- Guqin (Chinese zither)\n")
                    f.write("- Erhu (Chinese violin)\n")
                    f.write("- Bamboo flute\n")
                    f.write("- Traditional percussion\n\n")
                
                f.write("=" * 80 + "\n")
                f.write("END OF POETRY GENERATION RECORD\n")
                f.write("=" * 80 + "\n")
                
            print_success(f"Poetry generation record saved to: {record_file}")
            
        except Exception as e:
            print_warning(f"Error saving poetry generation record: {str(e)}")

    def create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for poetry processing."""
        workflow = StateGraph(VisionState)

        if self.pure_image_mode:
            # Pure image mode workflow (no video generation)
            workflow.add_node("convert_poetry_to_pinyin", self.convert_poetry_to_pinyin)
            workflow.add_node("generate_poetry_story", self.generate_poetry_story)
            workflow.add_node("generate_poetry_characters", self.generate_poetry_characters)
            workflow.add_node("generate_poetry_scenes", self.generate_poetry_scenes)
            workflow.add_node("generate_prompts", self.generate_prompts)
            workflow.add_node("generate_multiple_images", self.generate_multiple_images)
            
            # Conditionally add audio generation node if enabled
            if self.enable_audio:
                workflow.add_node("generate_poetry_audio", self.generate_poetry_audio)

            # Set entry point and edges for pure image mode
            workflow.set_entry_point("convert_poetry_to_pinyin")
            workflow.add_edge("convert_poetry_to_pinyin", "generate_poetry_story")
            workflow.add_edge("generate_poetry_story", "generate_poetry_characters")
            workflow.add_edge("generate_poetry_characters", "generate_poetry_scenes")
            workflow.add_edge("generate_poetry_scenes", "generate_prompts")
            workflow.add_edge("generate_prompts", "generate_multiple_images")
            
            # Add audio generation to workflow if enabled
            if self.enable_audio:
                workflow.add_edge("generate_multiple_images", "generate_poetry_audio")
                workflow.add_edge("generate_poetry_audio", END)
            else:
                workflow.add_edge("generate_multiple_images", END)
        else:
            # Regular video mode workflow
            workflow.add_node("convert_poetry_to_pinyin", self.convert_poetry_to_pinyin)
            workflow.add_node("generate_poetry_story", self.generate_poetry_story)
            workflow.add_node("generate_poetry_characters", self.generate_poetry_characters)
            workflow.add_node("generate_poetry_scenes", self.generate_poetry_scenes)
            workflow.add_node("generate_prompts", self.generate_prompts)
            workflow.add_node("generate_images", self.generate_images)
            workflow.add_node("generate_videos", self.generate_videos)
            workflow.add_node("generate_poetry_audio", self.generate_poetry_audio)
            workflow.add_node("wait_for_videos", self.wait_for_videos)

            # Set entry point and edges for video mode
            workflow.set_entry_point("convert_poetry_to_pinyin")
            workflow.add_edge("convert_poetry_to_pinyin", "generate_poetry_story")
            workflow.add_edge("generate_poetry_story", "generate_poetry_characters")
            workflow.add_edge("generate_poetry_characters", "generate_poetry_scenes")
            workflow.add_edge("generate_poetry_scenes", "generate_prompts")
            workflow.add_edge("generate_prompts", "generate_images")
            workflow.add_edge("generate_images", "generate_videos")
            workflow.add_edge("generate_videos", "generate_poetry_audio")
            workflow.add_edge("generate_poetry_audio", "wait_for_videos")
            workflow.add_edge("wait_for_videos", END)

        return workflow.compile()

    def generate(self, prompt: str) -> VisionState:
        """Generate a complete poetry video from Chinese poetry input."""
        self.reset_retry_counter()
        
        # Create initial state with prompt (no default style)
        initial_state = VisionState(
            prompt=HumanMessage(content=prompt),
        )
        
        # Create and run the workflow
        workflow = self.create_workflow()
        result = workflow.invoke(initial_state)
        
        return result