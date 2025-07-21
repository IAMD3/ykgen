"""
LLM-based LoRA selection for group mode.

This module handles dynamic LoRA selection per image based on scene content
and LoRA descriptions using LLM intelligence.
"""

from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from kgen.console import status_update, print_success, print_warning
from kgen.providers import get_llm
from kgen.config.constants import GenerationLimits
import time


class LoRASelectionResult(BaseModel):
    """Result of LLM-based LoRA selection."""
    selected_loras: List[str] = Field(description="List of selected LoRA names")
    reasoning: str = Field(description="Explanation of why these LoRAs were selected")


class LoRASelector:
    """LLM-based LoRA selector for group mode."""
    
    def __init__(self):
        """Initialize the LoRA selector."""
        self.llm = get_llm()
        self.llm_with_tools = self.llm.bind_tools([LoRASelectionResult])
    
    def select_loras_for_all_scenes(
        self,
        scenes: List[Dict[str, Any]],
        required_loras: List[Dict[str, Any]],
        optional_loras: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Select LoRAs once for all scenes using LLM intelligence.
        
        This optimized approach analyzes all scenes together to select the most
        appropriate optional LoRAs for the entire story, ensuring consistency
        and reducing LLM API calls.
        
        Args:
            scenes: List of all scene descriptions with location, time, characters, action, and image prompts
            required_loras: List of LoRAs that must always be included
            optional_loras: List of LoRAs that can be optionally selected
            
        Returns:
            Dictionary with selected LoRAs and reasoning for the entire story
        """
        status_update(f"Analyzing {len(scenes)} scenes to select optimal LoRAs for entire story...", "bright_magenta")
        
        # Create the prompt for LLM selection
        system_message = (
            "You are an expert in visual style selection and LoRA model combinations for storytelling. "
            "Your task is to select the most appropriate optional LoRAs for an entire story based on "
            "all scenes, their content, image prompts, and LoRA descriptions. "
            "Consider the overall narrative arc, visual consistency, and how LoRAs will enhance "
            "the entire story rather than individual scenes. "
            "Pay special attention to the visual style keywords across all image prompts as they indicate "
            "the intended visual style for the entire story."
        )
        
        # Format all scenes information
        scenes_description = "All Story Scenes:\n"
        for i, scene in enumerate(scenes, 1):
            scene_description = f"""
Scene {i}:
- Location: {scene.get('location', 'Unknown')}
- Time: {scene.get('time', 'Unknown')}
- Action: {scene.get('action', 'Unknown')}
- Characters: {', '.join([char.get('name', 'Unknown') for char in scene.get('characters', [])])}
- Visual Style: {scene.get('image_prompt_positive', 'Unknown')}
- Avoid: {scene.get('image_prompt_negative', 'None')}
"""
            scenes_description += scene_description
        
        # Format required LoRAs
        required_info = "Required LoRAs (always included):\n"
        for i, lora in enumerate(required_loras, 1):
            required_info += f"{i}. {lora['name']}: {lora['description']}\n"
        
        # Format optional LoRAs
        optional_info = "Optional LoRAs (select best ones for entire story):\n"
        for i, lora in enumerate(optional_loras, 1):
            optional_info += f"{i}. {lora['name']}: {lora['description']}\n"
            if lora.get('trigger'):
                optional_info += f"   Trigger: {lora['trigger']}\n"
        
        # Create selection prompt
        selection_prompt = f"""
Based on all scenes in the story, their image prompts, and available LoRAs, select the most appropriate optional LoRAs for the ENTIRE story.

{scenes_description}

{required_info}

{optional_info}

Guidelines for Story-Wide LoRA Selection:
1. Select 1-3 optional LoRAs that best match the overall story's mood, setting, and visual needs
2. Consider visual consistency across ALL scenes - the selected LoRAs should work well for the entire narrative
3. Pay special attention to recurring visual style keywords across all image prompts (e.g., "watercolor", "pixel art", "cyberpunk")
4. Choose LoRAs that enhance the story's visual coherence and narrative flow
5. Avoid selecting LoRAs that might conflict with any scene's negative prompt or other selected LoRAs
6. Match LoRA trigger words with keywords that appear across multiple scenes when possible
7. Consider the story's emotional arc and how visual style should evolve or remain consistent
8. Provide clear reasoning for your selections based on the overall story analysis
9. If no optional LoRAs are suitable for the entire story, select none

Select the LoRA names exactly as they appear in the list above.
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("user", selection_prompt)
        ])
        
        def try_select():
            chain = prompt | self.llm_with_tools
            output = chain.invoke({})
            
            if not hasattr(output, "tool_calls") or not output.tool_calls:
                raise ValueError("No tool calls found in LLM output")
            
            if len(output.tool_calls) == 0:
                raise ValueError("Empty tool calls list")
            
            selection_result = output.tool_calls[0]["args"]
            
            # Validate selected LoRAs
            valid_lora_names = {lora["name"] for lora in optional_loras}
            selected_names = selection_result["selected_loras"]
            
            # Filter out invalid selections
            valid_selections = [name for name in selected_names if name in valid_lora_names]
            
            if len(valid_selections) != len(selected_names):
                invalid_selections = [name for name in selected_names if name not in valid_lora_names]
                print_warning(f"Invalid LoRA selections filtered out: {invalid_selections}")
            
            # Get the actual LoRA configs for selected names
            selected_lora_configs = []
            for lora in optional_loras:
                if lora["name"] in valid_selections:
                    selected_lora_configs.append(lora)
            
            result = {
                "selected_loras": selected_lora_configs,
                "reasoning": selection_result["reasoning"],
                "total_scenes": len(scenes)
            }
            
            # Log the selection
            if selected_lora_configs:
                selected_names = [lora["name"] for lora in selected_lora_configs]
                print_success(f"Story-wide LoRA selection: {', '.join(selected_names)}")
                print_success(f"Reasoning: {selection_result['reasoning']}")
            else:
                print_success(f"Story-wide LoRA selection: No optional LoRAs selected")
                
            return result
            
        def fallback():
            # Fallback: select first 1-2 optional LoRAs
            fallback_loras = optional_loras[:2] if len(optional_loras) >= 2 else optional_loras
            selected_names = [lora["name"] for lora in fallback_loras]
            
            result = {
                "selected_loras": fallback_loras,
                "reasoning": "Fallback selection due to LLM error - selected first available LoRAs",
                "total_scenes": len(scenes)
            }
            
            print_warning(f"Using fallback LoRA selection: {', '.join(selected_names)}")
            return result
        
        max_attempts = 3
        attempt = 0
        last_exception = None
        while attempt < max_attempts:
            try:
                return try_select()
            except Exception as e:
                attempt += 1
                last_exception = e
                print_warning(f"Error in story-wide LLM LoRA selection (attempt {attempt}): {str(e)}")
                if attempt < max_attempts:
                    print_warning(f"Retrying in {GenerationLimits.LLM_RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(GenerationLimits.LLM_RETRY_DELAY_SECONDS)
        print_warning(f"All {max_attempts} attempts failed. Using fallback selection.")
        return fallback()

    def select_loras_for_scene(
        self,
        scene: Dict[str, Any],
        required_loras: List[Dict[str, Any]],
        optional_loras: List[Dict[str, Any]],
        scene_index: int,
        total_scenes: int
    ) -> Dict[str, Any]:
        """
        Select LoRAs for a specific scene using LLM intelligence.
        
        Args:
            scene: Scene description with location, time, characters, action
            required_loras: List of LoRAs that must always be included
            optional_loras: List of LoRAs that can be optionally selected
            scene_index: Index of current scene (0-based)
            total_scenes: Total number of scenes
            
        Returns:
            Dictionary with selected LoRAs and reasoning
        """
        status_update(f"Scene {scene_index + 1}/{total_scenes}: Selecting LoRAs using LLM...", "bright_magenta")
        
        # Create the prompt for LLM selection
        system_message = (
            "You are an expert in visual style selection and LoRA model combinations. "
            "Your task is to select the most appropriate optional LoRAs for a specific scene "
            "based on the scene content, image prompts, and LoRA descriptions. "
            "Pay special attention to the visual style keywords in the image prompt as they directly indicate "
            "the intended visual style for the generated image. "
            "Consider the scene's mood, setting, characters, actions, and visual style when making selections."
        )
        
        # Format scene information
        scene_description = f"""
Scene Details:
- Location: {scene.get('location', 'Unknown')}
- Time: {scene.get('time', 'Unknown')}
- Action: {scene.get('action', 'Unknown')}
- Characters: {', '.join([char.get('name', 'Unknown') for char in scene.get('characters', [])])}
- Visual Style: {scene.get('image_prompt_positive', 'Unknown')}
- Avoid: {scene.get('image_prompt_negative', 'None')}
"""
        
        # Format required LoRAs
        required_info = "Required LoRAs (always included):\n"
        for i, lora in enumerate(required_loras, 1):
            required_info += f"{i}. {lora['name']}: {lora['description']}\n"
        
        # Format optional LoRAs
        optional_info = "Optional LoRAs (select appropriate ones):\n"
        for i, lora in enumerate(optional_loras, 1):
            optional_info += f"{i}. {lora['name']}: {lora['description']}\n"
            if lora.get('trigger'):
                optional_info += f"   Trigger: {lora['trigger']}\n"
        
        # Create selection prompt
        selection_prompt = f"""
Based on the scene description, image prompts, and available LoRAs, select the most appropriate optional LoRAs for this scene.

{scene_description}

{required_info}

{optional_info}

Guidelines:
1. Select 1-3 optional LoRAs that best match the scene's mood, setting, and visual needs
2. Pay special attention to visual style keywords in the image prompt (e.g., "watercolor", "pixel art", "cyberpunk")
3. Consider how each LoRA's style will complement the scene content and image prompt
4. Avoid selecting LoRAs that conflict with the negative prompt or other selected LoRAs
5. Match LoRA trigger words with keywords in the image prompt when possible
6. Provide clear reasoning for your selections based on the visual style alignment
7. If no optional LoRAs are suitable, select none

Select the LoRA names exactly as they appear in the list above.
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("user", selection_prompt)
        ])
        
        def try_select():
            chain = prompt | self.llm_with_tools
            output = chain.invoke({})
            
            if not hasattr(output, "tool_calls") or not output.tool_calls:
                raise ValueError("No tool calls found in LLM output")
            
            if len(output.tool_calls) == 0:
                raise ValueError("Empty tool calls list")
            
            selection_result = output.tool_calls[0]["args"]
            
            # Validate selected LoRAs
            valid_lora_names = {lora["name"] for lora in optional_loras}
            selected_names = selection_result["selected_loras"]
            
            # Filter out invalid selections
            valid_selections = [name for name in selected_names if name in valid_lora_names]
            
            if len(valid_selections) != len(selected_names):
                invalid_selections = [name for name in selected_names if name not in valid_lora_names]
                print_warning(f"Scene {scene_index + 1}: Invalid LoRA selections filtered out: {invalid_selections}")
            
            # Get the actual LoRA configs for selected names
            selected_lora_configs = []
            for lora in optional_loras:
                if lora["name"] in valid_selections:
                    selected_lora_configs.append(lora)
            
            result = {
                "selected_loras": selected_lora_configs,
                "reasoning": selection_result["reasoning"],
                "scene_index": scene_index
            }
            
            # Log the selection
            if selected_lora_configs:
                selected_names = [lora["name"] for lora in selected_lora_configs]
                print_success(f"Scene {scene_index + 1}: Selected optional LoRAs: {', '.join(selected_names)}")
            else:
                print_success(f"Scene {scene_index + 1}: No optional LoRAs selected")
                
            return result
            
        def fallback():
            # Fallback: select first 1-2 optional LoRAs
            fallback_loras = optional_loras[:2] if len(optional_loras) >= 2 else optional_loras
            selected_names = [lora["name"] for lora in fallback_loras]
            
            result = {
                "selected_loras": fallback_loras,
                "reasoning": "Fallback selection due to LLM error",
                "scene_index": scene_index
            }
            
            print_warning(f"Scene {scene_index + 1}: Using fallback LoRA selection: {', '.join(selected_names)}")
            return result
        
        try:
            return try_select()
        except Exception as e:
            print_warning(f"Scene {scene_index + 1}: Error in LLM LoRA selection: {str(e)}")
            return fallback()
    
    def combine_loras_for_generation(
        self,
        required_loras: List[Dict[str, Any]],
        selected_optional_loras: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Combine required and selected optional LoRAs for image generation.
        
        Args:
            required_loras: List of required LoRAs
            selected_optional_loras: List of selected optional LoRAs
            
        Returns:
            Combined LoRA configuration for image generation
        """
        all_loras = required_loras + selected_optional_loras
        
        if not all_loras:
            return None
        
        # Collect all triggers
        all_triggers = []
        for lora in all_loras:
            if lora.get("trigger"):
                all_triggers.append(lora["trigger"])
        
        # Create combined configuration
        if len(all_loras) == 1:
            # Single LoRA
            lora = all_loras[0]
            return {
                "name": lora["name"],
                "file": lora["file"],
                "trigger": lora.get("trigger", ""),
                "strength_model": lora.get("strength_model", 1.0),
                "strength_clip": lora.get("strength_clip", 1.0),
                "trigger_words": lora.get("trigger_words", {}),
                "essential_traits": lora.get("essential_traits", []),
                "is_multiple": False
            }
        else:
            # Multiple LoRAs
            prepared_loras = []
            for lora in all_loras:
                prepared_lora = {
                    "name": lora["name"],
                    "file": lora["file"],
                    "trigger": lora.get("trigger", ""),
                    "strength_model": lora.get("strength_model", 1.0),
                    "strength_clip": lora.get("strength_clip", 1.0),
                    "trigger_words": lora.get("trigger_words", {}),
                    "essential_traits": lora.get("essential_traits", [])
                }
                prepared_loras.append(prepared_lora)
            
            return {
                "is_multiple": True,
                "loras": prepared_loras,
                "trigger": ", ".join(all_triggers),
                "name": f"Combined LoRAs ({len(prepared_loras)} total)"
            }


def select_loras_for_all_scenes_optimized(
    scenes: List[Dict[str, Any]],
    group_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Select LoRAs once for all scenes using optimized approach.
    
    This function selects LoRAs once for the entire story instead of per scene,
    ensuring visual consistency and reducing LLM API calls.
    
    OPTIMIZATION: This function is called only once after all scenes and prompts
    are successfully generated, making a single LLM call instead of N calls.
    
    Args:
        scenes: List of scene descriptions (must include image prompts)
        group_config: Group mode configuration with required and optional LoRAs
        
    Returns:
        Single LoRA configuration to be used for all scenes
    """
    if group_config.get("mode") != "group":
        raise ValueError("This function is only for group mode")
    
    # Verify that scenes have image prompts
    for i, scene in enumerate(scenes):
        if not scene.get("image_prompt_positive"):
            raise ValueError(f"Scene {i+1} missing image_prompt_positive - prompts must be generated before LoRA selection")
    
    selector = LoRASelector()
    
    required_loras = group_config.get("required_loras", [])
    optional_loras = group_config.get("optional_loras", [])
    
    status_update(f"🎯 OPTIMIZED: Selecting LoRAs once for all {len(scenes)} scenes (after prompts generated)...", "bright_magenta")
    
    # Select LoRAs once for all scenes
    selection_result = selector.select_loras_for_all_scenes(
        scenes=scenes,
        required_loras=required_loras,
        optional_loras=optional_loras
    )
    
    # Combine required and selected optional LoRAs
    combined_config = selector.combine_loras_for_generation(
        required_loras=required_loras,
        selected_optional_loras=selection_result["selected_loras"]
    )
    
    # Add selection metadata
    if combined_config:
        combined_config["selection_reasoning"] = selection_result["reasoning"]
        combined_config["total_scenes"] = selection_result["total_scenes"]
        combined_config["optimized_selection"] = True
    
    print_success(f"✅ Optimized LoRA selection completed for {len(scenes)} scenes (single LLM call)")
    return combined_config


def select_loras_for_scenes(
    scenes: List[Dict[str, Any]],
    group_config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Select LoRAs for all scenes in group mode.
    
    Args:
        scenes: List of scene descriptions
        group_config: Group mode configuration with required and optional LoRAs
        
    Returns:
        List of LoRA configurations for each scene
    """
    if group_config.get("mode") != "group":
        raise ValueError("This function is only for group mode")
    
    selector = LoRASelector()
    scene_lora_configs = []
    
    required_loras = group_config.get("required_loras", [])
    optional_loras = group_config.get("optional_loras", [])
    
    status_update(f"Selecting LoRAs for {len(scenes)} scenes in group mode...", "bright_magenta")
    
    for i, scene in enumerate(scenes):
        # Select LoRAs for this scene
        selection_result = selector.select_loras_for_scene(
            scene=scene,
            required_loras=required_loras,
            optional_loras=optional_loras,
            scene_index=i,
            total_scenes=len(scenes)
        )
        
        # Combine required and selected optional LoRAs
        combined_config = selector.combine_loras_for_generation(
            required_loras=required_loras,
            selected_optional_loras=selection_result["selected_loras"]
        )
        
        # Add selection metadata
        if combined_config:
            combined_config["selection_reasoning"] = selection_result["reasoning"]
            combined_config["scene_index"] = i
        
        scene_lora_configs.append(combined_config)
    
    print_success(f"Group mode LoRA selection completed for {len(scenes)} scenes")
    return scene_lora_configs