import os
import json
from tools.logger import get_logger

logger = get_logger("TagManager")


class TagManager:
    def __init__(self, db_dir="database"):
        self.db_dir = db_dir
        self.asset_tags_dir = os.path.join(self.db_dir, "asset_tags")
        self._load_all_data()

    def _load_all_data(self):
        """Loads all JSON data files into memory."""
        self.shoots_config = self._load_json_file("shoots_config.json", self.db_dir)
        self.shoots_tags = self._load_json_file("shoots_tags.json", self.db_dir)
        self.vid_tags = self._load_json_file("vid_tags.json", self.db_dir)
        self.character_traits = self._load_json_file("character_traits.json", self.db_dir)
        self.clothing_definitions = self._load_json_file("clothing_definitions.json", self.db_dir)
        # [MODIFIED] تحميل تعريفات الأحداث مرة واحدة فقط
        self.event_definitions = self._load_json_file("event_definitions.json", self.db_dir)
        self.clothing_map = self._load_json_file("clothing.json", self.asset_tags_dir)
        self.bodyparts_map = self._load_json_file("bodyparts.json", self.asset_tags_dir)
        self.clothing_modifiers = self._load_json_file(
            "clothing_modifiers.json", self.asset_tags_dir
        )
        self.fullbody_map = self._load_json_file("fullbody.json", self.asset_tags_dir)

    def _load_json_file(self, filename, base_path):
        path = os.path.join(base_path, filename)
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                logger.info(f"Loaded '{filename}' successfully.")
                return data
        except FileNotFoundError:
            # If the file doesn't exist, create an empty one and return empty data
            logger.warning(f"File '{filename}' not found. Creating a new empty file.")
            os.makedirs(base_path, exist_ok=True)  # Ensure directory exists before creating file
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)
            return {}
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse '{filename}'. Error: {e}")
        return {}

    # --- [NEW/MODIFIED] Method to add and save event data ---
    def save_event_definition(self, event_name, event_data):
        """Adds an event definition to memory and saves the entire event_definitions.json file."""
        try:
            if not event_name:
                logger.error("Event name cannot be empty.")
                return False

            self.event_definitions[event_name] = event_data
            file_path = os.path.join(self.db_dir, "event_definitions.json")

            # التأكد من حفظ جميع تعريفات الأحداث المحدثة
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.event_definitions, f, indent=4)

            logger.info(
                f"Event '{event_name}' definition added/updated and saved to event_definitions.json"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save event definition: {e}")
            return False

    # ************************************************************
    # * [FIX] Renamed to match main_window.py's expected call    *
    # ************************************************************
    def get_all_traits(self):
        """Helper to get a flat list of all trait tags from character_traits.json.
        This replaces get_all_trait_tags to fix the AttributeError.
        """
        traits = ["--- Select Trait ---"]
        if not self.character_traits:
            return traits

        # character_traits structure: {Category: {SubCategory: {TraitName: {tag: 'tag_value', ...}}}}
        for category in self.character_traits.values():
            if isinstance(category, dict):
                for sub_cat in category.values():
                    if isinstance(sub_cat, dict):
                        for data in sub_cat.values():
                            if isinstance(data, dict) and data.get("tag"):
                                traits.append(data["tag"])

        return sorted(list(set(traits)))

    # --- Getters ---
    def get_shoots_config(self):
        return self.shoots_config

    def get_shoots_tags(self):
        return self.shoots_tags

    def get_vid_tags(self):
        return self.vid_tags

    def get_character_traits(self):
        return self.character_traits

    def get_clothing_definitions(self):
        return self.clothing_definitions

    def get_clothing_map(self):
        return self.clothing_map

    def get_bodyparts_map(self):
        return self.bodyparts_map

    def get_clothing_modifiers(self):
        return self.clothing_modifiers

    def get_fullbody_map(self):
        return self.fullbody_map

    def get_event_definitions(self):
        return self.event_definitions

    def add_new_tag(self, file_key: str, base_key: str, display_name: str, tag_value: str):
        # This function remains unchanged
        target_dict = None
        file_path = ""
        asset_tags_path = os.path.join(self.db_dir, "asset_tags")
        if file_key == "clothing":
            target_dict = self.clothing_map
            file_path = os.path.join(asset_tags_path, "clothing.json")
        else:
            logger.error(f"Add-new-tag is not supported for file key: {file_key}")
            return False
        if not target_dict:
            logger.error(f"Dictionary for '{file_key}' not loaded.")
            return False
        if base_key not in target_dict:
            target_dict[base_key] = {}
        if display_name in target_dict[base_key]:
            logger.warning(f"Tag '{display_name}' already exists in '{base_key}'.")
            return True
        target_dict[base_key][display_name] = tag_value
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(target_dict, f, indent=2, ensure_ascii=False)
            logger.info(
                f"Successfully added '{display_name}' to '{base_key}' in {os.path.basename(file_path)}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save updated JSON to {file_path}: {e}")
            return False
