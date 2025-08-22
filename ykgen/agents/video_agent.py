"""
AI agents for story and video generation.

This module contains the main agents and workflow functions for generating
stories, characters, and scenes using LangChain and LangGraph.
"""

import os
from typing import Optional, Dict

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import END
from langgraph.graph import StateGraph

from .base_agent import BaseAgent
from ..config.model_types import get_model_display_name
from ..audio import generate_story_audio
from ..video import wait_for_all_videos, generate_videos_from_images
from ykgen.config.config import config
from ..console import (
    print_info,
    print_success,
    print_warning,
    status_update,
)
from ykgen.model.models import Characters, SceneList, VisionState
from ..providers import get_llm


class VideoAgent(BaseAgent):
    """Main agent for video/story generation workflows."""

    def __init__(
        self,
        style: str = "",
        enable_audio: bool = True,
        lora_config: Optional[Dict] = None,
        video_provider: str = "siliconflow",
        song_language: str = "english",
    ):
        """
        Initialize VideoAgent.
        
        Args:
            provider: LLM provider to use
            enable_audio: Whether to generate audio
            lora_config: LoRA configuration for image generation
            video_provider: Video generation provider
            song_language: Language for song generation ("english" or "chinese")
        """
        super().__init__(enable_audio, style, lora_config, video_provider)
        
        # Validate song language
        if song_language not in ["english", "chinese"]:
            raise ValueError("song_language must be 'english' or 'chinese'")
        
        self.song_language = song_language

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
        """Generate characters from the story with LoRA-aware character descriptions."""
        status_update("Extracting characters from story with LoRA optimization...", "bright_blue")

        # Build LoRA context for character generation
        lora_context = self._build_lora_context_for_characters()
        
        system_message = (
            "You are a writer specializing in writing stories and character development. "
            "You will be provided with a story and your goal is to generate characters based on that story. "
            "When creating character descriptions, focus on visual details that will help with consistent image generation."
        )

        story_prompt = f"""Generate characters (maximum: {config.MAX_CHARACTERS}) based on the following story.
        
        Story: {state['story_full'].content}
        
        {lora_context}
        
        Requirements for character descriptions:
        1. Include detailed physical appearance (hair color/style, eye color, facial features, body type)
        2. Specify clothing style and distinctive accessories
        3. Mention any unique visual characteristics or markings
        4. Keep descriptions consistent with the story's setting and tone
        5. If LoRA information is provided above, consider incorporating relevant style elements
        6. Focus on visual details that will help maintain character consistency across multiple images
        
        Generate characters that are visually distinctive and well-suited for image generation."""

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
        style = state.get("style") if "style" in state else self.style

        system_message = (
            "You are a writer specializing in breaking down stories into visual scenes. "
            "You will be provided with a story and characters, and your goal "
            "is to generate scene descriptions that capture the key moments and actions of the story. "
            "Focus on the narrative elements: location, time, characters present, and the action taking place. "
            "Do not generate image prompts - only describe the scenes in terms of story elements."
            "the scene is the stroyboard for small video, each scene should be around 5 seconds long"
        )

        # Build the prompt based on whether style is provided
        if style and style.strip():
            story_prompt = f"""Generate scenes (maximum: {config.MAX_SCENES}) based on the following story and characters.
        
        Story: {state['story_full'].content}
        Characters: {character_str}
        Visual Style: {style}
        
        IMPORTANT: You MUST only use the characters listed above. Do NOT create or introduce any new characters that are not in the provided character list. If the story mentions other entities, treat them as environmental elements or background elements, not as characters.
        
        For each scene, focus on:
        1. Location - Where the scene takes place
        2. Time - When in the story this happens (beginning, middle, end, etc.)
        3. Characters - Which characters from the provided list are present in this scene (use ONLY the provided characters)
        4. Action - What is happening in this scene
        
        Create scenes that tell the story visually through character actions and environmental details.
        Each scene should be a distinct moment that advances the narrative."""
        else:
            story_prompt = f"""Generate scenes (maximum: {config.MAX_SCENES}) based on the following story and characters.
        
        Story: {state['story_full'].content}
        Characters: {character_str}
        
        IMPORTANT: You MUST only use the characters listed above. Do NOT create or introduce any new characters that are not in the provided character list. If the story mentions other entities, treat them as environmental elements or background elements, not as characters.
        
        For each scene, focus on:
        1. Location - Where the scene takes place
        2. Time - When in the story this happens (beginning, middle, end, etc.)
        3. Characters - Which characters from the provided list are present in this scene (use ONLY the provided characters)
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
                style=style if style else "",
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
                style=style if style else "",
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
           raise EnvironmentError("model config error")
        
        # Check if we're in group mode or all mode
        lora_mode = getattr(self, 'lora_mode', 'all')
        
        if lora_mode == 'group':
            status_update(
                f"Generating images for {len(state['scenes'])} scenes using {model_name} (Group Mode - Dynamic LoRA selection)...",
                "bright_cyan",
            )
        elif lora_mode == 'none':
            status_update(
                f"Generating images for {len(state['scenes'])} scenes using {model_name} (None Mode - Base model only)...",
                "bright_cyan",
            )
        else:
            status_update(
                f"Generating images for {len(state['scenes'])} scenes using {model_name} (All Mode - Consistent LoRA usage)...",
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

            return VisionState(
                prompt=state["prompt"],
                story_full=state["story_full"],
                characters_full=state["characters_full"],
                scenes=state["scenes"],
                image_paths=image_paths,
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

            # Store task references in state for tracking
            state["video_tasks"] = video_tasks
            print_success(f"Started {len(video_tasks)} video generation tasks")

            return state

        except Exception as e:
            print_warning(f"Error starting video generation: {str(e)}")
            return state

    def generate_audio(self, state: VisionState) -> VisionState:
        """Generate audio/song for the story based on scenes."""
        if not state.get("scenes") or not state.get("story_full"):
            print_warning("No scenes or story available for audio generation")
            return state

        # Get the output directory from image paths or create one
        if state.get("image_paths"):
            output_dir = os.path.dirname(state["image_paths"][0])
        else:
            # Fallback to creating a new directory
            import uuid
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y_%m_%d")
            unique_suffix = str(uuid.uuid4())[:8]
            output_dir = (
                f"{config.DEFAULT_OUTPUT_DIR}/{timestamp}_images4story_{unique_suffix}"
            )
            os.makedirs(output_dir, exist_ok=True)

        status_update(f"Generating {self.song_language} audio/song for the story...", "bright_yellow")

        try:
            if self.song_language == "chinese":
                # Generate Chinese audio using pinyin format
                audio_path = self._generate_chinese_audio(state, output_dir)
            else:
                # Generate English audio using legacy format
                audio_path = generate_story_audio(state, output_dir, self.llm)

            if audio_path:
                state["audio_path"] = audio_path
                print_success(f"Audio generation completed: {audio_path}")
            else:
                print_warning("Audio generation failed")
                state["audio_path"] = None

            return state

        except Exception as e:
            print_warning(f"Error in audio generation: {str(e)}")
            state["audio_path"] = None
            return state

    def _generate_chinese_audio(self, state: VisionState, output_dir: str) -> Optional[str]:
        """Generate Chinese audio using pinyin format similar to PoetryAgent."""
        try:
            # Generate Chinese lyrics and convert to pinyin
            chinese_lyrics = self._generate_chinese_lyrics(state)
            pinyin_lyrics = self._convert_to_pinyin(chinese_lyrics)
            
            # Store pinyin lyrics in state for reference
            state["pinyin_lyrics"] = pinyin_lyrics
            
            # Calculate duration based on number of scenes
            num_scenes = len(state["scenes"])
            duration_seconds = num_scenes * config.AUDIO_DURATION_PER_SCENE
            
            # Generate Chinese music tags
            chinese_tags = "chinese traditional, guqin, erhu, bamboo flute, peaceful, meditative, classical chinese, poetic, vocal-driven, immediate vocals"
            
            # Generate audio using ComfyUI
            from ..audio.comfyui_audio import ComfyUIAudioClient
            
            client = ComfyUIAudioClient()
            audio_path = os.path.join(output_dir, "chinese_story_song.mp3")
            
            success = client.generate_audio(
                lyrics=pinyin_lyrics,
                output_path=audio_path,
                tags=chinese_tags,
                duration_seconds=duration_seconds,
            )
            
            if success:
                return audio_path
            else:
                return None
                
        except Exception as e:
            print_warning(f"Error in Chinese audio generation: {str(e)}")
            return None

    def _generate_chinese_lyrics(self, state: VisionState) -> str:
        """Generate Chinese lyrics based on the story and scenes."""
        system_message = (
            "You are a Chinese poet and songwriter. "
            "Create beautiful Chinese lyrics based on the story and scenes provided."
        )

        lyrics_prompt = f"""Based on this story and scenes, create Chinese lyrics for a song:

Story: {state['story_full'].content}

Scenes: {[scene['action'] for scene in state['scenes']]}

Requirements:
1. Write lyrics in Chinese (Simplified or Traditional)
2. Create 4-8 lines of lyrics that capture the essence of the story
3. Make the lyrics poetic and suitable for singing
4. Focus on the emotional and visual elements of the story
5. Keep each line concise and melodic

Output ONLY the Chinese lyrics, no explanations."""

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_message), ("user", lyrics_prompt)]
        )

        def try_generate():
            chain = prompt | self.llm
            output = chain.invoke({})
            
            if not output or not output.content.strip():
                raise ValueError("Empty Chinese lyrics generated")
            
            return output.content.strip()

        def fallback():
            # Create basic fallback Chinese lyrics
            return "这是一个美丽的故事，充满了希望和梦想。让我们一起探索这个奇妙的世界。"

        return self._retry_with_fallback("Chinese lyrics generation", try_generate, fallback)

    def _convert_to_pinyin(self, chinese_text: str) -> str:
        """Convert Chinese text to pinyin format for audio generation."""
        system_message = (
            "You are an expert in Chinese pinyin conversion. "
            "Convert Chinese text to pinyin format suitable for singing."
        )

        pinyin_prompt = f"""Convert the following Chinese text into pinyin format for audio generation.

Chinese Text:
{chinese_text}

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
            [("system", system_message), ("user", pinyin_prompt)]
        )

        def try_convert():
            chain = prompt | self.llm
            output = chain.invoke({})
            
            if not output or not output.content.strip():
                raise ValueError("Empty pinyin conversion")
            
            return output.content.strip()

        def fallback():
            # Basic fallback - just use the original text
            print_warning("Pinyin conversion failed, using original text")
            return chinese_text

        return self._retry_with_fallback("Pinyin conversion", try_convert, fallback)

    def wait_for_videos(self, state: VisionState) -> VisionState:
        """Wait for all videos to complete generation."""
        video_tasks = state.get("video_tasks", [])

        if not video_tasks:
            print_info("No video tasks to wait for")
            return state

        status_update(
            f"Waiting for {len(video_tasks)} videos to complete...", "bright_blue"
        )

        # Get audio path from state if available
        audio_path = state.get("audio_path")

        # Wait for all videos to complete with audio enhancement
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

    def create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for story generation."""
        workflow = StateGraph(VisionState)

        # Add nodes
        workflow.add_node("generate_story", self.generate_story)
        workflow.add_node("generate_characters", self.generate_characters)
        workflow.add_node("generate_scenes", self.generate_scenes)
        workflow.add_node("generate_prompts", self.generate_prompts)
        workflow.add_node("generate_images", self.generate_images)
        workflow.add_node("generate_videos", self.generate_videos)
        workflow.add_node("generate_audio", self.generate_audio)
        workflow.add_node("wait_for_videos", self.wait_for_videos)

        # Set entry point and edges
        workflow.set_entry_point("generate_story")
        workflow.add_edge("generate_story", "generate_characters")
        workflow.add_edge("generate_characters", "generate_scenes")
        workflow.add_edge("generate_scenes", "generate_prompts")
        workflow.add_edge("generate_prompts", "generate_images")
        workflow.add_edge("generate_images", "generate_videos")
        workflow.add_edge("generate_videos", "generate_audio")
        workflow.add_edge("generate_audio", "wait_for_videos")
        workflow.add_edge("wait_for_videos", END)

        return workflow.compile()

    def generate(self, prompt: str) -> VisionState:
        """Generate a complete video story from a text prompt."""
        self.reset_retry_counter()
        
        # Create initial state with prompt
        initial_state = VisionState(
            prompt=HumanMessage(content=prompt),
        )
        
        # Add style if provided
        if self.style:
            initial_state["style"] = self.style
        
        # Create and run the workflow
        workflow = self.create_workflow()
        result = workflow.invoke(initial_state)
        
        return result
