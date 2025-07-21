#!/usr/bin/env python3
"""
Test script for SiliconFlow video generation functionality.
Tests video generation from an existing image with detailed logging.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path so we can import kgen modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from kgen.config.config import Config
from kgen.video.siliconflow_client import VideoGenerationClient

def setup_logging():
    """Set up detailed logging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Enable debug logging for our modules
    logging.getLogger('kgen.video.siliconflow_client').setLevel(logging.DEBUG)
    logging.getLogger('kgen.video.base_video_client').setLevel(logging.DEBUG)

def test_siliconflow_video_generation():
    """Test SiliconFlow video generation with an existing image"""
    print("=" * 60)
    print("TESTING SILICONFLOW VIDEO GENERATION")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = Config()
        
        # Check if SiliconFlow API key is configured
        siliconflow_api_key = config.SILICONFLOW_VIDEO_KEY
        if not siliconflow_api_key:
            logger.error("SILICONFLOW_VIDEO_KEY not found in configuration!")
            logger.error("Please set SILICONFLOW_VIDEO_KEY in your .env file")
            return False
        
        logger.info(f"SiliconFlow API key configured: {siliconflow_api_key[:8]}...")
        
        # Create SiliconFlow client
        logger.info("Creating SiliconFlow client...")
        siliconflow_client = VideoGenerationClient(api_key=siliconflow_api_key)
        
        # Find an existing image to use
        image_path = "output/2025_07_09_illustrious_fd5e7b9f/scene_001_00.png"
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return False
        
        logger.info(f"Using existing image: {image_path}")
        
        # Test video generation parameters
        prompt = "A dynamic and cinematic scene with smooth camera movement, showing the character in motion with natural lighting and atmospheric effects"
        model = "Wan-AI/Wan2.1-I2V-14B-720P-Turbo"  # Use SiliconFlow's I2V model
        image_size = "1280x720"  # 720P resolution
        
        logger.info("=" * 50)
        logger.info("VIDEO GENERATION PARAMETERS:")
        logger.info(f"  Image: {image_path}")
        logger.info(f"  Prompt: {prompt}")
        logger.info(f"  Model: {model}")
        logger.info(f"  Image Size: {image_size}")
        logger.info("=" * 50)
        
        # Generate video
        logger.info("Starting video generation...")
        
        # Step 1: Submit video generation request
        logger.info("Submitting video generation request...")
        request_id = siliconflow_client.submit_video_generation(
            image_path=image_path,
            prompt=prompt,
            model=model,
            image_size=image_size
        )
        
        if not request_id:
            logger.error("Failed to submit video generation request!")
            return False
        
        logger.info(f"Video generation submitted successfully! Request ID: {request_id}")
        
        # Step 2: Wait for completion and download
        output_video_path = f"output/test_siliconflow_video_{request_id}.mp4"
        logger.info(f"Waiting for video generation to complete and downloading to: {output_video_path}")
        
        result = siliconflow_client.wait_and_download_video(
            request_id=request_id,
            output_path=output_video_path,
            max_wait_time=600,  # 10 minutes max
            check_interval=10,  # Check every 10 seconds
            scene_name="test_scene"
        )
        
        if result:
            logger.info("=" * 50)
            logger.info("VIDEO GENERATION SUCCESSFUL!")
            logger.info(f"Video saved to: {output_video_path}")
            logger.info("=" * 50)
            return True
        else:
            logger.error("VIDEO GENERATION FAILED!")
            return False
            
    except Exception as e:
        logger.error(f"Error during video generation test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_siliconflow_video_generation()
    if success:
        print("\n✅ SiliconFlow video generation test PASSED!")
    else:
        print("\n❌ SiliconFlow video generation test FAILED!")
    
    sys.exit(0 if success else 1)