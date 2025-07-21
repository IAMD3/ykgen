"""
Audio generation module for YKGen using ComfyUI.

This module handles audio generation from text using ComfyUI's audio generation capabilities.
"""

import json
import os
import urllib.parse
import urllib.request
import uuid
from typing import Any, Dict, List, Optional

import websocket

from ykgen.config.config import config
from ykgen.model.models import Scene, VisionState


class ComfyUIAudioClient:
    """Client for generating audio using ComfyUI's audio models."""

    def __init__(self, server_address: Optional[str] = None):
        """Initialize ComfyUI audio client with server address."""
        self.server_address = server_address or config.comfyui_address
        self.client_id = str(uuid.uuid4())

        # Audio generation workflow template
        self.audio_workflow_template = {
            "14": {
                "inputs": {
                    "tags": "immediate vocals, vocal-driven, soft female vocals, anime, kawaii pop, j-pop, piano, guitar, synthesizer, fast, happy, cheerful, lighthearted, voice-first, early vocals",
                    "lyrics": "",  # Will be replaced with song lyrics
                    "lyrics_strength": 0.99,
                    "clip": ["40", 1],
                },
                "class_type": "TextEncodeAceStepAudio",
                "_meta": {"title": "TextEncodeAceStepAudio"},
            },
            "17": {
                "inputs": {"seconds": 120, "batch_size": 1},
                "class_type": "EmptyAceStepLatentAudio",
                "_meta": {"title": "EmptyAceStepLatentAudio"},
            },
            "18": {
                "inputs": {"samples": ["52", 0], "vae": ["40", 2]},
                "class_type": "VAEDecodeAudio",
                "_meta": {"title": "VAEDecodeAudio"},
            },
            "40": {
                "inputs": {"ckpt_name": "ace_step_v1_3.5b.safetensors"},
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"},
            },
            "44": {
                "inputs": {"conditioning": ["14", 0]},
                "class_type": "ConditioningZeroOut",
                "_meta": {"title": "ConditioningZeroOut"},
            },
            "49": {
                "inputs": {"model": ["51", 0], "operation": ["50", 0]},
                "class_type": "LatentApplyOperationCFG",
                "_meta": {"title": "LatentApplyOperationCFG"},
            },
            "50": {
                "inputs": {"multiplier": 1.0},
                "class_type": "LatentOperationTonemapReinhard",
                "_meta": {"title": "LatentOperationTonemapReinhard"},
            },
            "51": {
                "inputs": {"shift": 5.0, "model": ["40", 0]},
                "class_type": "ModelSamplingSD3",
                "_meta": {"title": "ModelSamplingSD3"},
            },
            "52": {
                "inputs": {
                    "seed": None,  # Will be randomized
                    "steps": 50,
                    "cfg": 5,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1,
                    "model": ["49", 0],
                    "positive": ["14", 0],
                    "negative": ["44", 0],
                    "latent_image": ["17", 0],
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"},
            },
            "59": {
                "inputs": {
                    "filename_prefix": "audio/ComfyUI",
                    "quality": "V0",
                    "audioUI": "",
                    "audio": ["18", 0],
                },
                "class_type": "SaveAudioMP3",
                "_meta": {"title": "Save Audio (MP3)"},
            },
        }

    def queue_prompt(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        """Queue a prompt to ComfyUI server."""
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode("utf-8")
        req = urllib.request.Request(f"http://{self.server_address}/prompt", data=data)
        response = urllib.request.urlopen(req)
        return json.loads(response.read())

    def get_audio(self, filename: str, subfolder: str, folder_type: str) -> bytes:
        """Get audio data from ComfyUI server."""
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(
            f"http://{self.server_address}/view?{url_values}"
        ) as response:
            return response.read()

    def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get history for a specific prompt ID."""
        with urllib.request.urlopen(
            f"http://{self.server_address}/history/{prompt_id}"
        ) as response:
            return json.loads(response.read())

    def wait_for_completion(self, ws: websocket.WebSocket, prompt_id: str) -> bool:
        """Wait for audio generation to complete."""
        while True:
            try:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message["type"] == "executing":
                        data = message["data"]
                        if data["node"] is None and data["prompt_id"] == prompt_id:
                            return True  # Execution is done
                else:
                    continue  # previews are binary data
            except Exception as e:
                print(f"Error receiving websocket message: {e}")
                return False

    def create_audio_prompt(
        self, lyrics: str, tags: Optional[str] = None, duration_seconds: int = 120
    ) -> Dict[str, Any]:
        """Create an audio generation workflow prompt."""
        prompt = json.loads(json.dumps(self.audio_workflow_template))  # Deep copy

        # Set lyrics
        prompt["14"]["inputs"]["lyrics"] = lyrics

        # Set tags if provided, otherwise use default
        if tags:
            prompt["14"]["inputs"]["tags"] = tags

        # Set duration
        prompt["17"]["inputs"]["seconds"] = duration_seconds

        # Randomize seed
        prompt["52"]["inputs"]["seed"] = int.from_bytes(
            os.urandom(8), byteorder="big"
        ) & ((1 << 63) - 1)

        return prompt

    def generate_audio(
        self,
        lyrics: str,
        output_path: str,
        tags: Optional[str] = None,
        duration_seconds: int = 120,
    ) -> bool:
        """
        Generate audio from lyrics and save to file.

        Args:
            lyrics: The lyrics/text for the song
            output_path: Path where to save the generated audio
            tags: Optional music style tags
            duration_seconds: Duration of the audio in seconds

        Returns:
            True if successful, False otherwise
        """
        ws = None
        try:
            # Connect to ComfyUI websocket
            ws = websocket.WebSocket()
            ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")

            # Create and queue the prompt
            audio_prompt = self.create_audio_prompt(lyrics, tags, duration_seconds)
            queue_result = self.queue_prompt(audio_prompt)
            prompt_id = queue_result["prompt_id"]

            print(f"Generating audio with prompt ID: {prompt_id}")

            # Wait for completion
            if not self.wait_for_completion(ws, prompt_id):
                print("Audio generation failed or timed out")
                return False

            # Get the generated audio from history
            history = self.get_history(prompt_id)[prompt_id]

            # Find the audio output (from SaveAudioMP3 node)
            for node_id, node_output in history["outputs"].items():
                if "audio" in node_output:
                    for audio_info in node_output["audio"]:
                        # Download the audio file
                        audio_data = self.get_audio(
                            audio_info["filename"],
                            audio_info["subfolder"],
                            audio_info["type"],
                        )

                        # Save to specified path
                        with open(output_path, "wb") as f:
                            f.write(audio_data)

                        print(f"Audio saved to: {output_path}")
                        return True

            print("No audio output found in generation results")
            return False

        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            return False
        finally:
            if ws:
                try:
                    ws.close()
                except Exception:
                    pass


def generate_song_lyrics(
    scenes: List[Scene], story: str, llm, duration_seconds: int
) -> str:
    """
    Generate song lyrics based on the story and scenes using an LLM.

    Args:
        scenes: List of Scene objects
        story: The full story text
        llm: The language model to use for generation
        duration_seconds: Duration of the song in seconds

    Returns:
        Generated song lyrics
    """
    from langchain_core.prompts import ChatPromptTemplate

    # Format scenes for the prompt
    scenes_description = "\n".join(
        [
            f"Scene {i+1}: {scene['action']} at {scene['location']} during {scene['time']}"
            for i, scene in enumerate(scenes)
        ]
    )

    # Calculate appropriate word count based on duration
    # Assuming average singing pace of 2-3 words per second
    min_words = int(duration_seconds * 1.5)
    max_words = int(duration_seconds * 2.5)

    system_message = (
        "You are a talented songwriter who creates catchy, emotional songs based on stories. "
        "Your songs should capture the essence of the story while being memorable and singable."
    )

    user_prompt = f"""Based on the following story and scenes, write song lyrics that capture the narrative and emotions.

Story:
{story}

Scenes:
{scenes_description}

Song Duration: {duration_seconds} seconds

Requirements:
- The lyrics should tell the story in a musical way
- Include a chorus that captures the main theme
- Make it emotional and engaging
- Keep it between {min_words}-{max_words} words to fit the {duration_seconds} second duration
- IMPORTANT: Start with vocals immediately - no long instrumental intro
- Begin with a strong opening line that hooks the listener right away
- Structure: Adjust the structure based on duration:
  * For songs under 30 seconds: Verse, Chorus (vocals start immediately)
  * For songs 30-60 seconds: Verse 1, Chorus, Verse 2, Chorus (vocals start immediately)
  * For songs over 60 seconds: Verse 1, Chorus, Verse 2, Chorus, Bridge (optional), Chorus (vocals start immediately)

Write only the lyrics, no explanations or formatting markers. Make sure the first line is strong and engaging since it will start the song."""

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_message), ("user", user_prompt)]
    )

    chain = prompt | llm
    output = chain.invoke({})

    return output.content


def generate_music_tags(scenes: List[Scene], story: str, llm) -> str:
    """
    Generate appropriate music style tags based on the story mood and content.

    Args:
        scenes: List of Scene objects
        story: The full story text
        llm: The language model to use for generation

    Returns:
        Comma-separated music style tags
    """
    from langchain_core.prompts import ChatPromptTemplate

    system_message = (
        "You are a music producer who selects appropriate musical styles and instruments "
        "based on story content and mood."
    )

    user_prompt = f"""Based on this story, suggest appropriate music style tags:

Story: {story}

Select tags that match the story's mood and genre. Examples of tags:
- Genres: pop, rock, jazz, classical, electronic, hip-hop, country, folk, metal, indie
- Mood: happy, sad, energetic, calm, dramatic, mysterious, romantic, dark, uplifting
- Instruments: piano, guitar, violin, drums, synthesizer, orchestra, acoustic
- Tempo: fast, slow, medium
- Style modifiers: epic, cinematic, ambient, lo-fi, acoustic, electronic
- Vocal timing: immediate vocals, early vocals, vocal-driven, voice-first

IMPORTANT: Include tags that emphasize immediate vocal entry and minimize instrumental intro. 
Prioritize "immediate vocals", "vocal-driven", or "voice-first" style tags.

Return only a comma-separated list of tags (10-15 tags maximum), no explanations."""

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_message), ("user", user_prompt)]
    )

    chain = prompt | llm
    output = chain.invoke({})

    return output.content.strip()


def generate_story_audio(state: VisionState, output_dir: str, llm) -> Optional[str]:
    """
    Generate audio/song for the story based on scenes.

    Args:
        state: The current VisionState with story and scenes
        output_dir: Directory to save the audio file
        llm: Language model for generating lyrics and tags

    Returns:
        Path to generated audio file if successful, None otherwise
    """
    try:
        # Calculate duration based on number of scenes
        num_scenes = len(state["scenes"])
        duration_seconds = num_scenes * config.AUDIO_DURATION_PER_SCENE
        print(
            f"Calculating audio duration: {num_scenes} scenes × {config.AUDIO_DURATION_PER_SCENE} seconds = {duration_seconds} seconds"
        )

        # Generate song lyrics based on story and scenes
        print("Generating song lyrics...")
        lyrics = generate_song_lyrics(
            state["scenes"], state["story_full"].content, llm, duration_seconds
        )
        print(f"Generated lyrics:\n{lyrics}\n")

        # Generate appropriate music tags
        print("Generating music style tags...")
        tags = generate_music_tags(state["scenes"], state["story_full"].content, llm)
        print(f"Music tags: {tags}\n")

        # Generate comprehensive generation record
        print("📝 Generating story generation record...")
        record_path = generate_story_record(
            state, output_dir, lyrics, tags, duration_seconds
        )
        if record_path:
            print(f"📋 Story record saved: {record_path}")

        # Generate audio using ComfyUI
        client = ComfyUIAudioClient()
        audio_path = os.path.join(output_dir, "story_song.mp3")

        print(
            f"Generating audio with ComfyUI (duration: {duration_seconds} seconds)..."
        )
        success = client.generate_audio(
            lyrics=lyrics,
            output_path=audio_path,
            tags=tags,
            duration_seconds=duration_seconds,
        )

        if success:
            print(f"✅ Audio generated successfully: {audio_path}")

            # Generate subtitle file from lyrics
            # NOTE: Subtitle generation is currently disabled as it may not be necessary
            # subtitle_path = os.path.join(output_dir, "story_song.srt")
            # if generate_subtitle_file(
            #     lyrics, subtitle_path, duration_seconds=duration_seconds
            # ):
            #     print(f"📝 Subtitles generated: {subtitle_path}")

            return audio_path
        else:
            print("❌ Failed to generate audio")
            return None

    except Exception as e:
        print(f"Error in audio generation: {str(e)}")
        return None


def generate_subtitle_file(
    lyrics: str, output_path: str, duration_seconds: int = 120
) -> bool:
    """
    Generate a subtitle file (SRT format) from lyrics.

    Args:
        lyrics: The song lyrics
        output_path: Path to save the subtitle file
        duration_seconds: Total duration of the audio

    Returns:
        True if successful, False otherwise
    """
    try:
        # Split lyrics into lines
        lines = [line.strip() for line in lyrics.strip().split("\n") if line.strip()]

        if not lines:
            print("No lyrics to generate subtitles from")
            return False

        # Calculate timing for each line
        time_per_line = duration_seconds / len(lines)

        # Generate SRT format
        srt_content = []
        for i, line in enumerate(lines):
            # Calculate start and end times
            start_seconds = i * time_per_line
            end_seconds = (i + 1) * time_per_line

            # Format timestamps (HH:MM:SS,mmm)
            start_time = format_srt_timestamp(start_seconds)
            end_time = format_srt_timestamp(end_seconds)

            # Add subtitle entry
            srt_content.append(f"{i + 1}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(line)
            srt_content.append("")  # Empty line between entries

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_content))

        return True

    except Exception as e:
        print(f"Error generating subtitle file: {str(e)}")
        return False


def format_srt_timestamp(seconds: float) -> str:
    """
    Format seconds into SRT timestamp format (HH:MM:SS,mmm).

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def generate_story_record(
    state: VisionState,
    output_dir: str,
    lyrics: str,
    music_tags: str,
    duration_seconds: int,
) -> Optional[str]:
    """
    Generate a comprehensive text record of the story generation process.

    Args:
        state: The current VisionState with all generation data
        output_dir: Directory to save the record file
        lyrics: Generated song lyrics
        music_tags: Generated music style tags
        duration_seconds: Calculated audio duration

    Returns:
        Path to the generated record file if successful, None otherwise
    """
    try:
        from datetime import datetime

        record_path = os.path.join(output_dir, "story_generation_record.txt")

        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build the comprehensive record
        record_content = []

        # Header
        record_content.append("=" * 80)
        record_content.append("STORY GENERATION RECORD")
        record_content.append("=" * 80)
        record_content.append(f"Generated on: {timestamp}")
        record_content.append(
            f"Total Duration: {duration_seconds} seconds ({len(state['scenes'])} scenes × 5 seconds)"
        )
        record_content.append("")

        # Original Prompt
        record_content.append("🎯 ORIGINAL PROMPT")
        record_content.append("-" * 40)
        record_content.append(state["prompt"].content)
        record_content.append("")

        # Generated Story
        record_content.append("📖 GENERATED STORY")
        record_content.append("-" * 40)
        record_content.append(state["story_full"].content)
        record_content.append("")

        # Characters
        record_content.append("👥 CHARACTERS")
        record_content.append("-" * 40)
        if state.get("characters_full"):
            for i, character in enumerate(state["characters_full"], 1):
                record_content.append(f"{i}. {character['name']}")
                record_content.append(f"   Description: {character['description']}")
                record_content.append("")
        else:
            record_content.append("No characters generated.")
            record_content.append("")

        # Scenes
        record_content.append("🎬 SCENES")
        record_content.append("-" * 40)
        for i, scene in enumerate(state["scenes"], 1):
            record_content.append(f"SCENE {i}")
            record_content.append(f"Location: {scene['location']}")
            record_content.append(f"Time: {scene['time']}")
            record_content.append(f"Action: {scene['action']}")
            record_content.append("")
            record_content.append("Characters in scene:")
            if scene.get("characters"):
                for char in scene["characters"]:
                    record_content.append(f"  - {char['name']}: {char['description']}")
            else:
                record_content.append("  - No specific characters listed")
            record_content.append("")
            record_content.append("Image Generation Prompts:")
            record_content.append(f"  Positive: {scene['image_prompt_positive']}")
            if scene.get("image_prompt_negative"):
                record_content.append(f"  Negative: {scene['image_prompt_negative']}")
            record_content.append("")
            record_content.append("-" * 60)
            record_content.append("")

        # Audio Information
        record_content.append("🎵 AUDIO GENERATION")
        record_content.append("-" * 40)
        record_content.append(f"Duration: {duration_seconds} seconds")
        record_content.append(f"Music Style Tags: {music_tags}")
        record_content.append("")
        record_content.append("Song Lyrics:")
        record_content.append(lyrics)
        record_content.append("")

        # Technical Details
        record_content.append("⚙️ TECHNICAL DETAILS")
        record_content.append("-" * 40)
        record_content.append(f"Number of scenes: {len(state['scenes'])}")
        record_content.append(f"Video duration per scene: 5 seconds")
        record_content.append(f"Total video duration: {duration_seconds} seconds")
        if state.get("image_paths"):
            record_content.append(f"Generated images: {len(state['image_paths'])}")
            record_content.append("Image files:")
            for img_path in state["image_paths"]:
                record_content.append(f"  - {os.path.basename(img_path)}")
        record_content.append("")

        # Reproduction Instructions
        record_content.append("🔄 REPRODUCTION INSTRUCTIONS")
        record_content.append("-" * 40)
        record_content.append("To reproduce this generation:")
        record_content.append("1. Use the original prompt above")
        record_content.append("2. Ensure the same characters are generated")
        record_content.append("3. Use the exact scene descriptions and image prompts")
        record_content.append(
            "4. Generate audio with the provided lyrics and music tags"
        )
        record_content.append("5. Set audio duration to the specified length")
        record_content.append("")

        # File Structure
        record_content.append("📁 OUTPUT FILE STRUCTURE")
        record_content.append("-" * 40)
        record_content.append("Expected files in this directory:")
        record_content.append("├── story_generation_record.txt  (this file)")
        record_content.append("├── story_song.mp3              (generated audio)")
        # record_content.append("├── story_song.srt              (audio subtitles)")
        for i in range(len(state["scenes"])):
            record_content.append(
                f"├── scene_{i+1:03d}_00.png          (scene {i+1} image)"
            )
            record_content.append(
                f"├── scene_{i+1:03d}.mp4             (scene {i+1} video)"
            )
            record_content.append(
                f"├── scene_{i+1:03d}_enhanced.mp4    (scene {i+1} with audio)"
            )
        record_content.append("├── combined_story.mp4           (combined video)")
        record_content.append(
            "└── combined_story_with_audio.mp4 (final video with soundtrack)"
        )
        record_content.append("")

        # Footer
        record_content.append("=" * 80)
        record_content.append("END OF RECORD")
        record_content.append("=" * 80)

        # Write to file
        with open(record_path, "w", encoding="utf-8") as f:
            f.write("\n".join(record_content))

        return record_path

    except Exception as e:
        print(f"Error generating story record: {str(e)}")
        return None
