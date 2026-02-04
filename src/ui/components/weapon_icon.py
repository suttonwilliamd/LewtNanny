"""Weapon Icon Component
Displays stylized SVG icons for different weapon types
"""

import logging

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPixmap, QRadialGradient
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class WeaponIconPainter:
    """Paint weapon icons using QPainter"""

    @staticmethod
    def create_weapon_pixmap(
        weapon_type: str,
        size: int = 64,
        rarity: str = "common",
        selected: bool = False,
        theme: str = "dark"
    ) -> QPixmap:
        """Create a weapon icon pixmap"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Colors based on theme
        if theme == "dark":
            primary_color = QColor("#4A90D9")
            secondary_color = QColor("#2D3D4F")
            accent_color = QColor("#4A90D9")
            glow_color = QColor("#4A90D9")
        else:
            primary_color = QColor("#2563EB")
            secondary_color = QColor("#E5E7EB")
            accent_color = QColor("#2563EB")
            glow_color = QColor("#2563EB")

        # Rarity colors
        rarity_colors = {
            "common": QColor("#9CA3AF"),
            "uncommon": QColor("#22C55E"),
            "rare": QColor("#3B82F6"),
            "epic": QColor("#A855F7"),
            "legendary": QColor("#F59E0B")
        }
        rarity_color = rarity_colors.get(rarity.lower(), rarity_colors["common"])

        # Selection glow
        if selected:
            glow = QRadialGradient(size/2, size/2, size/2)
            glow.setColorAt(0, QColor(glow_color).lighter(150))
            glow.setColorAt(0.5, QColor(glow_color).lighter(50))
            glow.setColorAt(1, Qt.GlobalColor.transparent)
            painter.fillRect(0, 0, size, size, glow)

        # Background circle
        bg_rect = QRect(size//8, size//8, size*3//4, size*3//4)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(secondary_color))
        painter.drawEllipse(bg_rect)

        # Inner ring
        ring_rect = QRect(size//6, size//6, size*2//3, size*2//3)
        painter.setPen(QColor(rarity_color))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(ring_rect)

        # Draw weapon icon based on type
        WeaponIconPainter._draw_weapon_icon(
            painter, weapon_type, size, primary_color, accent_color, rarity_color
        )

        painter.end()
        return pixmap

    @staticmethod
    def _draw_weapon_icon(
        painter: QPainter,
        weapon_type: str,
        size: int,
        primary_color: QColor,
        accent_color: QColor,
        rarity_color: QColor
    ):
        """Draw weapon-specific icon"""
        center = size // 2
        scale = size / 64.0

        painter.setPen(QPen(rarity_color, 2 * scale))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        weapon_type_lower = weapon_type.lower() if weapon_type else ""

        if "pistol" in weapon_type_lower or "laser pistol" in weapon_type_lower:
            WeaponIconPainter._draw_pistol(painter, center, scale, primary_color, accent_color)
        elif "rifle" in weapon_type_lower or "carbine" in weapon_type_lower or "assault" in weapon_type_lower:
            WeaponIconPainter._draw_rifle(painter, center, scale, primary_color, accent_color)
        elif "shotgun" in weapon_type_lower:
            WeaponIconPainter._draw_shotgun(painter, center, scale, primary_color, accent_color)
        elif "melee" in weapon_type_lower or "shortblade" in weapon_type_lower or "longblade" in weapon_type_lower:
            WeaponIconPainter._draw_melee(painter, center, scale, primary_color, accent_color)
        elif "flamethrower" in weapon_type_lower:
            WeaponIconPainter._draw_flamethrower(painter, center, scale, primary_color, accent_color)
        elif "bow" in weapon_type_lower or "crossbow" in weapon_type_lower:
            WeaponIconPainter._draw_bow(painter, center, scale, primary_color, accent_color)
        elif "mindforce" in weapon_type_lower:
            WeaponIconPainter._draw_mindforce(painter, center, scale, primary_color, accent_color)
        else:
            # Default - generic weapon shape
            WeaponIconPainter._draw_default(painter, center, scale, primary_color, accent_color)

    @staticmethod
    def _draw_pistol(painter: QPainter, center: int, scale: float, primary: QColor, accent: QColor):
        """Draw pistol icon"""
        painter.setPen(QPen(accent, 2 * scale))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Barrel
        painter.drawRect(center - 3*scale, center - 12*scale, 6*scale, 18*scale)
        # Grip
        painter.drawRect(center - 2*scale, center + 4*scale, 4*scale, 10*scale)
        # Trigger guard
        painter.drawArc(center - 5*scale, center + 2*scale, 10*scale, 10*scale, 0, 180*16)

    @staticmethod
    def _draw_rifle(painter: QPainter, center: int, scale: float, primary: QColor, accent: QColor):
        """Draw rifle icon"""
        painter.setPen(QPen(accent, 2 * scale))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Stock
        painter.drawRect(center - 18*scale, center - 4*scale, 12*scale, 8*scale)
        # Body
        painter.drawRect(center - 6*scale, center - 8*scale, 20*scale, 12*scale)
        # Barrel
        painter.drawRect(center + 14*scale, center - 4*scale, 12*scale, 4*scale)
        # Scope
        painter.drawRect(center - 2*scale, center - 14*scale, 8*scale, 6*scale)

    @staticmethod
    def _draw_shotgun(painter: QPainter, center: int, scale: float, primary: QColor, accent: QColor):
        """Draw shotgun icon"""
        painter.setPen(QPen(accent, 2 * scale))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Stock
        painter.drawRect(center - 20*scale, center - 3*scale, 16*scale, 6*scale)
        # Body
        painter.drawRect(center - 4*scale, center - 6*scale, 12*scale, 8*scale)
        # Barrels (double barrel)
        painter.drawRect(center + 8*scale, center - 8*scale, 16*scale, 10*scale)
        # Pump
        painter.drawRect(center - 8*scale, center - 10*scale, 4*scale, 12*scale)

    @staticmethod
    def _draw_melee(painter: QPainter, center: int, scale: float, primary: QColor, accent: QColor):
        """Draw melee weapon icon"""
        painter.setPen(QPen(accent, 2 * scale))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Blade
        path = QPainterPath()
        path.moveTo(center, center - 18*scale)
        path.lineTo(center + 6*scale, center)
        path.lineTo(center, center + 20*scale)
        path.lineTo(center - 6*scale, center)
        path.closeSubpath()
        painter.drawPath(path)
        # Handle
        painter.drawRect(center - 2*scale, center + 18*scale, 4*scale, 8*scale)

    @staticmethod
    def _draw_flamethrower(painter: QPainter, center: int, scale: float, primary: QColor, accent: QColor):
        """Draw flamethrower icon"""
        painter.setPen(QPen(accent, 2 * scale))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Tank
        painter.drawRoundedRect(center - 6*scale, center, 12*scale, 14*scale, 2*scale, 2*scale)
        # Barrel
        painter.drawRect(center - 4*scale, center - 16*scale, 8*scale, 18*scale)
        # Nozzle
        painter.drawEllipse(center, center - 18*scale, 6*scale, 4*scale)

    @staticmethod
    def _draw_bow(painter: QPainter, center: int, scale: float, primary: QColor, accent: QColor):
        """Draw bow/crossbow icon"""
        painter.setPen(QPen(accent, 2 * scale))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Bow curve
        painter.drawArc(center - 8*scale, center - 16*scale, 16*scale, 32*scale, 0, 180*16)
        # String
        painter.drawLine(center - 8*scale, center - 16*scale, center - 8*scale, center + 16*scale)
        # Arrow
        painter.drawLine(center, center - 14*scale, center, center + 14*scale)
        # Grip
        painter.drawRect(center - 2*scale, center - 2*scale, 4*scale, 4*scale)

    @staticmethod
    def _draw_mindforce(painter: QPainter, center: int, scale: float, primary: QColor, accent: QColor):
        """Draw mindforce icon"""
        painter.setPen(QPen(accent, 2 * scale))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Orb
        gradient = QRadialGradient(center, center, 12*scale)
        gradient.setColorAt(0, accent.lighter(150))
        gradient.setColorAt(0.7, accent)
        gradient.setColorAt(1, Qt.GlobalColor.transparent)
        painter.setBrush(gradient)
        painter.drawEllipse(center, center, 16*scale, 16*scale)
        # Ring
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, center, 20*scale, 8*scale)

    @staticmethod
    def _draw_default(painter: QPainter, center: int, scale: float, primary: QColor, accent: QColor):
        """Draw default generic weapon icon"""
        painter.setPen(QPen(accent, 2 * scale))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Generic weapon shape
        painter.drawRect(center - 4*scale, center - 14*scale, 8*scale, 24*scale)
        painter.drawRect(center - 6*scale, center + 8*scale, 12*scale, 4*scale)


class WeaponIconLabel(QLabel):
    """Label that displays a weapon icon"""

    def __init__(
        self,
        weapon_type: str = "Unknown",
        size: int = 64,
        rarity: str = "common",
        parent: QWidget | None = None
    ):
        super().__init__(parent)
        self._weapon_type = weapon_type
        self._size = size
        self._rarity = rarity
        self._selected = False
        self._theme = "dark"

        self.setFixedSize(size, size)
        self._update_icon()

    def setWeaponType(self, weapon_type: str):
        """Set weapon type and update icon"""
        self._weapon_type = weapon_type
        self._update_icon()

    def setSize(self, size: int):
        """Set icon size"""
        self._size = size
        self.setFixedSize(size, size)
        self._update_icon()

    def setRarity(self, rarity: str):
        """Set rarity level"""
        self._rarity = rarity
        self._update_icon()

    def setSelected(self, selected: bool):
        """Set selection state"""
        self._selected = selected
        self._update_icon()

    def setTheme(self, theme: str):
        """Set theme (dark/light)"""
        self._theme = theme
        self._update_icon()

    def _update_icon(self):
        """Update the displayed icon"""
        pixmap = WeaponIconPainter.create_weapon_pixmap(
            self._weapon_type,
            self._size,
            self._rarity,
            self._selected,
            self._theme
        )
        self.setPixmap(pixmap)


class WeaponIconDisplay(QWidget):
    """Widget displaying weapon icon with stats"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._weapon_type = "Unknown"
        self._weapon_name = ""
        self._rarity = "common"
        self._size = 80

        self.setup_ui()

    def setup_ui(self):
        """Setup the UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Icon
        self.icon_label = WeaponIconLabel(self._weapon_type, self._size, self._rarity)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        # Name label
        self.name_label = QLabel(self._weapon_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("""
            font-size: 12px;
            color: #E0E1E3;
            font-weight: bold;
        """)
        layout.addWidget(self.name_label)

        # Type label
        self.type_label = QLabel(self._weapon_type)
        self.type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.type_label.setStyleSheet("""
            font-size: 10px;
            color: #888;
        """)
        layout.addWidget(self.type_label)

    def setWeapon(self, name: str, weapon_type: str, rarity: str = "common"):
        """Set weapon information"""
        self._weapon_name = name
        self._weapon_type = weapon_type
        self._rarity = rarity

        self.icon_label.setWeaponType(weapon_type)
        self.icon_label.setRarity(rarity)
        self.name_label.setText(name)
        self.type_label.setText(weapon_type)

    def setSelected(self, selected: bool):
        """Set selection state"""
        self.icon_label.setSelected(selected)

    def setTheme(self, theme: str):
        """Set theme"""
        self._theme = theme
        self.icon_label.setTheme(theme)

        if theme == "dark":
            self.name_label.setStyleSheet("""
                font-size: 12px;
                color: #E0E1E3;
                font-weight: bold;
            """)
            self.type_label.setStyleSheet("""
                font-size: 10px;
                color: #888;
            """)
        else:
            self.name_label.setStyleSheet("""
                font-size: 12px;
                color: #19232D;
                font-weight: bold;
            """)
            self.type_label.setStyleSheet("""
                font-size: 10px;
                color: #666;
            """)
