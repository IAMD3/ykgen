# KGen - AI Story & Video Generator

[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

## Language / 语言

- [English](README.md) | [中文](README_CN.md)

## Introduction 

KGen is a AI generation content tool that transforms simple text prompts into complete AI generated stories with images and videos , creating a consistent and steamless storytelling experience.
  * textual story generation
  * textual characters generation
  * textual scene generation
  * textual song lyrics generation
  * textual image prompt generation
  * image generation (comfyui) : support custom model and loras
  * video generation (siliconflow api ,but wired quality)
  * audio song generation with ACE TTS
  * consistant content (prompt, same seed, lora , etc)
  * log all the related info for repeating regeneration
  * "smart" lora selection (group mode, an extra llm call for selection)


### Interactive Mode

The simplest way to use KGen is through its interactive CLI:

```bash
# Start KGen
uv run python main.py
```

The system will guide you through:
1. Selecting an agent type (VideoAgent, PoetryAgent, or PureImageAgent)
2. Choosing a video provider if you choose video agent  (SiliconFlow)
3. Selecting LoRA models for image style enhancement
4. Entering your creative prompt
5. Watching the generation process with real-time progress display



## ComfyUI Integration

KGen relies on ComfyUI for high-quality image generation. ComfyUI setup requires downloading large AI models and proper configuration.

**📖 Complete Setup Guide**: [ComfyUI Setup Guide](COMFYUI_SETUP.md)

The setup guide covers:
- ComfyUI installation and configuration
- Required model downloads (Flux-Schnell, Illustrious-vPred)
- LoRA model setup for enhanced styles
- Performance optimization
- Troubleshooting common issues

**Quick Start**: Once ComfyUI is running on `http://127.0.0.1:8188`, KGen will automatically connect and use it for image generation.


## Technology Stack

- **Language Models**: DeepSeek-R1 for story generation and creative tasks
- **Image Generation**: ComfyUI with Flux-Schnell (ultra-fast) or Illustrious-vPred (anime-style)
- **Video Generation**: SiliconFlow (Wan2.1 I2V)
- **Audio Synthesis**: ACE TTS for background music
- **Package Management**: uv for modern Python dependency management
- **Orchestration**: LangGraph for AI workflow management
- **Video Processing**: FFmpeg for professional video assembly

## Installation

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- ComfyUI server with required models ([setup guide](COMFYUI_SETUP.md))
- FFmpeg
- API keys for DeepSeek and video providers (SiliconFlow)


## Configuration

Create a `.env` file with your API keys:

```env
# Required API Keys
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=https://api.your-provider.com/v1
LLM_MODEL=your_model_name
SILICONFLOW_VIDEO_KEY=your_siliconflow_video_key_here


# Optional Settings
COMFYUI_HOST=127.0.0.1
COMFYUI_PORT=8188
MAX_SCENES=3
```

## Usage

## Agent Types

### VideoAgent
Creates complete video stories from text prompts:
- Generates story with characters and scenes
- Creates images for each scene
- Converts images to videos
- Adds background music
- Combines into a final video

### PoetryAgent
Transforms Chinese poetry into visual experiences:
- Converts Chinese poetry to pinyin format
- Creates visual story from poetry imagery
- Generates images with cultural aesthetics
- Creates videos with appropriate atmosphere
- Adds traditional music with pinyin vocals

### PureImageAgent
Generates images only, with options:
- Multiple images per scene (1-10)
- Optional audio generation
- Language selection for audio (English or Chinese)
- Saves video prompts to text files for manual video creation

## LoRA Model Enhancement

KGen supports LoRA models for specialized artistic styles:

### Flux-Schnell (Default)
- Ultra-fast 4-step generation (~1-2 seconds per image)
- 8 specialized LoRA options (pixel art, anime, watercolor, etc.)

### Illustrious-vPred
- High-quality anime/manga style generation
- Character-specific LoRA for detailed anime visuals

### LoRA Selection Modes
- **All Mode**: Apply all selected LoRAs to every image
- **Group Mode**: AI intelligently selects appropriate LoRAs for each scene

## Advanced Features

### Style Customization
KGen does not apply any default style, allowing users full control:
- Specify style directly in your story prompt
- The AI derives appropriate style from story content when not specified
- Programmatically specify custom styles when using the API

### Intelligent Retry System
- Automatic retries for failed video generations
- Exponential backoff between retry attempts
- Smart detection of retryable errors

### Multiple Video Providers
- **SiliconFlow**: Wan2.1 I2V model, 5-second clips, 720P

### Audio Language Options
- **English**: Western musical style with English lyrics
- **Chinese**: Traditional Chinese music with pinyin conversion

## Project Architecture

KGen follows a clean, modular architecture:

```
kgen/
├── agents/           # AI Workflow Orchestration
├── audio/            # Audio Generation
├── config/           # Configuration Management
├── console/          # User Interface
├── image/            # Image Generation
├── providers/        # External Integrations
└── video/            # Video Generation & Processing
```

## Image Generation Workflow

KGen follows a sophisticated multi-step process to ensure high-quality, consistent image generation:

### 1. Story Analysis & Scene Planning
- AI analyzes your prompt to create a detailed story structure
- Breaks down narrative into coherent scenes with character consistency
- Generates optimized prompts for each scene

### 2. Style & LoRA Selection
- Intelligent selection of appropriate LoRA models based on content
- Style consistency maintained across all scenes
- Optional manual LoRA selection for creative control

### 3. Image Generation Process
- **Seed Management**: Uses consistent seeds for character/style continuity
- **Prompt Engineering**: Enhanced prompts with style triggers and quality tags
- **Model Selection**: Automatic choice between Flux-Schnell and Illustrious-vPred models
- **Quality Control**: Built-in retry mechanism for failed generations

### 4. Post-Processing & Assembly
- Image optimization and enhancement
- Video conversion with smooth transitions
- Audio synchronization and final assembly

## Image Consistency Solutions

KGen employs multiple techniques to maintain visual consistency across generated content:

### Current Implementation
- **LoRA Models**: Specialized style models ensure consistent artistic direction
- **Seed Consistency**: Same seed values maintain character and style coherence
- **Prompt Engineering**: Carefully crafted prompts with consistent style triggers
- **Model Selection**: Intelligent choice of base models for optimal results

### Advanced Consistency Features
- **Character Persistence**: Maintains character appearance across scenes
- **Style Continuity**: Consistent artistic style throughout the story
- **Quality Assurance**: Automatic retry for inconsistent results

## Output Examples

Each generation creates a timestamped directory with:
- Complete generation record
- Generated images
- Video clips for each scene
- Background audio
- Final combined video

## Next Stage Roadmap

We're continuously improving KGen with exciting new features on the horizon:

### 🎬 Enhanced Video Generation
- **Keling AI Integration**: Automated video generation with Keling's advanced AI models
- **Google Veo 3 Support**: Next-generation video synthesis capabilities
- **Multi-Provider Pipeline**: Seamless switching between video generation services

### 🎨 Advanced Image Consistency
- **Character Reference System**: Maintain exact character appearance across all scenes
- **Style Transfer Enhancement**: More sophisticated style consistency algorithms
- **Cross-Scene Continuity**: Advanced techniques for maintaining visual coherence

### 🚀 Performance & Quality
- **Optimized Generation Pipeline**: Faster processing with maintained quality
- **Enhanced Model Support**: Integration with latest AI models and techniques
- **Smart Resource Management**: Better GPU memory utilization and batch processing

*Stay tuned for these exciting developments that will make KGen even more powerful and user-friendly!*

## Development

```bash
# Run all tests
uv run pytest

# Run specific tests
uv run python tests/video_tester.py

# Format code
uv run black kgen/ tests/
uv run isort kgen/ tests/

# Lint and check
uv run ruff check kgen/ tests/
uv run mypy kgen/
```

## Links

- [GitHub Repository](https://github.com/username/kgen)
- [Issue Tracker](https://github.com/username/kgen/issues)