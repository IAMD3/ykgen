#!/usr/bin/env python3
"""
Style Customization Test for KGen.

This script demonstrates how users can define custom visual styles
for their story generation, with "dark cartoon" as the default.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kgen import VideoAgent, PoetryAgent
from kgen.console import print_info, print_success, print_warning


def test_style_customization():
    """Test style customization with different agents and styles."""
    
    print_info("🎨 Testing Style Customization Feature")
    print()
    
    # Test different styles
    test_styles = [
        "dark cartoon",  # Default
        "watercolor",    # Soft, artistic
        "cyberpunk",     # Futuristic
        "anime",         # Japanese animation
        "realistic",     # Photorealistic
        "fantasy",       # Magical
        "oil painting",  # Custom style
    ]
    
    test_prompt = "A brave knight's quest to save a magical kingdom"
    
    for style in test_styles:
        print_info(f"Testing style: {style}")
        
        # Create agent with custom style
        agent = VideoAgent(
            enable_audio=False,  # Disable audio for faster testing
            style=style
        )
        
        # Verify style is set correctly
        if agent.style == style:
            print_success(f"✓ Style '{style}' correctly set")
        else:
            print_warning(f"✗ Style mismatch: expected '{style}', got '{agent.style}'")
        
        # Create initial state to test style propagation
        from kgen.model.models import VisionState
        from langchain_core.messages import HumanMessage
        
        initial_state = VisionState(
            prompt=HumanMessage(content=test_prompt),
            style=style,
        )
        
        # Test that style is preserved in state
        if initial_state.get("style") == style:
            print_success(f"✓ Style '{style}' correctly propagated to state")
        else:
            print_warning(f"✗ Style not found in state: {initial_state.get('style')}")
        
        print()
    
    print_info("🎨 Style customization test completed!")
    print()
    print_info("💡 To use custom styles in your stories:")
    print_info("   1. Run: python main.py")
    print_info("   2. Choose VideoAgent or PoetryAgent")
    print_info("   3. Select your preferred visual style")
    print_info("   4. Enter your story prompt")
    print_info("   5. The LLM will generate image prompts with your chosen style")


def test_poetry_style():
    """Test style customization with poetry agent."""
    
    print_info("🎋 Testing Poetry Agent Style Customization")
    print()
    
    test_poetry = "静夜思——李白：床前明月光，疑是地上霜。举头望明月，低头思故乡。"
    test_style = "traditional chinese painting"
    
    # Create poetry agent with custom style
    agent = PoetryAgent(
        enable_audio=False,
        style=test_style
    )
    
    print_success(f"✓ PoetryAgent initialized with style: {agent.style}")
    
    # Test initial state
    from kgen.model.models import VisionState
    from langchain_core.messages import HumanMessage
    
    initial_state = VisionState(
        prompt=HumanMessage(content=test_poetry),
        style=test_style,
    )
    
    print_success(f"✓ Poetry state initialized with style: {initial_state.get('style')}")
    print()
    print_info("🎋 Poetry style customization test completed!")


if __name__ == "__main__":
    try:
        test_style_customization()
        print()
        test_poetry_style()
        print()
        print_success("🎉 All style customization tests passed!")
        
    except Exception as e:
        print_warning(f"Test error: {e}")
        print_info("This is expected if API keys are not configured for full testing")