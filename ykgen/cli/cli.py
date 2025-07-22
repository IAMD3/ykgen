"""
Command Line Interface for YKGen.

This module provides the main CLI class and entry point for the YKGen application.
The CLI class orchestrates the entire application flow, from user input collection
to content generation and result display.
"""

import os
import atexit
import threading
from typing import Optional, Dict, Any, Tuple

from ykgen.config import config
from ykgen.console import print_banner, print_prompt, print_error, print_info
from ykgen.console import print_key_status_elegant
from ykgen.lora.lora_loader import validate_lora_config
from ykgen.factories.agent_factory import AgentFactory
from ykgen.config.exceptions import (
    YKGenError, 
    ConfigurationError,
    ComfyUIError,
    VideoGenerationError,
    AudioGenerationError, 
    LLMError, 
    ValidationError
)

from .menu import AgentSelectionMenu, VideoProviderMenu, ModelSelectionMenu, LoRAModeMenu
from .input_handlers import get_user_prompt, get_images_per_scene, get_audio_preference_and_language
from .display import display_generation_info, display_results, display_completion
from .lora_selection import LoRASelectionHandler


# Type alias for user preferences tuple
UserPreferences = Tuple[str, str, str, str, Dict[str, Any], int, bool, str]

# Type for agent result (could be more specific based on what agent.generate returns)
AgentResult = Any


class CLI:
    """
    Main CLI class for the YKGen application.
    
    This class orchestrates the flow of the application, handling user input,
    agent creation, and result display. It provides a structured workflow
    for collecting user preferences, creating appropriate agents, generating
    content, and displaying results.
    
    The class follows a sequential workflow:
    1. Set up the environment and validate configuration
    2. Collect user preferences through interactive menus
    3. Create and configure an appropriate agent
    4. Generate content using the agent
    5. Handle completion and display results
    
    Each step is encapsulated in its own method for better separation of concerns
    and improved maintainability.
    """
    
    def __init__(self):
        """
        Initialize the CLI with necessary cleanup handling.
        
        Sets up an exit handler to ensure proper cleanup of resources
        when the application terminates.
        """
        atexit.register(self._cleanup_on_exit)
    
    def _cleanup_on_exit(self) -> None:
        """
        Cleanup function to handle proper shutdown.
        
        This method is automatically called when the application exits.
        It ensures that all daemon threads are properly terminated to
        prevent resource leaks.
        """
        # Force cleanup of any remaining threads
        for thread in threading.enumerate():
            if thread != threading.current_thread() and thread.daemon:
                try:
                    thread.join(timeout=1.0)
                except Exception:
                    pass
    
    def _validate_configuration(self) -> bool:
        """
        Validate that required configuration is present.
        
        Checks for required environment variables and API keys to ensure
        that the application can run properly. If any required configuration
        is missing, appropriate error messages are displayed.
        
        Returns:
            bool: True if configuration is valid, False otherwise.
        
        Raises:
            ConfigurationError: If configuration validation fails due to
                missing environment variables or invalid API keys.
        """
        try:
            missing_keys = config.validate_required_keys()
            if missing_keys:
                error_msg = f"Missing required environment variables: {', '.join(missing_keys)}"
                details = (
                    f"Please set the following environment variables:\n" +
                    "\n".join(f"  • {key}" for key in missing_keys) +
                    f"\n\nCopy env.example to .env and fill in your API keys."
                )
                raise ConfigurationError(error_msg, details)
            return True
        except ConfigurationError as e:
            print_error(e.message, e.details if hasattr(e, 'details') else None)
            return False
    
    def _setup_environment(self) -> bool:
        """
        Set up the application environment.
        
        This method performs the initial setup for the application:
        1. Displays the application banner
        2. Validates required configuration
        3. Validates LoRA configuration
        4. Displays API key status
        
        This is the first step in the application workflow and must
        complete successfully for the application to proceed.
        
        Returns:
            bool: True if setup was successful, False otherwise.
        
        Raises:
            ConfigurationError: If configuration is invalid, such as missing API keys.
            ValidationError: If LoRA configuration is invalid or cannot be loaded.
        """
        try:
            # Print banner
            print_banner()
            
            # Validate configuration
            if not self._validate_configuration():
                return False
            
            # Validate LoRA configuration
            if not validate_lora_config():
                raise ValidationError("Invalid LoRA configuration file", "Please check lora_config.json in project root")
            
            # Display key status
            status_lines = config.show_key_status().split('\n')
            print_key_status_elegant([line for line in status_lines if line.strip()])
            
            return True
        
        except ValidationError as e:
            print_error(e.message, e.details if hasattr(e, 'details') else None)
            return False
    
    def _collect_user_preferences(self) -> UserPreferences:
        """
        Collect user preferences for generation.
        
        This method handles all interactive menus to collect user preferences:
        1. Agent type selection (video, poetry, etc.)
        2. Video provider selection
        3. Model type selection
        4. LoRA mode selection
        5. LoRA configuration selection
        6. Additional settings for image-only agents
        
        The collected preferences guide the subsequent creation of the
        appropriate agent and the generation process.
        
        Returns:
            UserPreferences: A tuple containing all collected preferences:
                  (agent_type, video_provider, model_type, lora_mode, lora_config,
                   images_per_scene, enable_audio, language)
        
        Raises:
            ValidationError: If user input is invalid or cannot be processed.
            YKGenError: If any other error occurs during preference collection.
        """
        try:
            # Get user choices
            agent_type = self._get_agent_type()
            video_provider = self._get_video_provider(agent_type)
            model_type = self._get_model_type()
            lora_mode = self._get_lora_mode()
            lora_config = self._get_lora_config(model_type, lora_mode)
            
            # Get image and audio settings for image-only agents
            images_per_scene = 1
            enable_audio = False
            language = "english"
            if agent_type in ["pure_image_agent", "poetry_agent_pure_image"]:
                images_per_scene = get_images_per_scene()
                enable_audio, language = get_audio_preference_and_language()
                
            return (
                agent_type,
                video_provider,
                model_type,
                lora_mode,
                lora_config if lora_config is not None else {},
                images_per_scene,
                enable_audio,
                language
            )
        except Exception as e:
            # Convert unexpected exceptions to ValidationError
            if not isinstance(e, YKGenError):
                raise ValidationError(f"Failed to collect user preferences: {str(e)}")
            raise
    
    def _create_and_configure_agent(self, preferences: UserPreferences) -> Tuple[Any, str]:
        """
        Create and configure an agent based on user preferences.
        
        This method:
        1. Extracts relevant preferences from the user preferences tuple
        2. Gets the user's prompt for content generation
        3. Displays generation info to the user
        4. Creates the appropriate agent using AgentFactory
        5. Configures the agent's LoRA mode
        
        Args:
            preferences: Tuple containing all user preferences collected from
                        interactive menus and input prompts.
            
        Returns:
            Tuple[Any, str]: A tuple containing:
                - The configured agent ready for content generation
                - The user's prompt for generation
        
        Raises:
            ConfigurationError: If agent creation fails due to configuration issues,
                                such as invalid LoRA configuration.
            ValidationError: If user input for prompt is invalid or cannot be processed.
            YKGenError: If any other error occurs during agent creation or configuration.
        """
        try:
            (
                agent_type,
                video_provider,
                _,  # model_type (not used here)
                _,  # lora_mode (not used here)
                lora_config,
                images_per_scene,
                enable_audio,
                language
            ) = preferences
            
            # Get user prompt
            try:
                prompt = get_user_prompt(agent_type)
            except Exception as e:
                raise ValidationError(f"Failed to get valid user prompt: {str(e)}")
            
            # Show generation info
            display_generation_info(agent_type, images_per_scene)
            
            # Create agent
            try:
                agent = AgentFactory.create_agent(
                    agent_type,
                    lora_config,
                    video_provider,
                    images_per_scene,
                    enable_audio,
                    language
                )
            except Exception as e:
                raise ConfigurationError(f"Failed to create agent: {str(e)}")
            
            # Configure LoRA mode
            try:
                AgentFactory.configure_lora_mode(agent, lora_config)
            except Exception as e:
                raise ConfigurationError(f"Failed to configure LoRA mode: {str(e)}")
            
            return agent, prompt
            
        except Exception as e:
            # Convert unexpected exceptions to YKGenError
            if not isinstance(e, YKGenError):
                raise ConfigurationError(f"Agent creation failed: {str(e)}")
            raise
    
    def _generate_content(self, agent: Any, prompt: str, agent_type: str) -> AgentResult:
        """
        Generate content using the specified agent and prompt.
        
        This method:
        1. Displays the user's prompt
        2. Shows an appropriate status message based on the agent type
        3. Triggers the agent's generation process
        4. Handles any errors that occur during generation
        
        Args:
            agent: The configured agent to use for generation.
            prompt: The user's prompt for content generation.
            agent_type: The type of agent being used (e.g., "poetry_agent").
            
        Returns:
            AgentResult: The generated content, which could be a story, video,
                      poetry, images, or other media depending on the agent type.
        
        Raises:
            ComfyUIError: If ComfyUI-related operations fail.
            VideoGenerationError: If video generation fails.
            AudioGenerationError: If audio generation fails.
            LLMError: If language model processing fails.
            YKGenError: If any other generation error occurs.
        """
        # Print prompt
        print_prompt(prompt)
        
        # Print appropriate status message
        if agent_type == "poetry_agent":
            self._print_status("Starting poetry processing workflow...")
        elif agent_type == "poetry_agent_pure_image":
            self._print_status("Starting poetry pure image generation workflow...")
        elif agent_type == "pure_image_agent":
            self._print_status("Starting pure image generation workflow...")
        else:
            self._print_status("Starting story generation workflow...")
                
        # Generate content
        try:
            return agent.generate(prompt)
        except Exception as e:
            # Wrap the exception in an appropriate YKGenError type
            if "ComfyUI" in str(e):
                raise ComfyUIError(f"ComfyUI generation failed: {str(e)}")
            elif "video" in str(e).lower():
                raise VideoGenerationError(f"Video generation failed: {str(e)}")
            elif "audio" in str(e).lower():
                raise AudioGenerationError(f"Audio generation failed: {str(e)}")
            elif any(term in str(e).lower() for term in ["llm", "openai", "anthropic", "claude"]):
                raise LLMError(f"Language model processing failed: {str(e)}")
            else:
                # Generic YKGen error for other cases
                raise YKGenError(f"Content generation failed: {str(e)}")
    
    def _handle_completion(self, result: AgentResult, preferences: UserPreferences) -> None:
        """
        Handle the completion of content generation.
        
        This method:
        1. Displays the generation results to the user
        2. Shows a completion message
        3. Performs cleanup operations
        4. Exits the application
        
        This is the final step in the application workflow after
        successful content generation.
        
        Args:
            result: The generated content from the agent.
            preferences: Tuple containing user preferences, used to determine
                       how to display the results.
        """
        (
            agent_type,
            _,  # video_provider (not used here)
            _,  # model_type (not used here)
            _,  # lora_mode (not used here)
            _,  # lora_config (not used here)
            images_per_scene,
            enable_audio,
            language
        ) = preferences
        
        # Display results
        display_results(result, agent_type, images_per_scene, enable_audio, language)
        
        # Display completion message
        display_completion(result)
        
        # Clean exit
        print_info("Cleaning up...")
        self._cleanup_on_exit()
        
        # Force clean exit to avoid threading issues
        os._exit(0)
    
    def run(self) -> int:
        """
        Run the main application flow.
        
        This method orchestrates the entire application workflow:
        1. Sets up the environment
        2. Collects user preferences
        3. Creates and configures an agent
        4. Generates content using the agent
        5. Handles completion and displays results
        
        Each step is handled by a dedicated method, with appropriate
        error handling throughout the process.
        
        Returns:
            int: Exit code, 0 for success, non-zero for failure.
        """
        try:
            # Set up the environment
            if not self._setup_environment():
                return 1
            
            # Collect user preferences
            try:
                preferences = self._collect_user_preferences()
            except ValidationError as e:
                print_error(f"User input error: {e.message}", e.details if hasattr(e, 'details') else None)
                return 1
            except YKGenError as e:
                print_error(f"Error collecting preferences: {e.message}", e.details if hasattr(e, 'details') else None)
                return 1
                
            agent_type = preferences[0]  # Extract agent_type for later use
            
            # Create and configure agent
            try:
                agent, prompt = self._create_and_configure_agent(preferences)
            except ConfigurationError as e:
                print_error(f"Configuration error: {e.message}", e.details if hasattr(e, 'details') else None)
                return 1
            except ValidationError as e:
                print_error(f"Input validation error: {e.message}", e.details if hasattr(e, 'details') else None)
                return 1
            except YKGenError as e:
                print_error(f"Error creating agent: {e.message}", e.details if hasattr(e, 'details') else None)
                return 1
            
            # Generate content
            try:
                result = self._generate_content(agent, prompt, agent_type)
            except ComfyUIError as e:
                print_error(f"ComfyUI error: {e.message}", 
                           "Please check that ComfyUI server is running on 127.0.0.1:8188")
                return 1
            except VideoGenerationError as e:
                print_error(f"Video generation error: {e.message}", e.details if hasattr(e, 'details') else None)
                return 1
            except AudioGenerationError as e:
                print_error(f"Audio generation error: {e.message}", e.details if hasattr(e, 'details') else None)
                return 1
            except LLMError as e:
                print_error(f"Language model error: {e.message}", 
                           "Please check your API keys and internet connection")
                return 1
            except YKGenError as e:
                print_error(f"Generation error: {e.message}", e.details if hasattr(e, 'details') else None)
                return 1
            
            # Handle completion
            self._handle_completion(result, preferences)
            
            return 0
            
        except KeyboardInterrupt:
            print("\n\nGeneration interrupted by user.")
            print("Goodbye!")
            return 0
        except Exception as e:
            # Catch-all for any unexpected errors
            error_details = (
                "Please check that:\n"
                "• Your API keys are properly configured in .env\n"
                "• ComfyUI server is running on 127.0.0.1:8188\n" 
                "• Flux model is properly installed in ComfyUI"
            )
            print_error(f"Unexpected error during generation: {str(e)}", error_details)
            return 1
    
    def _print_status(self, message: str) -> None:
        """
        Print a status message with color.
        
        Displays a status message to the user with appropriate formatting.
        Used to indicate the start of different processing stages.
        
        Args:
            message: The status message to display to the user.
        """
        from ykgen.console import status_update
        status_update(message, "bright_cyan")
    
    def _get_agent_type(self) -> str:
        """
        Get the agent type selection from the user.
        
        Displays a menu of available agent types and gets the user's choice.
        The agent type determines what kind of content will be generated
        (e.g., story with video, poetry, images only).
        
        Returns:
            str: The selected agent type identifier (e.g., "video_agent").
        """
        menu = AgentSelectionMenu()
        menu.display()
        return menu.get_user_choice()
    
    def _get_video_provider(self, agent_type: str) -> str:
        """
        Get the video provider selection from the user.
        
        Displays a menu of available video providers for video-capable agents
        and gets the user's choice. For image-only agents, automatically
        selects a default provider.
        
        Args:
            agent_type: The type of agent being used, which determines
                       whether video provider selection is needed.
            
        Returns:
            str: The selected video provider identifier (e.g., "siliconflow").
        """
        # Skip for pure image agents
        if agent_type in ["pure_image_agent", "poetry_agent_pure_image"]:
            return "siliconflow"
            
        menu = VideoProviderMenu()
        menu.display()
        return menu.get_user_choice()
    
    def _get_model_type(self) -> str:
        """
        Get the model type selection from the user.
        
        Displays a menu of available image generation models and gets the
        user's choice. The model type affects the visual style and
        capabilities of the generated images.
        
        Returns:
            str: The selected model type identifier (e.g., "flux-schnell").
        """
        menu = ModelSelectionMenu()
        menu.display()
        return menu.get_user_choice()
    
    def _get_lora_mode(self) -> str:
        """
        Get the LoRA mode selection from the user.
        
        Displays a menu of available LoRA modes and gets the user's choice.
        The LoRA mode determines how LoRA models are applied during image
        generation (e.g., applying the same LoRAs to all images or
        different ones per group).
        
        Returns:
            str: The selected LoRA mode identifier (e.g., "all", "group").
        """
        menu = LoRAModeMenu()
        menu.display()
        return menu.get_user_choice()
    
    def _get_lora_config(self, model_type: str, lora_mode: str) -> Optional[Dict[str, Any]]:
        """
        Get the LoRA configuration from the user.
        
        Based on the selected model type and LoRA mode, displays available
        LoRA models and gets the user's selection. The LoRA configuration
        affects the visual style and content of generated images.
        
        Args:
            model_type: The selected image generation model type.
            lora_mode: The selected LoRA application mode.
            
        Returns:
            Optional[Dict[str, Any]]: The LoRA configuration dictionary or
                                   None if selection fails.
            
        Raises:
            ValidationError: If LoRA configuration selection fails due to
                          invalid input or configuration issues.
        """
        try:
            lora_handler = LoRASelectionHandler()
            return lora_handler.get_lora_config(model_type, lora_mode)
        except Exception as e:
            raise ValidationError(f"Failed to get LoRA configuration: {str(e)}")


def main() -> int:
    """
    Main entry point for the YKGen application.
    
    Creates an instance of the CLI class and runs the application workflow.
    This function is the primary entry point called by the main script.
    
    Returns:
        int: Exit code, 0 for success, non-zero for failure.
    """
    cli = CLI()
    return cli.run()


if __name__ == "__main__":
    main()