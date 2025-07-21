# KGen - AI Story & Video Generator

[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Language / 语言

- [English](README.md) | [中文](README_CN.md)

## Introduction (I'v rewritted AI generated content manually)

KGen is a AI generation content tool that transforms simple text prompts into complete AI generated images and video stories, creating a consistent and immersive storytelling experience.


## Key Features

- **Story Generation**: Creates rich narratives with characters and plot using openai standarad LLM
- **Image Creation**: Generates consistent images through ComfyUI with Flux-Schnell or Illustrious-vPred
- **Video Synthesis**: Converts images to fluid videos using SiliconFlow with Wan2.1 I2V (but wired quality)
- **Song generation**: Creates background music and voice narration with ACE TTS (somehow not too bade)
- **Multiple Generation Modes**: Supports video stories, poetry visualization, and pure image generation
- **Style Customization**: Enhanced image generation with various artistic styles through LoRA models

## Usage

KGen offers multiple ways to generate content based on your needs:

### Interactive Mode

The simplest way to use KGen is through its interactive CLI:

```bash
# Start KGen
uv run python main.py
```

The system will guide you through:
1. Selecting an agent type (VideoAgent, PoetryAgent, or PureImageAgent)
2. Choosing a video provider (SiliconFlow)
3. Selecting LoRA models for image style enhancement
4. Entering your creative prompt
5. Watching the generation process with real-time progress display

### Programmatic Usage

For more advanced use cases, KGen can be integrated into your Python projects:

#### Video Story Generation
```python
from kgen import VideoAgent

# Create agent (uses LLM configuration from environment)
agent = VideoAgent(
    enable_audio=True,
    video_provider="siliconflow"
)

result = agent.generate("A brave knight's quest to save a magical kingdom")
```

#### Poetry Visualization
```python
from kgen import PoetryAgent

# Create agent (uses LLM configuration from environment)
agent = PoetryAgent(
    enable_audio=True,
    video_provider="siliconflow"
)

poetry = """观沧海》——曹操：东临碣石，以观沧海。水何澹澹，山岛竦峙。
树木丛生，百草丰茂。秋风萧瑟，洪波涌起。日月之行，若出其中；
星汉灿烂，若出其里。幸甚至哉，歌以咏志。"""

result = agent.generate(poetry)
```

#### Pure Image Generation
```python
from kgen import PureImageAgent

# Create agent (uses LLM configuration from environment)
agent = PureImageAgent(
    enable_audio=False,
    images_per_scene=3  # Generate 3 images per scene
)

result = agent.generate("A mystical underwater city with glowing coral towers")
```

## ComfyUI Integration

KGen relies on ComfyUI for high-quality image generation. Follow these steps to set up ComfyUI for use with KGen:

### 1. Install ComfyUI

```bash
# Clone ComfyUI repository
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# Install dependencies
pip install -r requirements.txt
```

### 2. Download Required Models

Download the AI models and place them in the appropriate directories:

#### Main Models (Required)

```bash
# Create the checkpoints directory if it doesn't exist
mkdir -p models/checkpoints/
```

**Flux-Schnell Model** (Ultra-fast generation):
- Download from: [Hugging Face - FLUX.1-schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell)
- File: `flux1-schnell-fp8.safetensors`
- Place in: `models/checkpoints/`

**Illustrious-vPred Model** (High-quality anime/manga style):
- Download from: [CivitAI - NoobAI-XL](https://civitai.com/models/833294/noobai-xl-nai-xl)
- File: Model checkpoint file (`.safetensors`)
- Place in: `models/checkpoints/`

**WAI NSFW Illustrious Model** (Alternative anime model):
- Download from: [CivitAI - WAI-NSFW-illustrious-SDXL](https://civitai.com/models/827184/wai-nsfw-illustrious-sdxl)
- File: Model checkpoint file (`.safetensors`)
- Place in: `models/checkpoints/`

### 3. Download LoRA Models (Optional but Recommended)

For enhanced artistic styles, download LoRA models and place them in the LoRA directory:

```bash
# Create the LoRA directory
mkdir -p models/loras/

# Download LoRA models from Hugging Face, CivitAI, or other sources
```

### 4. Start ComfyUI Server

```bash
# Start ComfyUI with API enabled
python main.py --listen 127.0.0.1 --port 8188
```

The server should be accessible at `http://127.0.0.1:8188`

For detailed ComfyUI setup instructions, refer to the [ComfyUI Setup Guide](COMFYUI_SETUP.md).

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

```bash
# Clone the repository
git clone <repository-url>
cd kgen

# Install dependencies
uv sync

# Set up environment
cp env.example .env
# Edit .env with your API keys
```

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
- **Model Selection**: Automatic choice between Flux-Schnell, Illustrious-vPred, or WAI models
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

- [ComfyUI Setup Guide](COMFYUI_SETUP.md)
- [GitHub Repository](https://github.com/username/kgen)
- [Issue Tracker](https://github.com/username/kgen/issues)