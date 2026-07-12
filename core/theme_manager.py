from PyQt6.QtCore import QObject, pyqtSignal
from core.config import COLORS, THEMES

class ThemeManager(QObject):
    theme_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
    def set_theme(self, theme_name):
        if theme_name in THEMES:
            COLORS.update(THEMES[theme_name])
            self.theme_changed.emit()

theme_manager = ThemeManager()
