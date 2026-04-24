import os
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, 
                             QAbstractButton, QSizePolicy, QDialog, QFormLayout, QLineEdit, QComboBox)
from PySide6.QtCore import Qt, QRect, QSize, Property, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QPixmap
from core.utils import resource_path
from core.i18n import TEXTS
from ui.style import NeonStyle

class ModernSwitch(QAbstractButton):
    def __init__(self, parent=None, track_radius=10, thumb_radius=8):
        super().__init__(parent)
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        self._track_radius = track_radius
        self._thumb_radius = thumb_radius
        
        self._margin = 2
        self._base_width = 44
        self._base_height = 20
        
        self.setFixedSize(self._base_width, self._base_height)
        
        # Colors
        self._track_color_off = QColor("#333333")
        self._track_color_on = QColor("#bc00ff") # Neon Purple
        self._thumb_color = QColor("#ffffff")
        
        # Animation
        self._thumb_pos = self._margin + self._thumb_radius
        self._anim = QPropertyAnimation(self, b"thumb_pos")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.InOutCirc)

    def sizeHint(self):
        return QSize(self._base_width, self._base_height)

    def sync_visual_state(self):
        if self.isChecked():
            self._thumb_pos = self.width() - self._margin - self._thumb_radius
        else:
            self._thumb_pos = self._margin + self._thumb_radius
        self.update()

    @Property(float)
    def thumb_pos(self):
        return self._thumb_pos

    @thumb_pos.setter
    def thumb_pos(self, pos):
        self._thumb_pos = pos
        self.update()

    def nextCheckState(self):
        super().nextCheckState()
        start = self._thumb_pos
        end = self.width() - self._margin - self._thumb_radius if self.isChecked() else self._margin + self._thumb_radius
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw track
        track_rect = QRect(self._margin, self._margin, self.width() - 2*self._margin, self.height() - 2*self._margin)
        color = self._track_color_on if self.isChecked() else self._track_color_off
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(track_rect, self._track_radius, self._track_radius)
        
        # Draw thumb
        painter.setBrush(QBrush(self._thumb_color))
        painter.drawEllipse(self._thumb_pos - self._thumb_radius, self.height()/2 - self._thumb_radius, 
                            self._thumb_radius*2, self._thumb_radius*2)

class HeaderSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.banner_path = resource_path(os.path.join("src", "assets", "banner.jpg"))
        self.pixmap = QPixmap(self.banner_path)
        self.overlay_color = QColor(15, 15, 15, 180) # Dark gray with transparency

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.pixmap.isNull():
            # Draw pixmap scaled to fill
            scaled_pixmap = self.pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            # Center it
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
            
        # Draw overlay
        painter.setBrush(QBrush(self.overlay_color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

class CustomTitleBar(QWidget):
    lang_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(40)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # App Title
        self.title_label = QLabel(" DEAD AS DISCO - MOD MANAGER")
        self.title_label.setObjectName("TitleLabel")
        self.layout.addWidget(self.title_label)
        
        self.layout.addStretch()

        # Language Button
        self.lang_btn = QPushButton("ES")
        self.lang_btn.setObjectName("TitleButton")
        self.lang_btn.setFixedSize(45, 40)
        self.lang_btn.clicked.connect(self.lang_clicked.emit)
        self.layout.addWidget(self.lang_btn)
        
        # Minimize Button
        self.min_btn = QPushButton("0") # Marlett '0' is minimize
        self.min_btn.setObjectName("TitleButton")
        self.min_btn.setFixedSize(45, 40)
        self.min_btn.clicked.connect(self.window().showMinimized)
        self.layout.addWidget(self.min_btn)
        
        # Close Button
        self.close_btn = QPushButton("r") # Marlett 'r' is close
        self.close_btn.setObjectName("TitleButton")
        self.close_btn.setProperty("class", "CloseButton")
        self.close_btn.setFixedSize(45, 40)
        self.close_btn.clicked.connect(self.window().close)
        self.layout.addWidget(self.close_btn)
        
        self.start_pos = None

class AddModDialog(QDialog):
    def __init__(self, default_name, lang, parent=None):
        super().__init__(parent)
        self.lang = lang
        t = TEXTS[self.lang]
        self.setWindowTitle(t["add_mod_title"])
        self.setMinimumWidth(400)
        
        # Frameless window and transparent background for custom borders if needed
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        
        # Main Container
        self.container = QWidget(self)
        self.container.setObjectName("MainContainer") # Use same style as main window
        self.setStyleSheet(parent.styleSheet() if parent else "")
        
        container_layout = QVBoxLayout(self)
        container_layout.setContentsMargins(1, 1, 1, 1) # Border space
        container_layout.setSpacing(0)
        container_layout.addWidget(self.container)
        
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Custom Title Bar for Dialog
        self.title_bar = CustomTitleBar(self)
        self.title_bar.title_label.setText(f" {t['add_mod_title']}")
        # Hide minimize for dialog, keep only close
        self.title_bar.min_btn.hide()
        self.title_bar.lang_btn.hide()
        main_layout.addWidget(self.title_bar)
        
        # Content Layout
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(20)
        
        form = QFormLayout()
        form.setSpacing(15)
        
        self.name_edit = QLineEdit(default_name)
        form.addRow(t["mod_name_lbl"], self.name_edit)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem(t["type_character"], "character")
        self.type_combo.addItem(t["type_map"], "map")
        self.type_combo.addItem(t["type_other"], "other")
        form.addRow(t["mod_type_lbl"], self.type_combo)
        
        content_layout.addLayout(form)
        content_layout.addStretch()
        
        btns = QHBoxLayout()
        btns.setSpacing(15)
        
        self.cancel_btn = QPushButton(t["cancel_btn"])
        self.cancel_btn.setMinimumHeight(36)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.install_btn = QPushButton(t["install_btn"])
        self.install_btn.setObjectName("AccentButton")
        self.install_btn.setMinimumHeight(36)
        self.install_btn.clicked.connect(self.accept)
        
        btns.addStretch()
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.install_btn)
        content_layout.addLayout(btns)
        
        main_layout.addLayout(content_layout)

    def get_data(self):
        return self.name_edit.text().strip(), self.type_combo.currentData()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.start_pos:
            delta = event.globalPosition().toPoint() - self.start_pos
            self.window().move(self.window().pos() + delta)
            self.start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.start_pos = None

class ModListHeader(QWidget):
    def __init__(self, lang, parent=None):
        super().__init__(parent)
        self.lang = lang
        t = TEXTS[self.lang]
        
        self.layout = QHBoxLayout(self)
        # Added extra right margin (35) to compensate for QListWidget scrollbar
        self.layout.setContentsMargins(25, 10, 45, 5)
        self.layout.setSpacing(15)
        
        # Style for header labels
        style = f"color: {NeonStyle.TEXT_DIM}; font-size: 8pt; font-weight: bold; letter-spacing: 1px;"
        
        self.name_lbl = QLabel(t["header_mod_name"])
        self.name_lbl.setStyleSheet(style)
        self.layout.addWidget(self.name_lbl, 1)
        
        self.type_lbl = QLabel(t["header_mod_type"])
        self.type_lbl.setStyleSheet(style)
        self.type_lbl.setFixedWidth(130)
        self.type_lbl.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.type_lbl)
        
        self.rename_lbl = QLabel(t["header_mod_rename"])
        self.rename_lbl.setStyleSheet(style)
        self.rename_lbl.setFixedWidth(40)
        self.rename_lbl.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.rename_lbl)
        
        self.status_lbl = QLabel(t["header_mod_status"])
        self.status_lbl.setStyleSheet(style)
        self.status_lbl.setFixedWidth(60)
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_lbl)

    def retranslate(self, lang):
        self.lang = lang
        t = TEXTS[self.lang]
        self.name_lbl.setText(t["header_mod_name"])
        self.type_lbl.setText(t["header_mod_type"])
        self.rename_lbl.setText(t["header_mod_rename"])
        self.status_lbl.setText(t["header_mod_status"])

class ModItemWidget(QWidget):
    toggled = Signal(bool)
    rename_requested = Signal()
    type_changed = Signal(str)

    def __init__(self, mod_metadata, is_active=False, lang="es", parent=None):
        super().__init__(parent)
        self.mod_metadata = mod_metadata
        self.mod_name = mod_metadata["name"]
        self.folder_name = mod_metadata["folder_name"]
        self.lang = lang
        t = TEXTS[self.lang]

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 6, 20, 6)
        self.layout.setSpacing(15)
        self.layout.setAlignment(Qt.AlignVCenter)
        self.setMinimumHeight(64)

        # Mod Name
        self.name_label = QLabel(self.mod_name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self.name_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.layout.addWidget(self.name_label, 1)

        # Type Dropdown
        self.type_combo = QComboBox()
        self.type_combo.setFixedWidth(130)
        self.type_combo.addItem(t["type_character"], "character")
        self.type_combo.addItem(t["type_map"], "map")
        self.type_combo.addItem(t["type_other"], "other")
        
        idx = self.type_combo.findData(mod_metadata.get("type", "other"))
        if idx >= 0: self.type_combo.setCurrentIndex(idx)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        self.layout.addWidget(self.type_combo)

        # Rename Button
        self.rename_btn = QPushButton("✎")
        self.rename_btn.setFixedSize(40, 36)
        self.rename_btn.setCursor(Qt.PointingHandCursor)
        self.rename_btn.setToolTip(t.get("tooltip_rename", "Renombrar Mod"))
        self.rename_btn.clicked.connect(self.rename_requested.emit)
        self.layout.addWidget(self.rename_btn)

        # Toggle Switch (wrapped in fixed-width widget for header alignment)
        self.switch_container = QWidget()
        self.switch_container.setFixedWidth(60)
        switch_layout = QHBoxLayout(self.switch_container)
        switch_layout.setContentsMargins(0, 0, 0, 0)
        switch_layout.setAlignment(Qt.AlignCenter)
        
        self.switch = ModernSwitch()
        self.switch.setChecked(is_active)
        self.switch.sync_visual_state()
        self.switch.setFixedSize(self.switch.sizeHint())
        self.switch.clicked.connect(lambda: self.toggled.emit(self.switch.isChecked()))
        
        switch_layout.addWidget(self.switch)
        self.layout.addWidget(self.switch_container)

    def _on_type_changed(self, index):
        new_type = self.type_combo.itemData(index)
        self.type_changed.emit(new_type)

    def sizeHint(self):
        return QSize(100, 64)

    def set_active(self, active):
        self.switch.setChecked(active)

    def get_name(self):
        # We use folder_name for core logic (sync/active_mods)
        return self.folder_name
