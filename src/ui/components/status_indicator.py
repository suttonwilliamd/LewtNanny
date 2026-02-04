"""Status indicator component with glow effect
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QLabel


class StatusIndicator(QLabel):
    """Status indicator light with glow effect"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._status = "red"
        self._status_message = "chat.log not found"
        self._update_appearance()

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        messages = {
            "red": "chat.log not found",
            "yellow": "Character name not set / No weapon loadout selected",
            "green": "Ready",
        }
        self._status_message = messages.get(value, "Unknown")
        self._update_appearance()

    def _update_appearance(self):
        colors = {
            "red": ("#FF4444", "#880000"),
            "yellow": ("#FFAA00", "#884400"),
            "green": ("#44FF44", "#008800"),
        }
        core_color, glow_color = colors.get(self._status, colors["red"])

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {core_color};
                border-radius: 10px;
                border: 2px solid {glow_color};
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(glow_color))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)

    def enterEvent(self, event):
        self.setToolTip(self._status_message)

    def leaveEvent(self, a0):
        pass
