# GameMediaTool/project_data.py
import os
import json
from tools.logger import get_logger

# الاستيرادات اللازمة
from utils.json_aggregator import save_json
from tools.rpy_generator import generate_event_rpy
from utils.file_ops import ensure_folder

logger = get_logger("Project")


class Project:
    def __init__(self):
        self.source_type = None
        self.source_video_path = None
        self.source_image_paths = []
        self.video_duration = 0
        self.character_name = ""
        self.character_type = "Girl"
        self.final_output_path = ""
        self.yolo_analysis_cache = {}
        # Whether the current user/project has Pro features enabled
        self.pro_user = False
        # Add-on mode: when True, this project represents an add-on to an existing pack
        self.addon_mode = False
        # Components selected for add-on (e.g., ['fullbody', 'body', 'events'])
        self.addon_components = []
        # تم تحديث export_data ليحتوي على الحقول التي نستخدمها في المشروع
        self.export_data = {
            # الصور التي تم تحديدها واعتمادها من PhotoMaker
            "approved_images": [],
            # الصور النهائية التي تم معالجتها بالكامل
            "final_images": [],
            # مقاطع الفيديو التي تم تعليمها (Tagged) من VidMaker
            "tagged_videos": {},
            # شوتات الصور
            "photoshoots": {},
            # شوتات الفيديو
            "videoshoots": {},
            # جميع مقاطع الفيديو التي تم قصها (Clips) من VidMaker
            "all_created_clips": [],
            # [جديد] لتضمين ملفات الشوتس المشتركة
            "_shared_photoshoots": {},
            "_shared_videoshoots": {},
        }
        logger.info("Project instance created with default export data structure")

    # قائمة بملحقات الملفات التي نريد تحميلها
    MEDIA_EXTENSIONS = (".webp", ".png", ".jpg", ".jpeg", ".webm", ".mp4")

    def _scan_directory_for_media_absolute(self, directory_path):
        """
        Scans a directory recursively for media files and returns their ABSOLUTE paths.
        """
        media_paths = set()
        if not directory_path or not os.path.isdir(directory_path):
            return media_paths

        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith(self.MEDIA_EXTENSIONS):
                    media_paths.add(os.path.join(root, file))

        return media_paths

    def get_asset_file_paths(self):
        """
        [FIXED] Gathers all media paths from: Source, Temporary, and Exported Data.
        """
        all_paths = set()

        # مسار مجلد 'game' الذي يحوي الأصول النهائية
        game_folder = os.path.join(self.final_output_path, "game")

        logger.debug(
            f"Scanning Assets. final_output_path is set to: {self.final_output_path}"
        )  # <--- أضف هذا السطر

        # --------------------------------------------------------
        # 1. Source Media (الميديا الأصلية)
        # --------------------------------------------------------
        if (
            self.source_type == "video"
            and self.source_video_path
            and os.path.exists(self.source_video_path)
        ):
            all_paths.add(self.source_video_path)
        elif self.source_type == "folder" and self.source_image_paths:
            for img_path in self.source_image_paths:
                if os.path.exists(img_path):
                    all_paths.add(img_path)

        # --------------------------------------------------------
        # 2. Temporary Processed Media (الميديا المعالجة والمؤقتة في مجلد temp)
        # --------------------------------------------------------
        if self.final_output_path:
            temp_dir = os.path.join(self.final_output_path, "temp")
            temp_media_paths = self._scan_directory_for_media_absolute(temp_dir)
            all_paths.update(temp_media_paths)
            logger.debug(f"Found {len(temp_media_paths)} temporary assets in: {temp_dir}")

        # --------------------------------------------------------
        # 3. Explicitly Exported Data (الميديا النهائية - مسارات Ren'Py النسبية)
        # --------------------------------------------------------

        # أ. مسارات الصور النهائية التي تم تصديرها من PhotoMaker (المسارات التي ستكون داخل مجلد 'game')
        final_images = self.export_data.get("final_images", [])
        for path in final_images:
            all_paths.add(path)

        # ب. مقاطع الفيديو التي تم تعليمها (Tagged Clips) من VidMaker
        for path in self.export_data.get("tagged_videos", {}).keys():
            all_paths.add(path)

        # ج. جميع مقاطع الفيديو التي تم قصها (Clips) - يتم استخدامها في ShootMaker
        for clip_path in self.export_data.get("all_created_clips", []):
            all_paths.add(clip_path)

        # د. مسارات الأصول داخل الشوتات (Photoshoots/Videoshoots)
        # تم تعديل الكود ليتوافق مع هيكل ShootMakerWorkflow الذي يستخدم 'media_items'
        for shoot_key in [
            "photoshoots",
            "videoshoots",
            "_shared_photoshoots",
            "_shared_videoshoots",
        ]:
            for shoot_data in self.export_data.get(shoot_key, {}).values():
                # Shoot data uses 'media_items' list, which contains dicts with 'source_path'
                for item in shoot_data.get("media_items", []):
                    if isinstance(item, dict) and item.get("source_path"):
                        all_paths.add(item["source_path"])

        # تصفية وإرجاع قائمة بالمسارات الفريدة
        # التأكد من أن المسار هو سلسلة نصية وغير فارغ قبل الإرجاع
        return sorted([os.path.normpath(p) for p in all_paths if p and isinstance(p, str)])

    def has_tagged_vids(self):
        return bool(self.export_data.get("tagged_videos"))

    def is_ready_for_export(self):
        return any(self.export_data.values())

    def reset(self):
        self.__init__()

    # ************************************************************
    # * الدالة المحدثة لحفظ ملفات الحدث (.json و .rpy)             *
    # ************************************************************
    # بما أن الدالة موجودة بالفعل في main_window، أزلنا 'save_event_files' من هنا
    # لكن سنعيدها لتكون في مكانها الصحيح في كلاس Project
    def save_event_files(self, event_name, event_config_data, event_script_data):
        """
        Saves the event configuration (.json) and generates the Ren'Py script (.rpy).
        """
        if not self.final_output_path:
            logger.error("Final output path is not set. Cannot save event files.")
            return False

        # 1. تحديد مسار المجلد الخاص بهذا الحدث
        event_pack_folder = os.path.join(self.final_output_path, "game", "events", event_name)
        ensure_folder(event_pack_folder)

        success_rpy = False
        success_json = False

        # 2. حفظ ملف الكونفيج (event_config.json)
        json_file_path = os.path.join(event_pack_folder, f"event_{event_name}.json")
        try:
            # دمج الكونفيج والسكريبت لحفظهما في ملف JSON واحد
            full_event_data = {**event_config_data, "script": event_script_data}
            save_json(full_event_data, json_file_path)
            success_json = True
            logger.info(f"Event JSON data saved to: {json_file_path}")
            # Add to export_data for inclusion in final pack
            self.export_data.setdefault("events", {})[event_name] = full_event_data
        except Exception as e:
            logger.error(f"Failed to save event JSON data: {e}")

        # 3. توليد وحفظ ملف Ren'Py (.rpy)
        if isinstance(event_script_data, str):
            # If event_script_data is already the RPY content string, save it directly
            rpy_file_path = os.path.join(event_pack_folder, f"event_{event_name}.rpy")
            try:
                with open(rpy_file_path, "w", encoding="utf-8") as f:
                    f.write(event_script_data)
                success_rpy = True
                logger.info(f"Event RPY script saved to: {rpy_file_path}")
            except Exception as e:
                logger.error(f"Failed to save event RPY script: {e}")
                success_rpy = False
        else:
            # Assume it's structured data, generate RPY
            rpy_file_path = generate_event_rpy(
                event_config=event_config_data,
                event_script_data=event_script_data,
                event_folder=event_pack_folder,
            )
            if rpy_file_path:
                success_rpy = True

        return success_json and success_rpy
