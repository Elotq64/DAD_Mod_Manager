import os
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, 
                             QAbstractButton, QSizePolicy)
from PySide6.QtCore import Qt, QRect, QSize, Property, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QPixmap
from core.utils import resource_path

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

class ModItemWidget(QWidget):
    toggled = Signal(bool)
    rename_requested = Signal()

    def __init__(self, mod_name, is_active=False, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 6, 20, 6)
        self.layout.setSpacing(15)
        self.layout.setAlignment(Qt.AlignVCenter)
        self.setMinimumHeight(60)

        # Mod Name
        self.name_label = QLabel(mod_name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        self.name_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.layout.addWidget(self.name_label, 1)

        # Rename Button
        self.rename_btn = QPushButton("✎")
        self.rename_btn.setFixedSize(36, 36)
        self.rename_btn.setCursor(Qt.PointingHandCursor)
        self.rename_btn.setToolTip("Renombrar Mod")
        self.rename_btn.clicked.connect(self.rename_requested.emit)
        self.layout.addWidget(self.rename_btn)

        # Toggle Switch
        self.switch = ModernSwitch()
        self.switch.setChecked(is_active)
        self.switch.sync_visual_state()
        self.switch.setFixedSize(self.switch.sizeHint())
        self.switch.clicked.connect(lambda: self.toggled.emit(self.switch.isChecked()))
        self.layout.addWidget(self.switch)

    def sizeHint(self):
        return QSize(100, 60)

    def set_active(self, active):
        self.switch.setChecked(active)

    def get_name(self):
        return self.name_label.text()
