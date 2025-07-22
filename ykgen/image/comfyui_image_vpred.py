"""
ComfyUI integration for image generation via Illustrious vPred model.

This module provides functionality to call a local ComfyUI server
for generating images from scene descriptions using Illustrious vPred models.
"""

import copy
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .comfyui_image_base import ComfyUIImageClientBase
from .. import Scene


class ComfyUIVPredClient(ComfyUIImageClientBase):
    """Client for interacting with ComfyUI server for vPred models."""

    def __init__(self, lora_config: Optional[Dict[str, Any]] = None, model_name: Optional[str] = None):
        """Initialize the vPred client with optional model configuration."""
        super().__init__(lora_config)
        self.model_config = self._load_model_config(model_name)
    
    def _load_model_config(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Load model configuration from image_model_config.json."""
        config_path = Path(__file__).parent.parent / "config" / "image_model_config.json"
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            vpred_models = config.get("vpred", {}).get("models", [])
            
            if model_name:
                # Find specific model by name
                for model in vpred_models:
                    if model.get("name") == model_name:
                        return model
                raise ValueError(f"Model '{model_name}' not found in configuration")
            else:
                # Find default model
                for model in vpred_models:
                    if model.get("default", False):
                        return model
                # If no default, use first model
                if vpred_models:
                    return vpred_models[0]
                
            # Fallback to hardcoded values if config is missing
            return {
                "name": "Illustrious vPred",
                "checkpoint": "noobaiXLNAIXL_vPred10Version.safetensors",
                "steps": 26,
                "cfg": 5,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": 1,
                "sampling": "v_prediction",
                "zsnr": True,
                "rescale_cfg_multiplier": 0.6
            }
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not load model config: {e}. Using fallback values.")
            return {
                "name": "Illustrious vPred",
                "checkpoint": "noobaiXLNAIXL_vPred10Version.safetensors",
                "steps": 26,
                "cfg": 5,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": 1,
                "sampling": "v_prediction",
                "zsnr": True,
                "rescale_cfg_multiplier": 0.6
            }
    
    def get_lora_config_key(self) -> str:
        """Get the LoRA configuration key for this model."""
        return self.model_config.get("lora_config_key", "illustrious-vpred")

    def get_default_lora_config(self) -> Dict[str, Any]:
        """Get the default LoRA configuration for vPred models."""
        return {
            "name": "Elena Kimberlite (Character)",
            "file": "Elena_Kimberlite_(Character)_ILXL.safetensors",
            "trigger": "kinsou no vermeil"
        }

    def get_workflow_template(self) -> Dict[str, Any]:
        """Get the Illustrious vPred workflow template."""
        return {
            "3": {
                "inputs": {
                    "seed": None,  # Will be randomized
                    "steps": self.model_config.get("steps", 26),
                    "cfg": self.model_config.get("cfg", 5),
                    "sampler_name": self.model_config.get("sampler_name", "euler_ancestral"),
                    "scheduler": self.model_config.get("scheduler", "normal"),
                    "denoise": self.model_config.get("denoise", 1),
                    "model": ["27", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["14", 0],
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"}
            },
            "4": {
                "inputs": {
                    "ckpt_name": self.model_config.get("checkpoint", "noobaiXLNAIXL_vPred10Version.safetensors")
                },
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"}
            },
            "6": {
                "inputs": {
                    "text": "",  # Will be replaced with positive prompt
                    "clip": ["27", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Positive Prompt)"}
            },
            "7": {
                "inputs": {
                    "text": "worst quality, bad hands, bad quality, bad anatomy, jpeg artifacts, signature, scan, watermark, old, oldest",
                    "clip": ["27", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Negative Prompt)"}
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE Decode"}
            },
            "9": {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage",
                "_meta": {"title": "Save Image"}
            },
            "14": {
                "inputs": {
                    "width": 1216,
                    "height": 832,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage",
                "_meta": {"title": "EmptyLatentImage"}
            },
            "27": {
                "inputs": {
                    "model": ["47", 0],
                    "clip": ["4", 1],
                    "lora_name": "Elena_Kimberlite_(Character)_ILXL.safetensors",
                    "strength_model": 1,
                    "strength_clip": 1
                },
                "class_type": "LoraLoader",
                "_meta": {"title": "Load LoRA"}
            },
            "46": {
                "inputs": {
                    "sampling": self.model_config.get("sampling", "v_prediction"),
                    "zsnr": self.model_config.get("zsnr", True),
                    "model": ["4", 0]
                },
                "class_type": "ModelSamplingDiscrete",
                "_meta": {"title": "ModelSamplingDiscrete"}
            },
            "47": {
                "inputs": {
                    "multiplier": self.model_config.get("rescale_cfg_multiplier", 0.6),
                    "model": ["46", 0]
                },
                "class_type": "RescaleCFG",
                "_meta": {"title": "RescaleCFG"}
            }
        }

    def get_resolutions(self) -> List[tuple[int, int]]:
        """Get the available resolutions for vPred models."""
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
        """Get the model name for vPred models."""
        return self.model_config.get("name", "vPred Model")

    def get_output_dir_suffix(self) -> str:
        """Get the suffix for output directory naming."""
        return "illustrious"

    def create_prompt(
        self, positive_prompt: str, negative_prompt: str = "", resolution: Optional[tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """Create a vPred workflow prompt from text prompts with LoRA support."""
        prompt = copy.deepcopy(self.get_workflow_template())
        
        # Set seed if provided in lora_config
        if self.lora_config and "seed" in self.lora_config:
            prompt["3"]["inputs"]["seed"] = self.lora_config["seed"]

        # Handle LoRA configuration
        if not self.lora_config or self.lora_config.get("name") == "No LoRA" or self.lora_config.get("mode") == "none":
            # No LoRA: Remove LoRA loader and connect directly to RescaleCFG (node 47)
            del prompt["27"]  # Remove LoRA loader

            # Reconnect nodes to bypass LoRA - connect to node 47 (RescaleCFG) instead of node 27
            prompt["6"]["inputs"]["clip"] = ["4", 1]  # Connect positive prompt to checkpoint
            prompt["7"]["inputs"]["clip"] = ["4", 1]  # Connect negative prompt to checkpoint
            prompt["3"]["inputs"]["model"] = ["47", 0]  # Connect sampler to RescaleCFG (bypassing LoRA)

            # Set positive prompt as-is (no trigger words to add)
            prompt["6"]["inputs"]["text"] = positive_prompt
        elif self.lora_config.get("is_multiple"):
            # Multiple LoRAs: Create a chain of LoRA loaders
            loras = self.lora_config.get("loras", [])
            active_loras = [lora for lora in loras if lora.get("file")]
            
            if not active_loras:
                # No active LoRAs, treat as no LoRA
                del prompt["27"]

                prompt["6"]["inputs"]["clip"] = ["4", 1]
                prompt["7"]["inputs"]["clip"] = ["4", 1]
                prompt["3"]["inputs"]["model"] = ["47", 0]  # Connect to RescaleCFG (node 47)
                prompt["6"]["inputs"]["text"] = positive_prompt
            else:
                # Remove the single LoRA loader and related nodes
                del prompt["27"]

                
                # Create chain of LoRA loaders
                last_model_output = ["4", 0]  # Start from checkpoint
                last_clip_output = ["4", 1]
                
                for idx, lora in enumerate(active_loras):
                    lora_node_id = f"27_{idx}"  # 27_0, 27_1, 27_2, etc.
                    
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
                prompt["7"]["inputs"]["clip"] = last_clip_output
                prompt["3"]["inputs"]["model"] = last_model_output
                
                # Add trigger words to positive prompt
                trigger_words = self.lora_config.get("trigger", "")
                if trigger_words:
                    prompt["6"]["inputs"]["text"] = f"{trigger_words}, {positive_prompt}"
                else:
                    prompt["6"]["inputs"]["text"] = positive_prompt
        else:
            # Single LoRA: Update the existing LoRA loader
            prompt["27"]["inputs"]["lora_name"] = self.lora_config.get("file", "")
            prompt["27"]["inputs"]["strength_model"] = self.lora_config.get("strength_model", 1.0)
            prompt["27"]["inputs"]["strength_clip"] = self.lora_config.get("strength_clip", 1.0)
            
            # Add trigger words to positive prompt
            trigger_words = self.lora_config.get("trigger", "")
            if trigger_words:
                prompt["6"]["inputs"]["text"] = f"{trigger_words}, {positive_prompt}"
            else:
                prompt["6"]["inputs"]["text"] = positive_prompt

        # Apply recommended settings from LoRA if available
        if self.lora_config and self.lora_config.get("recommended_settings"):
            recommended_settings = self.lora_config["recommended_settings"]
            ksampler_node = prompt["3"]["inputs"]
            
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
                print(f"     🔧 Default: CFG={prompt['3']['inputs']['cfg']}, Sampler={prompt['3']['inputs']['sampler_name']}, Steps={prompt['3']['inputs']['steps']}")
        
        # Set negative prompt - use the default from the workflow plus any additional
        base_negative = "worst quality, bad hands, bad quality, bad anatomy, jpeg artifacts, signature, scan, watermark, old, oldest"
        
        # Add text exclusion to negative prompt
        text_exclusions = "text, words, letters, writing, characters, typography, calligraphy, signs, symbols, numbers, chinese characters, japanese characters, korean characters, arabic text, latin text, cyrillic text, any written language, speech bubble, sound effect, moaning, 2koma, comic, 4koma"
        
        if negative_prompt:
            # Combine all negative prompts
            final_negative_prompt = f"{base_negative}, {negative_prompt}, {text_exclusions}"
        else:
            final_negative_prompt = f"{base_negative}, {text_exclusions}"
        
        prompt["7"]["inputs"]["text"] = final_negative_prompt

        # Set resolution
        if resolution:
            prompt["14"]["inputs"]["width"] = resolution[0]
            prompt["14"]["inputs"]["height"] = resolution[1]

        # Randomize seed for KSampler
        prompt["3"]["inputs"]["seed"] = int.from_bytes(
            os.urandom(8), byteorder="big"
        ) & ((1 << 63) - 1)

        return prompt


def generate_illustrious_images_for_scenes(
    scenes: List[Scene], output_dir: Optional[str] = None, lora_config: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Convenience function to generate images for scenes using Illustrious vPred model.

    Args:
        scenes: List of Scene objects to generate images for
        output_dir: Optional custom output directory path
        lora_config: Optional LoRA configuration for enhanced image generation

    Returns:
        List of paths to generated image files
    """
    client = ComfyUIVPredClient(lora_config=lora_config)
    return client.generate_scene_images(scenes, output_dir)