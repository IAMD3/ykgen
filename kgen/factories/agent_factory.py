"""
Agent factory for KGen.

This module provides a factory class for creating and configuring
different types of agents in the KGen system.
"""

from typing import Dict, Any, Optional

from kgen import VideoAgent, PoetryAgent, PureImageAgent


class AgentFactory:
    """
    Factory class for creating and configuring different types of agents.
    
    This class implements the Factory pattern to create different agent types
    with the appropriate configuration based on user input.
    """
    
    @classmethod
    def create_agent(
        cls,
        agent_type: str,
        lora_config: Dict[str, Any],
        video_provider: str = "siliconflow",
        images_per_scene: int = 1,
        enable_audio: bool = False,
        language: str = "english"
    ) -> Any:
        """
        Create and configure an agent based on the specified type and parameters.
        
        Args:
            agent_type: The type of agent to create ('video_agent', 'poetry_agent', etc.)
            lora_config: The LoRA configuration dictionary
            video_provider: The video provider to use ('siliconflow')
            images_per_scene: Number of images to generate per scene
            enable_audio: Whether to enable audio generation
            language: The language to use for audio generation ('english' or 'chinese')
            
        Returns:
            The configured agent instance.
        """
        from kgen.console import print_info
        
        if agent_type == "poetry_agent":
            print_info("Initializing PoetryAgent for Chinese poetry processing...")
            return cls._create_poetry_agent(lora_config, video_provider)
            
        elif agent_type == "poetry_agent_pure_image":
            if enable_audio:
                print_info(f"Initializing PoetryAgent (Pure Image Mode) with audio generation ({images_per_scene} images per scene)...")
            else:
                print_info(f"Initializing PoetryAgent (Pure Image Mode) for image-only generation ({images_per_scene} images per scene)...")
            
            return cls._create_poetry_pure_image_agent(
                lora_config,
                video_provider,
                images_per_scene,
                enable_audio
            )
            
        elif agent_type == "pure_image_agent":
            if enable_audio:
                print_info(f"Initializing PureImageAgent with {language} audio generation ({images_per_scene} images per scene)...")
            else:
                print_info(f"Initializing PureImageAgent for image-only generation ({images_per_scene} images per scene)...")
            
            return cls._create_pure_image_agent(
                lora_config,
                images_per_scene,
                enable_audio,
                language
            )
            
        else:  # Default to video_agent
            print_info("Initializing VideoAgent for story generation...")
            return cls._create_video_agent(lora_config, video_provider)
    
    @staticmethod
    def _create_video_agent(lora_config: Dict[str, Any], video_provider: str) -> VideoAgent:
        """Create and configure a VideoAgent."""
        return VideoAgent(
            enable_audio=True,
            lora_config=lora_config,
            video_provider=video_provider,
        )
    
    @staticmethod
    def _create_poetry_agent(lora_config: Dict[str, Any], video_provider: str) -> PoetryAgent:
        """Create and configure a PoetryAgent."""
        return PoetryAgent(
            enable_audio=True,
            lora_config=lora_config,
            video_provider=video_provider,
        )
    
    @staticmethod
    def _create_poetry_pure_image_agent(
        lora_config: Dict[str, Any],
        video_provider: str,
        images_per_scene: int,
        enable_audio: bool
    ) -> PoetryAgent:
        """Create and configure a PoetryAgent in pure image mode."""
        return PoetryAgent(
            enable_audio=enable_audio,
            lora_config=lora_config,
            video_provider=video_provider,
            pure_image_mode=True,
            images_per_scene=images_per_scene,
        )
    
    @staticmethod
    def _create_pure_image_agent(
        lora_config: Dict[str, Any],
        images_per_scene: int,
        enable_audio: bool,
        language: str
    ) -> PureImageAgent:
        """Create and configure a PureImageAgent."""
        return PureImageAgent(
            enable_audio=enable_audio,
            lora_config=lora_config,
            images_per_scene=images_per_scene,
            language=language,
        )
    
    @staticmethod
    def configure_lora_mode(agent: Any, lora_config: Dict[str, Any]) -> None:
        """
        Configure the LoRA mode for the given agent.
        
        Args:
            agent: The agent to configure
            lora_config: The LoRA configuration
        """
        if hasattr(agent, 'lora_config') and isinstance(lora_config, dict):
            if lora_config.get('mode') == 'group':
                agent.lora_mode = 'group'
                agent.group_config = lora_config
            else:
                agent.lora_mode = 'all'
                agent.group_config = None