"""
Pure Image Agent for KGen.

This module contains the PureImageAgent class that generates images only,
without video generation. It allows users to specify how many images to generate
per scene and saves video prompts to a text file.
"""

import os
import time
from typing import Optional, List, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import END
from langgraph.graph import StateGraph

from .base_agent import BaseAgent
from kgen.config.config import config
from ..console import (
    print_success,
    print_warning,
    status_update,
)
from kgen.model.models import Characters, SceneList, VisionState
from ..providers import get_llm


class PureImageAgent(BaseAgent):
    """Agent for pure image generation workflows - generates images only, no videos."""

    def __init__(
        self,

        enable_audio: bool = False,  # Can be enabled for audio generation
        style: str = "",
        lora_config: Optional[dict] = None,
        images_per_scene: int = 1,
        language: str = "english",  # New parameter: "english" or "chinese"
    ):
        """Initialize the pure image agent."""
        # Note: video_provider is not used for PureImageAgent since it doesn't generate videos
        super().__init__(enable_audio, style, lora_config)
        self.images_per_scene = images_per_scene
        self.language = language.lower()  # Store language preference
        
        # Validate language parameter
        if self.language not in ["english", "chinese"]:
            print_warning(f"Unsupported language '{language}', defaulting to 'english'")
            self.language = "english"

    def convert_text_to_pinyin(self, text: str) -> str:
        """Convert Chinese text to pinyin format for audio generation."""
        if self.language != "chinese":
            return text  # Return as-is for non-Chinese text
            
        status_update("Converting Chinese text to pinyin format...", "bright_yellow")

        system_message = (
            "You are an expert in Chinese language and pinyin conversion. "
            "Your task is to convert Chinese text into pinyin format suitable for singing."
        )

        pinyin_prompt = f"""Convert the following Chinese text into pinyin format for audio generation.

Text:
{text}

Requirements:
1. Convert each Chinese character to its pinyin with tone numbers (1-4)
2. Group the pinyin by sentences, maintaining the original structure
3. Format as shown in the example:
   [verse]
   [zh]pinyin1 pinyin2 pinyin3...
   
4. Each line should start with [zh] followed by pinyin separated by spaces
5. Separate verses with [verse] markers
6. Maintain the narrative structure

Output ONLY the formatted pinyin, no explanations."""

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_message), ("user", pinyin_prompt)]
        )

        def try_convert():
            chain = prompt | self.llm
            output = chain.invoke({})
            
            if not output or not output.content.strip():
                raise ValueError("Empty pinyin conversion")
            
            print_success("Chinese text to pinyin conversion completed")
            return output.content.strip()

        def fallback():
            # Basic fallback - just use the original text
            print_warning("Pinyin conversion failed, using original text")
            return text

        return self._retry_with_fallback("Pinyin conversion", try_convert, fallback)

    def generate_story(self, state: VisionState) -> VisionState:
        """Generate a story based on the user prompt."""
        status_update("Generating story from prompt...", "bright_green")

        system_message = (
            "You are a writer specializing in writing stories. "
            "You will be provided with a prompt and your goal is to write a story based on that prompt."
        )

        story_prompt = f"""Write a story based on the following prompt. Your story should be engaging and creative, and should be between 100 and 300 words.
        Do not provide any explanations or text apart from the story, the story must be written in english.
        Prompt: {state['prompt'].content}"""

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_message), ("user", story_prompt)]
        )

        def try_generate():
            chain = prompt | self.llm
            output = chain.invoke({})
            
            if not output or not output.content.strip():
                raise ValueError("Empty story generated")
            
            result = VisionState(prompt=state["prompt"], story_full=output)
            print_success("Story generation completed")
            return result

        def fallback():
            # Create a basic fallback story
            fallback_story_content = f"Once upon a time, there was an adventure that began with: {state['prompt'].content}. The story unfolded with courage, challenges, and ultimately triumph."
            fallback_story = AIMessage(content=fallback_story_content)
            return VisionState(prompt=state["prompt"], story_full=fallback_story)

        return self._retry_with_fallback("Story generation", try_generate, fallback)

    def generate_characters(self, state: VisionState) -> VisionState:
        """Generate characters from the story."""
        status_update("Extracting characters from story...", "bright_blue")

        system_message = (
            "You are a writer specializing in writing stories. "
            "You will be provided with a story and your goal is to generate characters based on that story."
        )

        story_prompt = f"""Generate characters (maximum: {config.MAX_CHARACTERS}) based on the following story.
        Story: {state['story_full'].content}"""

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_message), ("user", story_prompt)]
        )

        model_with_tools = get_llm().bind_tools([Characters])
        chain = prompt | model_with_tools

        def try_generate():
            output = chain.invoke({})

            if not hasattr(output, "tool_calls") or not output.tool_calls:
                raise ValueError("No tool calls found in output")

            if len(output.tool_calls) == 0:
                raise ValueError("Empty tool calls list")

            characters = output.tool_calls[0]["args"]["characters"]

            if not isinstance(characters, list):
                raise ValueError("Characters is not a list")

            result = VisionState(
                prompt=state["prompt"],
                story_full=state["story_full"],
                characters_full=characters,
            )
            print_success(
                f"Character extraction completed - {len(characters)} characters generated"
            )
            return result

        def fallback():
            fallback_characters = self._create_fallback_characters(
                state["story_full"].content
            )
            return VisionState(
                prompt=state["prompt"],
                story_full=state["story_full"],
                characters_full=fallback_characters,
            )

        return self._retry_with_fallback("Character generation", try_generate, fallback)

    def generate_scenes(self, state: VisionState) -> VisionState:
        """Generate scenes from the story and characters (without image prompts)."""
        status_update("Creating visual scenes from story...", "bright_magenta")

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
            "You are a writer specializing in breaking down stories into visual scenes. "
            "You will be provided with a story and characters, and your goal "
            "is to generate scene descriptions that capture the key moments and actions of the story. "
            "Focus on the narrative elements: location, time, characters present, and the action taking place. "
            "Do not generate image prompts - only describe the scenes in terms of story elements."
        )

        # Build the prompt based on whether style is provided
        if style and style.strip():
            story_prompt = f"""Generate scenes (maximum: {config.MAX_SCENES}) based on the following story and characters.
        
        Story: {state['story_full'].content}
        Characters: {character_str}
        Visual Style: {style}
        
        For each scene, focus on:
        1. Location - Where the scene takes place
        2. Time - When in the story this happens (beginning, middle, end, etc.)
        3. Characters - Which characters are present in this scene
        4. Action - What is happening in this scene
        
        Create scenes that tell the story visually through character actions and environmental details.
        Each scene should be a distinct moment that advances the narrative."""
        else:
            story_prompt = f"""Generate scenes (maximum: {config.MAX_SCENES}) based on the following story and characters.
        
        Story: {state['story_full'].content}
        Characters: {character_str}
        
        For each scene, focus on:
        1. Location - Where the scene takes place
        2. Time - When in the story this happens (beginning, middle, end, etc.)
        3. Characters - Which characters are present in this scene
        4. Action - What is happening in this scene
        
        Create scenes that tell the story visually through character actions and environmental details.
        Each scene should be a distinct moment that advances the narrative."""

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_message), ("user", story_prompt)]
        )

        model_with_tools = get_llm().bind_tools([SceneList])
        chain = prompt | model_with_tools

        def try_generate():
            output = chain.invoke({})

            if not hasattr(output, "tool_calls") or not output.tool_calls:
                raise ValueError("No tool calls found in output")

            if len(output.tool_calls) == 0:
                raise ValueError("Empty tool calls list")

            scenes = output.tool_calls[0]["args"]["scenes"]

            if not isinstance(scenes, list):
                raise ValueError("Scenes is not a list")

            if len(scenes) == 0:
                raise ValueError("No scenes generated")

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
                style=style,
            )
            print_success(f"Scene generation completed - {len(processed_scenes)} scenes created")
            return result

        def fallback():
            fallback_scenes = self._create_fallback_scenes(
                state["story_full"].content, state["characters_full"], style
            )
            return VisionState(
                prompt=state["prompt"],
                story_full=state["story_full"],
                characters_full=state["characters_full"],
                scenes=fallback_scenes,
                style=style,
            )

        return self._retry_with_fallback("Scene generation", try_generate, fallback)

    def _create_fallback_characters(self, story_content: str) -> list:
        """Create basic fallback characters when LLM fails."""
        status_update("Creating fallback characters...", "yellow")
        # Simple heuristic-based character extraction
        common_names = [
            "hero",
            "protagonist",
            "character",
            "person",
            "knight",
            "warrior",
            "mage",
            "princess",
            "king",
            "queen",
        ]
        fallback_chars = []

        # Try to find character mentions in the story
        story_lower = story_content.lower()
        for name in common_names:
            if name in story_lower:
                fallback_chars.append(
                    {"name": name.title(), "description": f"A {name} from the story"}
                )
                if len(fallback_chars) >= 2:  # Limit to 2 fallback characters
                    break

        # If no characters found, create a generic one
        if not fallback_chars:
            fallback_chars.append(
                {
                    "name": "Main Character",
                    "description": "The protagonist of the story",
                }
            )

        return fallback_chars

    def _create_fallback_scenes(self, story_content: str, characters: list, style: str) -> list:
        """Create basic fallback scenes when LLM fails (without image prompts)."""
        status_update("Creating fallback scenes...", "yellow")

        # Create basic scenes based on story structure
        scenes = []

        # Scene 1: Beginning
        scenes.append(
            {
                "location": "Story setting",
                "time": "Beginning",
                "characters": characters,
                "action": "The story begins",
                "image_prompt_positive": None,  # Will be filled by generate_prompts
                "image_prompt_negative": None,  # Will be filled by generate_prompts
            }
        )

        # Scene 2: Middle (if story is long enough)
        if len(story_content) > 100:
            scenes.append(
                {
                    "location": "Story progression",
                    "time": "Middle",
                    "characters": characters,
                    "action": "The story develops",
                    "image_prompt_positive": None,  # Will be filled by generate_prompts
                    "image_prompt_negative": None,  # Will be filled by generate_prompts
                }
            )

        # Scene 3: End
        scenes.append(
            {
                "location": "Story conclusion",
                "time": "End",
                "characters": characters,
                "action": "The story concludes",
                "image_prompt_positive": None,  # Will be filled by generate_prompts
                "image_prompt_negative": None,  # Will be filled by generate_prompts
            }
        )

        return scenes

    def _generate_multiple_prompts_for_scene(self, scene: Dict[str, Any]) -> List[str]:
        """Generate multiple image prompts for a single scene using LLM.
        
        This ensures character descriptions remain consistent while varying other prompt elements.
        
        Args:
            scene: The scene to generate prompts for
            
        Returns:
            List of positive prompts for the scene
        """
        if self.images_per_scene <= 1:
            return [scene["image_prompt_positive"]]
            
        status_update(
            f"Generating {self.images_per_scene} different prompts for scene: {scene.get('location', 'Unknown')}...",
            "bright_yellow",
        )
        
        # Extract character descriptions to keep them consistent
        character_descriptions = []
        for character in scene.get("characters", []):
            if "name" in character and character["name"] in scene["image_prompt_positive"]:
                # Find the character description in the prompt
                prompt_parts = scene["image_prompt_positive"].split(",")
                for part in prompt_parts:
                    if character["name"] in part:
                        character_descriptions.append(part.strip())
                        break
        
        character_desc_text = ", ".join(character_descriptions) if character_descriptions else ""
        
        # Define a structured model for the prompts
        from langchain_core.tools import tool
        
        @tool
        def ScenePrompts(prompts: List[str]) -> List[str]:
            """Generate multiple prompts for a scene.
            
            Args:
                prompts: List of prompts for the scene
                
            Returns:
                The same list of prompts
            """
            return prompts
        
        system_message = (
            "You are an expert in creating image generation prompts. "
            "Your task is to create multiple variations of a prompt while keeping character descriptions consistent."
        )

        prompt_template = f"""Generate {self.images_per_scene} different image generation prompts for the same scene.

Scene details:
- Location: {scene.get('location', 'Unknown location')}
- Time: {scene.get('time', 'Unknown time')}
- Action: {scene.get('action', 'Unknown action')}
- Characters: {', '.join([c.get('name', 'Unknown') for c in scene.get('characters', [])])}

Original prompt:
{scene["image_prompt_positive"]}

Character descriptions to preserve in ALL prompts:
{character_desc_text}

Requirements:
1. Create {self.images_per_scene} distinct prompts that describe the same scene but with different perspectives, angles, or focus
2. Each prompt should be 50-100 words long
3. Keep ALL character descriptions exactly the same in each prompt
4. Vary elements like camera angle, lighting, focus, composition, or specific actions
5. Maintain the same overall scene and setting
6. Each prompt should be suitable for high-quality image generation
7. Format each prompt as a comma-separated list of descriptors

Return the prompts using the ScenePrompts tool."""

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_message), ("user", prompt_template)]
        )

        def try_generate():
            model_with_tools = get_llm().bind_tools([ScenePrompts])
            chain = prompt | model_with_tools
            output = chain.invoke({})
            
            if not hasattr(output, "tool_calls") or not output.tool_calls:
                raise ValueError("No tool calls found in output")
            
            if len(output.tool_calls) == 0:
                raise ValueError("Empty tool calls list")
            
            prompts = output.tool_calls[0]["args"]["prompts"]
            
            if not prompts or len(prompts) == 0:
                raise ValueError("Empty prompts generated")
            
            # Ensure we have the right number of prompts
            if len(prompts) < self.images_per_scene:
                # If we don't have enough, duplicate the last one
                prompts.extend([prompts[-1]] * (self.images_per_scene - len(prompts)))
            elif len(prompts) > self.images_per_scene:
                # If we have too many, truncate
                prompts = prompts[:self.images_per_scene]
            
            print_success(f"Generated {len(prompts)} prompt variations for the scene")
            return prompts

        def fallback():
            # Create basic variations by adding slight modifications
            base_prompt = scene["image_prompt_positive"]
            variations = [base_prompt]
            
            modifiers = [
                ", different angle", 
                ", different lighting", 
                ", different perspective", 
                ", different composition",
                ", different focus"
            ]
            
            for i in range(1, self.images_per_scene):
                idx = i % len(modifiers)
                variations.append(f"{base_prompt}{modifiers[idx]}")
            
            print_warning(f"Using fallback prompt variations for the scene")
            return variations

        return self._retry_with_fallback("Multiple prompt generation", try_generate, fallback)

    def generate_multiple_images(self, state: VisionState) -> VisionState:
        """Generate multiple images per scene using ComfyUI and selected model with adaptive LoRA mode."""
        model_type = self.lora_config.get("model_type", "flux-schnell") if self.lora_config else "flux-schnell"
        model_name = "Illustrious vPred" if model_type == "illustrious-vpred" else "Wai NSFW Illustrious" if model_type == "wai-illustrious" else "Flux-Schnell"
        
        # Check if we're in group mode or all mode
        lora_mode = getattr(self, 'lora_mode', 'all')
        
        total_images = len(state['scenes']) * self.images_per_scene
        
        if lora_mode == 'group':
            status_update(
                f"Generating {total_images} images ({self.images_per_scene} per scene) for {len(state['scenes'])} scenes using {model_name} (Group Mode - Dynamic LoRA selection)...",
                "bright_cyan",
            )
        else:
            status_update(
                f"Generating {total_images} images ({self.images_per_scene} per scene) for {len(state['scenes'])} scenes using {model_name} (All Mode - Consistent LoRA usage)...",
                "bright_cyan",
            )

        try:
            # Create output directory
            import uuid
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y_%m_%d")
            unique_suffix = str(uuid.uuid4())[:8]
            output_dir = f"{config.DEFAULT_OUTPUT_DIR}/{timestamp}_pure_images_{unique_suffix}"
            os.makedirs(output_dir, exist_ok=True)

            all_image_paths = []
            
            # Generate multiple images for each scene
            for scene_index, scene in enumerate(state["scenes"]):
                scene_image_paths = []
                
                # Generate a random seed for this scene (to be used for all images in this scene)
                import random
                scene_seed = random.randint(1, 2147483647)
                print_success(f"Using seed {scene_seed} for all images in scene {scene_index + 1}")
                
                # Generate multiple prompts for this scene if images_per_scene > 1
                if self.images_per_scene > 1:
                    prompts = self._generate_multiple_prompts_for_scene(scene)
                else:
                    prompts = [scene["image_prompt_positive"]]
                
                for image_index, prompt in enumerate(prompts):
                    status_update(
                        f"Generating image {image_index + 1}/{self.images_per_scene} for scene {scene_index + 1}/{len(state['scenes'])}...",
                        "bright_blue",
                    )
                    
                    # Create a modified scene with the current prompt
                    scene_copy = scene.copy()
                    scene_copy["image_prompt_positive"] = prompt
                    
                    # Create a single-scene list for the adaptive generation function
                    single_scene = [scene_copy]
                    
                    # Use the optimized adaptive image generation function
                    from ..image.group_mode_image_generator import generate_images_for_scenes_adaptive_optimized
                    
                    # Add seed to lora_config
                    lora_config_with_seed = self.lora_config.copy() if self.lora_config else {}
                    lora_config_with_seed["seed"] = scene_seed
                    
                    image_paths = generate_images_for_scenes_adaptive_optimized(
                        scenes=single_scene,
                        lora_config=lora_config_with_seed,
                        output_dir=output_dir,
            
                    )
                    
                    # Add the generated image path
                    if image_paths:
                        # Rename the image to include scene and image indices
                        old_path = image_paths[0]
                        new_filename = f"scene_{scene_index + 1:03d}_image_{image_index + 1:02d}.png"
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
                
                print_success(f"Generated {len(scene_image_paths)} images for scene {scene_index + 1}")
                
            # Save video prompts to file
            self._save_video_prompts(state, output_dir)
            
            print_success(f"Successfully generated {len(all_image_paths)} images with {model_name}")

            return VisionState(
                prompt=state["prompt"],
                story_full=state["story_full"],
                characters_full=state["characters_full"],
                scenes=state["scenes"],
                image_paths=all_image_paths,
                style=state.get("style", self.style),
            )
        except Exception as e:
            print_warning(f"Error generating images: {str(e)}")
            # Return state with empty image paths if generation fails
            return VisionState(
                prompt=state["prompt"],
                story_full=state["story_full"],
                characters_full=state["characters_full"],
                scenes=state["scenes"],
                image_paths=[],
                style=state.get("style", self.style),
            )

    def _save_video_prompts(self, state: VisionState, output_dir: str):
        """Save comprehensive video prompts to story_generation_record.txt file for manual video generation."""
        status_update("Saving comprehensive video prompts for manual video generation...", "bright_yellow")
        
        record_file = os.path.join(output_dir, "story_generation_record.txt")
        
        try:
            with open(record_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("STORY GENERATION RECORD - PURE IMAGE AGENT\n")
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
                
                # Write original prompt
                f.write("ORIGINAL PROMPT:\n")
                f.write("-" * 20 + "\n")
                f.write(f"{state['prompt'].content}\n\n")
                
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
                    f.write(f"SCENE {i} - VIDEO GENERATION GUIDE\n")
                    f.write("=" * 60 + "\n")
                    
                    # Scene details
                    f.write(f"Location: {scene.get('location', 'Unknown location')}\n")
                    f.write(f"Time: {scene.get('time', 'Unknown time')}\n")
                    f.write(f"Action: {scene.get('action', 'Unknown action')}\n")
                    f.write(f"Characters: {', '.join([c.get('name', 'Unknown') for c in scene.get('characters', [])])}\n\n")
                    
                    # Generated images for this scene
                    f.write(f"GENERATED IMAGES FOR SCENE {i}:\n")
                    for j in range(self.images_per_scene):
                        f.write(f"  - scene_{i:03d}_image_{j+1:02d}.png\n")
                    f.write("\n")
                    
                    # If multiple images per scene, note that they share the same seed
                    if self.images_per_scene > 1:
                        f.write(f"NOTE: All images for this scene were generated with the same seed to maintain visual consistency,\n")
                        f.write(f"      but with different prompt variations to provide different perspectives of the same scene.\n\n")
                        
                        # List the different prompts used
                        f.write("PROMPT VARIATIONS USED:\n")
                        # We don't have access to the actual prompts used here, so we'll mention they're in the logs
                        f.write("(See console logs for the exact prompts used for each image)\n\n")
                    
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
                    
                    # Add cinematic elements
                    video_prompt_parts.extend([
                        "cinematic camera movement",
                        "professional film quality",
                        "smooth transitions",
                        "dynamic composition",
                        "depth of field effects",
                        "natural lighting progression"
                    ])
                    
                    primary_prompt = ", ".join(video_prompt_parts)
                    f.write(f"Primary Prompt: {primary_prompt}\n\n")
                    
                    # Alternative prompts for different styles
                    f.write("Alternative Style Prompts:\n")
                    f.write(f"  - Dramatic: {primary_prompt}, dramatic lighting, emotional, intense colors\n")
                    f.write(f"  - Dreamy: {primary_prompt}, dreamy atmosphere, soft focus, gentle motion\n")
                    f.write(f"  - Action: {primary_prompt}, fast cuts, dynamic camera, energetic movement\n")
                    f.write(f"  - Nostalgic: {primary_prompt}, vintage film look, warm tones, film grain\n\n")
                    
                    # Character movement guidance
                    if scene.get('characters'):
                        f.write("Character Movement Guidance:\n")
                        for character in scene.get('characters', []):
                            char_name = character.get('name', 'Character')
                            f.write(f"  - {char_name}: natural movement, realistic expressions, fluid motion\n")
                        f.write("\n")
                    
                    # Technical settings
                    f.write("Recommended Technical Settings:\n")
                    f.write("  - Motion strength: Medium-high\n")
                    f.write("  - Frame interpolation: Enabled\n")
                    f.write("  - Style fidelity: High\n")
                    f.write("  - Duration: 4-6 seconds\n\n")
                
                f.write("=" * 60 + "\n")
                f.write("END OF VIDEO GENERATION GUIDE\n")
                f.write("=" * 60 + "\n")
                
            print_success(f"Saved comprehensive video prompts to {record_file}")
            
        except Exception as e:
            print_warning(f"Error saving video prompts: {str(e)}")

    def generate_story_audio(self, state: VisionState) -> VisionState:
        """Generate audio for the story with language-specific handling."""
        if not self.enable_audio:
            return state  # Skip audio generation if disabled
        
        # Get the output directory from image paths or create one
        if state.get("image_paths"):
            output_dir = os.path.dirname(state["image_paths"][0])
        else:
            import uuid
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y_%m_%d")
            unique_suffix = str(uuid.uuid4())[:8]
            output_dir = f"{config.DEFAULT_OUTPUT_DIR}/{timestamp}_pure_images_{unique_suffix}"
            os.makedirs(output_dir, exist_ok=True)

        status_update(f"Generating {self.language} audio for story...", "bright_yellow")

        try:
            # Generate lyrics for the story
            lyrics_text = self._generate_story_lyrics(state)
            
            # Convert to pinyin if Chinese
            if self.language == "chinese":
                lyrics_text = self.convert_text_to_pinyin(lyrics_text)
            
            # Generate appropriate music tags based on language
            music_tags = self._generate_language_specific_tags(state)
            
            # Use ComfyUI audio client directly
            from ..audio.comfyui_audio import ComfyUIAudioClient

            client = ComfyUIAudioClient()
            audio_path = os.path.join(output_dir, "story_song.mp3")

            # Calculate duration based on story length
            duration_seconds = max(30, len(lyrics_text) // 10)  # Rough estimate
            duration_seconds = min(duration_seconds, 120)  # Cap at 2 minutes

            success = client.generate_audio(
                lyrics=lyrics_text,
                output_path=audio_path,
                tags=music_tags,
                duration_seconds=duration_seconds,
            )

            if success:
                state["audio_path"] = audio_path
                print_success(f"Story audio generation completed: {audio_path}")
            else:
                print_warning("Story audio generation failed")
                state["audio_path"] = None

            return state

        except Exception as e:
            print_warning(f"Error in story audio generation: {str(e)}")
            state["audio_path"] = None
            return state

    def _generate_story_lyrics(self, state: VisionState) -> str:
        """Generate song lyrics based on the story content."""
        system_message = (
            "You are a talented songwriter who creates engaging song lyrics based on stories. "
            "Your songs should capture the essence of the story while being memorable and singable."
        )

        # Calculate appropriate word count
        duration_seconds = max(30, len(state["story_full"].content) // 10)
        duration_seconds = min(duration_seconds, 120)
        min_words = int(duration_seconds * 1.5)
        max_words = int(duration_seconds * 2.5)

        # Language-specific instructions
        if self.language == "chinese":
            language_instruction = "Write the lyrics in Chinese characters. The lyrics will be converted to pinyin for audio generation."
        else:
            language_instruction = "Write the lyrics in English."

        lyrics_prompt = f"""Based on the following story, write song lyrics that capture the narrative and emotions.

Story:
{state["story_full"].content}

Requirements:
- {language_instruction}
- The lyrics should tell the story in a musical way
- Include a chorus that captures the main theme
- Make it emotional and engaging
- Keep it between {min_words}-{max_words} words to fit the {duration_seconds} second duration
- Start with vocals immediately - no long instrumental intro
- Begin with a strong opening line that hooks the listener right away

Write only the lyrics, no explanations or formatting markers."""

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_message), ("user", lyrics_prompt)]
        )

        def try_generate():
            chain = prompt | self.llm
            output = chain.invoke({})
            
            if not output or not output.content.strip():
                raise ValueError("Empty lyrics generated")
            
            return output.content.strip()

        def fallback():
            # Create basic fallback lyrics
            if self.language == "chinese":
                return "这是一个美丽的故事，讲述着奇妙的冒险。让我们一起唱响这首歌，感受故事的魅力。"
            else:
                return "This is a beautiful story, telling of wonderful adventures. Let us sing this song together, feeling the story's magic."

        return self._retry_with_fallback("Lyrics generation", try_generate, fallback)

    def _generate_language_specific_tags(self, state: VisionState) -> str:
        """Generate music tags appropriate for the selected language."""
        if self.language == "chinese":
            # Chinese-specific tags (similar to poetry_agent)
            base_tags = "chinese traditional, guqin, erhu, bamboo flute, peaceful, meditative, classical chinese, vocal-driven, immediate vocals"
        else:
            # English/default tags
            base_tags = "immediate vocals, vocal-driven, soft vocals, pop, piano, guitar, synthesizer, happy, cheerful, lighthearted, voice-first, early vocals"

        # Generate additional tags based on story content
        system_message = (
            "You are a music producer who selects appropriate additional musical styles "
            f"based on story content. The base style is {self.language} music."
        )

        tags_prompt = f"""Based on this story, suggest 3-5 additional music style tags that complement the base {self.language} style:

Story: {state["story_full"].content}

Base tags: {base_tags}

Suggest additional tags that match the story's mood and genre. Focus on:
- Mood: happy, sad, energetic, calm, dramatic, mysterious, romantic, uplifting
- Tempo: fast, slow, medium
- Additional style modifiers that fit {self.language} music

Return only the additional tags as a comma-separated list, no explanations."""

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_message), ("user", tags_prompt)]
        )

        def try_generate():
            chain = prompt | self.llm
            output = chain.invoke({})
            
            additional_tags = output.content.strip()
            if additional_tags:
                return f"{base_tags}, {additional_tags}"
            else:
                return base_tags

        def fallback():
            return base_tags

        return self._retry_with_fallback("Music tags generation", try_generate, fallback)

    def create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for pure image generation."""
        workflow = StateGraph(VisionState)

        # Add nodes (no video generation)
        workflow.add_node("generate_story", self.generate_story)
        workflow.add_node("generate_characters", self.generate_characters)
        workflow.add_node("generate_scenes", self.generate_scenes)
        workflow.add_node("generate_prompts", self.generate_prompts)
        workflow.add_node("generate_multiple_images", self.generate_multiple_images)
        
        # Conditionally add audio generation node if enabled
        if self.enable_audio:
            workflow.add_node("generate_story_audio", self.generate_story_audio)

        # Set entry point and edges
        workflow.set_entry_point("generate_story")
        workflow.add_edge("generate_story", "generate_characters")
        workflow.add_edge("generate_characters", "generate_scenes")
        workflow.add_edge("generate_scenes", "generate_prompts")
        workflow.add_edge("generate_prompts", "generate_multiple_images")
        
        # Add audio generation to workflow if enabled
        if self.enable_audio:
            workflow.add_edge("generate_multiple_images", "generate_story_audio")
            workflow.add_edge("generate_story_audio", END)
        else:
            workflow.add_edge("generate_multiple_images", END)

        return workflow.compile()

    def generate(self, prompt: str) -> VisionState:
        """Generate pure images from a text prompt."""
        self.reset_retry_counter()
        
        # Create initial state with prompt
        initial_state = VisionState(
            prompt=HumanMessage(content=prompt),
        )
        
        # Create and run the workflow
        workflow = self.create_workflow()
        result = workflow.invoke(initial_state)
        
        return result