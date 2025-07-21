"""
Video management utilities for YKGen.

This module provides enhanced video management functionality,
breaking down complex operations into smaller, testable components.
"""

import os
import signal
import sys
import time
from typing import List, Optional, Dict, Any

from ykgen.config.constants import VideoDefaults
from ..utils import calculate_file_size_mb, format_duration


class VideoTaskMonitor:
    """Monitors video generation tasks with enhanced tracking."""
    
    def __init__(self, tasks: List[Any], max_wait_minutes: int = VideoDefaults.TIMEOUT_MINUTES):
        self.tasks = tasks
        self.max_wait_minutes = max_wait_minutes
        self.max_wait_seconds = max_wait_minutes * 60
        self.start_time = time.time()
        self._signal_handler_installed = False
        
    def install_signal_handler(self):
        """Install signal handler for graceful shutdown."""
        def signal_handler(signum, frame):
            print("\n⚠️ Received interrupt signal. Waiting for current operations to complete...")
            for task in self.tasks:
                if task.is_alive():
                    print(f"Stopping task for {task.scene_name}...")
            sys.exit(1)
        
        signal.signal(signal.SIGINT, signal_handler)
        self._signal_handler_installed = True
    
    def cleanup_signal_handler(self):
        """Clean up signal handler."""
        if self._signal_handler_installed:
            signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    def get_task_statistics(self) -> Dict[str, int]:
        """Get current task completion statistics."""
        completed = sum(1 for task in self.tasks if task.completed)
        successful = sum(1 for task in self.tasks if task.completed and task.success)
        failed = sum(1 for task in self.tasks if task.completed and not task.success)
        
        return {
            "total": len(self.tasks),
            "completed": completed,
            "successful": successful,
            "failed": failed,
            "running": len(self.tasks) - completed
        }
    
    def is_timeout_reached(self) -> bool:
        """Check if timeout has been reached."""
        return time.time() - self.start_time >= self.max_wait_seconds
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in minutes."""
        return (time.time() - self.start_time) / 60
    
    def print_progress(self):
        """Print current progress status."""
        stats = self.get_task_statistics()
        elapsed_minutes = self.get_elapsed_time()
        
        print(
            f"\r⏳ Progress: {stats['completed']}/{stats['total']} completed "
            f"({stats['successful']} successful, {stats['failed']} failed) "
            f"- {elapsed_minutes:.1f}/{self.max_wait_minutes} minutes",
            end="",
            flush=True,
        )


class VideoResultProcessor:
    """Processes completed video generation results."""
    
    def __init__(self, enable_audio: bool = True):
        self.enable_audio = enable_audio
    
    def collect_successful_videos(self, tasks: List[Any]) -> tuple[List[str], List[Dict]]:
        """
        Collect paths and data from successful video tasks.
        
        Returns:
            Tuple of (video_paths, scene_data)
        """
        video_paths = []
        scene_data = []
        
        for task in tasks:
            if task.success:
                video_path = os.path.join(task.output_dir, f"{task.scene_name}.mp4")
                if os.path.exists(video_path):
                    size_mb = calculate_file_size_mb(video_path)
                    print(f"  ✅ {task.scene_name}.mp4 ({size_mb} MB)")
                    video_paths.append(video_path)
                    
                    if hasattr(task, "scene_data"):
                        scene_data.append(task.scene_data)
        
        return video_paths, scene_data
    
    def combine_videos_if_multiple(self, video_paths: List[str], audio_path: Optional[str] = None) -> Optional[str]:
        """Combine multiple videos into one with optional audio track."""
        if len(video_paths) <= 1:
            return video_paths[0] if video_paths else None
        
        from .siliconflow_client import combine_scene_videos, combine_videos_with_audio
        
        print(f"\nCombining {len(video_paths)} videos into one...")
        output_dir = os.path.dirname(video_paths[0])
        
        combined_path = combine_scene_videos(
            output_dir, use_transitions=True, video_paths=video_paths
        )
        
        if combined_path:
            print(f"🎉 Combined video created: {combined_path}")
            
            # Add the generated audio/song to the combined video if available
            if audio_path and os.path.exists(audio_path):
                final_video_with_audio = combine_videos_with_audio(
                    combined_path, audio_path, output_dir
                )
                if final_video_with_audio:
                    print(f"🎵 Added soundtrack to final video")
                    return final_video_with_audio
            
            return combined_path
        else:
            print("⚠️ Failed to combine videos, but individual videos are available")
            return None
    
    def print_failed_videos(self, tasks: List[Any]):
        """Print information about failed video tasks."""
        failed_tasks = [task for task in tasks if task.completed and not task.success]
        
        if failed_tasks:
            print("❌ Failed videos:")
            for task in failed_tasks:
                error_msg = task.error or "Unknown error"
                print(f"  ❌ {task.scene_name}: {error_msg}")


def wait_for_all_videos(
    tasks: List[Any],
    max_wait_minutes: int = VideoDefaults.TIMEOUT_MINUTES,
    enhance_with_audio: bool = True,
    audio_path: Optional[str] = None,
) -> bool:
    """
    Wait for all video generation tasks to complete with enhanced monitoring.

    Args:
        tasks: List of VideoGenerationTask objects
        max_wait_minutes: Maximum time to wait in minutes
        enhance_with_audio: Whether to add audio and subtitles to videos
        audio_path: Optional path to the generated audio/song

    Returns:
        True if all videos completed successfully, False otherwise
    """
    if not tasks:
        print("No video tasks to wait for")
        return True

    # Initialize monitoring and processing components
    monitor = VideoTaskMonitor(tasks, max_wait_minutes)
    processor = VideoResultProcessor(enhance_with_audio)
    
    print(f"\n🎥 Waiting for {len(tasks)} videos to complete (max {max_wait_minutes} minutes)...")
    
    monitor.install_signal_handler()
    
    try:
        # Main monitoring loop
        while not monitor.is_timeout_reached():
            stats = monitor.get_task_statistics()
            monitor.print_progress()
            
            # Check if all tasks are completed
            if stats["completed"] == stats["total"]:
                print(f"\n✅ All video generation tasks completed!")
                print(f"Results: {stats['successful']} successful, {stats['failed']} failed")
                
                # Process successful videos
                if stats["successful"] > 0:
                    print("Generated videos:")
                    video_paths, scene_data = processor.collect_successful_videos(tasks)
                    
                    # Note: Individual scene audio enhancement has been removed
                    # Audio is now handled at the story level via ComfyUI background music
                    final_video_paths = video_paths
                    
                    # Combine videos if we have multiple successful ones
                    combined_path = processor.combine_videos_if_multiple(final_video_paths, audio_path)
                
                # No balance updates needed in normal mode
                
                # Print failed videos
                processor.print_failed_videos(tasks)
                
                return stats["successful"] == stats["total"]
            
            time.sleep(VideoDefaults.THREAD_CHECK_INTERVAL)
        
        # Timeout reached
        stats = monitor.get_task_statistics()
        elapsed_time = format_duration(int(monitor.get_elapsed_time() * 60))
        
        print(f"\n⏰ Timeout reached after {elapsed_time}")
        print(f"Final status: {stats['completed']}/{stats['total']} completed")
        
        return False

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        return False
    finally:
        monitor.cleanup_signal_handler()


class VideoQualityManager:
    """Manages video quality settings and optimization."""
    
    @staticmethod
    def get_optimal_ffmpeg_settings(target_quality: str = "high") -> Dict[str, str]:
        """Get optimal ffmpeg settings for different quality targets."""
        from ykgen.config.constants import FFmpegDefaults
        
        quality_presets = {
            "high": {
                "codec": FFmpegDefaults.VIDEO_CODEC,
                "crf": "18",  # Higher quality
                "preset": "slow",
                "profile": FFmpegDefaults.PROFILE,
                "level": FFmpegDefaults.LEVEL,
                "pixel_format": FFmpegDefaults.PIXEL_FORMAT,
            },
            "medium": {
                "codec": FFmpegDefaults.VIDEO_CODEC,
                "crf": str(VideoDefaults.CRF_VALUE),
                "preset": FFmpegDefaults.PRESET,
                "profile": FFmpegDefaults.PROFILE,
                "level": FFmpegDefaults.LEVEL,
                "pixel_format": FFmpegDefaults.PIXEL_FORMAT,
            },
            "fast": {
                "codec": FFmpegDefaults.VIDEO_CODEC,
                "crf": "28",  # Lower quality, faster encoding
                "preset": "ultrafast",
                "profile": "baseline",
                "level": "3.1",
                "pixel_format": FFmpegDefaults.PIXEL_FORMAT,
            }
        }
        
        return quality_presets.get(target_quality, quality_presets["medium"])
    
    @staticmethod
    def estimate_processing_time(video_count: int, quality: str = "medium") -> int:
        """Estimate total processing time in seconds."""
        base_time_per_video = {
            "fast": 30,    # 30 seconds per video
            "medium": 60,  # 1 minute per video
            "high": 120    # 2 minutes per video
        }
        
        return video_count * base_time_per_video.get(quality, 60)


def _update_used_keys_balance(tasks: List[Any]) -> None:
    """
    Update balances for API keys that were used in video generation.
    This function is no longer needed in normal mode.
    
    Args:
        tasks: List of VideoGenerationTask objects
    """
    # No balance updates needed in normal mode
    pass