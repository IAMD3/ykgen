#!/usr/bin/env python3
"""
Demo script showing the new interactive interface of KGen.

This script demonstrates the user interaction flow without actually
running the generation (useful for testing the UI).
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kgen.console import print_banner, print_info, print_success


def demo_interactive_flow():
    """Demonstrate the interactive flow."""
    print_banner()
    print_info("🎬 Interactive Demo - KGen UI Flow 🎬", "")
    print()
    
    print("This is how the new interactive interface works:")
    print()
    
    # Step 1: Agent Selection
    print_info("Step 1: Agent Selection", "1️⃣")
    print()
    print("📋 Available Agents:")
    print("  1. 🎭 VideoAgent    - Create original stories from text prompts")
    print("  2. 🎋 PoetryAgent   - Transform Chinese poetry into visual experiences")
    print()
    print("👉 Please choose an agent (1 or 2): 1")
    print_success("Selected: VideoAgent for story generation")
    print()
    
    # Step 2: Prompt Input
    print_info("Step 2: Prompt Input", "2️⃣")
    print()
    print("✍️  Prompt Input:")
    print("📝 Please enter your story prompt:")
    print("   Example: A brave knight's quest to save a magical kingdom")
    print()
    print("🎬 Enter story prompt: A magical forest where animals can speak")
    print()
    print("📋 You entered:")
    print("   A magical forest where animals can speak")
    print()
    print("✅ Proceed with this prompt? (y/n): y")
    print()
    
    # Step 3: Generation Info
    print_info("Step 3: Generation Process Preview", "3️⃣")
    print()
    print("🚀 Generation Process:")
    print("  1. 📝 Generate complete story from your prompt")
    print("  2. 🎭 Extract characters and their descriptions")
    print("  3. 🎬 Create visual scenes from the story")
    print("  4. 🖼️ Generate high-quality images for each scene")
    print("  5. 🎥 Convert images to dynamic videos")
    print("  6. 🎵 Create background music matching the story")
    print("  7. 🎞️ Combine everything into a final video")
    print()
    print("⏱️  Estimated time: 2-5 minutes")
    print("📁 Output will be saved in the 'output/' directory")
    print()
    
    # Poetry Demo
    print_info("Poetry Agent Demo", "🎋")
    print()
    print("For PoetryAgent, the flow would be:")
    print()
    print("👉 Please choose an agent (1 or 2): 2")
    print_success("Selected: PoetryAgent for Chinese poetry processing")
    print()
    print("✍️  Prompt Input:")
    print("📝 Please enter your Chinese poetry:")
    print("   Example: 观沧海——曹操：东临碣石，以观沧海。水何澹澹，山岛竦峙...")
    print()
    print("🎋 Enter Chinese poetry: 静夜思——李白：床前明月光，疑是地上霜。举头望明月，低头思故乡。")
    print()
    print("🚀 Generation Process:")
    print("  1. 🈴 Convert poetry to pinyin format")
    print("  2. 📖 Create visual story from poetry imagery")
    print("  3. 👥 Identify characters from the poetry")
    print("  4. 🎨 Design scenes with traditional Chinese aesthetics")
    print("  5. 🖼️ Generate images with poetic atmosphere")
    print("  6. 🎬 Create videos maintaining artistic mood")
    print("  7. 🎵 Generate traditional music with pinyin vocals")
    print("  8. 🎞️ Combine into final poetry video")
    print()
    
    print_success("✨ Interactive Demo Complete! ✨")
    print()
    print("To run the actual interactive KGen:")
    print("  uv run python main.py")
    print()


if __name__ == "__main__":
    demo_interactive_flow() 