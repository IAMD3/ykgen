"""
ComfyUI integration for image generation via waiNSFWIllustrious v120 model.

This module provides functionality to call a local ComfyUI server
for generating images from scene descriptions using waiNSFWIllustrious models.
"""

import copy
import os
from typing import Any, Dict, List, Optional

from .comfyui_image_base import ComfyUIImageClientBase
from kgen.model.models import Scene


class ComfyUIWaiClient(ComfyUIImageClientBase):
    """Client for interacting with ComfyUI server for waiNSFWIllustrious v120 models."""

    def get_default_lora_config(self) -> Dict[str, Any]:
        """Get the default LoRA configuration for waiNSFWIllustrious."""
        return {
            "name": "No LoRA",
            "file": None,
            "trigger": ""
        }

    def get_workflow_template(self) -> Dict[str, Any]:
        """Get the waiNSFWIllustrious workflow template."""
        return {
            "6": {
                "inputs": {
                    "text": "",  # Will be replaced with scene prompt
                    "clip": ["38", 1],  # Connect to LoRA loader output
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Positive Prompt)"},
            },
            "8": {
                "inputs": {"samples": ["31", 0], "vae": ["30", 2]},
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE Decode"},
            },
            "9": {
                "inputs": {"filename_prefix": "ComfyUI", "images": ["8", 0]},
                "class_type": "SaveImage",
                "_meta": {"title": "Save Image"},
            },
            "27": {
                "inputs": {"width": 1024, "height": 1024, "batch_size": 1},
                "class_type": "EmptyLatentImage",
                "_meta": {"title": "EmptySD3LatentImage"},
            },
            "30": {
                "inputs": {"ckpt_name": "waiNSFWIllustrious_v120.safetensors"},
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"},
            },
            "31": {
                "inputs": {
                    "seed": None,  # Will be randomized
                    "steps": 26,
                    "cfg": 7.0,
                    "sampler_name": "euler_ancestral",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["38", 0],  # Connect to LoRA loader output
                    "positive": ["6", 0],  # Connect to positive prompt directly
                    "negative": ["33", 0],
                    "latent_image": ["27", 0],
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"},
            },
            "33": {
                "inputs": {
                    "text": "",  # Empty negative prompt for Flux
                    "clip": ["38", 1],  # Connect to LoRA loader output
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Negative Prompt)"},
            },
            "38": {
                "inputs": {
                    "model": ["30", 0],
                    "clip": ["30", 1],
                    "lora_name": "None",  # Will be updated based on selection
                    "strength_model": 1.0,
                    "strength_clip": 1.0,
                },
                "class_type": "LoraLoader",
                "_meta": {"title": "Load LoRA"},
            },
        }

    def get_resolutions(self) -> List[tuple[int, int]]:
        """Get the available resolutions for waiNSFWIllustrious."""
        return [
            (768, 1344),   # Portrait
            (832, 1216),   # Portrait
            (896, 1152),   # Portrait
            (1024, 1024),  # Square
            (1152, 896),   # Landscape
            (1216, 832),   # Landscape
            (1344, 768),   # Landscape
        ]

    def get_model_name(self) -> str:
        """Get the model name for waiNSFWIllustrious."""
        return "waiNSFWIllustrious v120"

    def get_output_dir_suffix(self) -> str:
        """Get the suffix for output directory naming."""
        return "wai"

    def create_prompt(
        self, positive_prompt: str, negative_prompt: str = "", resolution: Optional[tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """Create a waiNSFWIllustrious workflow prompt from text prompts with LoRA support."""
        prompt = copy.deepcopy(self.get_workflow_template())

        # Set seed if provided in lora_config
        if self.lora_config and "seed" in self.lora_config:
            prompt["31"]["inputs"]["seed"] = self.lora_config["seed"]
            
        # Set resolution
        if resolution:
            prompt["27"]["inputs"]["width"] = resolution[0]
            prompt["27"]["inputs"]["height"] = resolution[1]

        # Handle LoRA configuration
        if not self.lora_config or self.lora_config.get("name") == "No LoRA":
            # No LoRA: Remove LoRA loader, connect directly to checkpoint
            del prompt["38"]  # Remove LoRA loader
            
            # Reconnect nodes to bypass LoRA
            prompt["6"]["inputs"]["clip"] = ["30", 1]  # Connect positive prompt to checkpoint
            prompt["33"]["inputs"]["clip"] = ["30", 1]  # Connect negative prompt to checkpoint
            prompt["31"]["inputs"]["model"] = ["30", 0]  # Connect sampler to checkpoint

            # Set positive prompt as-is (no trigger words to add)
            prompt["6"]["inputs"]["text"] = positive_prompt
        elif self.lora_config.get("is_multiple"):
            # Multiple LoRAs: Create a chain of LoRA loaders
            loras = self.lora_config.get("loras", [])
            active_loras = [lora for lora in loras if lora.get("file")]
            
            if not active_loras:
                # No active LoRAs, treat as no LoRA
                del prompt["38"]
                prompt["6"]["inputs"]["clip"] = ["30", 1]
                prompt["33"]["inputs"]["clip"] = ["30", 1]
                prompt["31"]["inputs"]["model"] = ["30", 0]
                prompt["6"]["inputs"]["text"] = positive_prompt
            else:
                # Remove the single LoRA loader
                del prompt["38"]
                
                # Create chain of LoRA loaders
                last_model_output = ["30", 0]  # Start from checkpoint
                last_clip_output = ["30", 1]
                
                for idx, lora in enumerate(active_loras):
                    lora_node_id = f"38_{idx}"  # 38_0, 38_1, 38_2, etc.
                    
                    prompt[lora_node_id] = {
                        "inputs": {
                            "model": last_model_output,
                            "clip": last_clip_output,
                            "lora_name": lora["file"],
                            "strength_model": lora.get("strength_model", 1.0),
                            "strength_clip": lora.get("strength_clip", 1.0),
                        },
                        "class_type": "LoraLoader",
                        "_meta": {"title": f"Load LoRA {idx + 1}"},
                    }
                    
                    # Update for next iteration
                    last_model_output = [lora_node_id, 0]
                    last_clip_output = [lora_node_id, 1]
                
                # Connect final LoRA outputs to the rest of the workflow
                prompt["6"]["inputs"]["clip"] = last_clip_output
                prompt["33"]["inputs"]["clip"] = last_clip_output
                prompt["31"]["inputs"]["model"] = last_model_output
                
                # Use positive prompt as-is (trigger words already included from prompt generation)
                prompt["6"]["inputs"]["text"] = positive_prompt
        else:
            # Single LoRA: Use existing logic with updated strength values
            if self.lora_config["file"] is None:
                # No LoRA file but config exists
                del prompt["38"]
                prompt["6"]["inputs"]["clip"] = ["30", 1]
                prompt["33"]["inputs"]["clip"] = ["30", 1]
                prompt["31"]["inputs"]["model"] = ["30", 0]
                prompt["6"]["inputs"]["text"] = positive_prompt
            else:
                # Single LoRA with strength values
                prompt["38"]["inputs"]["lora_name"] = self.lora_config["file"]
                prompt["38"]["inputs"]["strength_model"] = self.lora_config.get("strength_model", 1.0)
                prompt["38"]["inputs"]["strength_clip"] = self.lora_config.get("strength_clip", 1.0)
                
                # Use positive prompt as-is (trigger words already included from prompt generation)
                prompt["6"]["inputs"]["text"] = positive_prompt
        
        # Apply recommended settings from LoRA config if present
        # For multiple LoRAs, only use recommended_settings from the first LoRA
        recommended_settings = None
        applying_lora_name = None
        
        if self.lora_config:
            if self.lora_config.get("is_multiple"):
                # Multiple LoRAs: only use recommended_settings from the first LoRA
                loras = self.lora_config.get("loras", [])
                active_loras = [lora for lora in loras if lora.get("file")]
                if active_loras and "recommended_settings" in active_loras[0]:
                    recommended_settings = active_loras[0]["recommended_settings"]
                    applying_lora_name = active_loras[0]["name"]
            else:
                # Single LoRA: use recommended_settings from the main config
                if "recommended_settings" in self.lora_config:
                    recommended_settings = self.lora_config["recommended_settings"]
                    applying_lora_name = self.lora_config["name"]
        
        ksampler_node = prompt["31"]["inputs"]
        
        if recommended_settings:
            # Store original settings for logging
            original_cfg = ksampler_node["cfg"]
            original_sampler = ksampler_node["sampler_name"]
            original_steps = ksampler_node["steps"]
            
            # Apply CFG setting
            if "cfg" in recommended_settings:
                ksampler_node["cfg"] = recommended_settings["cfg"]
            
            # Apply sampler setting (config uses "sampler" but node uses "sampler_name")
            if "sampler" in recommended_settings:
                ksampler_node["sampler_name"] = recommended_settings["sampler"]
            
            # Apply steps setting
            if "steps" in recommended_settings:
                ksampler_node["steps"] = recommended_settings["steps"]
            
            # Log the settings changes
            from ..console import print_success
            print_success(f"⚙️  Applied recommended settings from LoRA: {applying_lora_name}")
            
            changes = []
            if "cfg" in recommended_settings and original_cfg != ksampler_node["cfg"]:
                changes.append(f"CFG: {original_cfg} → {ksampler_node['cfg']}")
            if "sampler" in recommended_settings and original_sampler != ksampler_node["sampler_name"]:
                changes.append(f"Sampler: {original_sampler} → {ksampler_node['sampler_name']}")
            if "steps" in recommended_settings and original_steps != ksampler_node["steps"]:
                changes.append(f"Steps: {original_steps} → {ksampler_node['steps']}")
            
            if changes:
                print(f"     🔧 Settings changed: {', '.join(changes)}")
            else:
                print(f"     ✅ No changes needed (settings already optimal)")
        else:
            # Log default settings when no LoRA recommended_settings
            if self.lora_config and self.lora_config.get("name", "No LoRA") != "No LoRA":
                print(f"     ⚙️  Using default settings (no recommended_settings in LoRA)")
                print(f"     🔧 Default: CFG={ksampler_node['cfg']}, Sampler={ksampler_node['sampler_name']}, Steps={ksampler_node['steps']}")
        
        # Set negative prompt with text exclusion
        if not negative_prompt:
            negative_prompt = "text, words, letters, writing, characters, typography, calligraphy, signs, symbols, numbers, chinese characters, japanese characters, korean characters, arabic text, latin text, cyrillic text, any written language"
        
        prompt["33"]["inputs"]["text"] = negative_prompt

        # Randomize seed
        prompt["31"]["inputs"]["seed"] = int.from_bytes(
            os.urandom(8), byteorder="big"
        ) & ((1 << 63) - 1)

        return prompt


def generate_wai_images_for_scenes(
    scenes: List[Scene], output_dir: Optional[str] = None, lora_config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Convenience function to generate images for scenes using waiNSFWIllustrious v120 model.

    Args:
        scenes: List of Scene objects to generate images for
        output_dir: Optional custom output directory path
        lora_config: Optional LoRA configuration for enhanced image generation

    Returns:
        List of paths to generated image files
    """
    client = ComfyUIWaiClient(lora_config=lora_config)
    return client.generate_scene_images(scenes, output_dir)