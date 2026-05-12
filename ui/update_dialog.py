from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QWidget)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from core.i18n import TEXTS
from ui.style import NeonStyle

class UpdateDialog(QDialog):
    def __init__(self, latest_version, url, changelog, lang="en", parent=None):
        super().__init__(parent)
        self.url = url
        self.t = TEXTS[lang]
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(500, 450)
        
        self.init_ui(latest_version, changelog)
        
    def init_ui(self, version, changelog):
        self.container = QWidget(self)
        self.container.setObjectName("UpdateContainer")
        self.container.setFixedSize(500, 450)
        self.setStyleSheet(NeonStyle.QSS + f"""
            #UpdateContainer {{ 
                background-color: #0d0d0d; 
                border: 2px solid {NeonStyle.ACCENT}; 
                border-radius: 15px;
            }}
            QLabel#Title {{ font-size: 18pt; font-weight: bold; color: {NeonStyle.ACCENT}; }}
            QLabel#SubTitle {{ font-size: 11pt; color: white; }}
            QTextEdit {{ 
                background-color: #1a1a1a; 
                border: 1px solid #333; 
                border-radius: 8px; 
                color: #ccc;
                font-family: 'Segoe UI', sans-serif;
                font-size: 10pt;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.container)
        
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(35, 35, 35, 35)
        main_layout.setSpacing(20)
        
        title = QLabel(self.t["update_available_title"])
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        subtitle = QLabel(self.t["update_available_msg"].format(version))
        subtitle.setObjectName("SubTitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        main_layout.addWidget(subtitle)
        
        if changelog:
            whats_new_lbl = QLabel(self.t["whats_new"])
            whats_new_lbl.setStyleSheet(f"color: {NeonStyle.TEXT_DIM}; font-weight: bold;")
            main_layout.addWidget(whats_new_lbl)
            
            self.notes = QTextEdit()
            self.notes.setReadOnly(True)
            self.notes.setPlainText(changelog)
            main_layout.addWidget(self.notes)
        
        main_layout.addStretch()
        
        # Buttons
        btns = QHBoxLayout()
        btns.setSpacing(15)
        
        self.update_btn = QPushButton(self.t["update_now_btn"])
        self.update_btn.setObjectName("AccentButton")
        self.update_btn.setMinimumHeight(45)
        self.update_btn.clicked.connect(self.open_update)
        
        self.later_btn = QPushButton(self.t["remind_later_btn"])
        self.later_btn.setMinimumHeight(45)
        self.later_btn.clicked.connect(self.reject)
        
        btns.addWidget(self.later_btn)
        btns.addWidget(self.update_btn)
        main_layout.addLayout(btns)

    def open_update(self):
        QDesktopServices.openUrl(QUrl(self.url))
        self.accept()
