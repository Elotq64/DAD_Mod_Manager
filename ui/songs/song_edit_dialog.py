from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QLabel, QMessageBox, QWidget, QHBoxLayout)
from PySide6.QtCore import Qt
from core.songs.song_editor import SongEditor
from ui.widgets import CustomTitleBar

class SongMetadataDialog(QDialog):
    def __init__(self, initial_data=None, song=None, lang="en", parent=None):
        super().__init__(parent)
        self.song = song
        self.lang = lang
        # initial_data can be a Song object or a dict
        if song:
            perf = song.performed_by
            if isinstance(perf, list):
                perf = ", ".join(perf)
            
            self.data = {
                "songName": song.song_name,
                "tempo": song.tempo,
                "performedBy": perf,
                "beatOffset": song.beat_offset,
                "startSongOffset": song.start_song_offset,
                "endSongOffset": song.end_song_offset
            }
        else:
            self.data = initial_data or {}
            
        self.start_pos = None
        
        # Frameless window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setMinimumWidth(450)
        
        self.init_ui()

    def init_ui(self):
        from core.i18n import TEXTS
        t = TEXTS[self.lang]
        # Main Container
        self.container = QWidget(self)
        self.container.setObjectName("MainContainer")
        if self.parent():
            self.setStyleSheet(self.parent().styleSheet())
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1) # Border
        layout.addWidget(self.container)
        
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Custom Title Bar
        self.title_bar = CustomTitleBar(self)
        self.title_bar.title_label.setText(f" {t['song_meta_dialog_title']}")
        self.title_bar.min_btn.hide()
        self.title_bar.lang_btn.hide()
        main_layout.addWidget(self.title_bar)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(30, 25, 30, 30)
        content_layout.setSpacing(20)
        
        title_text = t["song_meta_edit_title"].format(self.data.get('songName')) if self.song else t["song_meta_new_title"]
        header = QLabel(title_text)
        header.setObjectName("HeaderTitleSecondary")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        content_layout.addWidget(header)
        
        form = QFormLayout()
        form.setSpacing(15)
        
        self.name_edit = QLineEdit(str(self.data.get("songName", "")))
        
        perf = self.data.get("performedBy", "Unknown Artist")
        if isinstance(perf, list):
            perf = ", ".join(perf)
        self.artist_edit = QLineEdit(str(perf))
        
        self.tempo_edit = QLineEdit(str(self.data.get("tempo", "120.0")))
        self.beat_offset_edit = QLineEdit(str(self.data.get("beatOffset", "0.0")))
        self.start_offset_edit = QLineEdit(str(self.data.get("startSongOffset", "0.0")))
        self.end_offset_edit = QLineEdit(str(self.data.get("endSongOffset", "0.0")))
        
        form.addRow(t["song_name_lbl"], self.name_edit)
        form.addRow(t["artist_lbl"], self.artist_edit)
        form.addRow(t["tempo_bpm_lbl"], self.tempo_edit)
        form.addRow(t["beat_offset_lbl"], self.beat_offset_edit)
        form.addRow(t["start_offset_lbl"], self.start_offset_edit)
        form.addRow(t["end_offset_lbl"], self.end_offset_edit)
        
        content_layout.addLayout(form)
        
        help_label = QLabel(t["song_meta_help"])
        help_label.setStyleSheet("color: #888888; font-style: italic;")
        content_layout.addWidget(help_label)
        
        # Action Buttons
        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(15)
        
        self.cancel_btn = QPushButton(t["cancel_btn"])
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton(t["confirm_btn"])
        self.save_btn.setObjectName("AccentButton")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self.on_accept)
        
        btns_layout.addStretch()
        btns_layout.addWidget(self.cancel_btn)
        btns_layout.addWidget(self.save_btn)
        content_layout.addLayout(btns_layout)
        
        main_layout.addLayout(content_layout)

    def get_metadata(self):
        return {
            "songName": self.name_edit.text().strip(),
            "performedBy": self.artist_edit.text().strip(),
            "tempo": float(self.tempo_edit.text().strip() or 120.0),
            "beatOffset": float(self.beat_offset_edit.text().strip() or 0.0),
            "startSongOffset": float(self.start_offset_edit.text().strip() or 0.0),
            "endSongOffset": float(self.end_offset_edit.text().strip() or 0.0)
        }

    def on_accept(self):
        from core.i18n import TEXTS
        t = TEXTS[self.lang]
        try:
            # Validate numeric fields
            float(self.tempo_edit.text().strip())
            float(self.beat_offset_edit.text().strip())
            float(self.start_offset_edit.text().strip())
            float(self.end_offset_edit.text().strip())
            self.accept()
        except ValueError:
            QMessageBox.critical(self, t["msg_validation_error_title"], t["msg_validation_error_text"])

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.start_pos:
            delta = event.globalPosition().toPoint() - self.start_pos
            self.move(self.pos() + delta)
            self.start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.start_pos = None

