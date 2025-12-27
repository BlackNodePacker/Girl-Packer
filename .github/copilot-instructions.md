# Girl Packer AI Coding Instructions

## Project Overview
Girl Packer is a PySide6-based GUI tool for processing media assets (images/videos) into Ren'Py game content. It automates frame extraction, AI-powered asset detection/classification, image processing, and Ren'Py script generation for adult-themed visual novels.

## Architecture
- **GUI Layer**: PySide6 panels in `gui/` with QStackedWidget navigation via WorkflowManager
- **Core Classes**: 
  - `Project` (project_data.py): Manages source media, export data, and asset paths
  - `Pipeline` (ai/pipeline.py): Loads YOLO (detection) and CNN models (asset/action classification)
  - `TagManager` (utils/tag_manager.py): Handles JSON-based tagging system
- **Workflows**: Threaded processing in `workflows/` for photo/video/shoot/event creation
- **Data Flow**: Source media → temp/ processing → game/ output with Ren'Py scripts

## Key Conventions
- **Paths**: Use absolute paths; temp files in `temp/{character_name}/` subfolders
- **Threading**: Heavy tasks (extraction, AI, processing) run in QThread with workers from `gui/components/workers.py`
- **Logging**: loguru via `tools/logger.py` with context-specific loggers
- **Config**: YAML-based settings in `config.yaml` loaded via `utils/config_loader.py`
- **Assets**: Media extensions `('.webp', '.png', '.jpg', '.jpeg', '.webm', '.mp4')`
- **Ren'Py Output**: Events saved as JSON + .rpy scripts in project output/game/

## Critical Workflows
- **Photo Maker**: `workflows/photo_maker_workflow.py` - Frame extraction → YOLO detection → cropping/classification → final images
- **Video Maker**: Similar pipeline for video clips with tagging
- **Event Maker**: Combines assets into Ren'Py events with dialogue/script generation
- **AI Training**: `gui/ai_training_panel.py` for model retraining on new data

## AI Integration
- **Models**: YOLOv8 (ultralytics) for body/clothing detection, ResNet-based CNNs for asset/action classification
- **Preprocessing**: OpenCV transforms (BGR→RGB, resize 224x224, normalize)
- **Inference**: GPU if available, fallback CPU
- **Training Data**: Stored in `assets/cnn_training_data/` with max pool size 1000

## Build & Deployment
- **Standalone EXE**: Nuitka build with data files inclusion (style.qss, models)
- **Dependencies**: Pinned versions in `requirements_final_compatible.txt` for Python 3.11
- **FFmpeg**: Bundled binaries (ffmpeg.exe, ffprobe.exe) for video processing

## Common Patterns
- **Worker Threads**: Inherit from QObject, emit signals for progress/results
- **JSON Storage**: Event definitions, traits, tags stored as JSON in `database/`
- **Image Processing**: Pillow for format conversion, transparent-background for removal
- **Error Handling**: Try/catch with QMessageBox for user-facing errors, logger for debugging

## Development Tips
- **Debug GUI**: Run `python main.py` from project root
- **Test AI**: Use `ai/pipeline.py` methods directly with sample images
- **Add Panels**: Extend WorkflowManager panels dict and MainWindow setup
- **Config Changes**: Reload via `utils/config_loader.py` or restart app
- **Temp Cleanup**: Manual removal; workflows handle per-run cleanup

## File Structure Reference
- `main.py`: QApplication entry with Nuitka compatibility
- `gui/main_window.py`: Panel orchestration and project methods
- `ai/models/`: Pre-trained .pth files and class maps
- `database/`: JSON configs for traits, clothing, events
- `tools/`: Media utilities (cropper, frame_extractor, rpy_generator)
- `utils/`: Helpers (file_ops, tag_manager, config_loader)