"""
ComfyUI integration for image generation via Flux.

This module provides functionality to call a local ComfyUI server
for generating images from scene descriptions using Flux models.
"""

import copy
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .comfyui_image_base import ComfyUIImageClientBase
from ..config.image_model_loader import get_image_model_config_path
from ..console import print_success
from .. import Scene


class ComfyUISimpleClient(ComfyUIImageClientBase):
    """Client for interacting with ComfyUI server for simple models."""

    def __init__(self, lora_config: Optional[Dict[str, Any]] = None, model_name: Optional[str] = None):
        """Initialize the simple client with optional model configuration."""
        super().__init__(lora_config=lora_config)
        self.model_config = self._load_model_config(model_name)

    def _load_model_config(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Load model configuration from image_model_config.json."""
        config_path = get_image_model_config_path()

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            simple_models = config.get("simple", {}).get("models", [])

            if model_name:
                # Find specific model by name
                for model in simple_models:
                    if model.get("name") == model_name:
                        return model
                raise ValueError(f"Model '{model_name}' not found in configuration")
            else:
                # Find default model
                for model in simple_models:
                    if model.get("default", False):
                        return model
                # If no default, use first model
                if simple_models:
                    return simple_models[0]

            # Fallback to hardcoded values if config is missing
            return {
                "name": "Flux Schnell",
                "checkpoint": "flux1-schnell-fp8.safetensors",
                "steps": 4,
                "cfg": 1,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1,
                "guidance": 3.5
            }
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not load model config: {e}. Using fallback values.")
            return {
                "name": "Flux Schnell",
                "checkpoint": "flux1-schnell-fp8.safetensors",
                "steps": 4,
                "cfg": 1,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1,
                "guidance": 3.5
            }

    def get_lora_config_key(self) -> str:
        """Get the LoRA configuration key for this model."""
        return self.model_config.get("lora_config_key", "flux-schnell")

    def get_default_lora_config(self) -> Dict[str, Any]:
        """Get the default LoRA configuration for simple models."""
        return {"name": "No LoRA", "file": None, "trigger": ""}

    def get_workflow_template(self) -> Dict[str, Any]:
        """Get the Flux workflow template."""
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
                "class_type": "EmptySD3LatentImage",
                "_meta": {"title": "EmptySD3LatentImage"},
            },
            "30": {
                "inputs": {"ckpt_name": self.model_config.get("checkpoint", "flux1-schnell-fp8.safetensors")},
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"},
            },
            "31": {
                "inputs": {
                    "seed": None,  # Will be randomized
                    "steps": self.model_config.get("steps", 4),
                    "cfg": self.model_config.get("cfg", 1),
                    "sampler_name": self.model_config.get("sampler_name", "euler"),
                    "scheduler": self.model_config.get("scheduler", "simple"),
                    "denoise": self.model_config.get("denoise", 1),
                    "model": ["38", 0],  # Connect to LoRA loader output
                    "positive": ["39", 0],  # Connect to FluxGuidance output
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
                    "lora_name": "flux_illustriousXL_schnell_v1-rev2.safetensors",  # Will be updated based on selection
                    "strength_model": 0.5,
                    "strength_clip": 0.5,
                },
                "class_type": "LoraLoader",
                "_meta": {"title": "Load LoRA"},
            },
            "39": {
                "inputs": {
                    "conditioning": ["6", 0],
                    "guidance": self.model_config.get("guidance", 3.5),
                },
                "class_type": "FluxGuidance",
                "_meta": {"title": "FluxGuidance"},
            },
        }

    def get_resolutions(self) -> List[tuple[int, int]]:
        """Get the available resolutions for simple models."""
        return [
            (1024, 1024),  # Square (default for simple models)
        ]

    def get_model_name(self) -> str:
        """Get the model name for simple models."""
        return self.model_config.get("name", "Simple Model")

    def get_output_dir_suffix(self) -> str:
        """Get the suffix for output directory naming."""
        return "images4story"

    def create_prompt(
            self, positive_prompt: str, negative_prompt: str = "", resolution: Optional[tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """Create a simple model workflow prompt from text prompts with LoRA support."""
        prompt = copy.deepcopy(self.get_workflow_template())

        # Set seed if provided in lora_config
        if self.lora_config and "seed" in self.lora_config:
            prompt["31"]["inputs"]["seed"] = self.lora_config["seed"]

        # Handle LoRA configuration
        if not self.lora_config or self.lora_config.get("name") == "No LoRA" or self.lora_config.get("mode") == "none":
            # No LoRA: Remove LoRA loader and FluxGuidance, connect directly to checkpoint
            del prompt["38"]  # Remove LoRA loader
            del prompt["39"]  # Remove FluxGuidance

            # Reconnect nodes to bypass LoRA
            prompt["6"]["inputs"]["clip"] = ["30", 1]  # Connect positive prompt to checkpoint
            prompt["33"]["inputs"]["clip"] = ["30", 1]  # Connect negative prompt to checkpoint
            prompt["31"]["inputs"]["model"] = ["30", 0]  # Connect sampler to checkpoint
            prompt["31"]["inputs"]["positive"] = ["6", 0]  # Connect sampler to positive prompt directly

            # Set positive prompt as-is (no trigger words to add)
            prompt["6"]["inputs"]["text"] = positive_prompt
        elif self.lora_config.get("is_multiple"):
            # Multiple LoRAs: Create a chain of LoRA loaders
            loras = self.lora_config.get("loras", [])
            active_loras = [lora for lora in loras if lora.get("file")]

            if not active_loras:
                # No active LoRAs, treat as no LoRA
                del prompt["38"]
                del prompt["39"]
                prompt["6"]["inputs"]["clip"] = ["30", 1]
                prompt["33"]["inputs"]["clip"] = ["30", 1]
                prompt["31"]["inputs"]["model"] = ["30", 0]
                prompt["31"]["inputs"]["positive"] = ["6", 0]
                prompt["6"]["inputs"]["text"] = positive_prompt
            else:
                # Remove the single LoRA loader and FluxGuidance
                del prompt["38"]
                del prompt["39"]

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

                    # Update connections for next iteration
                    last_model_output = [lora_node_id, 0]
                    last_clip_output = [lora_node_id, 1]

                # Connect final outputs
                prompt["6"]["inputs"]["clip"] = last_clip_output
                prompt["33"]["inputs"]["clip"] = last_clip_output
                prompt["31"]["inputs"]["model"] = last_model_output
                prompt["31"]["inputs"]["positive"] = ["6", 0]

                # Add trigger words to positive prompt
                trigger_words = self.lora_config.get("trigger", "")
                if trigger_words:
                    prompt["6"]["inputs"]["text"] = f"{trigger_words}, {positive_prompt}"
                else:
                    prompt["6"]["inputs"]["text"] = positive_prompt
        else:
            # Single LoRA: Update the existing LoRA loader
            prompt["38"]["inputs"]["lora_name"] = self.lora_config.get("file", "")
            prompt["38"]["inputs"]["strength_model"] = self.lora_config.get("strength_model", 1.0)
            prompt["38"]["inputs"]["strength_clip"] = self.lora_config.get("strength_clip", 1.0)

            # Add trigger words to positive prompt
            trigger_words = self.lora_config.get("trigger", "")
            if trigger_words:
                prompt["6"]["inputs"]["text"] = f"{trigger_words}, {positive_prompt}"
            else:
                prompt["6"]["inputs"]["text"] = positive_prompt

        # Apply recommended settings from LoRA if available
        if self.lora_config and self.lora_config.get("recommended_settings"):
            recommended_settings = self.lora_config["recommended_settings"]
            ksampler_node = prompt["31"]["inputs"]

            # Store original values for logging
            original_cfg = ksampler_node["cfg"]
            original_sampler = ksampler_node["sampler_name"]
            original_steps = ksampler_node["steps"]

            # Apply recommended settings
            if "cfg" in recommended_settings:
                ksampler_node["cfg"] = recommended_settings["cfg"]
            if "sampler" in recommended_settings:
                ksampler_node["sampler_name"] = recommended_settings["sampler"]
            if "steps" in recommended_settings:
                ksampler_node["steps"] = recommended_settings["steps"]

            # Log the changes
            applying_lora_name = self.lora_config.get("name", "Unknown LoRA")
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

            # Log ignored settings for multiple LoRAs
            if self.lora_config and self.lora_config.get("is_multiple"):
                loras = self.lora_config.get("loras", [])
                active_loras = [lora for lora in loras if lora.get("file")]
                ignored_loras = [lora for lora in active_loras[1:] if "recommended_settings" in lora]

                if ignored_loras:
                    print(f"     ⚠️  Ignored settings from {len(ignored_loras)} additional LoRA(s):")
                    for i, lora in enumerate(ignored_loras, 2):
                        settings = lora["recommended_settings"]
                        ignored_parts = []
                        if "cfg" in settings:
                            ignored_parts.append(f"CFG: {settings['cfg']}")
                        if "sampler" in settings:
                            ignored_parts.append(f"Sampler: {settings['sampler']}")
                        if "steps" in settings:
                            ignored_parts.append(f"Steps: {settings['steps']}")
                        print(f"        {i}. {lora['name']}: {', '.join(ignored_parts)}")
        else:
            # Log default settings when no LoRA recommended_settings
            if self.lora_config and self.lora_config.get("name", "No LoRA") != "No LoRA":
                print(f"     ⚙️  Using default settings (no recommended_settings in LoRA)")
                print(
                    f"     🔧 Default: CFG={prompt['31']['inputs']['cfg']}, Sampler={prompt['31']['inputs']['sampler_name']}, Steps={prompt['31']['inputs']['steps']}")

        # Set negative prompt with text exclusion
        if not negative_prompt:
            negative_prompt = "text, words, letters, writing, characters, typography, calligraphy, signs, symbols, numbers, chinese characters, japanese characters, korean characters, arabic text, latin text, cyrillic text, any written language"

        prompt["33"]["inputs"]["text"] = negative_prompt

        # Randomize seed
        prompt["31"]["inputs"]["seed"] = int.from_bytes(
            os.urandom(8), byteorder="big"
        ) & ((1 << 63) - 1)

        return prompt


def generate_images_for_scenes(
        scenes: List[Scene], output_dir: Optional[str] = None, lora_config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Convenience function to generate images for scenes using default ComfyUI client.

    Args:
        scenes: List of Scene objects to generate images for
        output_dir: Optional custom output directory path
        lora_config: Optional LoRA configuration for enhanced image generation

    Returns:
        List of paths to generated image files
    """
    client = ComfyUISimpleClient(lora_config=lora_config)
    return client.generate_scene_images(scenes, output_dir)
