# ComfyUI Setup Guide for KGen

This guide will help you set up ComfyUI for image generation in KGen using Flux models.

## Prerequisites

- Python 3.8 or higher
- NVIDIA GPU with at least 8GB VRAM (recommended for Flux)
- Git

## Installation Steps

### 1. Install ComfyUI

```bash
# Clone ComfyUI repository
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# Install dependencies
pip install -r requirements.txt
```

### 2. Download Flux Model

Download the Flux model file `flux1-schnell-fp8.safetensors` and place it in the `models/checkpoints/` directory:

```bash
# Create the checkpoints directory if it doesn't exist
mkdir -p models/checkpoints/

# Download Flux model (you'll need to get this from Hugging Face or other sources)
# Example: huggingface-cli download black-forest-labs/FLUX.1-schnell flux1-schnell-fp8.safetensors --local-dir models/checkpoints/
```

### 3. Download LoRA Models (Optional but Recommended)

KGen supports LoRA models for enhanced artistic styles. Create the LoRA directory and download the models:

```bash
# Create the LoRA directory
mkdir -p models/loras/

# Download LoRA models (you'll need to get these from Hugging Face, CivitAI, or other sources)
# Place the following files in models/loras/:
```

**Available LoRA Models for KGen:**

| Model File | Style | Trigger Words | Source |
|------------|--------|---------------|---------|
| `HEZI_F.1竖版像素游戏风格_v5.0.safetensors` | Pixel Game Style | `HEZI` | CivitAI/Hugging Face |
| `pixel-art-flux-v3-learning-rate-4.safetensors` | Modern Pixel Art | `pixel art` | CivitAI/Hugging Face |
| `pixelart_schnell_v1.safetensors` | Fast Pixel Art | `pixel art` | CivitAI/Hugging Face |
| `flux_illustriousXL_schnell_v1-rev2.safetensors` | Anime Illustration | `illustrious style` | CivitAI/Hugging Face |
| `pvc-shnell-7250+7500.safetensors` | PVC Figure Style | `pvc figure, figma` | CivitAI/Hugging Face |
| `watercolor_schnell_v1.safetensors` | Watercolor Painting | `watercolor painting` | CivitAI/Hugging Face |
| `hinaFluxAsianMixLora-schnell_v4-rev2.safetensors` | Asian Portrait Style | `Asian girl` | CivitAI/Hugging Face |

**Final LoRA Directory Structure:**
```
ComfyUI/models/loras/
├── HEZI_F.1竖版像素游戏风格_v5.0.safetensors
├── pixel-art-flux-v3-learning-rate-4.safetensors
├── pixelart_schnell_v1.safetensors
├── flux_illustriousXL_schnell_v1-rev2.safetensors
├── pvc-shnell-7250+7500.safetensors
├── watercolor_schnell_v1.safetensors
└── hinaFluxAsianMixLora-schnell_v4-rev2.safetensors
```

### 4. Required ComfyUI Nodes

Make sure you have the following nodes installed (they should be available by default):

**Basic Nodes:**
- `CLIPTextEncode`
- `VAEDecode` 
- `SaveImage`
- `EmptySD3LatentImage`
- `CheckpointLoaderSimple`
- `KSampler`

**LoRA Enhancement Nodes:**
- `LoraLoader` (for LoRA model loading)
- `FluxGuidance` (for enhanced prompt guidance)

These additional nodes are typically included with ComfyUI by default, but if missing, you may need to update ComfyUI or install additional node packs.

### 5. Start ComfyUI Server

```bash
# Start ComfyUI with API enabled
python main.py --listen 127.0.0.1 --port 8188
```

The server should start and be accessible at `http://127.0.0.1:8188`

## Verification

### Test ComfyUI Connection

You can test if ComfyUI is running properly by visiting `http://127.0.0.1:8188` in your browser. You should see the ComfyUI interface.

### Test with KGen

```python
from kgen.comfyui import ComfyUIClient

# Test connection
client = ComfyUIClient()
print("ComfyUI client initialized successfully!")
```

### Test LoRA Functionality

```python
from kgen import VideoAgent

# Test with a LoRA model
lora_config = {
    "name": "Watercolor Schnell",
    "file": "watercolor_schnell_v1.safetensors",
    "trigger": "watercolor painting"
}

try:
    agent = VideoAgent(lora_config=lora_config)
    print("✅ LoRA configuration loaded successfully!")
    print(f"   LoRA: {lora_config['name']}")
    print(f"   Trigger: {lora_config['trigger']}")
except Exception as e:
    print(f"❌ LoRA test failed: {e}")
```

## Configuration

### Default Settings

KGen uses the following default Flux configuration:

- **Model**: `flux1-schnell-fp8.safetensors`
- **Resolution**: 1024x1024
- **Steps**: 4
- **Sampler**: Euler
- **Scheduler**: Simple
- **CFG**: 1.0 (Negative prompts ignored)

### Custom Configuration

You can customize the ComfyUI server address when initializing the client:

```python
from kgen.comfyui import ComfyUIClient

# Custom server address
client = ComfyUIClient(server_address="192.168.1.100:8188")
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Make sure ComfyUI server is running
   - Check that the port 8188 is not blocked by firewall
   - Verify the server address is correct

2. **Model Not Found**
   - Ensure `flux1-schnell-fp8.safetensors` is in the `models/checkpoints/` directory
   - Check file permissions

3. **Out of Memory Errors**
   - Reduce image resolution
   - Close other GPU-intensive applications
   - Consider using a smaller Flux model variant

4. **Slow Generation**
   - Flux Schnell is optimized for speed and should generate images much faster than Flux Dev
   - Each image typically takes 30-60 seconds depending on hardware

5. **LoRA Model Issues**
   - If LoRA models aren't loading, check they're in the `models/loras/` directory
   - Ensure LoRA file names match exactly what KGen expects
   - LoRA models require additional VRAM (consider reducing other settings if memory errors occur)
   - If LoRA effects aren't visible, verify the model is compatible with Flux

### Debug Mode

Enable debug logging in KGen:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Tips

1. **GPU Memory**: Flux models require significant GPU memory. 8GB+ VRAM recommended.
2. **Generation Time**: Flux Schnell is much faster - each image takes 30-60 seconds depending on your hardware.
3. **Batch Processing**: KGen processes scenes sequentially to avoid memory issues.
4. **Speed Advantage**: Flux Schnell is a distilled model that can generate good quality images with only 4 steps.

## Alternative Models

If Flux is too resource-intensive, you can modify the workflow in `kgen/comfyui.py` to use other models:

- SDXL models
- Stable Diffusion 1.5
- Other diffusion models supported by ComfyUI

Just update the `ckpt_name` in the `flux_workflow_template` and adjust other parameters as needed.