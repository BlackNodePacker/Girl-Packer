import os
from textwrap import indent
from tools.logger import get_logger
from utils.file_ops import sanitize_filename, ensure_folder

logger = get_logger("RPY_Generator")

# --- Helper Functions ---

def _format_dict_for_rpy(data: dict) -> str:
    """Converts a dictionary to a string suitable for RPY Python blocks."""
    if not data: return "{}"
    parts = []
    for k, v in data.items():
        # Ensure strings are quoted, numbers/booleans are not
        if isinstance(v, (int, float, bool)):
            parts.append(f'"{k}": {v}')
        elif isinstance(v, str):
            # Escape quotes within the string value itself if necessary, then wrap in quotes
            escaped_v = v.replace('"', '\\"')
            parts.append(f'"{k}": "{escaped_v}"')
        else: # Handle other types like lists or nested dicts by stringifying
            parts.append(f'"{k}": {repr(v)}')
    return "{" + ", ".join(parts) + "}"

# --- Main Functions ---

def generate_custom_traits_rpy(character_name: str, custom_traits_data: list, output_dir: str) -> str:
    """Generates an RPY file defining custom traits for a character."""
    if not custom_traits_data: return None
    safe_char_name = sanitize_filename(character_name).lower().replace('_', '')
    rpy_content = f"# Generated Custom Traits for {character_name} by Girl Packer Tool\n\ninit -1 python:\n"
    trait_definitions = []
    
    for data in custom_traits_data:
        tag_name = data.get('tag_name')
        if not tag_name: continue
        
        base_mod_str = _format_dict_for_rpy(data.get('base_stat_modifiers', {}))
        growth_mod_str = _format_dict_for_rpy(data.get('stat_growth_multipliers', {}))
        
        trait_code = f'    database_traits["{tag_name}"] = Trait(\n'
        trait_code += f'        name="{tag_name}",\n'
        trait_code += f'        display_name="{data.get("display_name", tag_name)}",\n'
        trait_code += f'        description="{data.get("description", "A custom trait.")}",\n'
        trait_code += f'        base_stat_modifiers={base_mod_str},\n'
        trait_code += f'        stat_growth_multipliers={growth_mod_str},\n'
        trait_code += f'        rarity=0, girl_only=True\n'
        trait_code += f'    )\n'
        trait_definitions.append(trait_code)
        
    rpy_content += indent("\n".join(trait_definitions), "    ") + "\n"
    
    final_dir = os.path.join(output_dir, sanitize_filename(character_name))
    ensure_folder(final_dir)
    final_path = os.path.join(final_dir, f"zz_custom_{safe_char_name}_traits.rpy")
    
    try:
        with open(final_path, 'w', encoding='utf-8') as f:
            f.write(rpy_content)
        logger.info(f"Custom RPY script generated successfully at: {final_path}")
        return final_path
    except Exception as e:
        logger.error(f"Failed to write RPY file: {e}")
        return None

def generate_event_rpy(event_config: dict, event_script_data: dict, event_folder: str) -> str:
    """
    Generates the RPY script file for a specific event based on the visual editor data.

    Args:
        event_config (dict): The configuration data for the event (from event_config.json).
        event_script_data (dict): The structured script data {stage_name: [commands]}.
        event_folder (str): The specific folder for this event inside the final pack.

    Returns:
        str: The path to the generated RPY file, or None on failure.
    """
    event_name = event_config.get("event_name")
    # In the JSON example we used 'script' keys, let's derive stages from those keys
    stages = list(event_script_data.keys()) 
    
    if not event_name or not stages:
        logger.error("Cannot generate RPY: Event name or script stages missing.")
        return None

    rpy_content = f"# Generated Event Script for '{event_config.get('display_name', event_name)}' by Girl Packer Tool\n\n"

    # Define participants storage globally (or within the event function if it was a function call)
    # This setup assumes the event runner in the game sets current_event before jumping here.
    
    rpy_content += f"init python:\n"
    # Placeholder for the first participant's character object for easy dialogue reference
    rpy_content += f"    selected_girl = None\n\n" 

    # Generate labels and commands for each stage
    for stage_name in stages:
        rpy_content += f"label {event_name}_{stage_name}:\n"
        
        # Logic to fetch participants and set the selected_girl at the start of the event
        if stage_name == 'start':
             rpy_content += f"    # This label is the entry point, assume current_event is set.\n"
             rpy_content += f"    python:\n"
             rpy_content += f"        global selected_girl\n"
             rpy_content += f"        if current_event and current_event.name == '{event_name}':\n"
             rpy_content += f"            # Assumes the primary participant is the first in the list\n"
             rpy_content += f"            selected_girl = current_event.participants[0] if current_event.participants else None\n\n"
        
        commands = event_script_data.get(stage_name, [])
        if not commands:
            rpy_content += "    pass # No actions defined for this stage\n"

        for command in commands:
            cmd_type = command.get("type")
            
            if cmd_type == "text" or cmd_type == "dialogue":
                speaker = command.get("speaker", "Protagonist")
                text = command.get("text", "")
                
                # Logic to map speaker to Ren'Py character object
                if speaker.lower() == "protagonist":
                    # Assume 'protagonist' is defined as the narrator or player character in the main game files
                    rpy_content += f'    p "{text}"\n' # Using 'p' for protagonist/player
                elif speaker.lower() == "maya":
                    # Use the character object determined at the start of the event
                    rpy_content += f'    selected_girl.character "{text}"\n'
                else: 
                    # Use a custom, quoted speaker name (e.g., "Narrator")
                    rpy_content += f'    "{speaker}" "{text}"\n'

            elif cmd_type == "show_image":
                filename = command.get("filename", "")
                pose_id = command.get("pose_id", "default")
                # Example: $ current_event.show_image("fullbodyatheletic1.webp", pose="stretch_01")
                rpy_content += f'    $ current_event.show_image("{filename}", pose="{pose_id}")\n'

            elif cmd_type == "show_video":
                filename = command.get("filename", "")
                rpy_content += f'    $ current_event.show_video("{filename}")\n'

            elif cmd_type == "hide_all":
                rpy_content += f"    hide screen event_visuals\n" # Assuming a screen handles event visuals

            elif cmd_type == "go_to":
                target_stage = command.get("stage", "end")
                rpy_content += f"    jump {event_name}_{target_stage}\n" # Jump to the next label

            elif cmd_type == "finish_event":
                rpy_content += f"    $ renpy.call_return(current_event.finish_label)\n" # Standard call/return to end event execution

            elif cmd_type == "pause":
                rpy_content += f"    pause\n"
            
            # --- [FUTURE] Add Logic for Choices Here ---

        # End of stage: If not explicitly ended by jump/finish, return to caller (event manager)
        if not any(cmd.get("type") in ["go_to", "finish_event"] for cmd in commands):
             rpy_content += "    return\n"

        rpy_content += "\n" # Blank line between labels

    # Save the file
    safe_event_name = sanitize_filename(event_name)
    rpy_file_path = os.path.join(event_folder, f"{safe_event_name}.rpy")
    ensure_folder(event_folder)
    try:
        with open(rpy_file_path, 'w', encoding='utf-8') as f:
            f.write(rpy_content)
        logger.info(f"Successfully generated RPY script: {rpy_file_path}")
        return rpy_file_path
    except Exception as e:
        logger.error(f"Failed to write event RPY script {rpy_file_path}: {e}")
        return None