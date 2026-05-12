from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QScrollArea, QWidget, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt

class ConflictResolverDialog(QDialog):
    def __init__(self, conflicts, lang="en", parent=None):
        super().__init__(parent)
        self.lang = lang
        from core.i18n import TEXTS
        t = TEXTS[self.lang]
        self.setWindowTitle(t["conflict_dialog_title"])
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.conflicts = conflicts # { folder_name: [reasons] }
        self.results = {} # { folder_name: 'replace' | 'new' | 'skip' }
        
        self.init_ui()

    def init_ui(self):
        from core.i18n import TEXTS
        t = TEXTS[self.lang]
        layout = QVBoxLayout(self)
        
        header = QLabel(t["conflict_header"])
        header.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        # Scroll Area for many conflicts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        
        self.groups = {}
        
        for folder, reasons in self.conflicts.items():
            item_widget = QWidget()
            item_layout = QVBoxLayout(item_widget)
            item_layout.setContentsMargins(10, 10, 10, 10)
            item_widget.setStyleSheet("background-color: #1a1a1a; border-radius: 5px; margin-bottom: 5px;")
            
            title = QLabel(t["conflict_song_lbl"].format(folder))
            title.setStyleSheet("font-weight: bold; color: #bc00ff;")
            item_layout.addWidget(title)
            
            reason_txt = t["conflict_reasons_lbl"].format(", ".join([r.replace('_', ' ') for r in reasons]))
            item_layout.addWidget(QLabel(reason_txt))
            
            opts_layout = QHBoxLayout()
            group = QButtonGroup(item_widget)
            
            rb_replace = QRadioButton(t["replace_opt"])
            rb_new = QRadioButton(t["add_new_opt"])
            rb_skip = QRadioButton(t["skip_opt"])
            
            # Default to 'new' if it's just an ID collision, 'replace' if the folder matches?
            # User requirement says present options.
            rb_new.setChecked(True)
            
            group.addButton(rb_replace, 0)
            group.addButton(rb_new, 1)
            group.addButton(rb_skip, 2)
            
            opts_layout.addWidget(rb_replace)
            opts_layout.addWidget(rb_new)
            opts_layout.addWidget(rb_skip)
            item_layout.addLayout(opts_layout)
            
            self.groups[folder] = group
            self.content_layout.addWidget(item_widget)
            
        self.content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Bulk Actions
        bulk_layout = QHBoxLayout()
        btn_all_replace = QPushButton(t["all_replace_btn"])
        btn_all_new = QPushButton(t["all_new_btn"])
        
        btn_all_replace.clicked.connect(lambda: self.set_all(0))
        btn_all_new.clicked.connect(lambda: self.set_all(1))
        
        bulk_layout.addWidget(btn_all_replace)
        bulk_layout.addWidget(btn_all_new)
        layout.addLayout(bulk_layout)

        # Bottom Buttons
        btns = QHBoxLayout()
        self.cancel_btn = QPushButton(t["cancel_all_btn"])
        self.cancel_btn.clicked.connect(self.reject)
        
        self.import_btn = QPushButton(t["process_import_btn"])
        self.import_btn.setStyleSheet("background-color: #bc00ff; color: white; font-weight: bold; padding: 8px;")
        self.import_btn.clicked.connect(self.collect_and_accept)
        
        btns.addStretch()
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.import_btn)
        layout.addLayout(btns)

    def set_all(self, id):
        for group in self.groups.values():
            btn = group.button(id)
            if btn: btn.setChecked(True)

    def collect_and_accept(self):
        for folder, group in self.groups.items():
            id = group.checkedId()
            strategy = {0: 'replace', 1: 'new', 2: 'skip'}[id]
            self.results[folder] = strategy
        self.accept()

    def get_results(self):
        return self.results
