# ComfyUI Setup Guide for KGen

This guide will help you set up ComfyUI for use with KGen's image generation capabilities. ComfyUI is essential for high-quality image generation in KGen.

## Overview

YKGen supports configurable image generation models through ComfyUI. You can configure models in `ykgen/config/image_model_config.json` and LoRAs in `ykgen/config/lora_config.json`.

### Suggested Models (Optional)
- **Flux-Schnell**: Ultra-fast generation (1-2 seconds per image)
- **WaiNSFW Illustrious**: High-quality NSFW-capable illustrative style (default)
- **Illustrious-vPred**: High-quality anime/manga style generation
- **Custom Models**: Add your own by editing the configuration files

## Prerequisites

- Python 3.8 or higher
- Git
- At least 8GB of GPU VRAM (recommended: 12GB+)
- Sufficient disk space for models (~20GB+)

## Step 1: Install ComfyUI

### Clone and Setup ComfyUI

```bash
# Clone the ComfyUI repository
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# Install Python dependencies
pip install -r requirements.txt
```

### Alternative Installation Methods

**Using conda:**
```bash
conda create -n comfyui python=3.10
conda activate comfyui
pip install -r requirements.txt
```

**Using virtual environment:**
```bash
python -m venv comfyui_env
source comfyui_env/bin/activate  # On Windows: comfyui_env\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Configure and Download Models

### Model Configuration

YKGen uses configuration files to manage models and LoRAs:
- **Model Config**: `ykgen/config/image_model_config.json` - Configure available models
- **LoRA Config**: `ykgen/config/lora_config.json` - Configure available LoRA styles

You can add your own models by editing these configuration files and placing the model files in the appropriate ComfyUI directories.

### Suggested Model Downloads (Optional)

The following are suggested models that work well with YKGen's default configuration:

Create the checkpoints directory if it doesn't exist:
```bash
mkdir -p models/checkpoints/
```

#### Flux-Schnell Model (Ultra-fast generation) - Optional

**Download Options:**
1. **Direct Download**: [Hugging Face - FLUX.1-schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell)
2. **Using git-lfs**:
   ```bash
   cd models/checkpoints/
   git lfs clone https://huggingface.co/black-forest-labs/FLUX.1-schnell
   ```

**File:**
- `flux1-schnell-fp8.safetensors`
- **Size**: ~23GB
- **Place in**: `models/checkpoints/`

#### WaiNSFW Illustrious Model (Default, NSFW-capable) - Suggested

**Download from**: [CivitAI - WaiNSFW Illustrious](https://civitai.com/models/833294)

**File:**
- `waiNSFWIllustrious_v120.safetensors`
- **Size**: ~6.6GB
- **Place in**: `models/checkpoints/`
- **Note**: This is the default model in YKGen's configuration

#### Illustrious-vPred Model (High-quality anime/manga style) - Optional

**Download from**: [CivitAI - NoobAI-XL](https://civitai.com/models/833294/noobai-xl-nai-xl)

**File:**
- `noobaiXLNAIXL_vPred10Version.safetensors`
- **Size**: ~6.6GB
- **Place in**: `models/checkpoints/`

### Additional Required Components

#### VAE Models
Some models may require specific VAE files. Download if needed:
```bash
mkdir -p models/vae/
# Download VAE files as required by your specific models
```

#### CLIP Models
Ensure CLIP models are available:
```bash
mkdir -p models/clip/
# CLIP models are usually included with main models
```

## Step 3: Configure and Download LoRA Models (Optional)

LoRA models enhance image generation with specific artistic styles. YKGen comes with pre-configured LoRAs in `ykgen/config/lora_config.json`.

### Setup LoRA Directory
```bash
mkdir -p models/loras/
```

### LoRA Configuration

YKGen includes configurations for:
- **Flux-Schnell LoRAs**: 8 professional styles (pixel art, anime, watercolor, etc.)
- **Illustrious LoRAs**: 18+ character and style LoRAs for anime/manga
- **WaiNSFW LoRAs**: NSFW-capable LoRAs for mature content

You can add custom LoRAs by:
1. Downloading LoRA files to `models/loras/`
2. Adding configuration entries to `ykgen/config/lora_config.json`

### LoRA Sources
- [Hugging Face LoRA Collection](https://huggingface.co/models?other=lora)
- [CivitAI LoRA Models](https://civitai.com/models?type=LORA)

### Popular LoRA Categories
- **Art Styles**: Watercolor, oil painting, pixel art
- **Character Styles**: Anime, realistic, cartoon
- **Photography**: Portrait, landscape, macro
- **Themes**: Fantasy, sci-fi, historical

## Step 4: Configure ComfyUI

### Basic Configuration

Create a configuration file (optional):
```bash
# Create config file
touch extra_model_paths.yaml
```

Example configuration:
```yaml
comfyui:
    base_path: /path/to/ComfyUI/
    checkpoints: models/checkpoints/
    vae: models/vae/
    loras: models/loras/
    clip: models/clip/
```

## Step 5: Start ComfyUI Server

### Basic Startup
```bash
# Start ComfyUI with API enabled
python main.py --listen 127.0.0.1 --port 8188
```

### Advanced Startup Options
```bash
# With specific GPU and memory settings
python main.py --listen 127.0.0.1 --port 8188 --gpu-only --highvram

# For low VRAM systems
python main.py --listen 127.0.0.1 --port 8188 --lowvram

# For CPU-only mode (very slow)
python main.py --listen 127.0.0.1 --port 8188 --cpu
```

### Verify Installation

Once started, ComfyUI should be accessible at:
- **Web Interface**: `http://127.0.0.1:8188`
- **API Endpoint**: `http://127.0.0.1:8188/api`

## Step 6: Test Integration with KGen

### Verify Connection
1. Ensure ComfyUI is running
2. Check that KGen can connect to ComfyUI
3. Test image generation with a simple prompt

### Configuration in KGen
Ensure your `.env` file contains:
```env
COMFYUI_HOST=127.0.0.1
COMFYUI_PORT=8188
```

## Troubleshooting

### Common Issues

**1. Out of Memory Errors**
- Use `--lowvram` or `--cpu` flags
- Reduce batch size in KGen settings
- Close other GPU-intensive applications

**2. Model Loading Errors**
- Verify model files are complete and not corrupted
- Check file permissions
- Ensure sufficient disk space

**3. Connection Issues**
- Verify ComfyUI is running on the correct port
- Check firewall settings
- Ensure no other services are using port 8188

**4. Slow Generation**
- Use Flux-Schnell for faster generation
- Enable GPU acceleration
- Optimize ComfyUI startup parameters

### Performance Optimization

**For High-End Systems (12GB+ VRAM):**
```bash
python main.py --listen 127.0.0.1 --port 8188 --gpu-only --highvram
```

**For Mid-Range Systems (6-12GB VRAM):**
```bash
python main.py --listen 127.0.0.1 --port 8188 --gpu-only
```

**For Low-End Systems (<6GB VRAM):**
```bash
python main.py --listen 127.0.0.1 --port 8188 --lowvram
```

## Directory Structure

After setup, your ComfyUI directory should look like:
```
ComfyUI/
├── models/
│   ├── checkpoints/
│   │   ├── flux1-schnell-fp8.safetensors (optional)
│   │   ├── waiNSFWIllustrious_v120.safetensors (suggested default)
│   │   ├── noobaiXLNAIXL_vPred10Version.safetensors (optional)
│   │   └── [your custom model files]
│   ├── loras/
│   │   └── [your LoRA files - see lora_config.json]
│   ├── vae/
│   └── clip/
├── main.py
├── requirements.txt
└── [other ComfyUI files]
```

## Model Configuration Files

YKGen uses these configuration files to manage models and LoRAs:
- `ykgen/config/image_model_config.json` - Configure available image generation models
- `ykgen/config/lora_config.json` - Configure available LoRA styles and enhancements

Edit these files to add your own models or modify existing configurations.

## Next Steps

Once ComfyUI is set up and running:
1. Return to the main KGen documentation
2. Configure your `.env` file with API keys
3. Start generating amazing content with KGen!

## Support

For ComfyUI-specific issues:
- [ComfyUI GitHub Repository](https://github.com/comfyanonymous/ComfyUI)
- [ComfyUI Documentation](https://github.com/comfyanonymous/ComfyUI#readme)

For KGen integration issues:
- Check the main KGen documentation
- Review the troubleshooting section above