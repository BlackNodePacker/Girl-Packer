# GameMediaTool/gui/components/player_widget.py (Final Corrected Version)

import sys
import vlc
from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout
from PySide6.QtGui import QPalette, QColor

from tools.logger import get_logger

logger = get_logger("PlayerWidget")


class PlayerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.instance = None
        self.mediaplayer = None

        self.videoframe = QFrame()
        palette = self.videoframe.palette()
        palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Window, QColor(0, 0, 0))
        self.videoframe.setPalette(palette)
        self.videoframe.setAutoFillBackground(True)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self.videoframe)
        self.setLayout(vbox)

    def _initialize_vlc(self):
        if self.instance is None:
            logger.info("Initializing new VLC instance with performance-oriented options...")

            vlc_options = [
                # Keep hardware DECODING disabled for stability with various video files
                "--avcodec-hw=none",
                # [THE FIX] Remove --vout=wingdi to let VLC use the default, fast,
                # hardware-accelerated RENDERER (like Direct3D). This is the main performance boost.
                # Keep other stability options
                "--no-osd",
                "--no-video-title-show",
                "--ignore-config",
                "--disable-screensaver",
                "--quiet",
            ]
            self.instance = vlc.Instance(vlc_options)

        if self.instance is None:
            logger.critical("VLC Instance creation failed!")
            return

        if self.mediaplayer is None:
            self.mediaplayer = self.instance.media_player_new()
            if sys.platform.startswith("win"):
                self.mediaplayer.set_hwnd(self.videoframe.winId())

    def load_video(self, path: str):
        self._initialize_vlc()
        if not self.mediaplayer:
            logger.error("Media player is not available. Cannot load video.")
            return
        media = self.instance.media_new(path)
        self.mediaplayer.set_media(media)
        self.play()

    def release_player(self):
        """
        [THE FIX] Stops and completely releases all VLC resources,
        including the main instance, to ensure a clean state next time.
        """
        logger.info("Releasing all VLC resources...")
        if self.mediaplayer:
            if self.mediaplayer.is_playing():
                self.mediaplayer.stop()
            self.mediaplayer.release()
            self.mediaplayer = None

        if self.instance:
            self.instance.release()
            self.instance = None

    # ... The rest of the functions remain exactly the same ...
    def play(self):
        if self.mediaplayer:
            self.mediaplayer.play()

    def pause(self):
        if self.mediaplayer:
            self.mediaplayer.pause()

    def toggle_play_pause(self):
        if self.mediaplayer and self.mediaplayer.is_playing():
            self.pause()
        else:
            self.play()

    def stop_video(self):
        if self.mediaplayer:
            self.mediaplayer.stop()

    def seek_video(self, time_change_ms):
        if self.mediaplayer:
            self.mediaplayer.set_time(max(0, self.mediaplayer.get_time() + time_change_ms))

    def set_position(self, pos: float):
        if self.mediaplayer:
            self.mediaplayer.set_position(pos)

    def get_position(self) -> float:
        return self.mediaplayer.get_position() if self.mediaplayer else 0.0

    def get_length(self) -> int:
        return self.mediaplayer.get_length() if self.mediaplayer else 0

    def get_time(self) -> int:
        return self.mediaplayer.get_time() if self.mediaplayer else 0

    def set_time(self, ms: int):
        if self.mediaplayer:
            self.mediaplayer.set_time(ms)

    def set_rate(self, rate: float):
        if self.mediaplayer:
            self.mediaplayer.set_rate(rate)

    def get_state(self):
        return self.mediaplayer.get_state() if self.mediaplayer else vlc.State.Error

    def get_media(self):
        return self.mediaplayer.get_media() if self.mediaplayer else None

    def is_playing(self) -> bool:
        return self.mediaplayer.is_playing() if self.mediaplayer else False
