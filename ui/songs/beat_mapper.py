import os
import time
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QWidget, QFrame, QSizePolicy, 
                             QMessageBox, QScrollArea, QGraphicsOpacityEffect,
                             QScrollBar)
from PySide6.QtCore import Qt, Signal, QRect, QSize, QTimer, QPoint, QRectF, QThread, QUrl
from PySide6.QtGui import (QPainter, QColor, QPen, QFont, QBrush, QLinearGradient, 
                          QPalette, QPainterPath)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from core.songs.bpm_analyzer import BpmAnalyzer
from ui.style import NeonStyle
from ui.widgets import CustomTitleBar
from core.i18n import TEXTS

class WaveformWorker(QThread):
    finished = Signal(list)
    
    def __init__(self, audio_path):
        super().__init__()
        self.audio_path = audio_path
        
    def run(self):
        data = BpmAnalyzer.get_waveform_data(self.audio_path)
        self.finished.emit(data)

class DetectWorker(QThread):
    finished = Signal(float)
    
    def __init__(self, audio_path):
        super().__init__()
        self.audio_path = audio_path
        
    def run(self):
        bpm = BpmAnalyzer.detect_bpm(self.audio_path)
        self.finished.emit(bpm if bpm else 0.0)

class LoadingOverlay(QWidget):
    def __init__(self, parent=None, text="LOADING..."):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.text = text
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 180))
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", 16, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text)

class WaveformWidget(QWidget):
    position_changed = Signal(float) # seconds
    view_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.waveform_data = []
        self.duration = 1.0 # seconds
        self.current_pos = 0.0 # seconds
        self.zoom_level = 1.0
        self.offset_x = 0
        
        self.tempo = 120.0
        self.beat_offset = 0.0
        self.start_time = 0.0
        self.end_time = 0.0
        self.tempo_sections = []
        
        self.MAX_ZOOM = 50.0
        self.MIN_ZOOM = 1.0
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_offset = 0
        self.seeking_drag = False
        
        self.setMinimumHeight(300)
        self.setMouseTracking(True)
        
    def set_data(self, waveform_data, duration):
        self.waveform_data = waveform_data
        self.duration = duration
        self.update()

    def set_metadata(self, tempo, offset, start, end, sections):
        self.tempo = tempo
        self.beat_offset = offset / 1000.0 # ms to s
        self.start_time = start
        self.end_time = end if end > 0 else self.duration
        self.tempo_sections = sections
        self.update()

    def set_position(self, pos):
        self.current_pos = pos
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        mid_y = h // 2
        
        # Background
        painter.fillRect(self.rect(), QColor("#0a0a0a"))
        
        if not self.waveform_data:
            return

        # Draw Timeline Grid
        self._draw_grid(painter, w, h)
        
        # Draw Waveform
        painter.setPen(QColor(NeonStyle.ACCENT_PURPLE))
        num_samples = len(self.waveform_data)
        px_per_sample = (w * self.zoom_level) / num_samples
        
        start_idx = int(self.offset_x / px_per_sample)
        end_idx = int((self.offset_x + w) / px_per_sample) + 1
        start_idx = max(0, start_idx)
        end_idx = min(num_samples, end_idx)
        
        for i in range(start_idx, end_idx):
            min_val, max_val = self.waveform_data[i]
            x = i * px_per_sample - self.offset_x
            y1 = mid_y + min_val * (h / 2) * 0.8
            y2 = mid_y + max_val * (h / 2) * 0.8
            painter.drawLine(x, y1, x, y2)

        # Draw Sections
        self._draw_sections(painter, w, h)
        
        # Draw Beats
        self._draw_beats(painter, w, h)

        # Draw Start/End Markers
        self._draw_markers(painter, w, h)

        # Draw Playhead
        playhead_x = (self.current_pos / self.duration) * (w * self.zoom_level) - self.offset_x
        if 0 <= playhead_x <= w:
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawLine(playhead_x, 0, playhead_x, h)
            # Playhead triangle at top
            poly = [QPoint(playhead_x - 5, 0), QPoint(playhead_x + 5, 0), QPoint(playhead_x, 10)]
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawPolygon(poly)

    def _draw_grid(self, painter, w, h):
        painter.setPen(QPen(QColor("#222222"), 1))
        interval = 5.0 / self.zoom_level
        if interval < 1.0: interval = 1.0
        
        num_intervals = int(self.duration / interval) + 1
        for i in range(num_intervals):
            t = i * interval
            x = (t / self.duration) * (w * self.zoom_level) - self.offset_x
            if 0 <= x <= w:
                painter.drawLine(x, 0, x, h)
                painter.drawText(x + 5, 15, f"{t:.1f}")

    def _draw_beats(self, painter, w, h):
        import math
        # Sort sections by time
        sections = sorted(self.tempo_sections, key=lambda x: x.get("startAbsoluteTime", 0))
        
        painter.setPen(QPen(QColor(NeonStyle.ACCENT), 1, Qt.DashLine))
        
        # Visible range in seconds
        logical_w = self.width() * self.zoom_level
        v_start = self.offset_x / logical_w * self.duration
        v_end = (self.offset_x + self.width()) / logical_w * self.duration

        def draw_segment(range_start, range_end, bpm, first_beat):
            if range_end < v_start or range_start > v_end: return
            
            beat_dur = 60.0 / bpm
            start_i = math.ceil((max(range_start, v_start) - first_beat) / beat_dur)
            
            i = start_i
            while True:
                t = first_beat + i * beat_dur
                if t > range_end or t > v_end: break
                
                x = (t / self.duration) * logical_w - self.offset_x
                if 0 <= x <= self.width():
                    painter.drawLine(x, 40, x, h - 40)
                i += 1

        # Segment 0: From start to first section
        first_sec_t = sections[0]["startAbsoluteTime"] if sections else self.duration
        draw_segment(0, first_sec_t, self.tempo, self.beat_offset)
        
        # Other segments
        for i, sec in enumerate(sections):
            start_t = sec["startAbsoluteTime"]
            end_t = sections[i+1]["startAbsoluteTime"] if i+1 < len(sections) else self.duration
            bpm = sec["tempo"]
            draw_segment(start_t, end_t, bpm, start_t)

    def _draw_sections(self, painter, w, h):
        for section in self.tempo_sections:
            t = section.get("startAbsoluteTime", 0)
            x = (t / self.duration) * (w * self.zoom_level) - self.offset_x
            if 0 <= x <= w:
                painter.setPen(QPen(QColor(NeonStyle.ACCENT), 3))
                painter.drawLine(x, 0, x, h)
                painter.setPen(QColor(NeonStyle.ACCENT))
                painter.drawText(x + 5, 30, f"BPM: {section.get('tempo')}")

    def _draw_markers(self, painter, w, h):
        start_x = (self.start_time / self.duration) * (w * self.zoom_level) - self.offset_x
        if 0 <= start_x <= w:
            painter.setPen(QPen(QColor(NeonStyle.SUCCESS), 2))
            painter.drawLine(start_x, 0, start_x, h)
            painter.drawText(start_x + 5, h - 10, "START")

        end_x = (self.end_time / self.duration) * (w * self.zoom_level) - self.offset_x
        if 0 <= end_x <= w:
            painter.setPen(QPen(QColor(NeonStyle.DANGER), 2))
            painter.drawLine(end_x, 0, end_x, h)
            painter.drawText(end_x - 40, h - 10, "END")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.seeking_drag = True
            self._emit_pos_at(event.position().x())
        elif event.button() == Qt.MiddleButton or event.button() == Qt.RightButton:
            self.dragging = True
            self.drag_start_x = event.position().x()
            self.drag_start_offset = self.offset_x
            self.setCursor(Qt.SizeAllCursor)

    def _emit_pos_at(self, x):
        logical_w = self.width() * self.zoom_level
        pos = (x + self.offset_x) / logical_w * self.duration
        pos = max(0, min(self.duration, pos))
        self.current_pos = pos
        self.position_changed.emit(pos)
        self.update()

    def mouseMoveEvent(self, event):
        if self.seeking_drag:
            self._emit_pos_at(event.position().x())
        elif self.dragging:
            delta = event.position().x() - self.drag_start_x
            self.offset_x = self.drag_start_offset - delta
            self._clamp_offset()
            self.view_changed.emit()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.seeking_drag = False
        elif self.dragging:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event):
        modifiers = event.modifiers()
        delta = event.angleDelta().y()
        
        if modifiers & Qt.ControlModifier:
            # Zoom
            old_zoom = self.zoom_level
            if delta > 0:
                self.zoom_level *= 1.1
            else:
                self.zoom_level /= 1.1
            
            # Limits
            self.zoom_level = max(self.MIN_ZOOM, min(self.MAX_ZOOM, self.zoom_level))
            
            # Adjust offset to zoom towards mouse position
            if old_zoom != self.zoom_level:
                mouse_x = event.position().x()
                scene_x = mouse_x + self.offset_x
                new_scene_x = scene_x * (self.zoom_level / old_zoom)
                self.offset_x = new_scene_x - mouse_x
                self._clamp_offset()
                self.view_changed.emit()
                self.update()
        else:
            # Scroll
            self.offset_x -= delta
            self._clamp_offset()
            self.view_changed.emit()
            self.update()

    def _clamp_offset(self):
        max_scroll = max(0, int(self.width() * self.zoom_level - self.width()))
        if self.offset_x < 0: self.offset_x = 0
        if self.offset_x > max_scroll: self.offset_x = max_scroll
        self.update()

class CalibrationDialog(QDialog):
    def __init__(self, audio_path, lang="en", parent=None):
        super().__init__(parent)
        self.audio_path = audio_path
        self.taps = []
        self.lang = lang
        self.t = TEXTS[lang]
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(400, 350)
        
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.7)
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(QUrl.fromLocalFile(audio_path))
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        self.setStyleSheet(f"background-color: #111111; border: 2px solid {NeonStyle.ACCENT_PURPLE}; border-radius: 15px;")
        
        title = QLabel(self.t["tap_calibration"])
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: white; border: none;")
        layout.addWidget(title)
        
        self.info = QLabel(self.t["tap_info"])
        self.info.setAlignment(Qt.AlignCenter)
        self.info.setStyleSheet(f"color: {NeonStyle.TEXT_DIM}; border: none;")
        layout.addWidget(self.info)
        
        self.bpm_label = QLabel("--- BPM")
        self.bpm_label.setAlignment(Qt.AlignCenter)
        self.bpm_label.setStyleSheet(f"font-size: 24pt; color: {NeonStyle.ACCENT}; font-weight: bold; border: none;")
        layout.addWidget(self.bpm_label)
        
        self.tap_btn = QPushButton("TAP")
        self.tap_btn.setMinimumHeight(100)
        self.tap_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {NeonStyle.ACCENT_PURPLE};
                font-size: 20pt;
                border-radius: 50px;
                border: none;
            }}
            QPushButton:pressed {{
                background-color: white;
                color: black;
            }}
        """)
        self.tap_btn.clicked.connect(self.on_tap)
        layout.addWidget(self.tap_btn)
        
        btns = QHBoxLayout()
        self.save_btn = QPushButton(self.t["save"])
        self.save_btn.clicked.connect(self.accept)
        self.save_btn.setEnabled(False)
        self.save_btn.setObjectName("AccentButton")
        
        self.cancel_btn = QPushButton(self.t["cancel_btn"])
        self.cancel_btn.clicked.connect(self.reject)
        
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.save_btn)
        layout.addLayout(btns)
        
        self.player.play()

    def on_tap(self):
        self.taps.append(time.time())
        if len(self.taps) > 1:
            intervals = [self.taps[i] - self.taps[i-1] for i in range(1, len(self.taps))]
            avg_interval = sum(intervals) / len(intervals)
            bpm = 60.0 / avg_interval
            self.bpm_label.setText(f"{bpm:.1f} BPM")
            
            if len(self.taps) >= 10:
                self.save_btn.setEnabled(True)
                self.info.setText(f"Taps: {len(self.taps)}")
            else:
                self.info.setText(f"Taps: {len(self.taps)} / 10")

    def get_bpm(self):
        if len(self.taps) < 2: return 120.0
        intervals = [self.taps[i] - self.taps[i-1] for i in range(1, len(self.taps))]
        avg_interval = sum(intervals) / len(intervals)
        return round(60.0 / avg_interval, 2)

    def closeEvent(self, event):
        self.player.stop()
        super().closeEvent(event)

class BeatMapperDialog(QDialog):
    def __init__(self, song, lang="en", parent=None):
        super().__init__(parent)
        self.song = song
        self.lang = lang
        self.t = TEXTS[lang]
        self.audio_path = os.path.join(song.folder_path, "Audio.ogg")
        self.start_pos = None
        self.workers = []
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.resize(1200, 800)
        
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.7)
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(QUrl.fromLocalFile(self.audio_path))
        self.player.positionChanged.connect(self.on_player_pos_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        
        self.tempo = song.tempo
        self.beat_offset = song.beat_offset
        self.start_time = song.start_song_offset
        self.end_time = song.end_song_offset
        self.tempo_sections = song.full_metadata.get("customTempoSections", [])
        
        self.init_ui()
        self.start_loading_waveform()

    def init_ui(self):
        self.container = QWidget(self)
        self.container.setObjectName("MainContainer")
        self.setStyleSheet(NeonStyle.QSS + f"""
            #MainContainer {{ background-color: #050505; border: 2px solid {NeonStyle.ACCENT_PURPLE}; }}
            QLabel#HeaderTitle {{ color: {NeonStyle.ACCENT_PURPLE}; font-size: 28pt; }}
            QLabel#ValueLabel {{ font-size: 14pt; font-weight: bold; color: white; }}
            QLabel#KeyLabel {{ color: {NeonStyle.TEXT_DIM}; font-size: 10pt; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(self.container)
        
        main_layout = QVBoxLayout(self.container)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title Bar
        self.title_bar = CustomTitleBar(self)
        self.title_bar.title_label.setText(f" {self.t['advanced_editor']}")
        self.title_bar.min_btn.hide()
        self.title_bar.lang_btn.hide()
        main_layout.addWidget(self.title_bar)
        
        content = QVBoxLayout()
        content.setContentsMargins(40, 20, 40, 20)
        content.setSpacing(20)
        
        # Song Info
        song_name = QLabel(self.song.song_name.upper())
        song_name.setObjectName("HeaderTitle")
        content.addWidget(song_name)
        
        # Stats / Controls Top Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(40)
        
        self.tempo_val = self._add_stat(stats_layout, self.t["tempo"], str(self.tempo))
        self.offset_val = self._add_stat(stats_layout, self.t["beat_offset"], str(self.beat_offset))
        self.start_val = self._add_stat(stats_layout, self.t["start_time"], f"{self.start_time:.2f}")
        self.end_val = self._add_stat(stats_layout, self.t["end_time"], f"{self.end_time:.2f}")
        
        content.addLayout(stats_layout)
        
        # Quick Actions Row
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        self.btn_adj_tempo = QPushButton(self.t["adjust_tempo"])
        self.btn_adj_tempo.clicked.connect(self.adjust_tempo)
        
        self.btn_adj_offset = QPushButton(self.t["adjust_offset"])
        self.btn_adj_offset.clicked.connect(self.adjust_offset)
        
        self.btn_adj_start = QPushButton(self.t["adjust_start"])
        self.btn_adj_start.clicked.connect(self.adjust_start)
        
        self.btn_adj_end = QPushButton(self.t["adjust_end"])
        self.btn_adj_end.clicked.connect(self.adjust_end)
        
        self.btn_add_section = QPushButton(self.t["add_section"])
        self.btn_add_section.setObjectName("AccentButton")
        self.btn_add_section.clicked.connect(self.add_bpm_section)
        
        actions_layout.addWidget(self.btn_adj_tempo)
        actions_layout.addWidget(self.btn_adj_offset)
        actions_layout.addWidget(self.btn_adj_start)
        actions_layout.addWidget(self.btn_adj_end)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_add_section)
        
        content.addLayout(actions_layout)
        
        # Waveform Area
        self.waveform_container = QWidget()
        self.waveform_container.setMinimumHeight(300)
        self.wf_layout = QVBoxLayout(self.waveform_container)
        self.wf_layout.setContentsMargins(0, 0, 0, 0)
        
        self.waveform = WaveformWidget()
        self.waveform.position_changed.connect(self.seek_to)
        self.waveform.view_changed.connect(self.update_scrollbar)
        self.wf_layout.addWidget(self.waveform)
        
        self.scrollbar = QScrollBar(Qt.Horizontal)
        self.scrollbar.setStyleSheet(f"""
            QScrollBar:horizontal {{ height: 12px; background: #111; }}
            QScrollBar::handle:horizontal {{ background: {NeonStyle.ACCENT_PURPLE}; border-radius: 6px; }}
        """)
        self.scrollbar.valueChanged.connect(self.on_scroll_changed)
        self.wf_layout.addWidget(self.scrollbar)
        
        content.addWidget(self.waveform_container, 1)
        
        # Playback Controls Row
        play_layout = QHBoxLayout()
        play_layout.setAlignment(Qt.AlignCenter)
        play_layout.setSpacing(15)
        
        self.btn_play = QPushButton("PLAY")
        self.btn_play.setFixedSize(120, 50)
        self.btn_play.setObjectName("AccentButton")
        self.btn_play.clicked.connect(self.toggle_play)
        
        self.btn_calibrate = QPushButton(self.t["calibrate"])
        self.btn_calibrate.setFixedSize(120, 50)
        self.btn_calibrate.clicked.connect(self.open_calibrate)
        
        self.btn_autodetect = QPushButton(self.t["autodetect"])
        self.btn_autodetect.setFixedSize(120, 50)
        self.btn_autodetect.clicked.connect(self.run_autodetect)
        
        play_layout.addWidget(self.btn_play)
        play_layout.addWidget(self.btn_calibrate)
        play_layout.addWidget(self.btn_autodetect)
        
        content.addLayout(play_layout)
        
        # Bottom Row
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 20, 0, 0)
        
        self.btn_save = QPushButton(self.t["save_exit"])
        self.btn_save.setObjectName("AccentButton")
        self.btn_save.setMinimumHeight(45)
        self.btn_save.clicked.connect(self.save_and_exit)
        
        bottom_layout.addWidget(self.btn_save)
        bottom_layout.addStretch()
        
        # Controls Legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(30)
        
        controls = [
            (f"🖱️ {self.t['left_click']}", self.t["seek_drag"]),
            (f"🖱️ {self.t['right_click']}", self.t["pan_view"]),
            (f"⌨️ {self.t['ctrl']} + {self.t['wheel']}", self.t["zoom"])
        ]
        
        for icon, desc in controls:
            item = QVBoxLayout()
            item.setSpacing(2)
            ic = QLabel(icon)
            ic.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            ic.setStyleSheet(f"font-size: 10pt; color: {NeonStyle.ACCENT}; font-weight: bold;")
            de = QLabel(desc.upper())
            de.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            de.setStyleSheet(f"font-size: 7pt; color: {NeonStyle.TEXT_DIM}; font-weight: bold;")
            item.addWidget(ic)
            item.addWidget(de)
            legend_layout.addLayout(item)
            
        bottom_layout.addLayout(legend_layout)
        
        content.addLayout(bottom_layout)
        main_layout.addLayout(content)
        
        # Loading Overlays
        self.loading_wf = LoadingOverlay(self.waveform_container, self.t["loading_waveform"])
        self.loading_wf.hide()
        
        self.loading_detect = LoadingOverlay(self, self.t["detecting_msg"])
        self.loading_detect.hide()

    def resizeEvent(self, event):
        self.loading_wf.setGeometry(self.waveform_container.rect())
        self.loading_detect.setGeometry(self.rect())
        self.update_scrollbar()
        super().resizeEvent(event)

    def _add_stat(self, layout, label, val):
        container = QVBoxLayout()
        l = QLabel(label.upper())
        l.setObjectName("KeyLabel")
        v = QLabel(val)
        v.setObjectName("ValueLabel")
        container.addWidget(l)
        container.addWidget(v)
        layout.addLayout(container)
        return v

    def start_loading_waveform(self):
        self.loading_wf.show()
        worker = WaveformWorker(self.audio_path)
        worker.finished.connect(self.on_waveform_loaded)
        self.workers.append(worker)
        worker.start()

    def on_waveform_loaded(self, data):
        # Remove finished worker from list
        sender = self.sender()
        if sender in self.workers:
            self.workers.remove(sender)
            
        self.loading_wf.hide()
        duration = self.player.duration() / 1000.0 if self.player.duration() > 0 else 1.0
        self.waveform.set_data(data, duration)
        self.update_waveform_meta()
        self.update_scrollbar()

    def update_scrollbar(self):
        max_scroll = max(0, int(self.waveform.width() * self.waveform.zoom_level - self.waveform.width()))
        self.scrollbar.setRange(0, max_scroll)
        self.scrollbar.setPageStep(self.waveform.width())
        self.scrollbar.setValue(int(self.waveform.offset_x))

    def on_scroll_changed(self, value):
        self.waveform.offset_x = value
        self.waveform.update()

    def on_duration_changed(self, duration):
        if duration > 0:
            new_duration = duration / 1000.0
            self.waveform.duration = new_duration
            self.update_waveform_meta()

    def update_waveform_meta(self):
        self.waveform.set_metadata(self.tempo, self.beat_offset, self.start_time, self.end_time, self.tempo_sections)
        self.tempo_val.setText(str(self.tempo))
        self.offset_val.setText(str(self.beat_offset))
        self.start_val.setText(f"{self.start_time:.2f}")
        self.end_val.setText(f"{self.end_time:.2f}")

    def on_player_pos_changed(self, pos):
        self.waveform.set_position(pos / 1000.0)

    def seek_to(self, pos):
        self.player.setPosition(int(pos * 1000))

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.btn_play.setText("PLAY")
        else:
            self.player.play()
            self.btn_play.setText("PAUSE")

    def open_calibrate(self):
        self.player.pause()
        self.btn_play.setText("PLAY")
        dlg = CalibrationDialog(self.audio_path, self.lang, self)
        if dlg.exec():
            self.tempo = dlg.get_bpm()
            self.update_waveform_meta()

    def run_autodetect(self):
        self.loading_detect.show()
        worker = DetectWorker(self.audio_path)
        worker.finished.connect(self.on_autodetect_finished)
        self.workers.append(worker)
        worker.start()

    def on_autodetect_finished(self, bpm):
        sender = self.sender()
        if sender in self.workers:
            self.workers.remove(sender)
            
        self.loading_detect.hide()
        if bpm > 0:
            bpm = round(bpm, 2)
            res = QMessageBox.question(
                self, self.t["autodetect"], 
                f"Detected BPM: {bpm}\n\nDo you want to apply this tempo?",
                QMessageBox.Yes | QMessageBox.No
            )
            if res == QMessageBox.Yes:
                self.tempo = bpm
                self.update_waveform_meta()
        else:
            QMessageBox.warning(self, self.t["autodetect"], "Could not detect BPM.")

    def adjust_tempo(self):
        from PySide6.QtWidgets import QInputDialog
        val, ok = QInputDialog.getDouble(self, self.t["adjust_tempo"], "BPM:", self.tempo, 1, 500, 2)
        if ok:
            self.tempo = val
            self.update_waveform_meta()

    def adjust_offset(self):
        from PySide6.QtWidgets import QInputDialog
        val, ok = QInputDialog.getInt(self, self.t["adjust_offset"], "MS:", int(self.beat_offset), -10000, 10000)
        if ok:
            self.beat_offset = val
            self.update_waveform_meta()

    def adjust_start(self):
        self.start_time = self.player.position() / 1000.0
        self.update_waveform_meta()

    def adjust_end(self):
        self.end_time = self.player.position() / 1000.0
        self.update_waveform_meta()

    def add_bpm_section(self):
        from PySide6.QtWidgets import QInputDialog
        bpm, ok = QInputDialog.getDouble(self, self.t["add_section"], "BPM:", self.tempo, 1, 500, 2)
        if ok:
            curr_time = self.player.position() / 1000.0
            slice_count = 24
            total_beats = curr_time * (self.tempo / 60.0)
            bar = int(total_beats // 4)
            beat = int(total_beats % 4)
            fraction = total_beats - int(total_beats)
            slice_num = int(fraction * slice_count)
            
            new_section = {
                "tempo": bpm,
                "startTimestamp": {
                    "barNumber": bar + 1,
                    "beatNumber": beat + 1,
                    "sliceNumber": slice_num,
                    "sliceCount": slice_count,
                    "msOffset": 0
                },
                "startAbsoluteTime": curr_time
            }
            self.tempo_sections.append(new_section)
            self.update_waveform_meta()

    def save_and_exit(self):
        self.song.tempo = self.tempo
        self.song.beat_offset = self.beat_offset
        self.song.start_song_offset = self.start_time
        self.song.end_song_offset = self.end_time
        self.song.full_metadata["customTempoSections"] = self.tempo_sections
        self.song.save()
        self.accept()

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

    def closeEvent(self, event):
        # Clean up workers
        for worker in self.workers:
            if worker.isRunning():
                worker.terminate()
                worker.wait()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.toggle_play()
        else:
            super().keyPressEvent(event)
