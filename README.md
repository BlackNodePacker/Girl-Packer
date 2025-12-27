# Girl Packer

Girl Packer is a PySide6-based GUI tool for processing media assets (images/videos) into Ren'Py game content. It automates frame extraction, AI-powered asset detection/classification, image processing, and Ren'Py script generation for adult-themed visual novels.

## Features

- **Photo Maker**: Extract frames from videos or folders, detect assets using YOLO, classify with CNN, crop and process images.
- **Video Maker**: Process video clips with tagging and splitting.
- **Shoot Maker**: Create photo/video shoots with AI suggestions.
- **Event Maker**: Generate Ren'Py events with dialogue and scripts.
- **AI Training**: Retrain models on new data.
- **Data Review**: Review and manage training data.

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

To build a standalone executable with Nuitka:
```bash
nuitka --onefile --enable-plugin=pyside6 --include-data-dir=gui=gui --include-data-dir=ai/models=ai/models main.py
```

Include FFmpeg binaries in the build.

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

## License

[Add license if any]
