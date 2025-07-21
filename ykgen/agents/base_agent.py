"""
Abstract base class for YKGen agents.

This module provides the base agent class that all specific agents should inherit from.
"""

from abc import ABC, abstractmethod
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph

from ykgen.config.config import config
from ..console import print_warning, status_update
from ykgen.model.models import VisionState, PromptGeneration
from ..providers import get_llm


class BaseAgent(ABC):
    """Abstract base class for all YKGen agents."""

    def __init__(
        self,
        enable_audio: bool = True,
        style: str = "",
        lora_config: Optional[dict] = None,
        video_provider: str = "siliconflow",
    ):
        """Initialize the base agent with LoRA configuration."""
        self.llm = get_llm()
        self.enable_audio = enable_audio
        self.style = style
        self.lora_config = lora_config or {"name": "No LoRA", "file": None, "trigger": ""}
        self.video_provider = video_provider
        self.shared_retry_count = 0

    def reset_retry_counter(self):
        """Reset the shared retry counter for a new generation workflow."""
        self.shared_retry_count = 0

    def _retry_with_fallback(
        self, operation_name: str, operation_func, fallback_func
    ):
        """Generic retry logic with shared fallback counter."""
        max_retries = config.MAX_GENERATION_RETRIES

        # Check if we've already exceeded the shared retry limit
        if self.shared_retry_count >= max_retries:
            print_warning(
                f"Skipping {operation_name} - already reached maximum {max_retries} retries across all generation methods"
            )
            return fallback_func()

        while self.shared_retry_count < max_retries:
            try:
                return operation_func()
            except (KeyError, IndexError, ValueError, AttributeError) as e:
                self.shared_retry_count += 1
                print_warning(
                    f"{operation_name} attempt {self.shared_retry_count} failed: {str(e)}"
                )
                if self.shared_retry_count >= max_retries:
                    print_warning(
                        f"Failed {operation_name.lower()} after {max_retries} total retries across all generation methods"
                    )
                    return fallback_func()
                else:
                    status_update(
                        f"Retrying {operation_name.lower()}... ({self.shared_retry_count + 1}/{max_retries} total retries)",
                        "yellow",
                    )
                    import time
                    time.sleep(2)
                    continue
            except Exception as e:
                self.shared_retry_count += 1
                print_warning(
                    f"{operation_name} attempt {self.shared_retry_count} failed with LLM error: {str(e)}"
                )
                if self.shared_retry_count >= max_retries:
                    print_warning(
                        f"Failed {operation_name.lower()} after {max_retries} total retries across all generation methods due to LLM issues"
                    )
                    return fallback_func()
                else:
                    status_update(
                        f"Retrying {operation_name.lower()}... ({self.shared_retry_count + 1}/{max_retries} total retries)",
                        "yellow",
                    )
                    import time
                    time.sleep(3)
                    continue
        return fallback_func()

    @abstractmethod
    def create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for the agent."""
        pass

    @abstractmethod
    def generate(self, prompt: str) -> VisionState:
        """Generate output based on the input prompt."""
        pass

    def generate_prompts(self, state: VisionState) -> VisionState:
        """Generate positive and negative prompts for scenes using LLM, including LoRA trigger words when configured."""
        status_update("Generating image prompts for scenes...", "bright_cyan")

        scenes = state["scenes"]
        characters = state["characters_full"]
        style = state.get("style", self.style)
        
        # Format characters for the prompt
        formatted_characters = []
        for character in characters:
            formatted_character = (
                f'name={character["name"]},description={character["description"]}'
            )
            formatted_characters.append(formatted_character)

        character_str = "| ".join(formatted_characters)

        # Build base system message for prompt generation
        system_message = (
            "You are an expert prompt engineer for AI image generation models like Stable Diffusion. "
            "Your task is to generate high-quality positive and negative prompts for each scene to create "
            "stunning visual content. Focus on creating accurate and precise prompt text that maintains "
            "character consistency across scenes.\n\n"
            "EXAMPLE OF HIGH-QUALITY PROMPTS:\n"
            "Positive prompt: 1girl, saber alter, weapon, artoria pendragon \\(fate\\), armor, sword, excalibur morgan \\(fate\\), solo, armored dress, holding sword, holding weapon, holding, blonde hair, gauntlets, yellow eyes, dress, breastplate, braid, masterpiece, best quality, newest, absurdres, highres, very awa\n"
            "Negative prompt: low quality, worst quality, normal quality, text, signature, jpeg artifacts, bad anatomy, old, early\n\n"
            "Follow this format and quality level for all prompts you generate."
        )

        # Build LoRA trigger words context
        lora_context = ""
        if self.lora_config:
            # Handle group mode vs all mode trigger words
            if self.lora_config.get("mode") == "group":
                # Group mode: use required_trigger
                trigger_words = self.lora_config.get("required_trigger", "")
                if trigger_words:
                    lora_context = f"\n\nIMPORTANT: You MUST include these essential trigger words in EVERY positive prompt: '{trigger_words}'. These are required for the required LoRA models to work properly."
            else:
                # All mode: use trigger
                trigger_words = self.lora_config.get("trigger", "")
                if trigger_words and self.lora_config.get("name", "No LoRA") != "No LoRA":
                    lora_context = f"\n\nIMPORTANT: You MUST include these essential trigger words in EVERY positive prompt: '{trigger_words}'. These are required for the LoRA model '{self.lora_config['name']}' to work properly."

        # Build style context only if style is provided
        style_context = ""
        style_requirements = ""
        if style and style.strip():
            style_context = f"Visual Style: {style}"
            style_requirements = f"2. Include the specified visual style ({style}) prominently"
        else:
            style_context = "Visual Style: Not specified - derive style from scene content naturally"
            style_requirements = "2. Derive appropriate visual style naturally from the scene content and story context"

        prompt_text = f"""Generate positive and negative image prompts for each scene below.

Characters: {character_str}
{style_context}
{lora_context}

Requirements for POSITIVE prompts:
1. Describe the scene clearly with who, what, where, and when
{style_requirements}
3. Specify composition (camera angle, framing, depth), lighting and mood
4. Include dominant color palette and any action or motion
5. Add dynamic action words like: dynamic, motion, movement, flowing, intense, dramatic, energetic, vibrant, powerful, striking
6. Maintain character consistency across all scenes
7. Add symbolic elements and contrasts if appropriate
8. Keep under 77 describing words
9. CRITICAL: Images must contain NO TEXT, NO WORDS, NO LETTERS, NO WRITING
10. Focus purely on visual storytelling without any written elements
{"11. MUST include trigger words: '" + (self.lora_config.get("required_trigger", "") if self.lora_config.get("mode") == "group" else self.lora_config.get("trigger", "")) + "' in every prompt" if (self.lora_config.get("mode") == "group" and self.lora_config.get("required_trigger")) or (self.lora_config.get("mode") != "group" and self.lora_config.get("trigger")) else ""}
12. Follow the example format: "1girl, character name, specific details, actions, physical features, quality tags"

Requirements for NEGATIVE prompts:
1. List elements to avoid: text, words, letters, writing, poor quality
2. Include: "text, words, letters, writing, low quality, blurry, distorted, deformed"
3. Add style-specific negative elements if needed
4. Keep concise but comprehensive
5. Follow the example format: "low quality, worst quality, normal quality, text, signature, jpeg artifacts, bad anatomy, old, early"

EXAMPLE FORMAT TO FOLLOW:
Positive: "1girl, saber alter, weapon, artoria pendragon \\(fate\\), armor, sword, excalibur morgan \\(fate\\), solo, armored dress, holding sword, holding weapon, holding, blonde hair, gauntlets, yellow eyes, dress, breastplate, braid, masterpiece, best quality, newest, absurdres, highres, very awa"
Negative: "low quality, worst quality, normal quality, text, signature, jpeg artifacts, bad anatomy, old, early"

Scenes to process: {len(scenes)} scenes

""" + "\n".join([f"Scene {i+1}:\n- Location: {scene.get('location', 'Unknown location')}\n- Time: {scene.get('time', 'Unknown time')}\n- Action: {scene.get('action', 'Unknown action')}\n- Characters: {', '.join([c.get('name', 'Unknown') for c in scene.get('characters', [])])}" for i, scene in enumerate(scenes)]) + f"""

Generate prompts maintaining character and environment consistency across all scenes."""

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_message), ("user", prompt_text)]
        )

        # Use the new PromptGeneration model to get structured prompts
        model_with_tools = get_llm().bind_tools([PromptGeneration])
        chain = prompt | model_with_tools

        def try_generate():
            # Call LLM to generate prompts for all scenes
            output = chain.invoke({})

            if not hasattr(output, "tool_calls") or not output.tool_calls:
                raise ValueError("No tool calls found in output")

            if len(output.tool_calls) == 0:
                raise ValueError("Empty tool calls list")

            prompt_generation = output.tool_calls[0]["args"]["prompts"]

            if not isinstance(prompt_generation, list):
                raise ValueError("Generated prompts is not a list")

            if len(prompt_generation) != len(scenes):
                raise ValueError(f"Prompt count mismatch: expected {len(scenes)}, got {len(prompt_generation)}")

            # Update the original scenes with generated prompts
            updated_scenes = []
            for i, scene in enumerate(scenes):
                updated_scene = scene.copy()
                scene_prompt = prompt_generation[i]
                
                # Extract and validate prompts
                positive_prompt = scene_prompt.get("image_prompt_positive", "")
                negative_prompt = scene_prompt.get("image_prompt_negative", "text, words, letters, writing, low quality, blurry, distorted, deformed")
                
                # Ensure LoRA trigger words are included in positive prompt
                if self.lora_config:
                    if self.lora_config.get("mode") == "group":
                        # Group mode: use required_trigger
                        required_trigger = self.lora_config.get("required_trigger", "")
                        if required_trigger:
                            # Check if all required trigger parts are already present
                            trigger_parts = [part.strip() for part in required_trigger.split(",")]
                            all_parts_present = all(part.lower() in positive_prompt.lower() for part in trigger_parts)
                            if not all_parts_present:
                                positive_prompt = f"{required_trigger}, {positive_prompt}"
                    elif self.lora_config.get("is_multiple"):
                        # Multiple LoRAs - ensure combined trigger words are included
                        combined_trigger = self.lora_config.get("trigger", "")
                        if combined_trigger and combined_trigger not in positive_prompt:
                            positive_prompt = f"{combined_trigger}, {positive_prompt}"
                    else:
                        # Single LoRA
                        if self.lora_config.get("trigger") and self.lora_config.get("name", "No LoRA") != "No LoRA":
                            trigger_words = self.lora_config["trigger"]
                            if trigger_words not in positive_prompt:
                                positive_prompt = f"{trigger_words}, {positive_prompt}"
                
                updated_scene["image_prompt_positive"] = positive_prompt
                updated_scene["image_prompt_negative"] = negative_prompt
                
                # Enhanced logging for prompt generation

                # Display LoRA information (only once)
                if i == 0 and self.lora_config:
                    if self.lora_config.get("mode") == "group":
                        print(f"🎨 Group Mode LoRAs:")
                        print(f"   Required LoRAs (always used):")
                        for j, lora in enumerate(self.lora_config.get("required_loras", []), 1):
                            print(f"     {j}. {lora['name']} (Model: {lora.get('strength_model', 1.0)}, CLIP: {lora.get('strength_clip', 1.0)})")
                        
                        print(f"   Optional LoRAs (LLM decides per image):")
                        for j, lora in enumerate(self.lora_config.get("optional_loras", []), 1):
                            print(f"     {j}. {lora['name']} (Model: {lora.get('strength_model', 1.0)}, CLIP: {lora.get('strength_clip', 1.0)})")
                        
                        if self.lora_config.get("required_trigger"):
                            print(f"🔑 Required Trigger Words: '{self.lora_config['required_trigger']}'")
                    elif self.lora_config.get("is_multiple"):
                        print(f"🎨 Multiple LoRAs: {self.lora_config.get('name', 'Unknown')}")
                        for j, lora in enumerate(self.lora_config.get("loras", []), 1):
                            if lora["name"] != "No LoRA":
                                print(f"   {j}. {lora['name']} (Model: {lora.get('strength_model', 1.0)}, CLIP: {lora.get('strength_clip', 1.0)})")
                        
                        if self.lora_config.get("trigger"):
                            print(f"🔑 Combined Trigger Words: '{self.lora_config['trigger']}'")
                    else:
                        print(f"🎨 LoRA Model: {self.lora_config.get('name', 'Unknown')}")
                        print(f"🔧 Strength - Model: {self.lora_config.get('strength_model', 1.0)}, CLIP: {self.lora_config.get('strength_clip', 1.0)}")
                        
                        if self.lora_config.get("trigger"):
                            print(f"🔑 Trigger Words: '{self.lora_config['trigger']}'")
                    print()
                
                print(f"Scene {i+1} Prompts:")
                print(f"  📍 Location: {scene.get('location', 'Unknown location')}")
                print(f"  ⏰ Time: {scene.get('time', 'Unknown time')}")
                print(f"  🎬 Action: {scene.get('action', 'No action')}")
                print(f"  ✅ Positive: {positive_prompt}")
                print(f"  ❌ Negative: {negative_prompt}")
                print()
                
                updated_scenes.append(updated_scene)
            
            return {"scenes": updated_scenes}

        def fallback():
            # Create basic fallback prompts
            updated_scenes = []
            for scene in scenes:
                fallback_scene = scene.copy()
                
                # Basic positive prompt with LoRA trigger words and optional style
                positive_parts = []
                
                # Add LoRA trigger words first if available
                if self.lora_config:
                    if self.lora_config.get("mode") == "group":
                        # Group mode: use required_trigger
                        required_trigger = self.lora_config.get("required_trigger", "")
                        if required_trigger:
                            positive_parts.append(required_trigger)
                    elif self.lora_config.get("is_multiple"):
                        # Multiple LoRAs - use combined trigger words
                        if self.lora_config.get("trigger"):
                            positive_parts.append(self.lora_config["trigger"])
                    else:
                        # Single LoRA
                        if self.lora_config.get("trigger") and self.lora_config.get("name", "No LoRA") != "No LoRA":
                            positive_parts.append(self.lora_config["trigger"])
                
                # Add style only if provided
                if style and style.strip():
                    positive_parts.extend([style, "style"])
                
                # Add basic scene description following the example format
                positive_parts.extend([
                    scene.get("action", "scene"),
                    "dynamic composition",
                    "masterpiece",
                    "best quality",
                    "newest",
                    "absurdres",
                    "highres",
                    "detailed",
                    "no text"
                ])
                
                fallback_scene["image_prompt_positive"] = ", ".join(positive_parts)
                fallback_scene["image_prompt_negative"] = "low quality, worst quality, normal quality, text, signature, jpeg artifacts, bad anatomy, old, early"
                
                # Log fallback prompt generation

                print("⚠️  Using fallback prompt generation")
                
                # Display LoRA information
                if self.lora_config:
                    if self.lora_config.get("mode") == "group":
                        print(f"🎨 Group Mode LoRAs:")
                        print(f"   Required LoRAs (always used):")
                        for i, lora in enumerate(self.lora_config.get("required_loras", []), 1):
                            print(f"     {i}. {lora['name']} (Model: {lora.get('strength_model', 1.0)}, CLIP: {lora.get('strength_clip', 1.0)})")
                        
                        print(f"   Optional LoRAs (LLM decides per image):")
                        for i, lora in enumerate(self.lora_config.get("optional_loras", []), 1):
                            print(f"     {i}. {lora['name']} (Model: {lora.get('strength_model', 1.0)}, CLIP: {lora.get('strength_clip', 1.0)})")
                        
                        if self.lora_config.get("required_trigger"):
                            print(f"🔑 Required Trigger Words: '{self.lora_config['required_trigger']}'")
                    elif self.lora_config.get("is_multiple"):
                        print(f"🎨 Multiple LoRAs: {self.lora_config.get('name', 'Unknown')}")
                        for i, lora in enumerate(self.lora_config.get("loras", []), 1):
                            if lora["name"] != "No LoRA":
                                print(f"  {i}. {lora['name']} (Model: {lora.get('strength_model', 1.0)}, CLIP: {lora.get('strength_clip', 1.0)})")
                    else:
                        print(f"🎨 LoRA Model: {self.lora_config.get('name', 'Unknown')}")
                        print(f"🔧 Strength - Model: {self.lora_config.get('strength_model', 1.0)}, CLIP: {self.lora_config.get('strength_clip', 1.0)}")
                    
                    if self.lora_config.get("trigger"):
                        print(f"🔑 Trigger Words: '{self.lora_config['trigger']}'")
                
                print(f"\nScene {len(updated_scenes) + 1} Fallback Prompts:")
                print(f"  📍 Location: {scene.get('location', 'Unknown location')}")
                print(f"  ⏰ Time: {scene.get('time', 'Unknown time')}")
                print(f"  🎬 Action: {scene.get('action', 'No action')}")
                print(f"  ✅ Positive: {fallback_scene['image_prompt_positive']}")
                print(f"  ❌ Negative: {fallback_scene['image_prompt_negative']}")
                print()
                
                updated_scenes.append(fallback_scene)
            
            return {"scenes": updated_scenes}

        return self._retry_with_fallback("Prompt generation", try_generate, fallback)