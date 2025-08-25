#!/usr/bin/env python3
"""
Web UI for YKGen - A FastAPI-based web interface for the YKGen content generation system.

This module provides a web interface that allows users to:
1. Select agent types (VideoAgent, PoetryAgent, PureImageAgent)
2. Configure generation parameters
3. Upload prompts and generate content
4. View and download generated results
"""

import os
import sys
import json
import asyncio
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ykgen.factories.agent_factory import AgentFactory
from ykgen.lora.lora_loader import load_lora_config
from ykgen.config.config import config
from ykgen.console import print_info, print_error
from langchain_core.messages import HumanMessage
from ykgen.cli.lora_selection import LoRASelectionHandler

# Pydantic models for API requests
class GenerationRequest(BaseModel):
    agent_type: str  # 'video_agent', 'poetry_agent', 'pure_image_agent', 'poetry_agent_pure_image'
    prompt: str
    lora_config: Dict[str, Any] = {}
    video_provider: str = "siliconflow"
    images_per_scene: int = 1
    enable_audio: bool = False
    language: str = "english"
    max_characters: int = 3
    max_scenes: int = 5
    lora_mode: str = "all"
    selected_loras: Optional[List[str]] = None
    required_loras: Optional[List[str]] = None  # For group mode
    optional_loras: Optional[List[str]] = None  # For group mode
    model_name: str = "WaiNSFW Illustrious"
    # Advanced configuration (optional, uses .env defaults if not provided)
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    comfyui_host: Optional[str] = None
    comfyui_port: Optional[int] = None

class GenerationStatus(BaseModel):
    task_id: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    progress: float = 0.0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Global storage for generation tasks
generation_tasks: Dict[str, GenerationStatus] = {}

# Progress tracking utilities
class ProgressTracker:
    """Tracks detailed progress for generation workflows."""
    
    def __init__(self, task_id: str, agent_type: str):
        self.task_id = task_id
        self.agent_type = agent_type
        self.current_step = 0
        self.total_steps = self._get_total_steps()
        
    def _get_total_steps(self) -> int:
        """Get total number of steps based on agent type."""
        if self.agent_type == "video_agent":
            return 8  # story, characters, scenes, prompts, images, videos, audio, wait
        elif self.agent_type in ["poetry_agent", "poetry_agent_pure_image"]:
            return 6  # story, characters, scenes, prompts, images, audio
        elif self.agent_type == "pure_image_agent":
            return 3  # prompt processing, image generation, finalization
        return 5  # default
    
    async def update_step(self, step_name: str, progress_percent: float, details: str = ""):
        """Update progress for a specific step."""
        self.current_step += 1
        message = f"📋 Step {self.current_step}/{self.total_steps}: {step_name}"
        if details:
            message += f" - {details}"
        await update_progress(self.task_id, progress_percent, message)
        
    async def complete_step(self, step_name: str, progress_percent: float, result_info: str = ""):
        """Mark a step as completed."""
        message = f"✅ {step_name} completed"
        if result_info:
            message += f" - {result_info}"
        await update_progress(self.task_id, progress_percent, message)

async def update_progress(task_id: str, progress: float, message: str):
    """Update progress for a generation task."""
    if task_id in generation_tasks:
        generation_tasks[task_id].progress = progress
        generation_tasks[task_id].message = message
        generation_tasks[task_id].updated_at = datetime.now()
        # Small delay to make progress visible
        await asyncio.sleep(0.1)

async def generate_with_progress(agent, prompt: str, tracker: ProgressTracker):
    """Generate content with detailed progress tracking."""
    # Step 1: Story Generation
    await tracker.update_step("Story Generation", 15.0, "Creating narrative from your prompt")
    
    # Create initial state
    from langchain_core.messages import HumanMessage
    from ykgen.model.models import VisionState
    
    initial_state = VisionState(prompt=HumanMessage(content=prompt))
    if hasattr(agent, 'style') and agent.style:
        initial_state["style"] = agent.style
    
    # Execute story generation (run in executor to avoid blocking)
    import asyncio
    loop = asyncio.get_event_loop()
    state = await loop.run_in_executor(None, agent.generate_story, initial_state)
    await tracker.complete_step("Story Generation", 25.0, "Narrative created successfully")
    
    if tracker.agent_type in ["poetry_agent", "video_agent", "poetry_agent_pure_image"]:
        # Step 2: Character Extraction
        await tracker.update_step("Character Extraction", 35.0, "Analyzing story for character details")
        state = await loop.run_in_executor(None, agent.generate_characters, state)
        char_count = len(state.get("characters_full", []))
        await tracker.complete_step("Character Extraction", 45.0, f"{char_count} characters identified")
        
        # Step 3: Scene Generation
        await tracker.update_step("Scene Generation", 55.0, "Breaking story into visual scenes")
        state = await loop.run_in_executor(None, agent.generate_scenes, state)
        scene_count = len(state.get("scenes", []))
        await tracker.complete_step("Scene Generation", 65.0, f"{scene_count} scenes created")
        
        # Step 4: Prompt Generation
        await tracker.update_step("Prompt Generation", 70.0, "Creating detailed image prompts")
        state = await loop.run_in_executor(None, agent.generate_prompts, state)
        await tracker.complete_step("Prompt Generation", 75.0, "Image prompts optimized")
        
        # Step 5: Image Generation
        await tracker.update_step("Image Generation", 80.0, "Generating images with ComfyUI")
        state = await loop.run_in_executor(None, agent.generate_images, state)
        await tracker.complete_step("Image Generation", 85.0, "Images generated successfully")
        
        if tracker.agent_type == "video_agent":
            # Step 6: Video Generation
            await tracker.update_step("Video Generation", 87.0, "Creating videos from images")
            state = await loop.run_in_executor(None, agent.generate_videos, state)
            await tracker.complete_step("Video Generation", 89.0, "Videos created")
            
            # Step 7: Audio Generation
            if hasattr(agent, 'enable_audio') and agent.enable_audio:
                await tracker.update_step("Audio Generation", 91.0, "Generating background audio")
                state = await loop.run_in_executor(None, agent.generate_audio, state)
                await tracker.complete_step("Audio Generation", 93.0, "Audio track created")
            
            # Step 8: Final Processing
            await tracker.update_step("Final Processing", 94.0, "Waiting for video completion")
            state = await loop.run_in_executor(None, agent.wait_for_videos, state)
        elif hasattr(agent, 'enable_audio') and agent.enable_audio:
            # Audio for poetry agents
            await tracker.update_step("Audio Generation", 87.0, "Generating background audio")
            state = await loop.run_in_executor(None, agent.generate_audio, state)
            await tracker.complete_step("Audio Generation", 90.0, "Audio track created")
    
    elif tracker.agent_type == "pure_image_agent":
        # Step 2: Image Processing
        await tracker.update_step("Image Processing", 50.0, "Processing image prompt")
        state = await loop.run_in_executor(None, agent.generate, prompt)
        await tracker.complete_step("Image Processing", 80.0, "Image generated successfully")
    
    return state

# Initialize FastAPI app
app = FastAPI(
    title="YKGen Web UI",
    description="Web interface for YKGen content generation system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directory if it doesn't exist
static_dir = Path("webui_static")
static_dir.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web UI page."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YKGen Web UI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        
        .form-section {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            border: 1px solid #e9ecef;
        }
        
        .form-section h3 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.3em;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        
        input, select, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        textarea {
            resize: vertical;
            min-height: 120px;
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .checkbox-group input[type="checkbox"] {
            width: auto;
        }
        
        .btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            width: 100%;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .progress-section {
            display: none;
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            margin-top: 20px;
            border: 1px solid #e9ecef;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 15px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(45deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s ease;
        }
        
        .status-message {
            color: #666;
            font-style: italic;
            margin-top: 10px;
        }
        
        .overall-progress {
            margin-bottom: 20px;
        }
        
        .overall-progress h4 {
            margin: 0 0 10px 0;
            color: #333;
            font-size: 16px;
        }
        
        .progress-percentage {
            text-align: center;
            font-weight: bold;
            color: #667eea;
            margin-top: 5px;
        }
        
        .step-status {
            background: #fff;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }
        
        .step-status h5 {
            margin: 0 0 8px 0;
            color: #333;
            font-size: 14px;
        }
        
        .step-details {
            color: #666;
            font-size: 13px;
            margin-top: 5px;
        }
        
        .step-timeline {
            background: #fff;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
        }
        
        .step-timeline h5 {
            margin: 0 0 15px 0;
            color: #333;
            font-size: 14px;
        }
        
        .timeline-step {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            padding: 8px;
            border-radius: 5px;
            transition: background-color 0.3s ease;
        }
        
        .timeline-step.completed {
            background: #d4edda;
            color: #155724;
        }
        
        .timeline-step.active {
            background: #cce7ff;
            color: #004085;
            font-weight: bold;
        }
        
        .timeline-step.pending {
            background: #f8f9fa;
            color: #6c757d;
        }
        
        .step-icon {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
        }
        
        .timeline-step.completed .step-icon {
            background: #28a745;
            color: white;
        }
        
        .timeline-step.active .step-icon {
            background: #007bff;
            color: white;
        }
        
        .timeline-step.pending .step-icon {
            background: #e9ecef;
            color: #6c757d;
        }
        
        .results-section {
            display: none;
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            margin-top: 20px;
            border: 1px solid #e9ecef;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        

        
        .lora-checkbox {
            margin: 5px 0;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: #f9f9f9;
        }
        
        .lora-checkbox input[type="checkbox"] {
            margin-right: 8px;
        }
        
        .lora-description {
            font-size: 12px;
            color: #666;
            margin-left: 20px;
        }
        
        .success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .agent-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            border: 2px solid #e9ecef;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .agent-card:hover {
            border-color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        
        .agent-card.selected {
            border-color: #667eea;
            background: #f0f4ff;
        }
        
        .agent-card h4 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .agent-card p {
            color: #666;
            font-size: 0.9em;
        }
        
        /* LoRA Models Styling */
        .lora-models-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 10px;
        }
        
        .lora-card {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 16px;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
        }
        
        .lora-card:hover {
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
            transform: translateY(-2px);
        }
        
        .lora-card.selected {
            border-color: #667eea;
            background: linear-gradient(135deg, #f0f4ff 0%, #e8f2ff 100%);
            box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
        }
        
        .lora-card input[type="checkbox"] {
            position: absolute;
            top: 12px;
            right: 12px;
            width: 20px;
            height: 20px;
            accent-color: #667eea;
        }
        
        .lora-card-content {
            margin-right: 30px;
        }
        
        .lora-name {
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            font-size: 1.1em;
        }
        
        .lora-description {
            color: #666;
            font-size: 0.9em;
            line-height: 1.4;
            margin-bottom: 6px;
        }
        
        .lora-trigger {
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.8em;
        }
        
        /* Enhanced button styles */
        .btn {
            border: none;
            cursor: pointer;
            font-family: inherit;
            text-decoration: none;
            display: inline-block;
            text-align: center;
            vertical-align: middle;
            user-select: none;
            transition: all 0.3s ease;
            font-weight: 500;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: 1px solid #667eea;
            box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
        }
        
        .btn-primary:hover {
            background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: linear-gradient(135deg, #6c757d 0%, #545b62 100%);
            color: white;
            border: 1px solid #6c757d;
            box-shadow: 0 2px 4px rgba(108, 117, 125, 0.2);
        }
        
        .btn-secondary:hover {
            background: linear-gradient(135deg, #545b62 0%, #383d41 100%);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(108, 117, 125, 0.4);
        }
        
        .btn-success {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            border: 1px solid #28a745;
            box-shadow: 0 2px 4px rgba(40, 167, 69, 0.2);
        }
        
        .btn-success:hover {
            background: linear-gradient(135deg, #218838 0%, #1abc9c 100%);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(40, 167, 69, 0.4);
        }
        
        .btn-outline-primary {
            background: transparent;
            color: #667eea;
            border: 2px solid #667eea;
            box-shadow: 0 2px 4px rgba(102, 126, 234, 0.1);
        }
        
        .btn-outline-primary:hover {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.3);
        }
        
        /* Step labels enhancement */
        .group-step-label {
            font-size: 1.2em;
            font-weight: 600;
            color: #495057;
            margin-bottom: 20px;
            padding: 15px 20px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 12px;
            border-left: 5px solid #667eea;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        
        /* Form control enhancements */
        .form-control, .form-select {
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 12px 16px;
            transition: all 0.3s ease;
            font-size: 14px;
        }
        
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            outline: none;
        }
        
        /* Card enhancements */
        .card {
            border: none;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }
        
        .card:hover {
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }
        
        /* Progress bar enhancements */
        .progress {
            height: 8px;
            border-radius: 4px;
            background: #e9ecef;
            overflow: hidden;
        }
        
        .progress-bar {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
        }
        
        /* Alert enhancements */
        .alert {
            border: none;
            border-radius: 8px;
            padding: 16px 20px;
        }
        
        .alert-info {
            background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
            color: #0c5460;
        }
        
        .alert-success {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            color: #155724;
        }
        
        .alert-danger {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            color: #721c24;
            font-family: monospace;
            display: inline-block;
            margin-top: 8px;
        }
        
        .loading-spinner {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px;
            color: #666;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 16px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .no-lora-message {
            text-align: center;
            padding: 40px;
            color: #666;
            font-style: italic;
        }
        
        /* Collapsible Advanced Configuration */
        .collapsible-header {
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #ddd;
            margin-bottom: 0;
            user-select: none;
        }
        
        .collapsible-header:hover {
            background-color: #f8f9fa;
            padding-left: 10px;
            padding-right: 10px;
            margin-left: -10px;
            margin-right: -10px;
            border-radius: 5px;
        }
        
        .toggle-icon {
            transition: transform 0.3s ease;
            font-size: 14px;
        }
        
        .toggle-icon.rotated {
            transform: rotate(180deg);
        }
        
        .collapsible-content {
            overflow: hidden;
            transition: max-height 0.3s ease;
        }
        
        .collapsible-content.expanded {
            max-height: 500px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>YKGen Web UI</h1>
            <p>Generate videos, images, and poetry with AI</p>
        </div>
        
        <form id="generationForm">
            <div class="form-section">
                <h3>Select Agent Type</h3>
                <div class="grid">
                    <div class="agent-card" data-agent="pure_image_agent">
                        <h4>Pure Image Agent</h4>
                        <p>Generate images only with customizable count per scene</p>
                    </div>
                    <div class="agent-card" data-agent="video_agent">
                        <h4>Video Agent</h4>
                        <p>Create complete video stories from text prompts</p>
                    </div>
                    <div class="agent-card" data-agent="poetry_agent">
                        <h4>Poetry Agent</h4>
                        <p>Transform Chinese poetry into visual experiences</p>
                    </div>
                    <div class="agent-card" data-agent="poetry_agent_pure_image">
                        <h4>Poetry Agent (Pure Image)</h4>
                        <p>Generate poetry images only, no videos</p>
                    </div>
                </div>
                <input type="hidden" id="agentType" name="agent_type" required>
            </div>
            
            <div class="form-section">
                <h3>Content Settings</h3>
                <div class="form-group">
                    <label for="prompt">Prompt:</label>
                    <textarea id="prompt" name="prompt" placeholder="Enter your creative prompt here..." required></textarea>
                </div>
                

                
                <div class="form-group">
                    <label for="model_name">Image Model:</label>
                    <select id="model_name" name="model_name" required>
                        <option value="WaiNSFW Illustrious">WaiNSFW Illustrious (Default)</option>
                        <option value="Flux Schnell">Flux Schnell</option>
                        <option value="Chinese style">Chinese Style</option>
                        <option value="illustrious-xl standard">Illustrious XL Standard</option>
                        <option value="Illustrious vPred">Illustrious vPred</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="imagesPerScene">Images per Scene:</label>
                    <select id="imagesPerScene" name="images_per_scene">
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                        <option value="4">4</option>
                        <option value="5">5</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="maxScenes">Max Scenes:</label>
                    <select id="maxScenes" name="max_scenes">
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                        <option value="4">4</option>
                        <option value="5" selected>5</option>
                        <option value="6">6</option>
                        <option value="7">7</option>
                        <option value="8">8</option>
                        <option value="9">9</option>
                        <option value="10">10</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="maxCharacters">Max Characters:</label>
                    <select id="maxCharacters" name="max_characters">
                        <option value="1">1</option>
                        <option value="2" selected>2</option>
                        <option value="3">3</option>
                        <option value="4">4</option>
                        <option value="5">5</option>
                        <option value="6">6</option>
                        <option value="7">7</option>
                        <option value="8">8</option>
                        <option value="9">9</option>
                        <option value="10">10</option>
                    </select>
                </div>
            </div>
            
            <div class="form-section">
                <h3>Audio Settings</h3>
                <div class="checkbox-group">
                    <input type="checkbox" id="enableAudio" name="enable_audio">
                    <label for="enableAudio">Enable Audio Generation</label>
                </div>
                
                <div class="form-group">
                    <label for="language">Audio Language:</label>
                    <select id="language" name="language">
                        <option value="english">English</option>
                        <option value="chinese">Chinese</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="lora_mode">LoRA Mode:</label>
                    <select id="lora_mode" name="lora_mode">
                        <option value="all">All (Apply to all scenes)</option>
                        <option value="group">Group (Required + Optional)</option>
                        <option value="none">None (No LoRA)</option>
                    </select>
                </div>
                
                <div class="form-group" id="lora_selection_group" style="display: block;">
                    <div id="lora_mode_all" style="display: block;">
                        <label for="lora_models">LoRA Models:</label>
                        <div id="lora_models_container" class="lora-models-grid">
                            <div class="loading-spinner">
                                <div class="spinner"></div>
                                <p>Loading LoRA models...</p>
                            </div>
                        </div>
                    </div>
                    
                    <div id="lora_mode_group" style="display: none;">
                        <div id="group_step_1" style="display: block;">
                            <label>Step 1: Select Required LoRAs (always used):</label>
                            <div id="required_loras_container" class="lora-models-grid">
                                <div class="loading-spinner">
                                    <div class="spinner"></div>
                                    <p>Loading LoRA models...</p>
                                </div>
                            </div>
                            <button type="button" id="next_to_optional" class="btn btn-primary" style="margin-top: 15px; display: none; padding: 10px 20px; border-radius: 8px; font-weight: 500; transition: all 0.3s ease;">Next: Select Optional LoRAs →</button>
                        </div>
                        
                        <div id="group_step_2" style="display: none;">
                            <label>Step 2: Select Optional LoRAs (LLM decides per image):</label>
                            <div id="optional_loras_container" class="lora-models-grid">
                                <div class="loading-spinner">
                                    <div class="spinner"></div>
                                    <p>Loading LoRA models...</p>
                                </div>
                            </div>
                            <div style="margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap;">
                                <button type="button" id="back_to_required" class="btn btn-secondary" style="padding: 10px 20px; border-radius: 8px; font-weight: 500; transition: all 0.3s ease;">← Back: Edit Required LoRAs</button>
                                <button type="button" id="finish_group_selection" class="btn btn-success" style="padding: 10px 20px; border-radius: 8px; font-weight: 500; transition: all 0.3s ease;">Finish Selection ✓</button>
                            </div>
                        </div>
                        
                        <div id="group_summary" style="display: none; margin-top: 20px; padding: 20px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; border: 1px solid #dee2e6; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <h4 style="margin: 0 0 15px 0; color: #495057; font-weight: 600;">📋 Group Mode Selection Summary</h4>
                            <div style="margin-bottom: 12px; padding: 8px 12px; background: white; border-radius: 6px; border-left: 4px solid #007bff;">
                                <strong style="color: #007bff;">Required LoRAs:</strong> 
                                <span id="required_summary" style="color: #6c757d; margin-left: 8px;">None</span>
                            </div>
                            <div style="margin-bottom: 15px; padding: 8px 12px; background: white; border-radius: 6px; border-left: 4px solid #28a745;">
                                <strong style="color: #28a745;">Optional LoRAs:</strong> 
                                <span id="optional_summary" style="color: #6c757d; margin-left: 8px;">None</span>
                            </div>
                            <button type="button" id="edit_group_selection" class="btn btn-outline-primary" style="padding: 8px 16px; border-radius: 6px; font-weight: 500; transition: all 0.3s ease;">✏️ Edit Selection</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="form-section">
                <h3 class="collapsible-header" onclick="toggleAdvancedConfig()">
                    <span>Advanced Configuration</span>
                    <span class="toggle-icon">▼</span>
                </h3>
                <div class="collapsible-content" id="advancedConfig" style="display: none;">
                    <div class="form-group">
                        <label for="llmApiKey">LLM API Key:</label>
                        <input type="password" id="llmApiKey" name="llm_api_key" placeholder="Leave empty to use .env default">
                    </div>
                    
                    <div class="form-group">
                        <label for="llmBaseUrl">LLM Base URL:</label>
                        <input type="text" id="llmBaseUrl" name="llm_base_url" placeholder="Leave empty to use .env default">
                    </div>
                    
                    <div class="form-group">
                        <label for="comfyuiHost">ComfyUI Host:</label>
                        <input type="text" id="comfyuiHost" name="comfyui_host" placeholder="Leave empty to use .env default (127.0.0.1)">
                    </div>
                    
                    <div class="form-group">
                        <label for="comfyuiPort">ComfyUI Port:</label>
                        <input type="number" id="comfyuiPort" name="comfyui_port" placeholder="Leave empty to use .env default (8188)">
                    </div>
                </div>
            </div>
            
            <button type="submit" class="btn" id="generateBtn">Generate Content</button>
        </form>
        
        <div class="progress-section" id="progressSection">
            <h3>🎯 Generation Progress</h3>
            
            <!-- Overall Progress -->
            <div class="overall-progress">
                <h4>Overall Progress</h4>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="progress-percentage" id="progressPercentage">0%</div>
            </div>
            
            <!-- Current Step Status -->
            <div class="step-status">
                <h5>Current Step</h5>
                <div id="currentStepName">Initializing</div>
                <div class="step-details" id="currentStepDetails">🚀 Preparing generation...</div>
            </div>
            
            <!-- Step Timeline -->
            <div class="step-timeline">
                <h5>Workflow Steps</h5>
                <div class="timeline-step pending" id="timeline-step-0">
                    <div class="step-icon">1</div>
                    <div>Story Generation</div>
                </div>
                <div class="timeline-step pending" id="timeline-step-1">
                    <div class="step-icon">2</div>
                    <div>Character Extraction</div>
                </div>
                <div class="timeline-step pending" id="timeline-step-2">
                    <div class="step-icon">3</div>
                    <div>Scene Generation</div>
                </div>
                <div class="timeline-step pending" id="timeline-step-3">
                    <div class="step-icon">4</div>
                    <div>Image Generation</div>
                </div>
                <div class="timeline-step pending" id="timeline-step-4">
                    <div class="step-icon">5</div>
                    <div>Video Generation</div>
                </div>
                <div class="timeline-step pending" id="timeline-step-5">
                    <div class="step-icon">6</div>
                    <div>Audio Generation</div>
                </div>
            </div>
            
            <div class="status-message" id="statusMessage">🚀 Initializing...</div>
        </div>
        
        <div class="results-section" id="resultsSection">
            <h3>Results</h3>
            <div id="resultsContent"></div>
        </div>
    </div>
    
    <script>
        let currentTaskId = null;
        let pollInterval = null;
        
        // Load configurations on page load
         document.addEventListener('DOMContentLoaded', function() {
             loadLoRAConfigs();
             loadModels();
             // Load LoRA models initially if not in 'none' mode
             const initialLoRAMode = document.getElementById('lora_mode').value;
             if (initialLoRAMode !== 'none') {
                 document.getElementById('lora_selection_group').style.display = 'block';
                 loadLoRAModels();
             }
         });
         
         // Handle LoRA mode changes
         document.getElementById('lora_mode').addEventListener('change', function() {
             const mode = this.value;
             const selectionGroup = document.getElementById('lora_selection_group');
             const allModeDiv = document.getElementById('lora_mode_all');
             const groupModeDiv = document.getElementById('lora_mode_group');
             
             if (mode === 'none') {
                 selectionGroup.style.display = 'none';
             } else {
                 selectionGroup.style.display = 'block';
                 
                 if (mode === 'group') {
                     allModeDiv.style.display = 'none';
                     groupModeDiv.style.display = 'block';
                     // Reset group mode to step 1
                     showGroupStep(1);
                 } else {
                     allModeDiv.style.display = 'block';
                     groupModeDiv.style.display = 'none';
                 }
                 
                 loadLoRAModels();
             }
         });
         
         // Group mode navigation functions
         function showGroupStep(step) {
             const step1 = document.getElementById('group_step_1');
             const step2 = document.getElementById('group_step_2');
             const summary = document.getElementById('group_summary');
             
             if (step === 1) {
                 step1.style.display = 'block';
                 step2.style.display = 'none';
                 summary.style.display = 'none';
             } else if (step === 2) {
                 step1.style.display = 'none';
                 step2.style.display = 'block';
                 summary.style.display = 'none';
             } else if (step === 'summary') {
                 step1.style.display = 'none';
                 step2.style.display = 'none';
                 summary.style.display = 'block';
                 updateGroupSummary();
             }
         }
         
         // Group mode button event handlers
         document.addEventListener('DOMContentLoaded', function() {
             // Next to optional button
             document.getElementById('next_to_optional').addEventListener('click', function() {
                 showGroupStep(2);
             });
             
             // Back to required button
             document.getElementById('back_to_required').addEventListener('click', function() {
                 showGroupStep(1);
             });
             
             // Finish group selection button
             document.getElementById('finish_group_selection').addEventListener('click', function() {
                 showGroupStep('summary');
             });
             
             // Edit group selection button
             document.getElementById('edit_group_selection').addEventListener('click', function() {
                 showGroupStep(1);
             });
         });
         
         // Handle model changes - reload LoRA models when model changes
         document.getElementById('model_name').addEventListener('change', function() {
             const loraMode = document.getElementById('lora_mode').value;
             if (loraMode !== 'none') {
                 loadLoRAModels();
             }
         });
         
         // Load available models
         async function loadModels() {
             try {
                 const response = await fetch('/api/models');
                 const data = await response.json();
                 
                 const modelSelect = document.getElementById('model_name');
                 modelSelect.innerHTML = '';
                 
                 data.models.forEach(model => {
                     const option = document.createElement('option');
                     option.value = model.id;
                     option.textContent = model.name;
                     option.title = model.description;
                     if (model.id === 'WaiNSFW Illustrious') {
                         option.selected = true;
                     }
                     modelSelect.appendChild(option);
                 });
             } catch (error) {
                 console.error('Failed to load models:', error);
             }
         }
        
        async function loadLoRAConfigs() {
            try {
                const response = await fetch('/api/lora/configs');
                if (response.ok) {
                    const configs = await response.json();
                    // Store configs for later use
                    window.loraConfigs = configs;
                }
            } catch (error) {
                console.error('Failed to load LoRA configs:', error);
            }
        }
        
        async function loadLoRAModels() {
            const loraMode = document.getElementById('lora_mode').value;
            const modelName = document.getElementById('model_name').value;
            
            if (loraMode === 'group') {
                // Load models for group mode
                await loadLoRAModelsForGroup();
            } else {
                // Load models for all mode
                const container = document.getElementById('lora_models_container');
                try {
                    const response = await fetch(`/api/lora/models?model_name=${encodeURIComponent(modelName)}`);
                    if (response.ok) {
                        const models = await response.json();
                        displayLoRAModels(models, container);
                    } else {
                        container.innerHTML = '<p>Failed to load LoRA models</p>';
                    }
                } catch (error) {
                    container.innerHTML = '<p>Error loading LoRA models</p>';
                    console.error('Failed to load LoRA models:', error);
                }
            }
        }
        
        async function loadLoRAModelsForGroup() {
            const modelName = document.getElementById('model_name').value;
            
            try {
                const response = await fetch(`/api/lora/models?model_name=${encodeURIComponent(modelName)}`);
                if (response.ok) {
                    const models = await response.json();
                    // Load models into both required and optional containers
                    const requiredContainer = document.getElementById('required_loras_container');
                    const optionalContainer = document.getElementById('optional_loras_container');
                    
                    displayLoRAModels(models, requiredContainer, 'required');
                    displayLoRAModels(models, optionalContainer, 'optional');
                } else {
                    document.getElementById('required_loras_container').innerHTML = '<p>Failed to load LoRA models</p>';
                    document.getElementById('optional_loras_container').innerHTML = '<p>Failed to load LoRA models</p>';
                }
            } catch (error) {
                document.getElementById('required_loras_container').innerHTML = '<p>Error loading LoRA models</p>';
                document.getElementById('optional_loras_container').innerHTML = '<p>Error loading LoRA models</p>';
                console.error('Failed to load LoRA models:', error);
            }
        }
        
        function displayLoRAModels(models, container, mode = 'all') {
            let html = '';
            
            const modelEntries = Object.entries(models).filter(([key]) => key !== '1');
            
            if (modelEntries.length === 0) {
                container.innerHTML = '<div class="no-lora-message">No LoRA models available for this agent type</div>';
                return;
            }
            
            const namePrefix = mode === 'all' ? 'lora_models' : `${mode}_loras`;
            
            for (const [key, model] of modelEntries) {
                html += `
                    <div class="lora-card" data-lora-id="${key}" data-mode="${mode}">
                        <input type="checkbox" id="${mode}_lora_${key}" name="${namePrefix}" value="${key}">
                        <div class="lora-card-content">
                            <div class="lora-name">${model.name}</div>
                            <div class="lora-description">${model.description}</div>
                            ${model.display_trigger ? `<div class="lora-trigger">Trigger: ${model.display_trigger}</div>` : ''}
                        </div>
                    </div>
                `;
            }
            
            container.innerHTML = html;
            
            // Add click handlers for cards
            container.querySelectorAll('.lora-card').forEach(card => {
                card.addEventListener('click', function(e) {
                    if (e.target.type !== 'checkbox') {
                        const checkbox = this.querySelector('input[type="checkbox"]');
                        checkbox.checked = !checkbox.checked;
                        checkbox.dispatchEvent(new Event('change'));
                    }
                });
            });
            
            // Add change handlers for checkboxes to update card appearance
            container.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    const card = this.closest('.lora-card');
                    if (this.checked) {
                        card.classList.add('selected');
                    } else {
                        card.classList.remove('selected');
                    }
                    
                    // Handle group mode logic
                    if (mode === 'required') {
                        updateRequiredLoRAButtons();
                    }
                });
            });
        }
        
        function getSelectedLoRAs() {
            const loraMode = document.getElementById('lora_mode').value;
            console.log('getSelectedLoRAs called with mode:', loraMode);
            
            if (loraMode === 'group') {
                const required = getSelectedLoRAsByType('required');
                const optional = getSelectedLoRAsByType('optional');
                console.log('Group mode - required checkboxes found:', required);
                console.log('Group mode - optional checkboxes found:', optional);
                return {
                    required_loras: required,
                    optional_loras: optional
                };
            } else {
                const checkboxes = document.querySelectorAll('input[name="lora_models"]:checked');
                const selected = Array.from(checkboxes).map(cb => cb.value);
                console.log('Non-group mode - selected:', selected);
                return selected;
            }
        }
        
        function getSelectedLoRAsByType(type) {
            const selector = `input[name="${type}_loras"]:checked`;
            console.log('getSelectedLoRAsByType selector:', selector);
            const checkboxes = document.querySelectorAll(selector);
            console.log('Found checkboxes for', type, ':', checkboxes.length);
            const values = Array.from(checkboxes).map(cb => cb.value);
            console.log('Values for', type, ':', values);
            return values;
        }
        
        function updateRequiredLoRAButtons() {
            const selectedRequired = getSelectedLoRAsByType('required');
            const nextButton = document.getElementById('next_to_optional');
            
            if (selectedRequired.length > 0) {
                nextButton.style.display = 'inline-block';
            } else {
                nextButton.style.display = 'none';
            }
        }
        
        function updateGroupSummary() {
            const requiredLoras = getSelectedLoRAsByType('required');
            const optionalLoras = getSelectedLoRAsByType('optional');
            
            document.getElementById('required_summary').textContent = 
                requiredLoras.length > 0 ? requiredLoras.join(', ') : 'None';
            document.getElementById('optional_summary').textContent = 
                optionalLoras.length > 0 ? optionalLoras.join(', ') : 'None';
        }
        
        // Agent selection
        document.querySelectorAll('.agent-card').forEach(card => {
            card.addEventListener('click', () => {
                document.querySelectorAll('.agent-card').forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
                document.getElementById('agentType').value = card.dataset.agent;
                
                // Reload LoRA models when agent type changes
                const loraMode = document.getElementById('lora_mode').value;
                if (loraMode !== 'none') {
                    loadLoRAModels();
                }
            });
        });
        
        // Form submission
        document.getElementById('generationForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const loraMode = formData.get('lora_mode');
            const selectedLoras = getSelectedLoRAs();
            
            const data = {
                agent_type: formData.get('agent_type'),
                prompt: formData.get('prompt'),
                images_per_scene: parseInt(formData.get('images_per_scene')),
                enable_audio: formData.has('enable_audio'),
                language: formData.get('language'),
                video_provider: 'siliconflow',
                lora_config: {},
                lora_mode: loraMode,
                model_name: formData.get('model_name'),
                max_scenes: parseInt(formData.get('max_scenes')),
                max_characters: parseInt(formData.get('max_characters')),
                llm_api_key: formData.get('llm_api_key') || null,
                llm_base_url: formData.get('llm_base_url') || null,
                comfyui_host: formData.get('comfyui_host') || null,
                comfyui_port: formData.get('comfyui_port') ? parseInt(formData.get('comfyui_port')) : null
            };
            
            // Handle LoRA selection based on mode
            console.log('LoRA Mode:', loraMode);
            console.log('Selected LoRAs:', selectedLoras);
            
            if (loraMode === 'group') {
                data.required_loras = selectedLoras.required_loras;
                data.optional_loras = selectedLoras.optional_loras;
                data.selected_loras = null;
                console.log('Group mode - Required:', data.required_loras);
                console.log('Group mode - Optional:', data.optional_loras);
            } else {
                data.selected_loras = selectedLoras;
                data.required_loras = null;
                data.optional_loras = null;
                console.log('Non-group mode - Selected:', data.selected_loras);
            }
            
            console.log('Final request data:', data);
            
            if (!data.agent_type) {
                alert('Please select an agent type');
                return;
            }
            
            try {
                document.getElementById('generateBtn').disabled = true;
                document.getElementById('progressSection').style.display = 'block';
                document.getElementById('resultsSection').style.display = 'none';
                
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    currentTaskId = result.task_id;
                    startPolling();
                } else {
                    showError(result.detail || 'Generation failed');
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            }
        });
        
        function startPolling() {
            pollInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/api/status/${currentTaskId}`);
                    const status = await response.json();
                    
                    updateProgress(status);
                    
                    if (status.status === 'completed') {
                        clearInterval(pollInterval);
                        showResults(status.result);
                        document.getElementById('generateBtn').disabled = false;
                    } else if (status.status === 'failed') {
                        clearInterval(pollInterval);
                        showError(status.error || 'Generation failed');
                        document.getElementById('generateBtn').disabled = false;
                    }
                } catch (error) {
                    console.error('Polling error:', error);
                }
            }, 2000);
        }
        
        function updateProgress(status) {
            const progressFill = document.getElementById('progressFill');
            const statusMessage = document.getElementById('statusMessage');
            const progressPercentage = document.getElementById('progressPercentage');
            const currentStepName = document.getElementById('currentStepName');
            const currentStepDetails = document.getElementById('currentStepDetails');
            
            // Update overall progress
            progressFill.style.width = `${status.progress}%`;
            progressPercentage.textContent = `${Math.round(status.progress)}%`;
            statusMessage.textContent = status.message;
            
            // Parse step information from message
            const stepInfo = parseStepInfo(status.message);
            if (stepInfo) {
                currentStepName.textContent = stepInfo.name;
                currentStepDetails.textContent = stepInfo.details;
                updateTimeline(stepInfo.name, stepInfo.status);
            }
        }
        
        function parseStepInfo(message) {
            // Extract step information from progress messages
            if (message.includes('Story generation')) {
                return { name: 'Story Generation', details: message, status: message.includes('completed') ? 'completed' : 'active' };
            } else if (message.includes('Character')) {
                return { name: 'Character Extraction', details: message, status: message.includes('completed') ? 'completed' : 'active' };
            } else if (message.includes('Scene')) {
                return { name: 'Scene Generation', details: message, status: message.includes('completed') ? 'completed' : 'active' };
            } else if (message.includes('Image')) {
                return { name: 'Image Generation', details: message, status: message.includes('completed') ? 'completed' : 'active' };
            } else if (message.includes('Video')) {
                return { name: 'Video Generation', details: message, status: message.includes('completed') ? 'completed' : 'active' };
            } else if (message.includes('Audio')) {
                return { name: 'Audio Generation', details: message, status: message.includes('completed') ? 'completed' : 'active' };
            }
            return { name: 'Processing', details: message, status: 'active' };
        }
        
        function updateTimeline(currentStep, status) {
            const steps = ['Story Generation', 'Character Extraction', 'Scene Generation', 'Image Generation', 'Video Generation', 'Audio Generation'];
            
            steps.forEach((step, index) => {
                const stepElement = document.getElementById(`timeline-step-${index}`);
                if (stepElement) {
                    stepElement.className = 'timeline-step';
                    const icon = stepElement.querySelector('.step-icon');
                    
                    if (step === currentStep) {
                        stepElement.classList.add(status === 'completed' ? 'completed' : 'active');
                        icon.textContent = status === 'completed' ? '✓' : (index + 1);
                    } else if (steps.indexOf(currentStep) > index) {
                        stepElement.classList.add('completed');
                        icon.textContent = '✓';
                    } else {
                        stepElement.classList.add('pending');
                        icon.textContent = index + 1;
                    }
                }
            });
        }
        

        
        function showResults(result) {
            const resultsSection = document.getElementById('resultsSection');
            const resultsContent = document.getElementById('resultsContent');
            
            let html = '<div class="success">Generation completed successfully!</div>';
            
            if (result.output_dir) {
                html += `<p><strong>Output Directory:</strong> ${result.output_dir}</p>`;
            }
            
            if (result.files && result.files.length > 0) {
                html += '<h4>Generated Files:</h4><ul>';
                result.files.forEach(file => {
                    html += `<li><a href="/api/download/${encodeURIComponent(file)}" target="_blank">${file}</a></li>`;
                });
                html += '</ul>';
            }
            
            resultsContent.innerHTML = html;
            resultsSection.style.display = 'block';
            document.getElementById('progressSection').style.display = 'none';
        }
        
        function showError(message) {
            const resultsSection = document.getElementById('resultsSection');
            const resultsContent = document.getElementById('resultsContent');
            
            resultsContent.innerHTML = `<div class="error">Error: ${message}</div>`;
            resultsSection.style.display = 'block';
            document.getElementById('progressSection').style.display = 'none';
            document.getElementById('generateBtn').disabled = false;
        }
        
        function toggleAdvancedConfig() {
            const content = document.getElementById('advancedConfig');
            const icon = document.querySelector('.toggle-icon');
            
            if (content.style.display === 'none' || content.style.display === '') {
                content.style.display = 'block';
                icon.classList.add('rotated');
                icon.textContent = '▲';
            } else {
                content.style.display = 'none';
                icon.classList.remove('rotated');
                icon.textContent = '▼';
            }
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/config")
async def get_config():
    """Get available configuration options."""
    try:
        lora_config = load_lora_config()
        return {
            "lora_models": lora_config,
            "max_scenes": config.MAX_SCENES,
            "max_characters": config.MAX_CHARACTERS,
            "available_agents": [
                "pure_image_agent",
                "video_agent", 
                "poetry_agent",
                "poetry_agent_pure_image"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
async def generate_content(request: GenerationRequest, background_tasks: BackgroundTasks):
    """Start content generation in the background."""
    task_id = str(uuid.uuid4())
    
    # Create task status
    generation_tasks[task_id] = GenerationStatus(
        task_id=task_id,
        status="pending",
        progress=0.0,
        message="Initializing generation...",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Start background task
    background_tasks.add_task(run_generation, task_id, request)
    
    return {"task_id": task_id, "status": "started"}

@app.get("/api/status/{task_id}")
async def get_generation_status(task_id: str):
    """Get the status of a generation task."""
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return generation_tasks[task_id]

@app.get("/api/lora/configs")
async def get_lora_configs():
    """Get available LoRA configurations."""
    try:
        config_path = get_lora_config_path()
        with open(config_path, 'r') as f:
            lora_configs = json.load(f)
        return lora_configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load LoRA configs: {str(e)}")

@app.get("/api/lora/models")
async def get_lora_models(model_name: str = "WaiNSFW Illustrious"):
    """Get available LoRA models for a specific model."""
    try:
        # Load image model config to get lora_config_key for the selected model
        image_config_path = os.path.join(os.path.dirname(__file__), "image_model_config.json")
        with open(image_config_path, 'r') as f:
            image_configs = json.load(f)
        
        # Find the lora_config_key for the selected model
        lora_config_key = None
        for config_type in image_configs.values():
            for model in config_type.get("models", []):
                if model["name"] == model_name:
                    lora_config_key = model.get("lora_config_key")
                    break
            if lora_config_key:
                break
        
        if not lora_config_key:
            # Fallback to flux-schnell if model not found
            lora_config_key = "flux-schnell"
        
        # Load LoRA configs
        config_path = get_lora_config_path()
        with open(config_path, 'r') as f:
            lora_configs = json.load(f)
        
        # Return LoRAs for the determined config key
        if lora_config_key not in lora_configs:
            return {}
        
        return lora_configs[lora_config_key]["loras"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load LoRA models: {str(e)}")

@app.get("/api/models")
async def get_available_models():
    """Get available image generation models."""
    try:
        models = [
            {"id": "WaiNSFW Illustrious", "name": "WaiNSFW Illustrious (Default)", "description": "High-quality anime-style image generation"},
            {"id": "Flux Schnell", "name": "Flux Schnell", "description": "Fast and efficient image generation"},
            {"id": "Chinese style", "name": "Chinese Style", "description": "Traditional Chinese art style"},
            {"id": "illustrious-xl standard", "name": "Illustrious XL Standard", "description": "High-resolution standard model"},
            {"id": "Illustrious vPred", "name": "Illustrious vPred", "description": "Advanced prediction model"}
        ]
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load models: {str(e)}")

# WebSocket functionality removed for simplified UI

@app.get("/api/download/{file_path:path}")
async def download_file(file_path: str):
    """Download a generated file."""
    # Security: Only allow downloads from the output directory
    output_dir = Path(config.DEFAULT_OUTPUT_DIR)
    full_path = output_dir / file_path
    
    # Ensure the path is within the output directory
    try:
        full_path = full_path.resolve()
        output_dir = output_dir.resolve()
        if not str(full_path).startswith(str(output_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(str(full_path))

async def run_generation(task_id: str, request: GenerationRequest):
    """Run the generation process in the background."""
    try:
        # Update status
        generation_tasks[task_id].status = "running"
        generation_tasks[task_id].progress = 5.0
        generation_tasks[task_id].message = "Initializing system..."
        generation_tasks[task_id].updated_at = datetime.now()
        
        # Process LoRA configuration
        lora_config = None
        # Check if we should process LoRA config based on mode and available selections
        should_process_lora = (
            request.lora_mode != "none" and (
                request.selected_loras or  # For 'all' mode
                (request.lora_mode == "group" and (request.required_loras or request.optional_loras))  # For 'group' mode
            )
        )
        
        if should_process_lora:
            generation_tasks[task_id].progress = 10.0
            generation_tasks[task_id].message = "Configuring LoRA models..."
            generation_tasks[task_id].updated_at = datetime.now()
            lora_config = await process_lora_config(request, task_id)
        
        # Ensure lora_config has model_type for agent compatibility
        if not lora_config:
            # Import the proper function to get LoRA key for model
            from ykgen.lora.lora_loader import get_lora_key_for_model_type
            
            # Use the selected model name to get the correct LoRA config key
            model_type = get_lora_key_for_model_type(request.model_name)
            
            # Generate a consistent seed based on the prompt for webui mode (no LoRA case)
            import hashlib
            prompt_key = f"webui_{request.prompt.lower()}"
            hash_object = hashlib.md5(prompt_key.encode())
            hash_hex = hash_object.hexdigest()
            webui_seed = int(hash_hex[:8], 16) % 2147483647 + 1
            
            lora_config = {
                "name": "No LoRA",
                "file": None,
                "trigger": "",
                "model_type": model_type,
                "seed": webui_seed  # Add seed for no LoRA case
            }
        
        # Set environment variables for MAX_CHARACTERS and MAX_SCENES
        os.environ["MAX_CHARACTERS"] = str(request.max_characters)
        os.environ["MAX_SCENES"] = str(request.max_scenes)
        
        # Set advanced configuration environment variables if provided
        if request.llm_api_key:
            os.environ["LLM_API_KEY"] = request.llm_api_key
        if request.llm_base_url:
            os.environ["LLM_BASE_URL"] = request.llm_base_url
        if request.comfyui_host:
            os.environ["COMFYUI_HOST"] = request.comfyui_host
        if request.comfyui_port:
            os.environ["COMFYUI_PORT"] = str(request.comfyui_port)
        
        # Clear cached properties if they exist
        if hasattr(config, '_max_characters'):
            delattr(config, '_max_characters')
        if hasattr(config, '_max_scenes'):
            delattr(config, '_max_scenes')
        if hasattr(config, '_llm_api_key'):
            delattr(config, '_llm_api_key')
        if hasattr(config, '_llm_base_url'):
            delattr(config, '_llm_base_url')
        if hasattr(config, '_comfyui_host'):
            delattr(config, '_comfyui_host')
        if hasattr(config, '_comfyui_port'):
            delattr(config, '_comfyui_port')
        
        generation_tasks[task_id].progress = 15.0
        generation_tasks[task_id].message = "Setting up generation environment..."
        generation_tasks[task_id].updated_at = datetime.now()
        
        # Set model environment variable
        os.environ["SELECTED_MODEL"] = request.model_name
        
        # Create agent
        generation_tasks[task_id].progress = 20.0
        generation_tasks[task_id].message = "Creating agent..."
        generation_tasks[task_id].updated_at = datetime.now()
        
        agent = AgentFactory.create_agent(
            agent_type=request.agent_type,
            lora_config=lora_config,
            video_provider=request.video_provider,
            images_per_scene=request.images_per_scene,
            enable_audio=request.enable_audio,
            language=request.language
        )
        
        # Configure LoRA mode if needed
        if lora_config:
            AgentFactory.configure_lora_mode(agent, lora_config)
        
        # Start detailed progress tracking
        await update_progress(task_id, 10.0, "🚀 Initializing generation workflow...")
        
        # Create progress tracker for this generation
        progress_tracker = ProgressTracker(task_id, request.agent_type)
        
        # Generate content using string prompt with progress tracking
        result = await generate_with_progress(agent, request.prompt, progress_tracker)
        
        # Mark workflow completion
        await update_progress(task_id, 95.0, "✅ Generation workflow completed successfully!")
        
        # Final processing
        generation_tasks[task_id].progress = 90.0
        generation_tasks[task_id].message = "Processing final output..."
        generation_tasks[task_id].updated_at = datetime.now()
        
        # Process results
        output_files = []
        output_dir = None
        
        if hasattr(result, 'get') and 'output_dir' in result:
            output_dir = result['output_dir']
            # List files in output directory
            if output_dir and os.path.exists(output_dir):
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        rel_path = os.path.relpath(os.path.join(root, file), config.DEFAULT_OUTPUT_DIR)
                        output_files.append(rel_path)
                # Files generated successfully
        
        # Complete task
        generation_tasks[task_id].status = "completed"
        generation_tasks[task_id].progress = 100.0
        generation_tasks[task_id].message = "Complete!"
        generation_tasks[task_id].result = {
            "output_dir": output_dir,
            "files": output_files,
            "agent_type": request.agent_type
        }
        generation_tasks[task_id].updated_at = datetime.now()
        
    except Exception as e:
        # Handle errors
        generation_tasks[task_id].status = "failed"
        generation_tasks[task_id].error = str(e)
        generation_tasks[task_id].message = f"Failed: {str(e)}"
        generation_tasks[task_id].updated_at = datetime.now()
        print_error(f"Generation failed for task {task_id}: {str(e)}")


def get_lora_config_path() -> str:
    """Get the path to the LoRA configuration file."""
    return os.path.join(os.path.dirname(__file__), "lora_config.json")


def get_lora_key_for_model_type(model_type: str) -> str:
    """Get the LoRA configuration key for a given model type."""
    # Map model types to LoRA config keys
    model_mapping = {
        "flux-schnell": "flux_schnell_loras",
        "flux-dev": "flux_dev_loras",
        "sd15": "sd15_loras",
        "sdxl": "sdxl_loras"
    }
    return model_mapping.get(model_type, "flux_schnell_loras")


async def process_lora_config(request: GenerationRequest, task_id: str) -> Optional[Dict[str, Any]]:
    """Process LoRA configuration based on user selection."""
    try:
        # Debug logging
        print_info(f"Processing LoRA config for mode: {request.lora_mode}")
        if request.lora_mode == "group":
            print_info(f"Required LoRAs: {request.required_loras}")
            print_info(f"Optional LoRAs: {request.optional_loras}")
        else:
            print_info(f"Selected LoRAs: {request.selected_loras}")
        
        # Check if we have any LoRA selection based on mode
        if request.lora_mode == "group":
            if not request.required_loras and not request.optional_loras:
                print_info("No LoRAs selected for group mode, returning None")
                return None
        else:
            if not request.selected_loras:
                print_info("No LoRAs selected for non-group mode, returning None")
                return None
        
        # Load LoRA configurations
        config_path = get_lora_config_path()
        with open(config_path, 'r') as f:
            lora_configs = json.load(f)
        
        # Import the proper function to get LoRA key for model
        from ykgen.lora.lora_loader import get_lora_key_for_model_type
        
        # Use the selected model name to get the correct LoRA config key
        model_type = get_lora_key_for_model_type(request.model_name)
        
        if model_type not in lora_configs:
            print_error(f"LoRA config for model type '{model_type}' not found")
            return None
        
        available_loras = lora_configs[model_type]["loras"]
        selected_lora_configs = []
        
        # Build selected LoRA configurations based on mode
        if request.lora_mode == "group":
            # For group mode, combine required and optional LoRAs
            all_selected = []
            if request.required_loras:
                all_selected.extend(request.required_loras)
            if request.optional_loras:
                all_selected.extend(request.optional_loras)
        else:
            # For non-group mode, use selected_loras
            all_selected = request.selected_loras or []
        
        for lora_id in all_selected:
            if lora_id in available_loras:
                lora_config = available_loras[lora_id]
                selected_lora_configs.append({
                    "name": lora_config["name"],
                    "file": lora_config["file"],
                    "trigger": lora_config.get("display_trigger", ""),
                    "description": lora_config["description"],
                    "strength_model": lora_config.get("strength_model", 1.0),
                    "strength_clip": lora_config.get("strength_clip", 1.0),
                    "trigger_words": lora_config.get("trigger_words", {}),
                    "essential_traits": lora_config.get("essential_traits", [])
                })
                # LoRA selected successfully
        
        if not selected_lora_configs:
            return None
        
        # Generate a consistent seed based on the prompt for webui mode
        # This ensures different prompts get different seeds but same prompt gets same seed
        import hashlib
        prompt_key = f"webui_{request.prompt.lower()}"
        hash_object = hashlib.md5(prompt_key.encode())
        hash_hex = hash_object.hexdigest()
        webui_seed = int(hash_hex[:8], 16) % 2147483647 + 1
        
        # Create LoRA configuration based on mode
        if request.lora_mode == "all":
            if len(selected_lora_configs) == 1:
                config_result = selected_lora_configs[0]
                config_result["seed"] = webui_seed  # Add seed to single LoRA config
                return config_result
            else:
                # Multiple LoRAs for "all" mode
                combined_name = " + ".join([lora["name"] for lora in selected_lora_configs])
                combined_trigger = ", ".join([lora["trigger"] for lora in selected_lora_configs if lora["trigger"]])
                
                return {
                    "name": combined_name,
                    "file": None,
                    "trigger": combined_trigger,
                    "model_type": model_type,
                    "loras": selected_lora_configs,
                    "is_multiple": True,
                    "seed": webui_seed  # Add seed to multiple LoRA config
                }
        elif request.lora_mode == "group":
            # For group mode, handle required and optional LoRAs separately
            print_info("Processing group mode LoRA configuration")
            required_lora_configs = []
            optional_lora_configs = []
            
            # Process required LoRAs
            if request.required_loras:
                for lora_id in request.required_loras:
                    if lora_id in available_loras:
                        lora_config = available_loras[lora_id]
                        required_lora_configs.append({
                            "name": lora_config["name"],
                            "file": lora_config["file"],
                            "trigger": lora_config.get("display_trigger", ""),
                            "description": lora_config["description"],
                            "strength_model": lora_config.get("strength_model", 1.0),
                            "strength_clip": lora_config.get("strength_clip", 1.0),
                            "trigger_words": lora_config.get("trigger_words", {}),
                            "essential_traits": lora_config.get("essential_traits", [])
                        })
            
            # Process optional LoRAs
            if request.optional_loras:
                for lora_id in request.optional_loras:
                    if lora_id in available_loras:
                        lora_config = available_loras[lora_id]
                        optional_lora_configs.append({
                            "name": lora_config["name"],
                            "file": lora_config["file"],
                            "trigger": lora_config.get("display_trigger", ""),
                            "description": lora_config["description"],
                            "strength_model": lora_config.get("strength_model", 1.0),
                            "strength_clip": lora_config.get("strength_clip", 1.0),
                            "trigger_words": lora_config.get("trigger_words", {}),
                            "essential_traits": lora_config.get("essential_traits", [])
                        })
            
            # Create optional descriptions for LLM
            optional_descriptions = []
            for lora in optional_lora_configs:
                description = {
                    "name": lora["name"],
                    "description": lora["description"],
                    "trigger": lora.get("trigger", ""),
                    "strength_model": lora["strength_model"],
                    "strength_clip": lora["strength_clip"]
                }
                optional_descriptions.append(description)
            
            group_config = {
                "mode": "group",
                "model_type": model_type,
                "required_loras": required_lora_configs,
                "optional_loras": optional_lora_configs,
                "required_trigger": ", ".join([lora["trigger"] for lora in required_lora_configs if lora["trigger"]]),
                "optional_descriptions": optional_descriptions,
                "seed": webui_seed  # Add seed to group mode config
            }
            print_info(f"Group mode config created: {group_config['mode']}, Required: {len(required_lora_configs)}, Optional: {len(optional_lora_configs)}")
            return group_config
        
        return None
        
    except Exception as e:
        print_error(f"Error processing LoRA config: {str(e)}")
        return None

if __name__ == "__main__":
    import uvicorn
    
    print_info("Starting YKGen Web UI...")
    print_info(f"ComfyUI Host: {config.COMFYUI_HOST}:{config.COMFYUI_PORT}")
    print_info(f"Output Directory: {config.DEFAULT_OUTPUT_DIR}")
    
    uvicorn.run(
        "webui:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )