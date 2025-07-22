# YKGen ComfyUI 设置指南

本指南将帮助您为YKGen的图像生成功能设置ComfyUI。ComfyUI是YKGen唯一需要的外部依赖。

## 概述

**您可以完全自由地选择任何您喜欢的图像生成模型和LoRA。** YKGen设计为通过可配置的JSON文件与任何ComfyUI兼容的模型一起工作。

### 配置文件
- **模型配置**: `ykgen/config/image_model_config.json` - 配置您偏好的模型
- **LoRA配置**: `ykgen/config/lora_config.json` - 配置您偏好的LoRA风格

### 推荐模型（可选）
- **Flux-Schnell**：超快速生成（每张图像1-2秒）
- **WaiNSFW Illustrious**：高质量NSFW功能的插画风格（默认）
- **Illustrious-vPred**：高质量动漫/漫画风格生成
- **任何自定义模型**：只需将它们添加到配置文件中

## 系统要求

- Python 3.8 或更高版本
- Git
- 至少8GB显存（推荐：12GB+）
- 足够的磁盘空间存储模型（约20GB+）

## 步骤1：安装ComfyUI

### 克隆并设置ComfyUI

```bash
# 克隆ComfyUI仓库
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# 安装Python依赖
pip install -r requirements.txt
```

### 其他安装方法

**使用conda：**
```bash
conda create -n comfyui python=3.10
conda activate comfyui
pip install -r requirements.txt
```

**使用虚拟环境：**
```bash
python -m venv comfyui_env
source comfyui_env/bin/activate  # Windows系统：comfyui_env\Scripts\activate
pip install -r requirements.txt
```

## 步骤2：选择和配置您的模型

### 模型自由度

**您可以使用任何您喜欢的模型！** YKGen与任何ComfyUI兼容的模型一起工作。只需：
1. 将您偏好的模型下载到ComfyUI的`models/checkpoints/`目录
2. 编辑`ykgen/config/image_model_config.json`添加您的模型
3. 可选择在`ykgen/config/lora_config.json`中配置LoRA

### 示例模型下载（可选推荐）

以下是一些与YKGen配合良好的热门模型，但您可以自由使用任何您偏好的模型：

如果不存在，创建checkpoints目录：
```bash
mkdir -p models/checkpoints/
```

#### Flux-Schnell模型（超快速生成）- 可选

**下载选项：**
1. **直接下载**：[Hugging Face - FLUX.1-schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell)
2. **使用git-lfs**：
   ```bash
   cd models/checkpoints/
   git lfs clone https://huggingface.co/black-forest-labs/FLUX.1-schnell
   ```

**必需文件：**
- `flux1-schnell-fp8.safetensors`
- **大小**：约23GB
- **放置位置**：`models/checkpoints/`

#### Illustrious-vPred模型（高质量动漫/漫画风格）

**下载地址**：[CivitAI - NoobAI-XL](https://civitai.com/models/833294/noobai-xl-nai-xl)

**必需文件：**
- `noobaiXLNAIXL_vPred10Version.safetensors`
- **大小**：约6.6GB
- **放置位置**：`models/checkpoints/`

### 其他必需组件

#### VAE模型
某些模型可能需要特定的VAE文件。如需要请下载：
```bash
mkdir -p models/vae/
# 根据您的特定模型需求下载VAE文件
```

#### CLIP模型
确保CLIP模型可用：
```bash
mkdir -p models/clip/
# CLIP模型通常包含在主模型中
```

## 步骤3：添加LoRA模型（可选）

**使用任何您喜欢的LoRA！** LoRA模型可以通过特定艺术风格增强图像生成效果。

### 设置LoRA目录
```bash
mkdir -p models/loras/
```

### 添加您的LoRA

1. 将任何您想要的LoRA文件下载到`models/loras/`
2. 将它们添加到`ykgen/config/lora_config.json`配置中
3. YKGen将自动检测并使用它们

**注意**：YKGen附带一些预配置的LoRA作为示例，但您可以用任何您偏好的LoRA替换它们。

### LoRA来源
- [Hugging Face LoRA合集](https://huggingface.co/models?other=lora)
- [CivitAI LoRA模型](https://civitai.com/models?type=LORA)

### 热门LoRA类别
- **艺术风格**：水彩、油画、像素艺术
- **角色风格**：动漫、写实、卡通
- **摄影风格**：肖像、风景、微距
- **主题风格**：奇幻、科幻、历史

## 步骤4：配置ComfyUI

### 基本配置

创建配置文件（可选）：
```bash
# 创建配置文件
touch extra_model_paths.yaml
```

配置示例：
```yaml
comfyui:
    base_path: /path/to/ComfyUI/
    checkpoints: models/checkpoints/
    vae: models/vae/
    loras: models/loras/
    clip: models/clip/
```

## 步骤5：启动ComfyUI服务器

### 基本启动
```bash
# 启用API启动ComfyUI
python main.py --listen 127.0.0.1 --port 8188
```

### 高级启动选项
```bash
# 指定GPU和内存设置
python main.py --listen 127.0.0.1 --port 8188 --gpu-only --highvram

# 低显存系统
python main.py --listen 127.0.0.1 --port 8188 --lowvram

# 仅CPU模式（非常慢）
python main.py --listen 127.0.0.1 --port 8188 --cpu
```

### 验证安装

启动后，ComfyUI应该可以在以下地址访问：
- **Web界面**：`http://127.0.0.1:8188`
- **API端点**：`http://127.0.0.1:8188/api`

## 步骤6：测试与KGen的集成

### 验证连接
1. 确保ComfyUI正在运行
2. 检查KGen能否连接到ComfyUI
3. 使用简单提示测试图像生成

### KGen中的配置
确保您的`.env`文件包含：
```env
COMFYUI_HOST=127.0.0.1
COMFYUI_PORT=8188
```

## 故障排除

### 常见问题

**1. 内存不足错误**
- 使用`--lowvram`或`--cpu`标志
- 在KGen设置中减少批处理大小
- 关闭其他占用GPU的应用程序

**2. 模型加载错误**
- 验证模型文件完整且未损坏
- 检查文件权限
- 确保有足够的磁盘空间

**3. 连接问题**
- 验证ComfyUI在正确端口运行
- 检查防火墙设置
- 确保没有其他服务使用8188端口

**4. 生成速度慢**
- 使用Flux-Schnell进行更快生成
- 启用GPU加速
- 优化ComfyUI启动参数

### 性能优化

**高端系统（12GB+显存）：**
```bash
python main.py --listen 127.0.0.1 --port 8188 --gpu-only --highvram
```

**中端系统（6-12GB显存）：**
```bash
python main.py --listen 127.0.0.1 --port 8188 --gpu-only
```

**低端系统（<6GB显存）：**
```bash
python main.py --listen 127.0.0.1 --port 8188 --lowvram
```

## 目录结构

设置完成后，您的ComfyUI目录应该如下所示：
```
ComfyUI/
├── models/
│   ├── checkpoints/
│   │   ├── flux1-schnell-fp8.safetensors
│   │   └── noobaiXLNAIXL_vPred10Version.safetensors
│   ├── loras/
│   │   └── [您的LoRA文件]
│   ├── vae/
│   └── clip/
├── main.py
├── requirements.txt
└── [其他ComfyUI文件]
```

## 使用您自己的模型

**完全自由**：YKGen设计为与任何ComfyUI兼容的模型一起工作。配置文件只是示例：
- `ykgen/config/image_model_config.json` - 添加您偏好的图像生成模型
- `ykgen/config/lora_config.json` - 添加您偏好的LoRA风格

**只需编辑这些文件即可使用您自己的模型而不是默认模型。**

## 下一步

ComfyUI设置并运行后：
1. 返回主YKGen文档
2. 使用API密钥配置您的`.env`文件
3. 开始使用YKGen生成精彩内容！

## 支持

ComfyUI相关问题：
- [ComfyUI GitHub仓库](https://github.com/comfyanonymous/ComfyUI)
- [ComfyUI文档](https://github.com/comfyanonymous/ComfyUI#readme)

YKGen集成问题：
- 查看主YKGen文档
- 查看上述故障排除部分