# GameMediaTool/media_exporter.py

import os, sys, shutil, json, subprocess
from typing import Dict, Any, List
from PIL import Image
import cv2
from tools.logger import get_logger
import re
from tools.rpy_generator import generate_custom_traits_rpy, generate_event_rpy
from utils.file_ops import ensure_folder, sanitize_filename
from tools.background_remover import remove_background

logger = get_logger("MediaExporter")
# يجب تعديل مسار FFMPEG ليتناسب مع بيئتك (F:/ffmpeg-8.0-essentials_build/bin/ffmpeg.exe)
if getattr(sys, "frozen", False):
    base_dir = sys._MEIPASS
    FFMPEG_PATH = os.path.join(base_dir, "ffmpeg.exe")
else:
    FFMPEG_PATH = "F:/ffmpeg-8.0-essentials_build/bin/ffmpeg.exe"
# Constants for image resizing
SHOOT_WIDTH = 1920
SHOOT_HEIGHT = 1080

# --- Training Data Pool Paths ---
# هذه المسارات تتطابق مع المسارات المحددة في TrainerManager.py
CNN_POOL_DIR = "assets/cnn_data_pool"
CNN_POOL_JSON = os.path.join(CNN_POOL_DIR, "cnn_pool_data.json")

YOLO_POOL_DIR = "assets/yolo_data_pool"
YOLO_IMAGES_POOL = os.path.join(YOLO_POOL_DIR, "images")
YOLO_LABELS_POOL = os.path.join(YOLO_POOL_DIR, "labels")


# --- Helper functions ---
def _run_ffmpeg_command(command):
    """Runs an FFmpeg command in a subprocess."""
    try:
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(command, check=True, capture_output=True, text=True, startupinfo=startupinfo)
        return True, ""
    except Exception as e:
        logger.error(f"FFmpeg command failed: {e}")
        return False, str(e)


def _convert_to_webm(input_path, output_path, size_limit_mb=4):
    """Converts a video file to WebM (VP9/Opus) format with a size limit."""
    size_limit_bytes = size_limit_mb * 1024 * 1024
    command = [
        FFMPEG_PATH,
        "-i",
        str(input_path),
        "-c:v",
        "libvpx-vp9",
        "-crf",
        "34",
        "-b:v",
        "0",
        "-c:a",
        "libopus",
        "-b:a",
        "96k",
        "-fs",
        str(size_limit_bytes),
        str(output_path),
        "-y",
    ]
    success, error = _run_ffmpeg_command(command)
    if success:
        logger.info(f"  - Converted: {os.path.basename(output_path)}")
    return success


def _create_thumbnail(video_path, thumb_path):
    """Creates a thumbnail image (first frame) from a video file."""
    if not _run_ffmpeg_command(
        [
            FFMPEG_PATH,
            "-ss",
            "00:00:01",
            "-i",
            str(video_path),
            "-vframes",
            "1",
            "-q:v",
            "90",
            str(thumb_path),
            "-y",
        ]
    )[0]:
        logger.warning(f"  - Could not create thumbnail for: {os.path.basename(video_path)}")


def _copy_and_convert_to_webp(source_path, dest_path):
    """Copies an image and converts it to lossless WebP format."""
    try:
        if not os.path.exists(source_path):
            logger.warning(f"Source not found for webp: {source_path}")
            return False
        img = Image.open(source_path).convert("RGBA")
        ensure_folder(os.path.dirname(dest_path))
        img.save(dest_path, "webp", lossless=True)
        return True
    except Exception as e:
        logger.error(f"Failed webp conversion {source_path}: {e}")
        return False


def _resize_and_convert_shoot_image(source_path, dest_path):
    """Resizes wide images for shoots to 1920x1080 and converts to webp."""
    try:
        if not os.path.exists(source_path):
            logger.warning(f"Shoot image source not found: {source_path}")
            return False
        img = Image.open(source_path).convert("RGB")

        # Only resize if the image is 'wide' (width > height)
        if img.width > img.height:
            target_size = (SHOOT_WIDTH, SHOOT_HEIGHT)
            img = img.resize(target_size, Image.Resampling.LANCZOS)

        ensure_folder(os.path.dirname(dest_path))
        # Ensure the extension is webp
        base_name, _ = os.path.splitext(dest_path)
        dest_path_webp = f"{base_name}.webp"

        img.save(dest_path_webp, "webp", quality=90)
        return True
    except Exception as e:
        logger.error(f"Failed shoot image conversion {source_path}: {e}")
        return False


# --- Export functions ---


def _collect_training_data(approved_images: List[Dict[str, Any]], pipeline: Any):
    """
    يجمع الأصول المعتمدة في مجلدات CNN و YOLO Pool لتدريب النماذج.
    """
    if not approved_images:
        return

    logger.info("Collecting assets for AI training pools...")
    ensure_folder(CNN_POOL_DIR)
    ensure_folder(YOLO_IMAGES_POOL)
    ensure_folder(YOLO_LABELS_POOL)

    cnn_pool_data = {}
    cnn_collected = 0
    yolo_collected = 0

    for asset in approved_images:
        src_path = asset.get("path")
        final_name = asset.get("final_name")  # e.g. 'plain_bra_001.png'
        cat = asset.get("asset_category")  # e.g. 'clothing'
        clothing_type = asset.get("cover_type")  # e.g. 'bra' (لـ CNN)
        yolo_label = asset.get("yolo_label_path")  # مسار ملف YOLO .txt (لـ YOLO)

        if not all([src_path, final_name, cat]) or not os.path.exists(src_path):
            continue

        base_name, ext = os.path.splitext(final_name)
        # حفظ بصيغة PNG في الـ Pool لضمان الجودة
        pool_filename = f"{base_name}.png"

        # 1. تجميع بيانات CNN (لتصنيف الملابس - clothing/bodypart)
        if cat == "clothing" and clothing_type:
            dest_path = os.path.join(CNN_POOL_DIR, pool_filename)
            # نسخ الصورة إلى مجلد CNN Pool
            shutil.copy2(src_path, dest_path)
            # تخزين الفئة في ملف JSON
            cnn_pool_data[pool_filename] = clothing_type  # استخدام 'bra' أو 'panties' كفئة
            cnn_collected += 1

        # 2. تجميع بيانات YOLO (للكشف عن الأجسام)
        if yolo_label and os.path.exists(yolo_label):
            # نسخ الصورة إلى مجلد YOLO Images Pool
            shutil.copy2(src_path, os.path.join(YOLO_IMAGES_POOL, pool_filename))

            # نسخ ملف الـ Label إلى مجلد YOLO Labels Pool
            label_filename = f"{base_name}.txt"
            shutil.copy2(yolo_label, os.path.join(YOLO_LABELS_POOL, label_filename))
            yolo_collected += 1

    # حفظ ملف CNN Pool JSON
    if cnn_pool_data:
        try:
            with open(CNN_POOL_JSON, "w", encoding="utf-8") as f:
                json.dump(cnn_pool_data, f, indent=4)
            logger.info(f"CNN Pool Data saved: {cnn_collected} items.")
        except Exception as e:
            logger.error(f"Failed to save CNN pool JSON: {e}")

    logger.info(f"YOLO Pool Data collected: {yolo_collected} images/labels pairs.")


def _export_vids(vid_dict: Dict[str, Any], pack_root: str):
    """Exports and converts loose video files (non-shoot)."""
    if not vid_dict:
        return
    vids_dir = os.path.join(pack_root, "vids")
    ensure_folder(vids_dir)
    logger.info(f"Exporting {len(vid_dict)} final videos...")
    for _, data in vid_dict.items():
        # Uses 'final_filename' which is assumed to be correctly tagged (using underscores)
        if "final_filename" in data:
            # Note: _convert_to_webm handles conversion and logging internally
            _convert_to_webm(data["source_path"], os.path.join(vids_dir, data["final_filename"]))


def _export_assets(approved_images: List[Dict[str, Any]], pack_root: str):
    """Exports and converts static image assets (body parts, full bodies, etc.) to webp."""
    if not approved_images:
        return
    logger.info(f"Exporting {len(approved_images)} image assets...")

    # تحديد المجلدات الرئيسية تحت جذر الحزمة
    body_dir = os.path.join(pack_root, "body_images")
    full_dir = os.path.join(pack_root, "fullbody_images")
    clothing_base_dir = os.path.join(pack_root, "clothing")

    for asset in approved_images:
        src, name, cat = asset.get("path"), asset.get("final_name"), asset.get("asset_category")
        if not all([src, name, cat]):
            continue

        base_name = os.path.splitext(name)[0]
        dest_path = ""

        # الأصول التي لا تحتاج لمسار متفرع (Full Body & Body Parts)
        if cat in ("bodypart", "fullbody"):
            dest_name = f"{sanitize_filename(base_name)}.webp"

            if cat == "bodypart":
                dest_path = os.path.join(body_dir, dest_name)
            elif cat == "fullbody":
                dest_path = os.path.join(full_dir, dest_name)

        # [MODIFIED LOGIC] - جميع أصول الملابس تستخدم المنطق المتفرع الجديد
        elif cat == "clothing":
            # يجب أن يتم تمرير المسارات الفرعية من ImageWorkshopPanel (FinalProcessorWorker)
            # هذه المفاتيح تأتي من الـ Worker بعد التعديل
            body_part_cover = asset.get("body_part_cover")  # e.g., pussy_cover, ass_cover
            cover_type = asset.get("cover_type")  # e.g., panties, bra

            if body_part_cover and cover_type:
                # final_name يتميز بالشرطة السفلية بين الكلمات (مثال: plain_bra)
                final_clothing_name = f"{base_name}.webp"

                # المسار سيكون: clothing / body_part_cover / cover_type / final_name
                # مثال: clothing/pussy_cover/panties/plain_thong_001.webp
                dest_path = os.path.join(
                    clothing_base_dir, body_part_cover, cover_type, final_clothing_name
                )
            else:
                logger.warning(
                    f"Clothing asset {name} skipped: Missing path components (body_part_cover/cover_type) for folder placement."
                )
                continue

        if dest_path:
            # Apply background removal for specific tags just before exporting
            base_type = asset.get("base_type", "")
            asset_category = asset.get("asset_category", "")
            if base_type in ["face", "portrait", "tportrait"] or asset_category == "fullbody":
                try:
                    # Load image
                    img = cv2.imread(src, cv2.IMREAD_UNCHANGED)
                    if img is not None:
                        # Apply background removal
                        img_with_alpha = remove_background(img)
                        # Save to temp path with alpha
                        temp_path = src.replace('.png', '_bg_removed.png')
                        cv2.imwrite(temp_path, img_with_alpha)
                        src = temp_path  # Use the modified image for export
                        logger.info(f"  - Applied background removal to: {os.path.basename(src)}")
                except Exception as e:
                    logger.error(f"Failed to apply background removal to {src}: {e}")

            # نستخدم _copy_and_convert_to_webp التي تتأكد من أن dest_path ينتهي بـ .webp
            if _copy_and_convert_to_webp(src, dest_path):
                logger.info(f"  - Exported asset: {os.path.basename(dest_path)}")
            else:
                logger.warning(f"  - Failed to export asset: {os.path.basename(dest_path)}")


def _process_shoot_media(shoot_folder, media_list: List[Dict[str, Any]], is_photo_shoot: bool):
    """Processes and copies all media files for a single photoshoot or videoshoot."""
    if not media_list:
        return 0

    exported_count = 0
    for media in media_list:
        src = media.get("source_path")
        final_filename = media.get("final_filename")

        if not all([src, final_filename]):
            continue

        dest_path = os.path.join(shoot_folder, final_filename)

        try:
            if is_photo_shoot:
                # Photoshoots: resize wide images to 1920x1080 and convert to webp
                # NOTE: _resize_and_convert_shoot_image handles webp extension creation
                if _resize_and_convert_shoot_image(src, dest_path):
                    exported_count += 1
            else:  # Videoshoots: copy video and create thumbnail
                # Videoshoot: video must be .webm (assuming it was pre-converted or copied as is)
                shutil.copy2(src, dest_path)
                # Create thumbnail in the same folder
                thumb_name = os.path.splitext(final_filename)[0] + ".webp"
                _create_thumbnail(dest_path, os.path.join(shoot_folder, thumb_name))
                exported_count += 1
        except Exception as e:
            logger.error(f"  - Failed processing media {final_filename} for shoot: {e}")

    return exported_count


def _export_shoots(
    shoots_dict: Dict[str, Any], pack_root: str, shoot_type_folder: str, config_filename: str
):
    """Exports photoshoots or videoshoots configurations and media."""
    if not shoots_dict:
        return

    is_photo_shoot = "photo" in shoot_type_folder.lower()
    logger.info(f"Exporting {len(shoots_dict)} {shoot_type_folder}...")

    shoots_base_dir = os.path.join(pack_root, shoot_type_folder)
    ensure_folder(shoots_base_dir)

    for shoot_name, shoot_data in shoots_dict.items():
        shoot_folder = os.path.join(shoots_base_dir, shoot_name)
        ensure_folder(shoot_folder)

        # 1. Save shoot_config.json
        config_path = os.path.join(shoot_folder, config_filename)
        shoot_config = shoot_data.get("config", {})

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(shoot_config, f, indent=4)
            logger.info(f"  - Saved config for shoot: {shoot_name}")
        except Exception as e:
            logger.error(f"  - Failed config save for {shoot_name}: {e}")

        # 2. Process and copy media files
        media_list = shoot_data.get("media", [])

        # Ensure 'cover.webp' is copied if it exists in the media list
        cover_media = next(
            (
                m
                for m in media_list
                if m.get("final_filename") and m["final_filename"].endswith(",cover.webp")
            ),
            None,
        )
        if cover_media:
            # The cover image is tagged and renamed like other media, so process it with others.
            pass

        exported_count = _process_shoot_media(shoot_folder, media_list, is_photo_shoot)

        if exported_count > 0:
            logger.info(f"  - Processed {exported_count} media files for {shoot_name}")


def _export_events(project, pack_root: str):
    """Exports event configuration, RPY script, and media files for events."""
    events_data = project.export_data.get("events", {})
    if not events_data:
        logger.info("No events to export.")
        return

    logger.info(f"Exporting {len(events_data)} events...")
    events_base_dir = os.path.join(pack_root, "events")
    ensure_folder(events_base_dir)
    media_copied_for_event = set()  # Keep track of media copied per event

    for event_name, event_config in events_data.items():
        event_folder = os.path.join(events_base_dir, event_name)
        ensure_folder(event_folder)

        # 1. Save event_config.json
        config_path = os.path.join(event_folder, "event_config.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(event_config, f, indent=4)
            logger.info(f"  - Saved config for event: {event_name}")
        except Exception as e:
            logger.error(f"  - Failed config save {event_name}: {e}")

        # 2. Generate the RPY script
        event_script_data = event_config.get("script", {})  # Get script data saved from panel
        rpy_path = generate_event_rpy(event_config, event_script_data, event_folder)
        if not rpy_path:
            logger.error(f"  - Failed RPY generation for {event_name}")

        # 3. Copy used media files
        media_copied_for_event.clear()
        for stage_name, commands in event_script_data.items():
            for command in commands:
                if command.get("type") in ["show_image", "show_video"]:
                    source_path = command.get("path")
                    dest_filename = command.get("filename")

                    # NOTE: Event media names are generated based on event requirements and should retain original naming
                    if (
                        source_path
                        and dest_filename
                        and os.path.exists(source_path)
                        and dest_filename not in media_copied_for_event
                    ):
                        dest_path = os.path.join(event_folder, dest_filename)
                        try:
                            # Convert images to webp, copy videos as is
                            if command["type"] == "show_image":
                                # Ensure image conversion uses the webp extension for the destination path
                                base_name, _ = os.path.splitext(dest_path)
                                dest_webp_path = f"{base_name}.webp"

                                if _copy_and_convert_to_webp(source_path, dest_webp_path):
                                    media_copied_for_event.add(dest_filename)
                            else:  # show_video
                                shutil.copy2(source_path, dest_path)
                                media_copied_for_event.add(dest_filename)
                        except Exception as e:
                            logger.error(
                                f"  - Failed copying media {dest_filename} for {event_name}: {e}"
                            )
        if media_copied_for_event:
            logger.info(f"  - Copied {len(media_copied_for_event)} media files for {event_name}")


# --- Config and Main Export functions ---


def _create_main_config(pack_root, project):
    """Creates the main girl_config.json or mother_config.json file."""
    logger.info("Creating main config file...")
    parts = project.character_name.split(" ")
    first = parts[0]
    last = " ".join(parts[1:]) if len(parts) > 1 else ""
    char_id = sanitize_filename(project.character_name).lower().replace(" ", "_")
    config_data = {"id": char_id, "first_name": first, "last_name": last}
    details = project.character_details
    config_data.update(
        {
            "modder": details.get("modder", ""),
            "generate_additional_traits": details.get("generate_additional_traits", False),
            "area_sensitivity": details.get("area_sensitivity", {}),
            "traits": details.get("traits", []),
        }
    )
    export_data = project.export_data
    config_data["photoshoots"] = list(export_data.get("photoshoots", {}).keys())
    config_data["videoshoots"] = list(export_data.get("videoshoots", {}).keys())
    config_data["events"] = list(
        export_data.get("events", {}).keys()
    )  # [MODIFIED] Added events list
    config_filename = (
        "mother_config.json" if project.character_type == "Mother" else "girl_config.json"
    )
    with open(os.path.join(pack_root, config_filename), "w") as f:
        json.dump(config_data, f, indent=4)
    logger.info(f"Main config created: {config_filename}")


def export_media_pack(project, pipeline):
    """Main entry point for exporting the complete media pack."""
    char_name = project.character_name
    pack_root = os.path.join(project.final_output_path, sanitize_filename(char_name))
    # Ensure event definitions are pulled from the project export_data (only saved events)
    # project.export_data["events"] = pipeline.tag_manager.event_definitions  # Removed to avoid auto-inclusion of all definitions
    kwargs = project.export_data

    # 🆕 1. تجميع بيانات التدريب قبل التصدير والمسح
    _collect_training_data(kwargs.get("approved_images", []), pipeline)

    if os.path.exists(pack_root):
        shutil.rmtree(pack_root)
    ensure_folder(pack_root)
    logger.info(f"--- Starting Final Export for '{char_name}' to '{pack_root}' ---")

    # 2. التصدير الفعلي
    _export_vids(kwargs.get("tagged_videos", {}), pack_root)
    _export_assets(kwargs.get("approved_images", []), pack_root)

    # [FIX] Added _export_shoots function calls
    _export_shoots(
        kwargs.get("photoshoots", {}), pack_root, "photoshoots", "photoshoot_config.json"
    )
    _export_shoots(
        kwargs.get("_shared_photoshoots", {}),
        pack_root,
        "_shared_photoshoots",
        "shared_photoshoot_config.json",
    )
    _export_shoots(
        kwargs.get("videoshoots", {}), pack_root, "videoshoots", "videoshoot_config.json"
    )
    _export_shoots(
        kwargs.get("_shared_videoshoots", {}),
        pack_root,
        "_shared_videoshoots",
        "shared_videoshoot_config.json",
    )

    _export_events(project, pack_root)  # [NEW] Call the event export function

    if project.character_details.get("create_char_config", True):
        _create_main_config(pack_root, project)
    custom_traits = project.character_details.get("custom_traits", [])
    if custom_traits:
        generate_custom_traits_rpy(char_name, custom_traits, pack_root)

    logger.info("--- GIRL PACK EXPORT COMPLETED! ---")
    try:
        temp_project_folder = os.path.join("temp", sanitize_filename(char_name))
        if os.path.isdir(temp_project_folder):
            shutil.rmtree(temp_project_folder)
            logger.info(f"Cleaned up temp folder: {temp_project_folder}")
    except Exception as e:
        logger.error(f"Could not clean up temp folder: {e}")
    return pack_root
