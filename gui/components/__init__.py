# GameMediaTool/gui/components/__init__.py (Updated)

from .player_widget import PlayerWidget
from .custom_slider import MarkerSlider
from .video_clipper_panel import VideoClipperPanel
from .contact_sheet_panel import ContactSheetPanel
from .image_workshop_panel import ImageWorkshopPanel
from .vid_tagger_panel import VidTaggerPanel
from .image_viewer_widget import ImageViewerWidget
from .custom_trait_dialog import CustomTraitDialog
from .manual_crop_dialog import ManualCropDialog
from .frame_extraction_dialog import FrameExtractionDialog  # <-- [ADD THIS LINE]

from .workers import (
    FrameExtractorWorker,
    YOLOWorker,
    FinalProcessorWorker,
    ExportWorker,
    VideoSplitterWorker,
)
