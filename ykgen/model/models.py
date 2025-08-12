"""
Core data models for YKGen.

This module contains the core state models used throughout the application,
including VisionState (formerly XVisionState) and related types.
"""

from typing import Annotated, TypedDict, Optional

from langchain_core.messages import AIMessage, HumanMessage


class Character(TypedDict):
    """A character in the story."""

    name: Annotated[str, "the name of the character"]
    description: Annotated[
        str, "the description of the character, with appearance and characteristics"
    ]
    seed: Annotated[Optional[int], "consistent seed for character image generation across scenes"]


class Characters(TypedDict):
    """Collection of characters."""

    characters: list[Character]


class Scene(TypedDict):
    """A scene in the story/video."""

    location: Annotated[str, "the location of the scene"]
    time: Annotated[str, "the time of the scene"]
    characters: Annotated[list[Character], "the characters in the scene"]
    action: Annotated[str, "the action of the scene"]
    image_prompt_positive: Annotated[
        Optional[str], "the positive image prompt of the scene, used for image generation"
    ]
    image_prompt_negative: Annotated[
        Optional[str], "the negative image prompt of the scene, used to avoid unwanted elements in image generation"
    ]


class SceneList(TypedDict):
    """Collection of scenes."""

    scenes: list[Scene]


class ScenePrompt(TypedDict):
    """Prompts for a specific scene."""
    
    scene_index: Annotated[int, "the index of the scene (0-based)"]
    image_prompt_positive: Annotated[
        str, "the positive image prompt for this scene, describing what should be included"
    ]
    image_prompt_negative: Annotated[
        str, "the negative image prompt for this scene, describing what should be avoided"
    ]


class PromptGeneration(TypedDict):
    """Collection of generated prompts for scenes."""
    
    prompts: list[ScenePrompt]


class VisionState(TypedDict, total=False):
    """
    Core state model for video/story generation workflow.

    This is the main state that flows through the LangGraph workflow,
    containing all the information needed for story and scene generation.
    All fields are optional to allow gradual population during workflow execution.
    """

    prompt: HumanMessage
    story_full: AIMessage
    characters_full: list[Character]
    scenes: list[Scene]
    current_scene_index: int
    image_paths: list[str]  # Paths to generated scene images
    video_tasks: list  # List of video generation tasks
    audio_path: str  # Path to generated audio/song file
    pinyin_lyrics: str  # Pinyin version of poetry for audio generation (PoetryAgent)
    style: str  # Visual style for image generation (e.g., "dark cartoon", "watercolor", "cyberpunk")
