"""
Video generation module for KGen.

This module handles video generation from images using the SiliconFlow API
with Wan-AI models.
"""

import base64
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from ..console import (
    print_info,
    print_success,
    print_warning,
    status_update,
)
from kgen.config.config import config
from kgen.config.constants import VideoDefaults


class VideoGenerationClient:
    """Client for generating videos using SiliconFlow API."""

    def __init__(self, api_key: str, base_url: str = "https://api.siliconflow.cn/v1"):
        """
        Initialize the video generation client.

        Args:
            api_key: SiliconFlow API key
            base_url: Base URL for the API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        # Initialize request kwargs
        self.request_kwargs = {}

    def _encode_image_to_base64(self, image_path: str) -> str:
        """Encode an image file to base64 string."""
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded}"

    def submit_video_generation(
        self,
        image_path: str,
        prompt: str,
        model: str = "Wan-AI/Wan2.1-I2V-14B-720P-Turbo",
        image_size: str = "1280x720",
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> Optional[str]:
        """
        Submit a video generation request.

        Args:
            image_path: Path to the input image
            prompt: Text prompt for video generation
            model: Model to use for generation
            image_size: Output video size
            negative_prompt: Negative prompt (optional)
            seed: Random seed (optional)

        Returns:
            Request ID if successful, None otherwise
        """
        url = f"{self.base_url}/video/submit"

        # Encode image to base64
        image_base64 = self._encode_image_to_base64(image_path)

        payload = {
            "model": model,
            "prompt": prompt,
            "image_size": image_size,
            "image": image_base64,
        }

        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["seed"] = seed

        try:
            response = requests.post(url, json=payload, headers=self.headers, **self.request_kwargs)
            response.raise_for_status()

            data = response.json()
            request_id = data.get("requestId")
            
            # Show full key for debugging if environment variable is set
            show_full_key = os.getenv("KGEN_DEBUG_KEYS", "false").lower() == "true"
            if show_full_key:
                key_display = self.api_key if self.api_key else "unknown"
            else:
                key_display = f"*{self.api_key[-8:]}" if self.api_key else "unknown"
            
            status_update(
                f"✅ Video generation submitted (Key: {key_display}, Request ID: {request_id})", "green"
            )
            return request_id

        except requests.exceptions.RequestException as e:
            print_warning(f"Error submitting video generation: {e}")
            if hasattr(e, "response") and e.response is not None:
                print_warning(f"Response: {e.response.text}")
            return None

    def check_video_status(self, request_id: str) -> Dict[str, Any]:
        """
        Check the status of a video generation request with retry logic.

        Args:
            request_id: The request ID returned by submit_video_generation

        Returns:
            Status response dictionary
        """
        return self._check_video_status_with_retry(request_id)

    def _check_video_status_with_retry(self, request_id: str, attempt: int = 1) -> Dict[str, Any]:
        """
        Check video status with retry logic for handling server errors.
        
        Args:
            request_id: The request ID to check
            attempt: Current attempt number (1-based)
            
        Returns:
            Status response dictionary
        """
        url = f"{self.base_url}/video/status"
        payload = {"requestId": request_id}

        try:
            response = requests.post(url, json=payload, headers=self.headers, **self.request_kwargs)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            # Check if this is a retryable error (502, 503, 504, connection errors)
            is_retryable = (
                (hasattr(e, 'response') and e.response is not None and e.response.status_code in [502, 503, 504]) or
                isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout))
            )
            
            if is_retryable and attempt < VideoDefaults.MAX_RETRY_ATTEMPTS:
                # Calculate delay with exponential backoff
                if VideoDefaults.RETRY_EXPONENTIAL_BACKOFF:
                    delay = VideoDefaults.RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
                else:
                    delay = VideoDefaults.RETRY_DELAY_SECONDS
                
                print_warning(f"Error checking video status (attempt {attempt}/{VideoDefaults.MAX_RETRY_ATTEMPTS}): {e}")
                print_warning(f"Retrying in {delay} seconds...")
                
                time.sleep(delay)
                return self._check_video_status_with_retry(request_id, attempt + 1)
            else:
                # Max retries reached or non-retryable error
                if attempt >= VideoDefaults.MAX_RETRY_ATTEMPTS:
                    print_warning(f"Max retries ({VideoDefaults.MAX_RETRY_ATTEMPTS}) reached for video status check: {e}")
                else:
                    print_warning(f"Non-retryable error checking video status: {e}")
                return {"status": "Failed", "reason": str(e)}

    def wait_and_download_video(
        self,
        request_id: str,
        output_path: str,
        max_wait_time: int = 600,
        check_interval: int = 5,
        scene_name: str = None,
    ) -> bool:
        """
        Wait for video generation to complete and download the result with retry logic.

        Args:
            request_id: The request ID to monitor
            output_path: Path where to save the video
            max_wait_time: Maximum time to wait in seconds
            check_interval: Interval between status checks in seconds
            scene_name: Optional scene name for better logging

        Returns:
            True if successful, False otherwise
        """
        return self._wait_and_download_with_retry(request_id, output_path, max_wait_time, check_interval, scene_name)

    def _wait_and_download_with_retry(
        self,
        request_id: str,
        output_path: str,
        max_wait_time: int,
        check_interval: int,
        scene_name: str,
        attempt: int = 1,
    ) -> bool:
        """
        Wait for video generation and download with retry logic.
        
        Args:
            request_id: The request ID to monitor
            output_path: Path where to save the video
            max_wait_time: Maximum time to wait in seconds
            check_interval: Interval between status checks in seconds
            scene_name: Optional scene name for better logging
            attempt: Current attempt number (1-based)
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()

        # Show full key for debugging if environment variable is set
        import os
        show_full_key = os.getenv("KGEN_DEBUG_KEYS", "false").lower() == "true"
        
        if show_full_key:
            key_display = self.api_key if self.api_key else "unknown"
        else:
            key_display = f"*{self.api_key[-8:]}" if self.api_key else "unknown"
        
        # Add retry information to logging
        if attempt > 1:
            status_update(f"🔄 Retry attempt {attempt}/{VideoDefaults.MAX_RETRY_ATTEMPTS} for {scene_name or 'video'}", "yellow")
        
        while time.time() - start_time < max_wait_time:
            status_response = self.check_video_status(request_id)
            status = status_response.get("status")

            elapsed_time = int(time.time() - start_time)
            
            # Enhanced logging with scene context
            if scene_name:
                status_update(f"📊 {scene_name} status: {status} (Key: {key_display}, elapsed: {elapsed_time}s)", "cyan")
            else:
                status_update(f"📊 Video status: {status} (Key: {key_display}, elapsed: {elapsed_time}s)", "cyan")

            if status == "Succeed":
                # Download the video
                results = status_response.get("results", {})
                videos = results.get("videos", [])

                if videos and videos[0].get("url"):
                    video_url = videos[0]["url"]
                    status_update(f"Downloading video...", "bright_cyan")

                    try:
                        video_response = requests.get(video_url, **self.request_kwargs)
                        video_response.raise_for_status()

                        # Save the video
                        with open(output_path, "wb") as f:
                            f.write(video_response.content)

                        file_size = len(video_response.content) / (1024 * 1024)  # MB
                        print_success(f"Video downloaded successfully using Key {key_display}")
                        print_success(f"   └─ Saved to: {output_path} ({file_size:.1f} MB)")
                        return True

                    except requests.exceptions.RequestException as e:
                        print_warning(f"Error downloading video: {e}")
                        # Check if download should be retried
                        if attempt < VideoDefaults.MAX_RETRY_ATTEMPTS:
                            print_warning(f"Will retry download for {scene_name or 'video'}")
                            return self._retry_download(request_id, output_path, max_wait_time, check_interval, scene_name, attempt, str(e))
                        return False
                else:
                    print_warning("No video URL in response")
                    # Check if this should be retried
                    if attempt < VideoDefaults.MAX_RETRY_ATTEMPTS:
                        print_warning(f"Will retry download for {scene_name or 'video'}")
                        return self._retry_download(request_id, output_path, max_wait_time, check_interval, scene_name, attempt, "No video URL in response")
                    return False

            elif status == "Failed":
                reason = status_response.get("reason", "Unknown error")
                print_warning(f"Video generation failed: {reason}")
                # Check if this failure should be retried
                if attempt < VideoDefaults.MAX_RETRY_ATTEMPTS and self._is_retryable_failure(reason):
                    print_warning(f"Will retry download for {scene_name or 'video'}")
                    return self._retry_download(request_id, output_path, max_wait_time, check_interval, scene_name, attempt, reason)
                return False

            # Still in progress, wait before checking again
            time.sleep(check_interval)

        print_warning(
            f"Timeout waiting for video generation after {max_wait_time} seconds"
        )
        # Check if timeout should be retried
        if attempt < VideoDefaults.MAX_RETRY_ATTEMPTS:
            print_warning(f"Will retry download for {scene_name or 'video'}")
            return self._retry_download(request_id, output_path, max_wait_time, check_interval, scene_name, attempt, "Timeout")
        return False

    def _is_retryable_failure(self, reason: str) -> bool:
        """Check if a failure reason indicates a retryable error."""
        retryable_keywords = [
            "502", "503", "504", "Bad Gateway", "Service Unavailable", 
            "Gateway Timeout", "Connection", "Network", "Timeout"
        ]
        return any(keyword.lower() in reason.lower() for keyword in retryable_keywords)

    def _retry_download(self, request_id: str, output_path: str, max_wait_time: int, 
                       check_interval: int, scene_name: str, attempt: int, error_reason: str) -> bool:
        """Handle retry logic for failed downloads."""
        # Calculate delay with exponential backoff
        if VideoDefaults.RETRY_EXPONENTIAL_BACKOFF:
            delay = VideoDefaults.RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
        else:
            delay = VideoDefaults.RETRY_DELAY_SECONDS
        
        print_warning(f"Retrying in {delay} seconds... (Reason: {error_reason})")
        time.sleep(delay)
        
        return self._wait_and_download_with_retry(
            request_id, output_path, max_wait_time, check_interval, scene_name, attempt + 1
        )


class VideoGenerationTask:
    """Wrapper for video generation task with proper thread management."""

    def __init__(
        self,
        client,  # Can be any BaseVideoClient (VideoGenerationClient)
        image_path: str,
        prompt: str,
        output_dir: str,
        scene_name: str,
        api_key: str,
        scene_data: Dict[str, Any] = None,
        **kwargs,
    ):
        self.client = client
        self.image_path = image_path
        self.prompt = prompt
        self.output_dir = output_dir
        self.scene_name = scene_name
        self.api_key = api_key  # Store the API key used for this task
        self.scene_data = scene_data  # Store scene data for audio enhancement
        self.kwargs = kwargs
        self.request_id = None
        self.success = False
        self.completed = False
        self.error = None
        self.thread = None
        self.retry_count = 0

    def start(self):
        """Start the video generation task."""
        self.thread = threading.Thread(target=self._run, daemon=False)
        self.thread.start()
        return self.thread

    def _run(self):
        """Run the video generation task with retry logic."""
        self._run_with_retry()

    def _run_with_retry(self, attempt: int = 1):
        """Run the video generation task with retry logic."""
        # Show full key for debugging if environment variable is set
        import os
        show_full_key = os.getenv("KGEN_DEBUG_KEYS", "false").lower() == "true"
        
        if show_full_key:
            key_display = self.api_key if self.api_key else "unknown"
        else:
            key_display = f"*{self.api_key[-8:]}" if self.api_key else "unknown"
        
        try:
            if attempt > 1:
                print_info(f"🔄 Retrying {self.scene_name} generation (attempt {attempt}/{VideoDefaults.MAX_RETRY_ATTEMPTS}) with Key {key_display}")
            else:
                print_info(f"🚀 Starting {self.scene_name} generation with Key {key_display}")
            
            self.request_id = self.client.submit_video_generation(
                self.image_path, self.prompt, **self.kwargs
            )
            if self.request_id:
                output_path = os.path.join(self.output_dir, f"{self.scene_name}.mp4")
                self.success = self.client.wait_and_download_video(
                    self.request_id, output_path, scene_name=self.scene_name
                )
                if self.success:
                    print_success(f"✅ {self.scene_name} completed successfully using Key {key_display}")
                    # Additional debug info
                    print_success(f"   └─ Request ID: {self.request_id}")
                    if attempt > 1:
                        print_success(f"   └─ Succeeded after {attempt} attempts")
                else:
                    print_warning(f"❌ {self.scene_name} failed during download using Key {key_display}")
                    print_warning(f"   └─ Request ID: {self.request_id}")
                    # Check if we should retry
                    if attempt < VideoDefaults.MAX_RETRY_ATTEMPTS:
                        self._handle_retry(attempt, f"Download failed for Request ID: {self.request_id}")
                        return
                    else:
                        print_warning(f"   └─ Max retries ({VideoDefaults.MAX_RETRY_ATTEMPTS}) reached")
                        self.error = f"Download failed after {VideoDefaults.MAX_RETRY_ATTEMPTS} attempts"
            else:
                self.error = "Failed to submit video generation request"
                print_warning(f"❌ {self.scene_name} submission failed with Key {key_display}")
                # Check if we should retry submission
                if attempt < VideoDefaults.MAX_RETRY_ATTEMPTS:
                    self._handle_retry(attempt, "Video generation submission failed")
                    return
                else:
                    print_warning(f"   └─ Max retries ({VideoDefaults.MAX_RETRY_ATTEMPTS}) reached")
                    self.error = f"Submission failed after {VideoDefaults.MAX_RETRY_ATTEMPTS} attempts"
        except Exception as e:
            self.error = str(e)
            print_warning(f"❌ {self.scene_name} error with Key {key_display}: {str(e)}")
            # Check if we should retry on exception
            if attempt < VideoDefaults.MAX_RETRY_ATTEMPTS and self._is_retryable_error(str(e)):
                self._handle_retry(attempt, str(e))
                return
            else:
                if attempt >= VideoDefaults.MAX_RETRY_ATTEMPTS:
                    print_warning(f"   └─ Max retries ({VideoDefaults.MAX_RETRY_ATTEMPTS}) reached")
                    self.error = f"Error after {VideoDefaults.MAX_RETRY_ATTEMPTS} attempts: {str(e)}"
        finally:
            self.completed = True

    def _is_retryable_error(self, error: str) -> bool:
        """Check if an error is retryable."""
        retryable_keywords = [
            "502", "503", "504", "Bad Gateway", "Service Unavailable", 
            "Gateway Timeout", "Connection", "Network", "Timeout", "RequestException"
        ]
        return any(keyword.lower() in error.lower() for keyword in retryable_keywords)

    def _handle_retry(self, attempt: int, error_reason: str):
        """Handle retry logic for failed tasks."""
        self.retry_count = attempt
        self.completed = False  # Reset completion status for retry
        
        # Calculate delay with exponential backoff
        if VideoDefaults.RETRY_EXPONENTIAL_BACKOFF:
            delay = VideoDefaults.RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
        else:
            delay = VideoDefaults.RETRY_DELAY_SECONDS
        
        print_warning(f"🔄 Will retry {self.scene_name} in {delay} seconds... (Reason: {error_reason})")
        time.sleep(delay)
        
        # Retry the task
        self._run_with_retry(attempt + 1)

    def is_alive(self):
        """Check if the thread is still running."""
        return self.thread and self.thread.is_alive()

    def join(self, timeout=None):
        """Wait for the thread to complete."""
        if self.thread:
            self.thread.join(timeout)


def generate_videos_from_images(
    image_paths: List[str],
    scenes: List[Dict[str, Any]],
    output_dir: Optional[str] = None,
    video_provider: str = "siliconflow",
) -> List[VideoGenerationTask]:
    """
    Generate videos from a list of images and scenes using the specified provider.

    Args:
        image_paths: List of paths to generated images
        scenes: List of scene dictionaries with prompts
        output_dir: Directory to save videos (uses same as images if not specified)
        video_provider: Video provider to use ("siliconflow")

    Returns:
        List of VideoGenerationTask objects
    """
    if not image_paths:
        print("No images provided for video generation")
        return []

    video_count = len(image_paths)
    provider_info = {"name": video_provider.title(), "key_display": "unknown"}
    
    # Handle different providers
    if video_provider.lower() == "siliconflow":
        # Allocate API keys for SiliconFlow video generation tasks
        key_allocation = config.allocate_keys_for_videos(video_count)
        if not key_allocation:
            print_warning("No SiliconFlow API keys available for video generation")
            return []

        # Display key allocation info for SiliconFlow
        unique_keys = len(set(key_allocation.values()))
        print_info(f"🔑 Using {unique_keys} SiliconFlow API key(s) for {video_count} video(s)")
        
        provider_info["name"] = "SiliconFlow"
        

        
    else:
        print_warning(f"Unknown video provider: {video_provider}")
        print_warning("Supported providers: siliconflow")
        return []

    # Use the same directory as images if not specified
    if output_dir is None:
        output_dir = str(Path(image_paths[0]).parent)

    tasks = []

    for i, (image_path, scene) in enumerate(zip(image_paths, scenes)):
        if not os.path.exists(image_path):
            print(f"Image not found: {image_path}")
            continue

        # Get the allocated API key for this video
        api_key = key_allocation.get(i)
        if not api_key:
            print(f"No API key allocated for video {i+1}")
            continue

        # Create the appropriate client based on provider
        if video_provider.lower() == "siliconflow":
            client = VideoGenerationClient(api_key)

        else:
            print(f"Unsupported video provider: {video_provider}")
            continue

        # Create video prompt from scene action and image prompt
        scene_location = scene.get("location", "")
        scene_time = scene.get("time", "")
        scene_action = scene.get("action", "")
        
        # Build video prompt based on provider
        if video_provider.lower() == "siliconflow":
            # SiliconFlow - conservative video prompts to avoid too much character movement
            video_prompt_parts = []
            
            # Start with static atmospheric elements only
            if scene_location:
                video_prompt_parts.append(f"static scene at {scene_location}")
            if scene_time:
                video_prompt_parts.append(f"during {scene_time}")
                
            # Minimize character movement - focus on environment instead of actions
            if scene_action:
                # Extract environmental elements and avoid character actions
                action_lower = scene_action.lower()
                
                # Only add very minimal, environmental movements
                if any(word in action_lower for word in ["wind", "breeze", "flowing", "rippling", "ripples"]):
                    video_prompt_parts.append("gentle environmental movement")
                elif any(word in action_lower for word in ["light", "glow", "shine", "sparkle", "glowing"]):
                    video_prompt_parts.append("subtle lighting effects")
                else:
                    # For any other action, just add minimal movement
                    video_prompt_parts.append("minimal movement")
            
            # Add very conservative atmospheric qualities that emphasize stillness
            video_prompt_parts.extend([
                "stable composition",
                "minimal character movement", 
                "environmental ambience",
                "subtle lighting changes only",
                "camera remains still"
            ])
            
            video_prompt = ", ".join(video_prompt_parts)
            


        scene_name = f"scene_{i+1:03d}"

        # Enhanced logging for video submission
        key_short = api_key[-8:]
        print_info(f"Submitting {scene_name} video generation with {provider_info['name']}:")
        print_info(f"   └─ Using Key *{key_short}")
        print_info(f"   └─ Original Scene Action: '{scene.get('action', 'No action')[:60]}...'")
        print_info(f"   └─ Video Prompt: '{video_prompt}'")
        
        # Create negative prompt based on provider
        if video_provider.lower() == "siliconflow":
            # SiliconFlow - conservative negative prompt for video to avoid excessive movement
            base_negative = scene.get("image_prompt_negative", "")
            video_negative_parts = [
                "too much movement",
                "excessive motion", 
                "fast movement",
                "rapid action",
                "dramatic gestures",
                "sudden changes",
                "camera shake",
                "blurry motion",
                "distorted movement"
            ]
            
            if base_negative:
                video_negative_prompt = f"{base_negative}, {', '.join(video_negative_parts)}"
            else:
                video_negative_prompt = ", ".join(video_negative_parts)
                

        
        print_info(f"   └─ Negative Prompt: '{video_negative_prompt}'")
        print()

        # Create task parameters based on provider
        task_kwargs = {
            "negative_prompt": video_negative_prompt,
            "scene_data": scene,
        }
        
        # Add provider-specific parameters
        # (Currently only SiliconFlow is supported)

        task = VideoGenerationTask(
            client=client,
            image_path=image_path,
            prompt=video_prompt,
            output_dir=output_dir,
            scene_name=scene_name,
            api_key=api_key,
            **task_kwargs
        )

        task.start()
        tasks.append(task)

    return tasks


def combine_videos(
    video_paths: List[str], output_path: str, transition_duration: float = 0.5
) -> bool:
    """
    Combine multiple videos into a single video with smooth transitions.

    Args:
        video_paths: List of paths to video files to combine
        output_path: Path for the combined output video
        transition_duration: Duration of crossfade transitions between videos

    Returns:
        True if successful, False otherwise
    """
    if not video_paths:
        print("No videos to combine")
        return False

    if len(video_paths) == 1:
        # If only one video, re-encode it for compatibility
        try:
            cmd = [
                "ffmpeg",
                "-i",
                video_paths[0],
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-profile:v",
                "high",
                "-level",
                "4.0",
                "-crf",
                "23",
                "-preset",
                "medium",
                "-movflags",
                "+faststart",
                "-y",
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Single video re-encoded for compatibility: {output_path}")
                return True
            else:
                # Fallback to simple copy
                import shutil

                shutil.copy2(video_paths[0], output_path)
                print(f"Single video copied to: {output_path}")
                return True
        except Exception:
            import shutil

            shutil.copy2(video_paths[0], output_path)
            print(f"Single video copied to: {output_path}")
            return True

    print(f"Combining {len(video_paths)} videos into one...")

    try:
        # Check if ffmpeg is available
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg not found. Please install ffmpeg to combine videos.")
        print(
            "Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Ubuntu)"
        )
        return False

    try:
        # Create a temporary file list for ffmpeg
        temp_list_file = output_path + ".txt"

        with open(temp_list_file, "w") as f:
            for video_path in video_paths:
                if os.path.exists(video_path):
                    f.write(f"file '{os.path.abspath(video_path)}'\n")

        # First try with re-encoding for better compatibility
        cmd = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            temp_list_file,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-profile:v",
            "high",
            "-level",
            "4.0",
            "-crf",
            "23",
            "-preset",
            "medium",
            "-movflags",
            "+faststart",  # Optimize for web playback
            "-y",
            output_path,
        ]

        print(f"Running ffmpeg to combine videos with compatibility encoding...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(
                f"✅ Videos successfully combined with compatible encoding: {output_path}"
            )

            # Get output file size
            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"Combined video size: {size_mb:.1f} MB")

            # Clean up temp file
            if os.path.exists(temp_list_file):
                os.remove(temp_list_file)

            return True
        else:
            print(f"⚠️ Compatible encoding failed: {result.stderr}")
            print("🔄 Falling back to stream copy...")

            # Fallback to stream copy (original method)
            cmd_fallback = [
                "ffmpeg",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                temp_list_file,
                "-c",
                "copy",  # Copy streams without re-encoding for speed
                "-y",
                output_path,
            ]

            result = subprocess.run(cmd_fallback, capture_output=True, text=True)

            if result.returncode == 0:
                print(
                    f"✅ Videos successfully combined with stream copy: {output_path}"
                )

                # Get output file size
                if os.path.exists(output_path):
                    size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    print(f"Combined video size: {size_mb:.1f} MB")

                # Clean up temp file
                if os.path.exists(temp_list_file):
                    os.remove(temp_list_file)

                return True
            else:
                print(f"❌ ffmpeg failed with error: {result.stderr}")
                return False

    except Exception as e:
        print(f"❌ Error combining videos: {e}")
        return False
    finally:
        # Clean up temp file if it exists
        if os.path.exists(temp_list_file):
            try:
                os.remove(temp_list_file)
            except Exception:
                pass


def combine_videos_with_transitions(
    video_paths: List[str], output_path: str, transition_duration: float = 1.0
) -> bool:
    """
    Combine videos with smooth crossfade transitions (requires re-encoding).

    Args:
        video_paths: List of paths to video files to combine
        output_path: Path for the combined output video
        transition_duration: Duration of crossfade transitions in seconds

    Returns:
        True if successful, False otherwise
    """
    if not video_paths:
        print("No videos to combine")
        return False

    if len(video_paths) == 1:
        import shutil

        shutil.copy2(video_paths[0], output_path)
        return True

    print(f"Combining {len(video_paths)} videos with transitions...")

    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg not found. Please install ffmpeg to combine videos.")
        return False

    try:
        # Build complex ffmpeg filter for crossfade transitions
        inputs = []
        filters = []

        # Add all input files
        for i, video_path in enumerate(video_paths):
            if os.path.exists(video_path):
                inputs.extend(["-i", video_path])

        # Build filter chain for crossfades
        if len(video_paths) >= 2:
            # Start with first two videos
            current_output = f"[0][1]xfade=transition=fade:duration={transition_duration}:offset=5[v01]"
            filters.append(current_output)

            # Add subsequent videos with crossfade
            for i in range(2, len(video_paths)):
                prev_label = f"v0{i-1}" if i == 2 else f"v{i-1}"
                current_label = f"v{i}"
                offset = 5 * i  # Approximate offset, adjust based on video length

                filter_str = f"[{prev_label}][{i}]xfade=transition=fade:duration={transition_duration}:offset={offset}[{current_label}]"
                filters.append(filter_str)

        filter_complex = ";".join(filters)
        final_output = f"v{len(video_paths)-1}" if len(video_paths) > 2 else "v01"

        cmd = [
            "ffmpeg",
            *inputs,
            "-filter_complex",
            filter_complex,
            "-map",
            f"[{final_output}]",
            "-c:v",
            "libx264",
            "-crf",
            "23",
            "-preset",
            "medium",
            "-y",
            output_path,
        ]

        print("Running ffmpeg with transitions (this may take longer)...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Videos with transitions combined: {output_path}")
            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"Combined video size: {size_mb:.1f} MB")
            return True
        else:
            print(f"❌ ffmpeg failed: {result.stderr}")
            # Fallback to simple concatenation
            print("🔄 Falling back to simple concatenation...")
            return combine_videos(video_paths, output_path)

    except Exception as e:
        print(f"❌ Error combining videos with transitions: {e}")
        # Fallback to simple concatenation
        return combine_videos(video_paths, output_path)


def combine_scene_videos(
    output_dir: str,
    use_transitions: bool = True,
    video_paths: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Find and combine all scene videos in a directory.

    Args:
        output_dir: Directory containing scene videos
        use_transitions: Whether to use crossfade transitions
        video_paths: Optional list of specific video paths to combine

    Returns:
        Path to combined video if successful, None otherwise
    """
    output_path = Path(output_dir)

    if video_paths:
        # Use provided video paths
        scene_videos = [Path(p) for p in video_paths if os.path.exists(p)]
    else:
        # Find all scene videos (both original and enhanced)
        scene_videos = sorted(output_path.glob("scene_*_enhanced.mp4"))
        if not scene_videos:
            scene_videos = sorted(output_path.glob("scene_*.mp4"))

    if not scene_videos:
        print("No scene videos found to combine")
        return None

    video_paths_list = [str(video) for video in scene_videos]
    combined_path = output_path / "combined_story.mp4"

    print(f"Found {len(video_paths_list)} scene videos to combine:")
    for video in video_paths_list:
        print(f"  📹 {Path(video).name}")

    # Choose combination method
    if use_transitions and len(video_paths_list) > 1:
        success = combine_videos_with_transitions(video_paths_list, str(combined_path))
    else:
        success = combine_videos(video_paths_list, str(combined_path))

    if success:
        return str(combined_path)
    return None


def add_audio_to_video(
    video_path: str,
    audio_path: str,
    output_path: str,
    subtitle_path: Optional[str] = None,
) -> bool:
    """
    Add audio track to a video file and optionally burn in subtitles.

    Args:
        video_path: Path to the video file
        audio_path: Path to the audio file
        output_path: Path for the output video with audio
        subtitle_path: Optional path to subtitle file to burn in

    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}")
        return False

    if not os.path.exists(audio_path):
        print(f"Audio file not found: {audio_path}")
        return False

    print(f"🎵 Adding audio to video: {Path(video_path).name}")

    try:
        # Check if ffmpeg is available
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg not found. Please install ffmpeg to add audio to videos.")
        return False

    try:
        # Build ffmpeg command
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-i",
            audio_path,
            "-c:v",
            "copy",  # Copy video stream without re-encoding
            "-c:a",
            "aac",  # Encode audio as AAC
            "-b:a",
            "192k",  # Audio bitrate
            "-map",
            "0:v:0",  # Map first video stream from first input
            "-map",
            "1:a:0",  # Map first audio stream from second input
            "-shortest",  # Finish when shortest stream ends
            "-y",
            output_path,
        ]

        # Add subtitle burning if subtitle path is provided
        # NOTE: Subtitle burning is currently disabled as it may not be necessary
        # if subtitle_path and os.path.exists(subtitle_path):
        #     print(f"📝 Also burning in subtitles from: {Path(subtitle_path).name}")
        #     # Need to re-encode video to burn in subtitles
        #     cmd = [
        #         "ffmpeg",
        #         "-i",
        #         video_path,
        #         "-i",
        #         audio_path,
        #         "-vf",
        #         f"subtitles={subtitle_path}",
        #         "-c:v",
        #         "libx264",
        #         "-crf",
        #         "23",
        #         "-preset",
        #         "medium",
        #         "-c:a",
        #         "aac",
        #         "-b:a",
        #         "192k",
        #         "-map",
        #         "0:v:0",
        #         "-map",
        #         "1:a:0",
        #         "-shortest",
        #         "-y",
        #         output_path,
        #     ]

        print("Running ffmpeg to add audio...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Audio added successfully: {output_path}")

            # Get output file size
            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"Output video size: {size_mb:.1f} MB")

            return True
        else:
            print(f"❌ ffmpeg failed with error: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error adding audio to video: {e}")
        return False


def combine_videos_with_audio(
    video_path: str, audio_path: str, output_dir: str
) -> Optional[str]:
    """
    Combine video with audio track, creating a final video with soundtrack.

    Args:
        video_path: Path to the combined video
        audio_path: Path to the generated audio/song
        output_dir: Directory to save the final video

    Returns:
        Path to the final video with audio if successful, None otherwise
    """
    if not os.path.exists(video_path):
        print(f"Combined video not found: {video_path}")
        return None

    if not os.path.exists(audio_path):
        print(f"Audio file not found: {audio_path}")
        return None

    # Create output path for final video
    output_path = os.path.join(output_dir, "combined_story_with_audio.mp4")

    # Check if subtitle file exists
    # NOTE: Subtitle functionality is currently disabled
    # subtitle_path = audio_path.replace(".mp3", ".srt")
    # if not os.path.exists(subtitle_path):
    #     subtitle_path = None
    subtitle_path = None

    print(f"\nCreating final video with soundtrack...")

    if add_audio_to_video(video_path, audio_path, output_path, subtitle_path):
        print(f"🎉 Final video with audio created: {output_path}")
        return output_path
    else:
        print("⚠️ Failed to add audio to video")
        return None


def wait_for_all_videos(
    tasks: List[VideoGenerationTask],
    max_wait_minutes: int = VideoDefaults.TIMEOUT_MINUTES,
    enhance_with_audio: bool = True,
    audio_path: Optional[str] = None,
) -> bool:
    """
    Wait for all video generation tasks to complete.
    
    This function now uses the optimized video management system
    for better monitoring and error handling.

    Args:
        tasks: List of VideoGenerationTask objects
        max_wait_minutes: Maximum time to wait in minutes
        enhance_with_audio: Whether to add audio and subtitles to videos
        audio_path: Optional path to the generated audio/song

    Returns:
        True if all videos completed successfully, False otherwise
    """
    # Import the optimized video manager
    try:
        from .video_manager import wait_for_all_videos as optimized_wait
        return optimized_wait(tasks, max_wait_minutes, enhance_with_audio, audio_path)
    except ImportError:
        # Fallback to basic implementation if video_manager is not available
        return _legacy_wait_for_all_videos(tasks, max_wait_minutes, enhance_with_audio, audio_path)


def _legacy_wait_for_all_videos(
    tasks: List[VideoGenerationTask],
    max_wait_minutes: int,
    enhance_with_audio: bool,
    audio_path: Optional[str],
) -> bool:
    """Legacy implementation for backward compatibility."""
    if not tasks:
        print("No video tasks to wait for")
        return True

    max_wait_seconds = max_wait_minutes * 60
    start_time = time.time()

    print(f"\n🎥 Waiting for {len(tasks)} videos to complete (max {max_wait_minutes} minutes)...")

    try:
        while time.time() - start_time < max_wait_seconds:
            completed = sum(1 for task in tasks if task.completed)
            successful = sum(1 for task in tasks if task.completed and task.success)
            
            if completed == len(tasks):
                print(f"\n✅ All video generation tasks completed!")
                return successful == len(tasks)
            
            time.sleep(VideoDefaults.THREAD_CHECK_INTERVAL)
        
        print(f"\n⏰ Timeout reached after {max_wait_minutes} minutes")
        return False

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        return False
