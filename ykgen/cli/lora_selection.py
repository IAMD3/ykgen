"""
LoRA selection handler for YKGen.

This module provides functions and classes for handling LoRA selection
and configuration in the YKGen application.
"""

import sys
import os
import json
from typing import Dict, List, Any, Optional

from rich.panel import Panel
from rich.text import Text
from rich import box

from ykgen.console.display import console
from ykgen.lora.lora_loader import (
    get_model_description,
    get_lora_by_choice,
    prepare_lora_for_agent,
    prepare_multiple_loras_for_agent,
    parse_strength_input
)


class LoRASelectionHandler:
    """
    Handler class for LoRA selection and configuration.
    
    This class implements methods to get LoRA configuration from the user,
    supporting both 'all' and 'group' modes.
    """
    
    def get_lora_config(self, model_type: str = "flux-schnell", lora_mode: str = "all") -> Optional[Dict[str, Any]]:
        """
        Get user LoRA selection with support for 'all', 'group', and 'none' modes.
        
        Args:
            model_type: The model type being used.
            lora_mode: The LoRA mode ('all', 'group', or 'none').
            
        Returns:
            Optional[Dict[str, Any]]: The LoRA configuration or None if selection fails.
        """
        try:
            # Load available LoRA configurations
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ykgen", "config/lora_config.json")
            
            with open(config_path, 'r') as f:
                lora_configs = json.load(f)
            
            if model_type not in lora_configs:
                from ykgen.console import print_error
                print_error(f"Model type '{model_type}' not found in LoRA configuration")
                return None
            
            available_loras = lora_configs[model_type]["loras"]
            
            if lora_mode == "all":
                # Original behavior - select LoRAs that will be used for all images
                return self._get_lora_selection_all_mode(available_loras, model_type)
            elif lora_mode == "group":
                # New behavior - select required and optional LoRAs
                return self._get_lora_selection_group_mode(available_loras, model_type)
            elif lora_mode == "none":
                # No LoRA mode - return empty configuration
                return {
                    "mode": "none",
                    "model_type": model_type,
                    "loras": [],
                    "trigger": ""
                }
            else:
                from ykgen.console import print_error
                print_error(f"Unknown LoRA mode: {lora_mode}")
                return None
                
        except Exception as e:
            from ykgen.console import print_error
            print_error(f"Error loading LoRA configuration: {str(e)}", "Please check ykgen/lora_config.json")
            sys.exit(1)

    def _ensure_trigger(self, lora_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure that the LoRA configuration has a 'trigger' key.
        
        Args:
            lora_config: The LoRA configuration dictionary.
            
        Returns:
            Dict[str, Any]: The LoRA configuration with a 'trigger' key.
        """
        if "trigger" not in lora_config:
            # Use display_trigger if available, otherwise empty string
            lora_config["trigger"] = lora_config.get("display_trigger", "")
        return lora_config

    def _get_lora_selection_all_mode(self, available_loras: Dict[str, Any], model_type: str) -> Dict[str, Any]:
        """
        Handle LoRA selection for 'all' mode.
        
        Args:
            available_loras: Dictionary of available LoRAs.
            model_type: The model type being used.
            
        Returns:
            Dict[str, Any]: The LoRA configuration for 'all' mode.
        """
        # Create beautiful LoRA selection panel
        lora_text = Text()
        lora_text.append(f"Choose LoRA models for {model_type.title()}:\n\n", style="bold bright_magenta")
        lora_text.append("Available LoRA Models:\n", style="bold white")
        
        # Display each LoRA option from the JSON configuration
        for choice_id, lora_config in available_loras.items():
            lora_text.append(f"  {choice_id}. ", style="bright_yellow")
            lora_text.append(lora_config["name"], style="yellow")
            lora_text.append(f" - {lora_config['description']}", style="white")
            
            # Show trigger words
            if lora_config.get("display_trigger"):
                lora_text.append(f" (trigger: '{lora_config['display_trigger']}')", style="dim white")
            lora_text.append("\n", style="white")
            
            # Show essential traits for character LoRAs
            if lora_config.get("essential_traits"):
                essential = ", ".join(lora_config["essential_traits"])
                lora_text.append(f"     Essential traits: {essential}\n", style="dim white")
            
            # Show default strength values
            strength_model = lora_config.get("strength_model", 1.0)
            strength_clip = lora_config.get("strength_clip", 1.0)
            lora_text.append(f"     Default strength - Model: {strength_model}, CLIP: {strength_clip}\n", style="dim cyan")
        
        lora_text.append(f"\nNote: ", style="bold bright_blue")
        lora_text.append(f"{get_model_description(model_type)}\n", style="blue")
        lora_text.append("      You can select multiple LoRAs (comma-separated) and customize strength values.\n", style="blue")
        lora_text.append("      Strength values should be between 0.1 and 1.0 (default: 1.0).", style="blue")
        
        # Show special notes if available
        if any(lora.get("notes") for lora in available_loras.values()):
            for lora_config in available_loras.values():
                if lora_config.get("notes"):
                    lora_text.append(f"\n      {lora_config['notes']}", style="blue")
        
        lora_panel = Panel(
            lora_text,
            title="[bold bright_magenta]Multiple LoRA Selection[/bold bright_magenta]",
            border_style="magenta",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.console.print(lora_panel)
        print()
        
        # Determine the choice range
        max_choice = max(int(k) for k in available_loras.keys())
        choice_range = f"1-{max_choice}" if max_choice > 1 else "1"
        
        # Show selection examples
        example_text = Text()
        example_text.append("Selection Examples:\n", style="bold bright_green")
        example_text.append("  Single LoRA: ", style="bright_white")
        example_text.append("2", style="green")
        example_text.append(" (select LoRA #2 with default strength)\n", style="white")
        example_text.append("  Multiple LoRAs: ", style="bright_white")
        example_text.append("2,5,7", style="green")
        example_text.append(" (select LoRAs #2, #5, and #7)\n", style="white")
        example_text.append("  With strength: ", style="bright_white")
        example_text.append("2:0.8", style="green")
        example_text.append(" (LoRA #2 with 0.8 strength for both model and CLIP)\n", style="white")
        example_text.append("  Custom strengths: ", style="bright_white")
        example_text.append("2:0.8,0.9", style="green")
        example_text.append(" (LoRA #2 with model strength 0.8, CLIP strength 0.9)\n", style="white")
        example_text.append("  Mixed example: ", style="bright_white")
        example_text.append("1,3:0.7,5:0.6,0.8", style="green")
        example_text.append(" (LoRA #1 default, #3 with 0.7, #5 with model 0.6/CLIP 0.8)", style="white")
        
        example_panel = Panel(
            example_text,
            title="[bold bright_green]Selection Examples[/bold bright_green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.console.print(example_panel)
        print()
        
        while True:
                try:
                    if max_choice == 1:
                        choice_input = input("  Select LoRA model (1) or press Enter: ").strip()
                        if choice_input == "":
                            choice_input = "1"
                    else:
                        choice_input = input(f"  Select LoRA models ({choice_range}): ").strip()
                    
                    if not choice_input:
                        print("  Please enter at least one LoRA selection.")
                        continue
                    
                    # Parse the input for multiple LoRAs with optional strength values
                    selected_loras_with_strength = []
                    
                    # Split by comma to get individual selections
                    selections = [s.strip() for s in choice_input.split(',')]
                    
                    for selection in selections:
                        if ':' in selection:
                            # Format: "2:0.8" or "2:0.8,0.9"
                            parts = selection.split(':', 1)
                            lora_choice = parts[0].strip()
                            strength_part = parts[1].strip()
                            
                            # Parse strength values
                            strength_model, strength_clip = parse_strength_input(strength_part)
                            if strength_model is None or strength_clip is None:
                                print(f"  Invalid strength values for LoRA {lora_choice}. Please use values between 0.1 and 1.0.")
                                continue
                        else:
                            # Just LoRA choice, use default strength
                            lora_choice = selection.strip()
                            strength_model, strength_clip = 1.0, 1.0
                        
                        # Get the LoRA configuration
                        lora_config = get_lora_by_choice(model_type, lora_choice)
                        if lora_config:
                            # Ensure trigger key exists
                            lora_config = self._ensure_trigger(lora_config)
                            # Override with custom strength values
                            lora_config["strength_model"] = strength_model
                            lora_config["strength_clip"] = strength_clip
                            selected_loras_with_strength.append(lora_config)
                        else:
                            print(f"  Invalid LoRA choice: {lora_choice}. Please enter a number from {choice_range}.")
                            break
                    else:
                        # All selections were valid
                        if not selected_loras_with_strength:
                            print(f"  Please select at least one valid LoRA from {choice_range}.")
                            continue
                        
                        # Prepare for agent use
                        if len(selected_loras_with_strength) == 1:
                            # Single LoRA
                            agent_lora_config = prepare_lora_for_agent(selected_loras_with_strength[0], model_type)
                        else:
                            # Multiple LoRAs
                            agent_lora_config = prepare_multiple_loras_for_agent(selected_loras_with_strength, model_type)
                        
                        # Elegant confirmation
                        confirm_text = Text()
                        
                        if agent_lora_config.get("is_multiple"):
                            # Multiple LoRAs selected
                            confirm_text.append(f"Selected {len(selected_loras_with_strength)} LoRAs:\n", style="bold white")
                            
                            for i, lora_config in enumerate(agent_lora_config["loras"], 1):
                                if lora_config["name"] != "No LoRA":
                                    confirm_text.append(f"  {i}. ", style="bright_yellow")
                                    confirm_text.append(f'{lora_config["name"]}', style="italic bright_magenta")
                                    confirm_text.append(f' (Model: {lora_config["strength_model"]}, CLIP: {lora_config["strength_clip"]})', style="dim bright_blue")
                                    if lora_config.get("trigger"):
                                        confirm_text.append(f'\n     Trigger: "{lora_config["trigger"]}"', style="dim cyan")
                                    confirm_text.append("\n")
                            
                            confirm_text.append(f'\nCombined trigger words: "{agent_lora_config.get("trigger", "")}"', style="dim bright_green")
                        else:
                            # Single LoRA selected
                            confirm_text.append("Selected LoRA: ", style="bold white")
                            confirm_text.append(f'{agent_lora_config["name"]}', style="italic bright_magenta")
                            confirm_text.append(f' (Model: {agent_lora_config["strength_model"]}, CLIP: {agent_lora_config["strength_clip"]})', style="dim bright_blue")
                            
                            if agent_lora_config.get("trigger"):
                                confirm_text.append(f'\nRequired trigger words: "{agent_lora_config["trigger"]}"', style="dim bright_blue")
                            
                            # Show optional trigger words if available
                            if agent_lora_config.get("trigger_words", {}).get("optional"):
                                optional_words = ", ".join(agent_lora_config["trigger_words"]["optional"])
                                confirm_text.append(f'\nOptional words: "{optional_words}"', style="dim bright_cyan")
                            
                            # Show essential traits if available
                            if agent_lora_config.get("essential_traits"):
                                essential = ", ".join(agent_lora_config["essential_traits"])
                                confirm_text.append(f'\nEssential traits: {essential}', style="dim white")
                        
                        confirm_panel = Panel(
                            confirm_text,
                            title="[bold bright_white]LoRA Confirmation[/bold bright_white]",
                            border_style="white",
                            box=box.ROUNDED,
                            padding=(1, 2),
                        )
                        console.console.print(confirm_panel)
                        print()
                        
                        if max_choice == 1 and len(selected_loras_with_strength) == 1:
                            # Auto-confirm for single model with single option
                            return agent_lora_config
                        else:
                            confirm = input("  Proceed with this LoRA configuration? (y/n): ").strip().lower()
                            if confirm in ['y', 'yes', '']:
                                return agent_lora_config
                            elif confirm in ['n', 'no']:
                                print("  Let's try again...")
                                print()
                                continue
                            else:
                                print("  Please enter 'y' for yes or 'n' for no.")
                                continue
                    
                    # If we reach here, there was an error in selection
                    continue
                        
                except KeyboardInterrupt:
                    print("\n\nGoodbye!")
                    sys.exit(0)
                except EOFError:
                    print("\n\nGoodbye!")
                    sys.exit(0)

    def _get_lora_selection_group_mode(self, available_loras: Dict[str, Any], model_type: str) -> Dict[str, Any]:
        """
        Handle LoRA selection for 'group' mode.
        
        Args:
            available_loras: Dictionary of available LoRAs.
            model_type: The model type being used.
            
        Returns:
            Dict[str, Any]: The LoRA configuration for 'group' mode.
        """
        # Create beautiful LoRA selection panel
        lora_text = Text()
        lora_text.append(f"Choose LoRA models for {model_type.title()} (Group Mode):\n\n", style="bold bright_magenta")
        lora_text.append("Available LoRA Models:\n", style="bold white")
        
        # Display each LoRA option from the JSON configuration
        for choice_id, lora_config in available_loras.items():
            lora_text.append(f"  {choice_id}. ", style="bright_yellow")
            lora_text.append(lora_config["name"], style="yellow")
            lora_text.append(f" - {lora_config['description']}", style="white")
            
            # Show trigger words
            if lora_config.get("display_trigger"):
                lora_text.append(f" (trigger: '{lora_config['display_trigger']}')", style="dim white")
            lora_text.append("\n", style="white")
            
            # Show essential traits for character LoRAs
            if lora_config.get("essential_traits"):
                essential = ", ".join(lora_config["essential_traits"])
                lora_text.append(f"     Essential traits: {essential}\n", style="dim white")
            
            # Show default strength values
            strength_model = lora_config.get("strength_model", 1.0)
            strength_clip = lora_config.get("strength_clip", 1.0)
            lora_text.append(f"     Default strength - Model: {strength_model}, CLIP: {strength_clip}\n", style="dim cyan")
        
        lora_text.append(f"\nNote: ", style="bold bright_blue")
        lora_text.append(f"{get_model_description(model_type)}\n", style="blue")
        lora_text.append("      GROUP MODE: First select required LoRAs (always used), then optional LoRAs (LLM decides per image).\n", style="blue")
        lora_text.append("      This gives dynamic variation while maintaining core style elements.", style="blue")
        
        lora_panel = Panel(
            lora_text,
            title="[bold bright_magenta]Group Mode LoRA Selection[/bold bright_magenta]",
            border_style="magenta",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.console.print(lora_panel)
        print()
        
        # Determine the choice range
        max_choice = max(int(k) for k in available_loras.keys())
        choice_range = f"1-{max_choice}" if max_choice > 1 else "1"
        
        # Step 1: Get required LoRAs
        required_loras = self._get_required_loras(available_loras, choice_range, model_type)
        if not required_loras:
            print("  No required LoRAs selected. Defaulting to all mode.")
            return self._get_lora_selection_all_mode(available_loras, model_type)
        
        # Step 2: Get optional LoRAs
        optional_loras = self._get_optional_loras(available_loras, choice_range, model_type, required_loras)
        
        # Step 3: Combine and return group mode configuration
        return self._prepare_group_mode_config(required_loras, optional_loras, model_type)
        
    def _get_required_loras(self, available_loras: Dict[str, Any], choice_range: str, model_type: str) -> List[Dict[str, Any]]:
        """Get required LoRAs that will always be used."""
        required_text = Text()
        required_text.append("Required LoRAs (Always Used):\n\n", style="bold bright_green")
        required_text.append("These LoRAs will be applied to EVERY image generated.\n", style="white")
        required_text.append("Use this for core style elements you want consistent across all images.\n\n", style="white")
        required_text.append("Selection Examples:\n", style="bold bright_blue")
        required_text.append("  Single required: ", style="bright_white")
        required_text.append("2", style="green")
        required_text.append(" (LoRA #2 always used)\n", style="white")
        required_text.append("  Multiple required: ", style="bright_white")
        required_text.append("1,2", style="green")
        required_text.append(" (LoRAs #1 and #2 always used)\n", style="white")
        required_text.append("  With strength: ", style="bright_white")
        required_text.append("2:0.8", style="green")
        required_text.append(" (LoRA #2 with 0.8 strength always used)\n", style="white")
        required_text.append("  Skip required: ", style="bright_white")
        required_text.append("none", style="green")
        required_text.append(" (no required LoRAs, pure optional mode)", style="white")
        
        required_panel = Panel(
            required_text,
            title="[bold bright_green]Step 1: Required LoRAs[/bold bright_green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.console.print(required_panel)
        print()
        
        while True:
            try:
                choice_input = input(f"  Select required LoRAs ({choice_range}) or 'none': ").strip()
                
                if choice_input.lower() == 'none':
                    return []
                
                if not choice_input:
                    print("  Please enter LoRA selections or 'none'.")
                    continue
                
                # Parse the input for multiple LoRAs with optional strength values
                selected_loras = self._parse_lora_selections(choice_input, available_loras, model_type)
                
                if selected_loras is None:
                    continue  # Error in parsing, try again
                
                if not selected_loras:
                    print("  No valid LoRAs selected. Please try again.")
                    continue
                
                # Confirm required LoRAs
                confirm_text = Text()
                confirm_text.append("Required LoRAs (always used):\n", style="bold white")
                for i, lora_config in enumerate(selected_loras, 1):
                    confirm_text.append(f"  {i}. ", style="bright_yellow")
                    confirm_text.append(f'{lora_config["name"]}', style="italic bright_green")
                    confirm_text.append(f' (Model: {lora_config["strength_model"]}, CLIP: {lora_config["strength_clip"]})', style="dim bright_blue")
                    if lora_config.get("trigger"):
                        confirm_text.append(f'\n     Trigger: "{lora_config["trigger"]}"', style="dim cyan")
                    confirm_text.append("\n")
                
                confirm_panel = Panel(
                    confirm_text,
                    title="[bold bright_white]Required LoRAs Confirmation[/bold bright_white]",
                    border_style="white",
                    box=box.ROUNDED,
                    padding=(1, 2),
                )
                console.console.print(confirm_panel)
                print()
                
                confirm = input("  Proceed with these required LoRAs? (y/n): ").strip().lower()
                if confirm in ['y', 'yes', '']:
                    return selected_loras
                elif confirm in ['n', 'no']:
                    print("  Let's try again...")
                    print()
                    continue
                else:
                    print("  Please enter 'y' for yes or 'n' for no.")
                    continue
                    
            except (KeyboardInterrupt, EOFError):
                print("\n\nGoodbye!")
                sys.exit(0)
                
    def _get_optional_loras(
        self, 
        available_loras: Dict[str, Any], 
        choice_range: str, 
        model_type: str, 
        required_loras: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get optional LoRAs that LLM will decide per image."""
        optional_text = Text()
        optional_text.append("Optional LoRAs (LLM Decides Per Image):\n\n", style="bold bright_yellow")
        optional_text.append("These LoRAs will be dynamically selected by the LLM for each image.\n", style="white")
        optional_text.append("The LLM will choose which ones to use based on scene content and LoRA descriptions.\n\n", style="white")
        optional_text.append("For example, if you have 3 images:\n", style="dim white")
        optional_text.append("  • Image 1 might use: Required + Optional LoRA #3\n", style="dim white")
        optional_text.append("  • Image 2 might use: Required + Optional LoRAs #5, #7\n", style="dim white")
        optional_text.append("  • Image 3 might use: Required + Optional LoRAs #3, #5, #7\n\n", style="dim white")
        optional_text.append("Selection Examples:\n", style="bold bright_blue")
        optional_text.append("  Multiple optional: ", style="bright_white")
        optional_text.append("3,5,7", style="yellow")
        optional_text.append(" (LoRAs #3, #5, #7 available for LLM selection)\n", style="white")
        optional_text.append("  With strength: ", style="bright_white")
        optional_text.append("3:0.7,5:0.6,7", style="yellow")
        optional_text.append(" (different strengths for each optional LoRA)\n", style="white")
        optional_text.append("  Skip optional: ", style="bright_white")
        optional_text.append("none", style="yellow")
        optional_text.append(" (no optional LoRAs, required only mode)", style="white")
        
        optional_panel = Panel(
            optional_text,
            title="[bold bright_yellow]Step 2: Optional LoRAs[/bold bright_yellow]",
            border_style="yellow",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.console.print(optional_panel)
        print()
        
        while True:
            try:
                choice_input = input(f"  Select optional LoRAs ({choice_range}) or 'none': ").strip()
                
                if choice_input.lower() == 'none':
                    return []
                
                if not choice_input:
                    print("  Please enter LoRA selections or 'none'.")
                    continue
                
                # Parse the input for multiple LoRAs with optional strength values
                selected_loras = self._parse_lora_selections(choice_input, available_loras, model_type)
                
                if selected_loras is None:
                    continue  # Error in parsing, try again
                
                if not selected_loras:
                    print("  No valid LoRAs selected. Please try again.")
                    continue
                
                # Check for overlap with required LoRAs
                required_names = {lora["name"] for lora in required_loras}
                overlapping_loras = [lora for lora in selected_loras if lora["name"] in required_names]
                
                if overlapping_loras:
                    print("  Warning: Some optional LoRAs are already in required list:")
                    for lora in overlapping_loras:
                        print(f"    - {lora['name']}")
                    print("  Please choose different optional LoRAs.")
                    continue
                
                # Confirm optional LoRAs
                confirm_text = Text()
                confirm_text.append("Optional LoRAs (LLM decides per image):\n", style="bold white")
                for i, lora_config in enumerate(selected_loras, 1):
                    confirm_text.append(f"  {i}. ", style="bright_yellow")
                    confirm_text.append(f'{lora_config["name"]}', style="italic bright_yellow")
                    confirm_text.append(f' (Model: {lora_config["strength_model"]}, CLIP: {lora_config["strength_clip"]})', style="dim bright_blue")
                    if lora_config.get("trigger"):
                        confirm_text.append(f'\n     Trigger: "{lora_config["trigger"]}"', style="dim cyan")
                    confirm_text.append("\n")
                
                confirm_panel = Panel(
                    confirm_text,
                    title="[bold bright_white]Optional LoRAs Confirmation[/bold bright_white]",
                    border_style="white",
                    box=box.ROUNDED,
                    padding=(1, 2),
                )
                console.console.print(confirm_panel)
                print()
                
                confirm = input("  Proceed with these optional LoRAs? (y/n): ").strip().lower()
                if confirm in ['y', 'yes', '']:
                    return selected_loras
                elif confirm in ['n', 'no']:
                    print("  Let's try again...")
                    print()
                    continue
                else:
                    print("  Please enter 'y' for yes or 'n' for no.")
                    continue
                    
            except (KeyboardInterrupt, EOFError):
                print("\n\nGoodbye!")
                sys.exit(0)
                
    def _parse_lora_selections(
        self, 
        choice_input: str, 
        available_loras: Dict[str, Any], 
        model_type: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Parse LoRA selections with strength values."""
        selected_loras = []
        
        # Split by comma to get individual selections
        selections = [s.strip() for s in choice_input.split(',')]
        
        for selection in selections:
            if ':' in selection:
                # Format: "2:0.8" or "2:0.8,0.9"
                parts = selection.split(':', 1)
                lora_choice = parts[0].strip()
                strength_part = parts[1].strip()
                
                # Parse strength values
                strength_model, strength_clip = parse_strength_input(strength_part)
                if strength_model is None or strength_clip is None:
                    print(f"  Invalid strength values for LoRA {lora_choice}. Please use values between 0.1 and 1.0.")
                    return None
            else:
                # Just LoRA choice, use default strength
                lora_choice = selection.strip()
                strength_model, strength_clip = 1.0, 1.0
            
            # Get the LoRA configuration
            lora_config = get_lora_by_choice(model_type, lora_choice)
            if lora_config:
                # Ensure trigger key exists
                lora_config = self._ensure_trigger(lora_config)
                # Override with custom strength values
                lora_config["strength_model"] = strength_model
                lora_config["strength_clip"] = strength_clip
                selected_loras.append(lora_config)
            else:
                max_choice = max(int(k) for k in available_loras.keys())
                choice_range = f"1-{max_choice}" if max_choice > 1 else "1"
                print(f"  Invalid LoRA choice: {lora_choice}. Please enter a number from {choice_range}.")
                return None
        
        return selected_loras
        
    def _prepare_group_mode_config(
        self, 
        required_loras: List[Dict[str, Any]], 
        optional_loras: List[Dict[str, Any]], 
        model_type: str
    ) -> Dict[str, Any]:
        """Prepare group mode configuration with required and optional LoRAs."""
        # Create group mode configuration
        group_config = {
            "mode": "group",
            "model_type": model_type,
            "required_loras": required_loras,
            "optional_loras": optional_loras,
            "required_trigger": "",
            "optional_descriptions": []
        }
        
        # Combine required LoRA triggers
        required_triggers = []
        for lora in required_loras:
            if lora.get("trigger"):
                required_triggers.append(lora["trigger"])
        group_config["required_trigger"] = ", ".join(required_triggers)
        
        # Collect optional LoRA descriptions for LLM
        for lora in optional_loras:
            description = {
                "name": lora["name"],
                "description": lora["description"],
                "trigger": lora.get("trigger", ""),  # Use get with default value
                "strength_model": lora["strength_model"],
                "strength_clip": lora["strength_clip"]
            }
            group_config["optional_descriptions"].append(description)
        
        # Show final configuration
        final_text = Text()
        final_text.append("Group Mode Configuration:\n\n", style="bold bright_white")
        
        final_text.append("Required LoRAs (always used):\n", style="bold bright_green")
        if required_loras:
            for i, lora in enumerate(required_loras, 1):
                final_text.append(f"  {i}. {lora['name']}", style="bright_green")
                final_text.append(f" (Model: {lora['strength_model']}, CLIP: {lora['strength_clip']})", style="dim bright_blue")
                if lora.get("trigger"):
                    final_text.append(f" - Trigger: '{lora['trigger']}'", style="dim cyan")
                final_text.append("\n")
        else:
            final_text.append("  None\n", style="dim white")
        
        final_text.append("\nOptional LoRAs (LLM decides per image):\n", style="bold bright_yellow")
        if optional_loras:
            for i, lora in enumerate(optional_loras, 1):
                final_text.append(f"  {i}. {lora['name']}", style="bright_yellow")
                final_text.append(f" (Model: {lora['strength_model']}, CLIP: {lora['strength_clip']})", style="dim bright_blue")
                if lora.get("trigger"):
                    final_text.append(f" - Trigger: '{lora['trigger']}'", style="dim cyan")
                final_text.append("\n")
        else:
            final_text.append("  None\n", style="dim white")
        
        final_text.append(f"\nTotal LoRA pool: {len(required_loras) + len(optional_loras)} LoRAs", style="bold bright_white")
        
        final_panel = Panel(
            final_text,
            title="[bold bright_white]Group Mode Configuration Complete[/bold bright_white]",
            border_style="white",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.console.print(final_panel)
        print()
        
        return group_config