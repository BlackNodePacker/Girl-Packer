# GameMediaTool/gui/components/workers.py (Corrected Version with Train/Val Split)

import os
import shutil
import cv2
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QProcess, QProcessEnvironment, QTimer

from tools.frame_extractor import extract_frames
from tools.video_splitter import get_ffmpeg_split_commands
from tools.logger import get_logger
from utils.file_ops import sanitize_filename, ensure_folder
from tools import media_exporter
from tools.background_remover import remove_background
from ai.yolo.yolo_utils import detect_objects

logger = get_logger("Workers")


class FrameExtractorWorker(QObject):
    progress = Signal(int)
    finished = Signal(list)

    def __init__(self, video_paths, output_folder, blur_threshold=60.0, interval_seconds=2):
        super().__init__()
        self.video_paths = video_paths if isinstance(video_paths, list) else [video_paths]
        self.output_folder = output_folder
        self.blur_threshold = blur_threshold
        self.interval_seconds = interval_seconds
        self.is_running = True

    def run(self):
        all_extracted_frames = []
        total_videos = len(self.video_paths)
        if total_videos == 0:
            if self.is_running:
                self.finished.emit([])
            return

        for i, video_path in enumerate(self.video_paths):
            if not self.is_running:
                break

            logger.info(f"Worker starting frame extraction for clip {i + 1}/{total_videos}")

            def progress_handler(sub_progress):
                overall_progress = int(((i * 100) + sub_progress) / total_videos)
                self.progress.emit(overall_progress)

            frames = extract_frames(
                video_path=video_path,
                output_folder=self.output_folder,
                progress_callback=progress_handler,
                blur_threshold=self.blur_threshold,
                interval_seconds=self.interval_seconds,
            )
            all_extracted_frames.extend(frames)

        if self.is_running:
            self.progress.emit(100)
            self.finished.emit(all_extracted_frames)

    def stop(self):
        self.is_running = False


class YOLOWorker(QObject):
    progress = Signal(int)
    finished = Signal(dict)

    def __init__(self, pipeline, frame_paths):
        super().__init__()
        self.pipeline = pipeline
        self.frame_paths = frame_paths
        self.is_running = True

    def run(self):
        import cv2
        import os
        yolo_results = {}
        total_frames = len(self.frame_paths)
        if total_frames == 0:
            if self.is_running:
                self.finished.emit({})
            return

        yolo_model_instance = self.pipeline.yolo_model

        if not yolo_model_instance:
            logger.error("YOLO model instance is None. Cannot run detection.")
            if self.is_running:
                self.finished.emit({})
            return

        for i, frame_path in enumerate(self.frame_paths):
            if not self.is_running:
                logger.warning("YOLO worker was stopped prematurely.")
                break

            try:
                # التأكد من استخدام يولو مودل انستانس وليس البايبلاين كله
                detections = detect_objects(frame_path, yolo_model_instance, conf_threshold=0.10)
                
                # Save YOLO label file
                image = cv2.imread(frame_path)
                if image is not None:
                    h, w = image.shape[:2]
                    label_path = os.path.splitext(frame_path)[0] + '.txt'
                    with open(label_path, 'w') as f:
                        for det in detections:
                            x1, y1, x2, y2 = det['bbox']
                            x_center = (x1 + x2) / 2 / w
                            y_center = (y1 + y2) / 2 / h
                            width = (x2 - x1) / w
                            height = (y2 - y1) / h
                            class_id = 0  # Assume class 0 for detection
                            f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                    yolo_results[frame_path] = {'detections': detections, 'label_path': label_path}
                else:
                    yolo_results[frame_path] = {'detections': detections, 'label_path': None}
            except Exception as e:
                logger.error(f"Error during YOLO detection for {frame_path}: {e}", exc_info=True)
                yolo_results[frame_path] = {'detections': [], 'label_path': None}

            progress_percent = int((i + 1) / total_frames * 100)
            self.progress.emit(progress_percent)

        if self.is_running:
            self.finished.emit(yolo_results)

    def stop(self):
        self.is_running = False


class FinalProcessorWorker(QObject):
    progress = Signal(int)
    finished = Signal(list)

    def __init__(self, main_window, instructions):
        super().__init__()
        self.main_window = main_window
        self.instructions = instructions
        self.is_running = True

    def run(self):
        final_processed_images = []
        char_name_safe = sanitize_filename(self.main_window.project.character_name)
        temp_processed_folder = os.path.join("temp", char_name_safe, "processed_assets")
        ensure_folder(temp_processed_folder)

        # [MODIFIED] تعريف مسارات التدريب الجديدة (Train/Val)
        base_cnn_path = self.main_window.config.get("training", {}).get(
            "cnn_data_dir", "assets/cnn_training_data"
        )
        train_data_dir = os.path.join(base_cnn_path, "train")
        val_data_dir = os.path.join(base_cnn_path, "val")

        ensure_folder(train_data_dir)
        ensure_folder(val_data_dir)

        # استعادة إعدادات التدريب والمقاسات من النسخة الصحيحة
        tm = self.main_window.tag_manager  # تم إضافتها لضمان التوافق مع الكود السابق

        target_sizes = self.main_window.config.get("image", {}).get("target_sizes", {})
        clothing_sizes = self.main_window.config.get("image", {}).get("clothing_dimensions", {})
        transparent_targets = self.main_window.config.get("image", {}).get(
            "transparent_targets", []
        )

        instruction_count = len(self.instructions)
        if instruction_count == 0:
            self.finished.emit([])
            return

        processed_count = 0
        filename_counters = {}

        for frame_path, items_to_create in self.instructions.items():
            if not self.is_running:
                break
            try:
                source_image = cv2.imread(frame_path)
                if source_image is None:
                    continue

                for item_data in items_to_create:
                    yolo_detection = item_data.get("yolo_detection")
                    if not yolo_detection:
                        continue

                    # استعادة استخراج البيانات الأساسية
                    final_class = item_data.get("final_class")
                    base_type = item_data.get("base_type")
                    asset_category = item_data.get("asset_category")
                    base_type_tag = item_data.get("base_type_tag")
                    final_class_tag = item_data.get("final_class_tag")

                    # 1. الاقتصاص (Crop)
                    bbox = yolo_detection["bbox"]
                    # تصحيح عملية التقريب والاقتصاص لتجنب الأخطاء
                    x1, y1, x2, y2 = [int(coord) for coord in bbox]
                    cropped_img = source_image[y1:y2, x1:x2]
                    if cropped_img.size == 0:
                        continue

                    # 2. حفظ بيانات التدريب (Training Data) - التعديل هنا
                    if asset_category in ["clothing", "bodypart", "fullbody"]:
                        # تأكد من أن final_class ليس None أو فارغاً قبل محاولة Split
                        if not final_class or not isinstance(final_class, str):
                            logger.warning(
                                f"Skipping training data save: final_class is invalid/missing for {frame_path}"
                            )
                            continue

                        try:
                            # 90% train, 10% val (230/256 ≈ 0.90)
                            target_base_dir = (
                                train_data_dir if os.urandom(1)[0] < 230 else val_data_dir
                            )

                            # استخدام أول جزء من الفئة كاسم للمجلد (لتبسيط التصنيف)
                            category_name = sanitize_filename(final_class.split("_")[0])

                            training_class_folder = os.path.join(target_base_dir, category_name)
                            ensure_folder(training_class_folder)

                            training_file_name = (
                                f"{char_name_safe}_{Path(frame_path).stem}_{final_class}.png"
                            )
                            cv2.imwrite(
                                os.path.join(training_class_folder, training_file_name), cropped_img
                            )

                        except Exception as e:
                            logger.error(
                                f"Failed to save training data for category '{category_name}' from '{frame_path}': {e}",
                                exc_info=True,
                            )

                    # 3. معالجة وتغيير حجم الصورة
                    # استعادة منطق تحديد base_name
                    base_name = (
                        final_class_tag if final_class_tag else sanitize_filename(final_class)
                    )

                    image_to_save = cropped_img
                    target_size_tuple = None

                    # تحديد المقاس المستهدف
                    if base_type_tag in clothing_sizes:
                        target_size_tuple = tuple(clothing_sizes[base_type_tag])
                    elif base_type_tag in target_sizes:
                        target_size_tuple = tuple(target_sizes[base_type_tag])

                    # تطبيق تغيير الحجم
                    if target_size_tuple:
                        image_to_save = cv2.resize(
                            cropped_img, target_size_tuple, interpolation=cv2.INTER_LANCZOS4
                        )

                    # إزالة الخلفية (يجب أن تكون آخر خطوة)
                    if base_type_tag in transparent_targets:
                        image_to_save = remove_background(image_to_save)

                    # 4. بناء اسم الملف ومعالجة التضارب (استعادة المنطق الصحيح)
                    counter = filename_counters.get(base_name, 1)
                    final_filename = f"{base_name}_{counter}.png"
                    while os.path.exists(os.path.join(temp_processed_folder, final_filename)):
                        counter += 1
                        final_filename = f"{base_name}_{counter}.png"
                    filename_counters[base_name] = counter + 1

                    final_path = os.path.join(temp_processed_folder, final_filename)
                    cv2.imwrite(final_path, image_to_save)  # cv2.imwrite يحفظ BGR/BGRA بشكل صحيح

                    asset_to_export = {
                        "path": final_path,
                        "final_name": final_filename,
                        "asset_category": asset_category,
                        "base_type": base_type_tag,
                        "yolo_detection": yolo_detection,
                    }

                    # Add YOLO label path if exists
                    label_path = os.path.splitext(frame_path)[0] + '.txt'
                    if os.path.exists(label_path):
                        asset_to_export["yolo_label_path"] = label_path

                    # [NEW FIX] إضافة مكونات مسار الملابس لتمريرها إلى media_exporter.py
                    if asset_category == "clothing":
                        # نعتمد على وجود هذه المفاتيح في item_data التي جاءت من واجهة المستخدم
                        asset_to_export["body_part_cover"] = item_data.get("body_part_cover", "")
                        asset_to_export["cover_type"] = item_data.get("cover_type", "")

                    final_processed_images.append(asset_to_export)

            except Exception as e:
                logger.error(f"Error processing item from {frame_path}: {e}", exc_info=True)

            processed_count += 1
            self.progress.emit(int(processed_count / instruction_count * 100))

        if self.is_running:
            self.finished.emit(final_processed_images)

    def stop(self):
        self.is_running = False


class ExportWorker(QObject):
    finished = Signal(object)

    def __init__(self, project, pipeline):
        super().__init__()
        self.project = project
        self.pipeline = pipeline
        self.is_running = True

    def run(self):
        try:
            # تم التأكيد: مسؤولية تصدير كل شيء تقع على media_exporter.export_media_pack
            result_path = media_exporter.export_media_pack(
                project=self.project, pipeline=self.pipeline
            )
            self.finished.emit(result_path)
        except Exception as e:
            logger.error(f"Critical error in ExportWorker: {e}", exc_info=True)
            self.finished.emit(None)

    def stop(self):
        self.is_running = False


class VideoSplitterWorker(QObject):
    finished = Signal(dict)
    progress = Signal(int)

    def __init__(self, video_path, output_folder, clips, pipeline):
        super().__init__()
        self.video_path = video_path
        self.output_folder = output_folder
        self.clips = clips
        self.pipeline = pipeline
        self.process = None
        self.commands_to_run = []
        self.created_files = {}
        self.current_clip_index = 0
        self.total_clips = 0
        self._is_running = True
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self._on_process_timeout)

    def run(self):
        self.created_files = {}
        self.commands_to_run = get_ffmpeg_split_commands(
            self.video_path, self.output_folder, self.clips
        )
        self.total_clips = len(self.commands_to_run)
        if not self.commands_to_run:
            logger.warning("No valid commands for video splitting.")
            self.finished.emit({})
            return
        self._start_next_process()

    def _start_next_process(self):
        if not self._is_running or self.current_clip_index >= self.total_clips:
            self.finished.emit(self.created_files)
            return
        command, output_path = self.commands_to_run[self.current_clip_index]
        executable = command[0]
        args = command[1:]

        logger.info(f"Starting FFmpeg command {self.current_clip_index + 1}/{self.total_clips}: {executable} {' '.join(args)}")

        self.process = QProcess(self)
        self.process.finished.connect(self._on_process_finished)
        self.process.errorOccurred.connect(self._on_process_error)
        self.process.readyReadStandardError.connect(self._on_process_stderr)
        self.process.readyReadStandardOutput.connect(self._on_process_stdout)

        # Set process environment and working directory
        env = QProcessEnvironment.systemEnvironment()
        self.process.setProcessEnvironment(env)
        self.process.setWorkingDirectory(os.path.dirname(executable))

        self.process.start(executable, args)

        # Check if process started
        if not self.process.waitForStarted(5000):  # 5 second timeout
            logger.error(f"Failed to start FFmpeg process for clip {self.current_clip_index + 1}")
            self._handle_process_failure()
            return

        logger.info(f"FFmpeg process started for clip {self.current_clip_index + 1}")

        # Start timeout timer (5 minutes per clip should be more than enough)
        self.timeout_timer.start(300000)  # 5 minutes

    def _on_process_error(self, error):
        # Stop the timeout timer
        self.timeout_timer.stop()

        error_msg = {
            QProcess.ProcessError.FailedToStart: "Failed to start",
            QProcess.ProcessError.Crashed: "Crashed",
            QProcess.ProcessError.Timedout: "Timed out",
            QProcess.ProcessError.WriteError: "Write error",
            QProcess.ProcessError.ReadError: "Read error",
            QProcess.ProcessError.UnknownError: "Unknown error"
        }.get(error, "Unknown error")

        logger.error(f"QProcess error for clip {self.current_clip_index + 1}: {error_msg}")
        self._handle_process_failure()

    def _on_process_stdout(self):
        stdout = self.process.readAllStandardOutput().data().decode("utf-8", "ignore")
        if stdout.strip():
            logger.debug(f"FFmpeg stdout: {stdout.strip()}")

    def _on_process_stderr(self):
        stderr = self.process.readAllStandardError().data().decode("utf-8", "ignore")
        if stderr.strip():
            logger.debug(f"FFmpeg stderr: {stderr.strip()}")

    def _on_process_timeout(self):
        logger.error(f"FFmpeg process timed out for clip {self.current_clip_index + 1}")
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
            self.process.waitForFinished(5000)  # Wait up to 5 seconds for clean shutdown
        self._handle_process_failure()

    def _handle_process_failure(self):
        """Handle process failure by skipping to next clip"""
        logger.warning(f"Skipping failed clip {self.current_clip_index + 1}")
        self.progress.emit(int(((self.current_clip_index + 1) / self.total_clips) * 100))
        self.current_clip_index += 1
        self._start_next_process()

    def _on_process_finished(self, exit_code, exit_status):
        # Stop the timeout timer
        self.timeout_timer.stop()

        if not self._is_running:
            return

        # Check if we already handled this clip due to an error
        if self.current_clip_index >= self.total_clips:
            return

        output_path = self.commands_to_run[self.current_clip_index][1]

        logger.info(f"FFmpeg process finished for clip {self.current_clip_index + 1} with exit code {exit_code}")

        # 1. التحقق من نجاح عملية FFmpeg
        if exit_status == QProcess.ExitStatus.NormalExit and exit_code == 0:

            # تم إزالة استدعاء دالة create_thumbnail_from_video الغير معرفة

            # 2. تحليل الذكاء الاصطناعي (AI Analysis)
            try:
                cap = cv2.VideoCapture(output_path)
                success, frame = cap.read()
                cap.release()
                if success and frame is not None:
                    action_suggestion = self.pipeline.suggest_action(frame)
                    self.created_files[output_path] = {
                        "ai_suggestion": action_suggestion,
                        "source_path": output_path,
                    }
                    logger.info(f"AI analysis completed for clip {output_path}: {action_suggestion}")
                else:
                    self.created_files[output_path] = {
                        "ai_suggestion": "unknown",
                        "source_path": output_path,
                    }
                    logger.warning(f"Could not read frame from clip {output_path}")
            except Exception as e:
                logger.error(f"AI analysis failed for clip {output_path}: {e}")
                self.created_files[output_path] = {
                    "ai_suggestion": "unknown",
                    "source_path": output_path,
                }
        else:
            error_output = self.process.readAllStandardError().data().decode("utf-8", "ignore")
            logger.error(
                f"Failed to create clip {self.current_clip_index + 1}. Exit code: {exit_code}, Stderr: {error_output}"
            )

        self.progress.emit(int(((self.current_clip_index + 1) / self.total_clips) * 100))
        self.current_clip_index += 1
        self._start_next_process()

    def stop(self):
        self._is_running = False
        self.timeout_timer.stop()
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.finished.disconnect(self._on_process_finished)
            self.process.kill()
            self.process.waitForFinished(3000)  # Wait up to 3 seconds
