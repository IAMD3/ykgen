"""
Abstract base class for ComfyUI image generation clients.

This module provides the common functionality shared across different
ComfyUI image generation implementations (illustrious, flux).
"""

import atexit
import json
import os
import threading
import urllib.parse
import urllib.request
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import websocket

from ykgen.config.config import config
from ..console import print_success, print_warning, step_progress
from ykgen.model.models import Scene

# Global registry for active websocket connections
_active_websockets = []
_websocket_lock = threading.Lock()


def _cleanup_websockets():
    """Cleanup function to properly close all websocket connections."""
    global _active_websockets
    with _websocket_lock:
        for ws in _active_websockets[:]:  # Copy list to avoid modification during iteration
            try:
                if hasattr(ws, "close") and callable(ws.close):
                    ws.close()
            except Exception:
                pass  # Ignore exceptions during cleanup
        _active_websockets.clear()


# Register cleanup function to run at exit
atexit.register(_cleanup_websockets)


class ComfyUIImageClientBase(ABC):
    """Abstract base class for ComfyUI image generation clients."""

    def __init__(self, server_address: Optional[str] = None, lora_config: Optional[Dict[str, Any]] = None):
        """Initialize ComfyUI client with server address and optional LoRA configuration."""
        self.server_address = server_address or config.comfyui_address
        self.client_id = str(uuid.uuid4())
        self.lora_config = lora_config or self.get_default_lora_config()

    @abstractmethod
    def get_default_lora_config(self) -> Dict[str, Any]:
        """Get the default LoRA configuration for this client."""
        pass

    @abstractmethod
    def get_workflow_template(self) -> Dict[str, Any]:
        """Get the workflow template for this client."""
        pass

    @abstractmethod
    def get_resolutions(self) -> List[tuple[int, int]]:
        """Get the available resolutions for this client."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name for this client."""
        pass

    @abstractmethod
    def get_output_dir_suffix(self) -> str:
        """Get the suffix for output directory naming."""
        pass

    @abstractmethod
    def create_prompt(
        self, positive_prompt: str, negative_prompt: str = "", resolution: Optional[tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """Create a workflow prompt from text prompts with LoRA support."""
        pass

    def queue_prompt(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        """Queue a prompt to ComfyUI server."""
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode("utf-8")
        req = urllib.request.Request(f"http://{self.server_address}/prompt", data=data)
        response = urllib.request.urlopen(req)
        return json.loads(response.read())

    def get_image(self, filename: str, subfolder: str, folder_type: str) -> bytes:
        """Get image data from ComfyUI server."""
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(
            f"http://{self.server_address}/view?{url_values}"
        ) as response:
            return response.read()

    def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get history for a specific prompt ID."""
        with urllib.request.urlopen(
            f"http://{self.server_address}/history/{prompt_id}"
        ) as response:
            return json.loads(response.read())

    def get_images(
        self, ws: websocket.WebSocket, prompt: Dict[str, Any]
    ) -> Dict[str, List[bytes]]:
        """Get generated images via websocket connection."""
        prompt_id = self.queue_prompt(prompt)["prompt_id"]
        output_images = {}

        while True:
            try:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message["type"] == "executing":
                        data = message["data"]
                        if data["node"] is None and data["prompt_id"] == prompt_id:
                            break  # Execution is done
                else:
                    continue  # previews are binary data
            except Exception as e:
                print(f"Error receiving websocket message: {e}")
                break

        history = self.get_history(prompt_id)[prompt_id]
        for node_id in history["outputs"]:
            node_output = history["outputs"][node_id]
            images_output = []
            if "images" in node_output:
                for image in node_output["images"]:
                    image_data = self.get_image(
                        image["filename"], image["subfolder"], image["type"]
                    )
                    images_output.append(image_data)
            output_images[node_id] = images_output

        return output_images

    def get_optimal_resolution(self, aspect_ratio: float) -> tuple[int, int]:
        """Get optimal resolution based on aspect ratio."""
        # Find the resolution with the closest aspect ratio
        best_resolution = (1024, 1024)  # Default square
        min_diff = float('inf')
        
        for width, height in self.get_resolutions():
            res_aspect_ratio = width / height
            diff = abs(res_aspect_ratio - aspect_ratio)
            if diff < min_diff:
                min_diff = diff
                best_resolution = (width, height)
        
        return best_resolution

    def generate_scene_images(
        self, scenes: List[Scene], output_dir: Optional[str] = None
    ) -> List[str]:
        """
        Generate images for all scenes and save them to the output directory.

        Args:
            scenes: List of Scene objects to generate images for
            output_dir: Optional custom output directory path

        Returns:
            List of paths to generated image files
        """
        if output_dir is None:
            # Create directory with pattern yyyy_MM_dd_images4story_xxx
            timestamp = datetime.now().strftime("%Y_%m_%d")
            unique_suffix = str(uuid.uuid4())[:8]
            output_dir = f"output/{timestamp}_{self.get_output_dir_suffix()}_{unique_suffix}"

        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        image_paths = []

        # Connect to ComfyUI websocket
        ws = None
        try:
            ws = websocket.WebSocket()

            # Register websocket for cleanup
            with _websocket_lock:
                _active_websockets.append(ws)

            ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")

            # Use progress bar for image generation
            with step_progress(f"Generating images with {self.get_model_name()}", len(scenes)) as (
                progress,
                task,
            ):
                for i, scene in enumerate(scenes, 1):
                    try:
                        progress.update(
                            task,
                            description=f"Generating scene {i}/{len(scenes)} image...",
                        )

                        # Log scene information
                        print_success(f"Scene {i}/{len(scenes)}: {scene.get('location', 'Unknown location')}")
                        print(f"  📝 Positive prompt: {scene['image_prompt_positive']}")
                        print(f"  ❌ Negative prompt: {scene.get('image_prompt_negative', 'None specified')}")
                        
                        # Get optimal resolution (default to landscape)
                        resolution = self.get_optimal_resolution(1216/832)
                        
                        # Create prompt for this scene
                        workflow_prompt = self.create_prompt(
                            positive_prompt=scene['image_prompt_positive'],
                            negative_prompt=scene.get('image_prompt_negative', ''),
                            resolution=resolution
                        )
                        
                        # Apply seed if provided in scene data or lora_config
                        seed_to_use = None
                        if "seed" in scene:
                            seed_to_use = scene["seed"]
                        elif self.lora_config and "seed" in self.lora_config:
                            seed_to_use = self.lora_config["seed"]
                        
                        if seed_to_use is not None:
                            # Find the KSampler node and set the seed
                            for node_id, node in workflow_prompt.items():
                                if node.get("class_type") == "KSampler" and "inputs" in node:
                                    node["inputs"]["seed"] = seed_to_use
                                    print(f"  🌱 Using seed: {seed_to_use}")
                                    break
                        
                        # Log final prompts sent to ComfyUI
                        self._log_prompt_details(workflow_prompt, resolution)
                        
                        # Generate images
                        output_images = self.get_images(ws, workflow_prompt)

                        # Save images from the SaveImage node (node "9")
                        if "9" in output_images:
                            for j, image_data in enumerate(output_images["9"]):
                                filename = f"scene_{i:03d}_{j:02d}.png"
                                filepath = os.path.join(output_dir, filename)

                                with open(filepath, "wb") as f:
                                    f.write(image_data)

                                image_paths.append(filepath)

                        progress.update(task, advance=1)

                    except Exception as e:
                        print_warning(f"Error generating image for scene {i}: {str(e)}")
                        progress.update(task, advance=1)
                        continue

        except Exception as e:
            print_warning(f"Error connecting to ComfyUI server: {str(e)}")
            raise
        finally:
            # Ensure proper cleanup
            if ws is not None:
                try:
                    # Remove from active websockets registry
                    with _websocket_lock:
                        if ws in _active_websockets:
                            _active_websockets.remove(ws)

                    # Close the websocket connection
                    if hasattr(ws, "close") and callable(ws.close):
                        ws.close()
                except Exception:
                    # Ignore exceptions during cleanup
                    pass

        return image_paths

    def _log_prompt_details(self, workflow_prompt: Dict[str, Any], resolution: tuple[int, int]) -> None:
        """Log the details of the workflow prompt being sent to ComfyUI."""
        # This method can be overridden by subclasses to provide specific logging
        # Default implementation logs basic information
        print(f"  📐 Resolution: {resolution[0]}x{resolution[1]}")
        
        # Show seed information if available
        seed_info = None
        for node_id, node in workflow_prompt.items():
            if node.get("class_type") == "KSampler" and "inputs" in node:
                seed = node["inputs"].get("seed")
                if seed is not None:
                    seed_info = seed
                    break
                    
        if seed_info is not None:
            print(f"  🌱 Seed: {seed_info}")
        else:
            print(f"  🌱 Seed: Random (auto-generated)")
        
        # Show LoRA configuration if applicable
        if self.lora_config and self.lora_config.get("name", "No LoRA") != "No LoRA":
            if self.lora_config.get("is_multiple"):
                # Multiple LoRAs
                print(f"  🎨 Multiple LoRAs: {self.lora_config.get('name', 'Unknown')}")
                active_loras = [lora for lora in self.lora_config.get("loras", []) if lora.get("file")]
                for idx, lora in enumerate(active_loras, 1):
                    print(f"     {idx}. {lora['name']} (Model: {lora.get('strength_model', 1.0)}, CLIP: {lora.get('strength_clip', 1.0)})")
                
                if self.lora_config.get("trigger"):
                    print(f"  🔑 Combined trigger words: {self.lora_config['trigger']}")
            else:
                # Single LoRA
                print(f"  🎨 LoRA model: {self.lora_config.get('name', 'No LoRA')}")
                print(f"  🔧 Strength - Model: {self.lora_config.get('strength_model', 1.0)}, CLIP: {self.lora_config.get('strength_clip', 1.0)}")
                if self.lora_config.get("trigger"):
                    print(f"  🔑 Trigger words: {self.lora_config['trigger']}")
        else:
            print(f"  🔧 No LoRA applied")
        
        print()