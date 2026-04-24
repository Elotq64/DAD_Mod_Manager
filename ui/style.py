
class NeonStyle:
    # Color Palette
    BG_DARK = "#0f0f0f"
    BG_PANEL = "#1a1a1a"
    ACCENT = "#00e5ff"  # Neon Cyan
    ACCENT_PURPLE = "#bc00ff" # Neon Purple
    TEXT_MAIN = "#e0e0e0"
    TEXT_DIM = "#888888"
    BORDER = "#333333"
    SUCCESS = "#00ff88"
    DANGER = "#ff3d00"

    QSS = f"""
    QMainWindow {{
        background-color: {BG_DARK};
        color: {TEXT_MAIN};
        border: 1px solid {BORDER};
    }}

    QWidget {{
        color: {TEXT_MAIN};
        font-family: 'Segoe UI', sans-serif;
        font-size: 10pt;
    }}
    
    /* Custom Title Bar */
    QWidget#TitleBar {{
        background-color: {BG_PANEL};
        border-bottom: 1px solid {BORDER};
    }}
    
    QLabel#TitleLabel {{
        font-weight: bold;
        color: {TEXT_DIM};
        padding-left: 10px;
    }}
    
    QPushButton#TitleButton {{
        background-color: transparent;
        border: none;
        border-radius: 0px;
        padding: 5px 15px;
        font-family: 'Marlett'; /* Windows system font for icons */
    }}
    
    QPushButton#TitleButton:hover {{
        background-color: {BORDER};
    }}
    
    QPushButton#CloseButton:hover {{
        background-color: {DANGER};
    }}

    QFrame#MainContainer {{
        background-color: {BG_DARK};
    }}

    QGroupBox {{
        font-weight: bold;
        text-transform: uppercase;
        border: 1px solid {BORDER};
        border-radius: 8px;
        margin-top: 15px;
        padding-top: 15px;
        color: {ACCENT_PURPLE};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 5px;
    }}
    
    QGroupBox#ModsGroup {{
        color: {ACCENT};
    }}

    QLabel {{
        color: {TEXT_MAIN};
    }}

    QLabel#HeaderTitle {{
        font-size: 24pt;
        font-weight: bold;
        color: {ACCENT};
        letter-spacing: 2px;
    }}
    
    QLabel#HeaderTitleSecondary {{
        color: {ACCENT_PURPLE};
    }}

    QLabel#HeaderSub {{
        font-size: 10pt;
        color: {TEXT_DIM};
        margin-top: -5px;
    }}

    QLineEdit {{
        background-color: {BG_PANEL};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 8px;
        color: {TEXT_MAIN};
    }}

    QLineEdit:focus {{
        border: 1px solid {ACCENT_PURPLE};
    }}

    QPushButton {{
        background-color: {BG_PANEL};
        color: {TEXT_MAIN};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 8px 15px;
        font-weight: bold;
    }}

    QPushButton:hover {{
        background-color: {ACCENT_PURPLE};
        color: white;
        border: 1px solid {ACCENT_PURPLE};
    }}

    QPushButton:pressed {{
        background-color: #8a00ba;
    }}

    QPushButton#AccentButton {{
        background-color: {ACCENT};
        color: black;
        border: none;
    }}

    QPushButton#AccentButton:hover {{
        background-color: #33ebff;
        color: black;
    }}

    QListWidget {{
        background-color: {BG_DARK};
        border: 1px solid {BORDER};
        border-radius: 8px;
        outline: none;
        padding: 5px;
    }}

    QListWidget::item {{
        background-color: {BG_PANEL};
        border-radius: 6px;
        margin: 6px 0px;
        padding: 0px;
    }}

    QListWidget::item:selected {{
        border: 1px solid {ACCENT};
    }}

    QScrollBar:vertical {{
        border: none;
        background: {BG_DARK};
        width: 10px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: {BORDER};
        min-height: 20px;
        border-radius: 5px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {TEXT_DIM};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QStatusBar {{
        background-color: {BG_PANEL};
        color: {TEXT_DIM};
        border-top: 1px solid {BORDER};
    }}

    QInputDialog {{
        background-color: {BG_DARK};
    }}

    QMessageBox {{
        background-color: {BG_DARK};
    }}
    """
