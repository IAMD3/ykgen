# YKGen Configuration System

This document explains how to configure image models and LoRA integration in YKGen.

## Image Model Configuration

The `image_model_config.json` file defines available image generation models and their parameters.

### Adding New Models

To add a new model to the "simple" category:

1. **Add model entry to `image_model_config.json`:**

```json
{
  "simple": {
    "models": [
      {
        "name": "Your Model Name",
        "checkpoint": "your-model-file.safetensors",
        "steps": 20,
        "cfg": 7,
        "sampler_name": "euler_ancestral",
        "scheduler": "normal",
        "denoise": 1,
        "guidance": 3.5,
        "lora_config_key": "flux-schnell",
        "default": false
      }
    ]
  }
}
```

2. **Key Parameters:**
   - `name`: Display name for the model
   - `checkpoint`: Model file name (must be in ComfyUI models directory)
   - `steps`: Number of sampling steps
   - `cfg`: CFG scale value
   - `sampler_name`: Sampler algorithm
   - `scheduler`: Scheduler type
   - `denoise`: Denoising strength (0.0-1.0)
   - `guidance`: Guidance scale (for Flux models)
   - `lora_config_key`: **IMPORTANT** - Links to LoRA configuration
   - `default`: Whether this is the default model for the category

## LoRA Integration

The `lora_config_key` field is crucial for LoRA compatibility:

### Available LoRA Configuration Keys

- `"flux-schnell"`: For Flux-based models with fast generation
- `"illustrious-vpred"`: For anime/manga style models

### Creating New LoRA Configurations

If your new model needs different LoRA options:

1. **Add new section to `lora_config.json`:**

```json
{
  "your-new-model-type": {
    "description": "Description of your model type",
    "loras": {
      "1": {
        "name": "Your LoRA Name",
        "description": "LoRA description",
        "file": "your-lora.safetensors",
        "trigger_words": {
          "required": ["trigger1"],
          "optional": ["optional1", "optional2"]
        },
        "display_trigger": "trigger1",
        "strength_model": 1.0,
        "strength_clip": 1.0,
        "download_source": "https://civitai.com/"
      }
    }
  }
}
```

2. **Update model mapping in `lora_config.json`:**

```json
{
  "_model_mapping": {
    "comment": "This section maps image model config keys to LoRA config keys",
    "simple": "flux-schnell",
    "vpred": "illustrious-vpred",
    "your-category": "your-new-model-type"
  }
}
```

3. **Set the `lora_config_key` in your model:**

```json
{
  "name": "Your Model",
  "lora_config_key": "your-new-model-type",
  // ... other parameters
}
```

## Model Categories

### Simple Models
- Fast generation models (like Flux)
- Use basic sampling parameters
- Compatible with `flux-schnell` LoRA configuration by default

### vPred Models
- High-quality models using v-prediction
- Include additional parameters: `sampling`, `zsnr`, `rescale_cfg_multiplier`
- Compatible with `illustrious-vpred` LoRA configuration by default

## Example: Adding a New Flux Variant

```json
{
  "simple": {
    "models": [
      {
        "name": "Flux Dev",
        "checkpoint": "flux1-dev-fp8.safetensors",
        "steps": 20,
        "cfg": 1,
        "sampler_name": "euler",
        "scheduler": "simple",
        "denoise": 1,
        "guidance": 3.5,
        "lora_config_key": "flux-schnell",
        "default": false
      }
    ]
  }
}
```

This new model will:
- Use 20 steps instead of 4
- Inherit all LoRA options from the `flux-schnell` configuration
- Work seamlessly with existing LoRA selection system

## Validation

The system includes automatic fallbacks:
- If `lora_config_key` is missing, defaults to category-appropriate key
- If LoRA configuration is not found, falls back to `flux-schnell`
- If model configuration fails to load, uses hardcoded fallback values

## Best Practices

1. **Always specify `lora_config_key`** for new models
2. **Test LoRA compatibility** after adding new models
3. **Use existing LoRA configurations** when possible
4. **Set only one model as `default: true`** per category
5. **Validate checkpoint file names** match actual files in ComfyUI