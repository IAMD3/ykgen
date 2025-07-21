# KGen - AI故事与视频生成器

[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Language / 语言

- [English](README.md) | [中文](README_CN.md)

## 项目介绍

KGen是一个强大的AI驱动工具，能够将简单的文本提示转换为完整的视频故事。它无缝集成了多种AI技术，生成连贯的叙述和匹配的视觉效果，创造出一致且沉浸式的故事体验。

该项目结合了用于故事生成的先进语言模型、通过ComfyUI进行的最先进图像生成，以及视频合成功能，从文本描述中产生高质量的视觉内容。无论您需要可视化创意概念、将诗歌转化为视觉艺术，还是生成一致的图像序列，KGen都提供了端到端的解决方案。

## 主要功能

- **完整故事生成**：使用DeepSeek-R1 LLM创建包含角色和情节的丰富叙述
- **高质量图像创建**：通过ComfyUI使用Flux-Schnell或Illustrious-vPred生成一致的图像
- **视频合成**：使用SiliconFlow的Wan2.1 I2V将图像转换为流畅的视频
- **音频集成**：使用ACE TTS创建背景音乐和语音旁白
- **多种生成模式**：支持视频故事、诗歌可视化和纯图像生成
- **风格定制**：通过LoRA模型增强各种艺术风格的图像生成
- **用户友好界面**：控制台中清晰、信息丰富的进度显示

## 使用方法

KGen根据您的需求提供多种内容生成方式：

### 交互模式

使用KGen最简单的方式是通过其交互式CLI：

```bash
# 启动KGen
uv run python main.py
```

系统将引导您完成：
1. 选择代理类型（VideoAgent、PoetryAgent或PureImageAgent）
2. 选择视频提供商（SiliconFlow）
3. 选择LoRA模型进行图像风格增强
4. 输入您的创意提示
5. 观看实时进度显示的生成过程

### 编程使用

对于更高级的用例，KGen可以集成到您的Python项目中：

#### 视频故事生成
```python
from kgen import VideoAgent

# 创建代理（使用环境中的LLM配置）
agent = VideoAgent(
    enable_audio=True,
    video_provider="siliconflow"
)

result = agent.generate("一个勇敢骑士拯救魔法王国的冒险")
```

#### 诗歌可视化
```python
from kgen import PoetryAgent

# 创建代理（使用环境中的LLM配置）
agent = PoetryAgent(
    enable_audio=True,
    video_provider="siliconflow"
)

poetry = """观沧海》——曹操：东临碣石，以观沧海。水何澹澹，山岛竦峙。
树木丛生，百草丰茂。秋风萧瑟，洪波涌起。日月之行，若出其中；
星汉灿烂，若出其里。幸甚至哉，歌以咏志。"""

result = agent.generate(poetry)
```

#### 纯图像生成
```python
from kgen import PureImageAgent

# 创建代理（使用环境中的LLM配置）
agent = PureImageAgent(
    enable_audio=False,
    images_per_scene=3  # 每个场景生成3张图像
)

result = agent.generate("一个神秘的水下城市，有发光的珊瑚塔")
```

## ComfyUI集成

KGen依赖ComfyUI进行高质量图像生成。按照以下步骤设置ComfyUI以与KGen配合使用：

### 1. 安装ComfyUI

```bash
# 克隆ComfyUI仓库
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# 安装依赖
pip install -r requirements.txt
```

### 2. 下载所需模型

下载AI模型并将其放置在适当的目录中：

#### 主要模型（必需）

```bash
# 如果不存在，创建checkpoints目录
mkdir -p models/checkpoints/
```

**Flux-Schnell模型**（超快速生成）：
- 下载地址：[Hugging Face - FLUX.1-schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell)
- 文件：`flux1-schnell-fp8.safetensors`
- 放置位置：`models/checkpoints/`

**Illustrious-vPred模型**（高质量动漫/漫画风格）：
- 下载地址：[CivitAI - NoobAI-XL](https://civitai.com/models/833294/noobai-xl-nai-xl)
- 文件：模型检查点文件（`.safetensors`）
- 放置位置：`models/checkpoints/`

**WAI NSFW Illustrious模型**（替代动漫模型）：
- 下载地址：[CivitAI - WAI-NSFW-illustrious-SDXL](https://civitai.com/models/827184/wai-nsfw-illustrious-sdxl)
- 文件：模型检查点文件（`.safetensors`）
- 放置位置：`models/checkpoints/`

### 3. 下载LoRA模型（可选但推荐）

为了增强艺术风格，下载LoRA模型并将其放置在LoRA目录中：

```bash
# 创建LoRA目录
mkdir -p models/loras/

# 从Hugging Face、CivitAI或其他来源下载LoRA模型
```

### 4. 启动ComfyUI服务器

```bash
# 启用API启动ComfyUI
python main.py --listen 127.0.0.1 --port 8188
```

服务器应该可以在`http://127.0.0.1:8188`访问

详细的ComfyUI设置说明，请参考[ComfyUI设置指南](COMFYUI_SETUP.md)。

## 技术栈

- **语言模型**：DeepSeek-R1用于故事生成和创意任务
- **图像生成**：ComfyUI配合Flux-Schnell（超快速）或Illustrious-vPred（动漫风格）
- **视频生成**：SiliconFlow（Wan2.1 I2V）
- **音频合成**：ACE TTS用于背景音乐
- **包管理**：uv用于现代Python依赖管理
- **编排**：LangGraph用于AI工作流管理
- **视频处理**：FFmpeg用于专业视频组装

## 安装

### 先决条件

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)包管理器
- 带有所需模型的ComfyUI服务器（[设置指南](COMFYUI_SETUP.md)）
- FFmpeg
- DeepSeek和视频提供商（SiliconFlow）的API密钥

```bash
# 克隆仓库
git clone <repository-url>
cd kgen

# 安装依赖
uv sync

# 设置环境
cp env.example .env
# 编辑.env文件添加您的API密钥
```

## 配置

创建包含您的API密钥的`.env`文件：

```env
# 必需的API密钥
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=https://api.your-provider.com/v1
LLM_MODEL=your_model_name
SILICONFLOW_VIDEO_KEY=your_siliconflow_video_key_here


# 可选设置
COMFYUI_HOST=127.0.0.1
COMFYUI_PORT=8188
MAX_SCENES=3
```

## 代理类型

### VideoAgent
从文本提示创建完整的视频故事：
- 生成包含角色和场景的故事
- 为每个场景创建图像
- 将图像转换为视频
- 添加背景音乐
- 合并成最终视频

### PoetryAgent
将中文诗歌转换为视觉体验：
- 将中文诗歌转换为拼音格式
- 从诗歌意象创建视觉故事
- 生成具有文化美学的图像
- 创建具有适当氛围的视频
- 添加带有拼音声乐的传统音乐

### PureImageAgent
仅生成图像，具有以下选项：
- 每个场景多张图像（1-10张）
- 可选音频生成
- 音频语言选择（英语或中文）
- 将视频提示保存到文本文件以供手动视频创建

## LoRA模型增强

KGen支持用于专业艺术风格的LoRA模型：

### Flux-Schnell（默认）
- 超快4步生成（每张图像约1-2秒）
- 8种专业LoRA选项（像素艺术、动漫、水彩等）

### Illustrious-vPred
- 高质量动漫/漫画风格生成
- 用于详细动漫视觉效果的角色特定LoRA

### LoRA选择模式
- **全部模式**：将所有选定的LoRA应用于每张图像
- **分组模式**：AI智能为每个场景选择适当的LoRA

## 高级功能

### 风格定制
KGen不应用任何默认风格，允许用户完全控制：
- 在故事提示中直接指定风格
- 当未指定时，AI从故事内容中推导适当的风格
- 使用API时以编程方式指定自定义风格

### 智能重试系统
- 对失败的视频生成自动重试
- 重试尝试之间的指数退避
- 智能检测可重试错误

### 多个视频提供商
- **SiliconFlow**：Wan2.1 I2V模型，5秒片段，720P

### 音频语言选项
- **英语**：西方音乐风格配英语歌词
- **中文**：传统中国音乐配拼音转换

## 项目架构

KGen遵循清晰的模块化架构：

```
kgen/
├── agents/           # AI工作流编排
├── audio/            # 音频生成
├── config/           # 配置管理
├── console/          # 用户界面
├── image/            # 图像生成
├── providers/        # 外部集成
└── video/            # 视频生成与处理
```

## 图像生成工作流程

KGen遵循复杂的多步骤流程，确保高质量、一致的图像生成：

### 1. 故事分析与场景规划
- AI分析您的提示以创建详细的故事结构
- 将叙述分解为具有角色一致性的连贯场景
- 为每个场景生成优化的提示

### 2. 风格与LoRA选择
- 基于内容智能选择适当的LoRA模型
- 在所有场景中保持风格一致性
- 可选的手动LoRA选择以实现创意控制

### 3. 图像生成过程
- **种子管理**：使用一致的种子确保角色/风格连续性
- **提示工程**：使用风格触发器和质量标签增强提示
- **模型选择**：在Flux-Schnell、Illustrious-vPred或WAI模型之间自动选择
- **质量控制**：内置重试机制处理失败的生成

### 4. 后处理与组装
- 图像优化和增强
- 具有平滑过渡的视频转换
- 音频同步和最终组装

## 图像一致性解决方案

KGen采用多种技术来保持生成内容的视觉一致性：

### 当前实现
- **LoRA模型**：专业风格模型确保一致的艺术方向
- **种子一致性**：相同的种子值保持角色和风格的连贯性
- **提示工程**：精心制作的提示，具有一致的风格触发器
- **模型选择**：智能选择基础模型以获得最佳结果

### 高级一致性功能
- **角色持久性**：在场景中保持角色外观
- **风格连续性**：整个故事中一致的艺术风格
- **质量保证**：对不一致结果的自动重试

## 输出示例

每次生成都会创建一个带时间戳的目录，包含：
- 完整的生成记录
- 生成的图像
- 每个场景的视频片段
- 背景音频
- 最终合并的视频

## 下一阶段路线图

我们正在不断改进KGen，即将推出令人兴奋的新功能：

### 🎬 增强视频生成
- **可灵AI集成**：使用可灵先进AI模型的自动化视频生成
- **Google Veo 3支持**：下一代视频合成能力
- **多提供商管道**：视频生成服务之间的无缝切换

### 🎨 高级图像一致性
- **角色参考系统**：在所有场景中保持精确的角色外观
- **风格转换增强**：更复杂的风格一致性算法
- **跨场景连续性**：保持视觉连贯性的高级技术

### 🚀 性能与质量
- **优化生成管道**：在保持质量的同时更快的处理速度
- **增强模型支持**：集成最新的AI模型和技术
- **智能资源管理**：更好的GPU内存利用和批处理

*敬请期待这些令人兴奋的发展，它们将使KGen更加强大和用户友好！*

## 开发

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run python tests/video_tester.py

# 格式化代码
uv run black kgen/ tests/
uv run isort kgen/ tests/

# 检查和验证
uv run ruff check kgen/ tests/
uv run mypy kgen/
```

## 许可证

本项目采用MIT许可证 - 详情请参见[LICENSE](LICENSE)文件。

## 链接

- [ComfyUI设置指南](COMFYUI_SETUP.md)
- [GitHub仓库](https://github.com/username/kgen)
- [问题跟踪器](https://github.com/username/kgen/issues)