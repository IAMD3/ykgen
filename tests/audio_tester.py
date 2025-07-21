"""
Test script for audio generation functionality.

This script tests the ComfyUI audio generation capabilities.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ykgen import ComfyUIAudioClient
from ykgen import generate_song_lyrics, generate_music_tags
from ykgen.providers import get_llm


def test_audio_generation():
    """Test audio generation with ComfyUI."""
    print("🎵 Testing audio generation with ComfyUI...")
    
    # Initialize client
    client = ComfyUIAudioClient()
    
    # Test lyrics
    test_lyrics = """In a world of code and dreams
    Where AI learns what magic means
    Stories come to life each day
    In a digital ballet
    
    We create, we innovate
    Through the screen we animate
    Every pixel tells a tale
    On this creative trail"""
    
    # Test tags
    test_tags = "electronic, uplifting, synthesizer, medium tempo, futuristic, inspirational"
    
    # Output path
    output_path = "output/test_audio.mp3"
    os.makedirs("output", exist_ok=True)
    
    try:
        # Generate audio
        success = client.generate_audio(
            lyrics=test_lyrics,
            output_path=output_path,
            tags=test_tags,
            duration_seconds=60  # 1 minute for testing
        )
        
        if success:
            print(f"✅ Audio generated successfully: {output_path}")
            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"📊 Audio file size: {size_mb:.2f} MB")
        else:
            print("❌ Audio generation failed")
            
    except Exception as e:
        print(f"❌ Error during audio generation: {str(e)}")


def test_lyrics_generation():
    """Test lyrics generation from story."""
    print("\n📝 Testing lyrics generation...")
    
    # Get LLM
    llm = get_llm()
    
    # Test story
    test_story = "A brave knight embarks on a quest to save the kingdom from an ancient dragon. Along the way, they discover the power of friendship and courage."
    
    # Test scenes
    test_scenes = [
        {
            "location": "Castle courtyard",
            "time": "Dawn",
            "action": "The knight prepares for the journey"
        },
        {
            "location": "Dark forest",
            "time": "Midnight",
            "action": "The knight faces their fears"
        },
        {
            "location": "Dragon's lair",
            "time": "Sunset",
            "action": "The final confrontation"
        }
    ]
    
    try:
        # Generate lyrics
        lyrics = generate_song_lyrics(test_scenes, test_story, llm)
        print("Generated lyrics:")
        print("-" * 40)
        print(lyrics)
        print("-" * 40)
        
        # Generate music tags
        tags = generate_music_tags(test_scenes, test_story, llm)
        print(f"\nGenerated music tags: {tags}")
        
    except Exception as e:
        print(f"❌ Error generating lyrics: {str(e)}")


def main():
    """Run all audio tests."""
    print("🎵 KGen Audio Generation Test")
    print("=" * 50)
    
    # Test lyrics generation first
    test_lyrics_generation()
    
    # Then test actual audio generation
    print("\n" + "=" * 50)
    response = input("\nProceed with audio generation test? (y/n): ")
    if response.lower() == 'y':
        test_audio_generation()
    else:
        print("Skipping audio generation test.")
    
    print("\n✅ Audio tests completed!")


if __name__ == "__main__":
    main()