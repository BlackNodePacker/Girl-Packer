# Girl Packer

Girl Packer is a PySide6-based GUI tool for processing media assets (images/videos) into Ren'Py game content. It automates frame extraction, AI-powered asset detection/classification, image processing, and Ren'Py script generation for adult-themed visual novels.

## Features

- **Photo Maker**: Extract frames from videos or folders, detect assets using YOLO, classify with CNN, crop and process images.
- **Video Maker**: Process video clips with tagging and splitting.
- **Shoot Maker**: Create photo/video shoots with AI suggestions.
- **Event Maker**: Generate Ren'Py events with dialogue and scripts.
- **AI Training**: Retrain models on new data.
- **Data Review**: Review and manage training data.
- **Pack Review and Rating**: Analyze completed packs for quality, errors, and rating before export (integrated with PackAnalyzer).
- **Auto-Pack (Pro Users)**: Automated pack creation from raw media using AI workflows (requires pro verification via Patreon key).

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ahmedasker115-cloud/Girl-Packer.git
   cd Girl-Packer
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements_final_compatible.txt
   ```

4. (Optional) Install development tools:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Run the application:
   ```bash
   python main.py
   ```

## Usage Manual

### Getting Started
1. Launch the application with `python main.py`.
2. The main window appears with a dashboard.

### Setting Up a Project
1. Go to "Character Setup" panel.
2. Define character name, type, traits from JSON databases.
3. Set source media: video file or image folder.

### Photo Maker Workflow
1. Select "Photo Maker" panel.
2. Choose source type: video or folder.
3. Adjust settings: blur threshold, interval.
4. Run frame extraction.
5. Select frames for YOLO analysis.
6. Review detections and classifications.
7. Process final images with cropping and background removal.

### Video Maker Workflow
1. Select "Vids Maker" panel.
2. Load video clips.
3. Tag clips with actions/assets.
4. Split and process videos.

### Event Maker Workflow
1. Select "Event Maker" panel.
2. Select assets from project.
3. Define event structure, dialogue.
4. Generate Ren'Py script and JSON.

### AI Training
1. Go to "AI Training" panel.
2. Add new training data.
3. Retrain models.

### Pack Review and Rating
1. Before exporting, access the "Pack Review" panel.
2. Select the pack folder to analyze.
3. View rating (0-100), positives, warnings, and errors.
4. Inspect media files and adjust as needed.
5. Proceed to export once satisfied.

### Auto-Pack for Pro Users
1. Subscribe via Patreon (patreon.com/girlpacker) or GitHub Sponsors at the repository.
2. Receive your license key automatically via email after subscription.
3. Enable pro mode in settings.
4. Select "Auto-Pack" panel.
5. Paste the license key into the "Pro Activation" dialog and click "Activate" (internet required for verification).
6. Choose pack type: Min (basic), Mid (moderate), or Top (comprehensive).
7. Select source media folder with raw assets and multiple long videos.
8. Check components to extract: bodyparts, clothing, events, photoshoots (from frames), video shoots (from split clips), fullbody pics.
9. Run automated processing: AI detection, cropping, tagging, config generation.
10. Review and export the completed pack.

### Configuration
Edit `config.yaml` for:
- Paths: temp, output, models.
- Video settings: bitrate, resolution.
- Image settings: quality, target sizes.
- AI settings: model paths, thresholds.

## Architecture Overview
- GUI: PySide6 with QStackedWidget for panels.
- Core: Project, Pipeline, TagManager.
- Workflows: Threaded processing with QThread.
- AI: YOLO for detection, CNN for classification.
- Data: JSON for traits, events; temp/ for processing, game/ for output.

## Build

### Prerequisites
- Python 3.11
- Nuitka or PyInstaller (for packaging)

### Development Setup
```bash
# Install in development mode
pip install -e .
```

### Building Standalone Executable

#### Option 1: Nuitka (Recommended)
```bash
# Install Nuitka
pip install nuitka

# Build executable
python build_nuitka.py
# or
build.bat nuitka
```

#### Option 2: PyInstaller
```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
python build_pyinstaller.py
# or
build.bat pyinstaller
```

#### Option 3: Manual Nuitka
```bash
nuitka --standalone --onefile --enable-plugin=pyside6 --enable-plugin=torch \
       --include-data-dir=assets=assets --include-data-dir=database=database \
       --include-data-file=gui/style.qss=style.qss \
       --include-data-file=ffmpeg.exe=ffmpeg.exe \
       --include-data-file=ffprobe.exe=ffprobe.exe \
       --include-data-file=config.yaml=config.yaml \
       --include-data-dir=ai/models=ai/models \
       --windows-disable-console \
       main.py
```

### Build Artifacts
- Executable: `dist/GirlPacker.exe`
- Build files: `build/` directory
- Distribution: `dist/` directory

### Cleaning Build
```bash
build.bat clean
```

## Dependencies

- Python 3.11
- PySide6
- PyTorch, torchvision
- OpenCV, Pillow
- Ultralytics
- Other libraries as in requirements.txt

## Contributing

- Follow PEP8.
- Add tests for new features.
- Update documentation.

See `todo_plan.md` for current development roadmap and upcoming features.

## License

This project is released under a proprietary license.
See the LICENSE file for full terms and restrictions.
