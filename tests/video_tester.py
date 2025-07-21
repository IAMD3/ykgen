#!/usr/bin/env python3
"""
Test script for video generation functionality.

This script tests the video generation API integration independently.
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ykgen import VideoGenerationClient


def test_video_generation():
    """Test video generation with a sample image."""
    # Get API key from config
    from ykgen.config.config import config
    api_key = config.SILICONFLOW_VIDEO_KEY
    
    if not api_key:
        print("❌ SILICONFLOW_VIDEO_KEY not configured in environment")
        print("Please set your API key in .env file")
        return
    
    # Initialize client
    client = VideoGenerationClient(api_key)
    
    # Find a test image
    output_dir = Path("output")
    test_image = None
    
    # Look for existing images in output directory
    for subdir in output_dir.glob("*"):
        if subdir.is_dir():
            for img in subdir.glob("*.png"):
                test_image = str(img)
                break
        if test_image:
            break
    
    if not test_image:
        print("❌ No test image found in output directory")
        print("Please run main.py first to generate some images")
        return
    
    print(f"🖼️ Using test image: {test_image}")
    
    # Test video generation
    prompt = "A dynamic action scene with smooth camera movement and dramatic lighting"
    
    print(f"📝 Video prompt: {prompt}")
    print("🎬 Submitting video generation request...")
    
    request_id = client.submit_video_generation(
        image_path=test_image,
        prompt=prompt,
        model="Wan-AI/Wan2.1-I2V-14B-720P-Turbo",
        image_size="1280x720"
    )
    
    if not request_id:
        print("❌ Failed to submit video generation request")
        return
    
    print(f"✅ Request submitted! ID: {request_id}")
    
    # Create output path
    output_path = str(Path(test_image).parent / "test_video.mp4")
    
    print("⏳ Waiting for video generation to complete...")
    print("This may take a few minutes...")
    
    # Wait and download
    success = client.wait_and_download_video(
        request_id=request_id,
        output_path=output_path,
        max_wait_time=300,  # 5 minutes
        check_interval=5
    )
    
    if success:
        print(f"✅ Video successfully generated and saved to: {output_path}")
    else:
        print("❌ Video generation failed or timed out")


def test_async_generation():
    """Test asynchronous video generation."""
    from ykgen.config.config import config
    api_key = config.SILICONFLOW_VIDEO_KEY
    
    if not api_key:
        print("❌ SILICONFLOW_VIDEO_KEY not configured in environment")
        return
    client = VideoGenerationClient(api_key)
    
    # Find test images
    output_dir = Path("output")
    test_images = []
    
    for subdir in output_dir.glob("*"):
        if subdir.is_dir():
            for img in subdir.glob("*.png"):
                test_images.append(str(img))
                if len(test_images) >= 3:  # Test with up to 3 images
                    break
        if len(test_images) >= 3:
            break
    
    if not test_images:
        print("❌ No test images found")
        return
    
    print(f"🖼️ Found {len(test_images)} test images")
    print("🎬 Starting async video generation for all images...")
    
    threads = []
    for i, img_path in enumerate(test_images):
        prompt = f"Dynamic scene {i+1} with smooth motion and cinematic effects"
        output_dir = str(Path(img_path).parent)
        
        thread = client.generate_video_async(
            image_path=img_path,
            prompt=prompt,
            output_dir=output_dir,
            scene_name=f"async_test_{i+1:02d}"
        )
        threads.append(thread)
        print(f"  Started thread for image {i+1}")
    
    print(f"\n⏳ {len(threads)} video generation threads running...")
    print("Videos will be saved as they complete")
    print("Waiting 30 seconds for progress updates...")
    
    time.sleep(30)
    
    # Check thread status
    alive_count = sum(1 for t in threads if t.is_alive())
    print(f"\n📊 Status: {alive_count} threads still running")
    
    if alive_count > 0:
        print("Videos are still being generated. Check the output directory later.")
    else:
        print("All threads have completed. Check output directory for videos.")


if __name__ == "__main__":
    print("🎥 KGen Video Generation Test")
    print("=" * 50)
    
    # Run tests
    print("\n1️⃣ Testing synchronous video generation...")
    test_video_generation()
    
    print("\n" + "=" * 50)
    print("\n2️⃣ Testing asynchronous video generation...")
    test_async_generation()
    
    print("\n✨ Tests complete!")