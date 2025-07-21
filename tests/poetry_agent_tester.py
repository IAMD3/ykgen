#!/usr/bin/env python3
"""
Test script for PoetryAgent functionality.

This script tests the PoetryAgent with Chinese poetry input.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ykgen import PoetryAgent
from ykgen.console import print_banner, print_prompt, print_info, print_success, print_error


def test_poetry_agent():
    """Test the PoetryAgent with Chinese poetry."""
    print_banner()
    print_info("Testing PoetryAgent", "🎋")
    
    # Initialize the poetry agent
    agent = PoetryAgent(
        enable_audio=True,
    )
    
    # Test poetry - 观沧海 by 曹操
    test_poetry = """观沧海》——曹操：东临碣石，以观沧海。水何澹澹，山岛竦峙。树木丛生，百草丰茂。秋风萧瑟，洪波涌起。日月之行，若出其中；星汉灿烂，若出其里。幸甚至哉，歌以咏志。"""
    
    print_prompt(test_poetry)
    
    try:
        # Generate the complete poetry video
        print_info("Starting poetry processing workflow...", "🌊")
        result = agent.generate(test_poetry)
        
        # Display results
        print_success("Poetry processing completed!")
        
        if 'pinyin_lyrics' in result:
            print_info("Pinyin Conversion:", "🎵")
            print(result['pinyin_lyrics'])
            print()
        
        if 'story_full' in result:
            print_info("Visual Story:", "📖")
            print(result['story_full'].content)
            print()
        
        if 'characters_full' in result:
            print_info(f"Characters ({len(result['characters_full'])} found):", "👥")
            for char in result['characters_full']:
                print(f"  - {char['name']}: {char['description']}")
            print()
        
        if 'scenes' in result:
            print_info(f"Scenes ({len(result['scenes'])} created):", "🎬")
            for i, scene in enumerate(result['scenes']):
                print(f"  Scene {i+1}: {scene['action']} at {scene['location']}")
            print()
        
        if 'image_paths' in result and result['image_paths']:
            print_info(f"Images ({len(result['image_paths'])} generated):", "🖼️")
            for path in result['image_paths']:
                print(f"  - {path}")
            print()
        
        if 'audio_path' in result and result['audio_path']:
            print_info("Audio generated:", "🎵")
            print(f"  - {result['audio_path']}")
            print()
        
        print_success("✨ Poetry video generation completed successfully! ✨")
        
    except Exception as e:
        print_error(f"Error during poetry processing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_poetry_agent()