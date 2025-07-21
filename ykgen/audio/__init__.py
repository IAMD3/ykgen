"""
Audio generation modules for YKGen.

This package contains audio generation and processing components.
"""

from .comfyui_audio import ComfyUIAudioClient, generate_story_audio, generate_song_lyrics, generate_music_tags

__all__ = ["ComfyUIAudioClient", "generate_story_audio", "generate_song_lyrics", "generate_music_tags"]