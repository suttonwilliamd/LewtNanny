"""Efficiency Visualization Component
Displays weapon cost efficiency with charts and metrics
"""

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class EfficiencyBar(QProgressBar):
    """Colored progress bar for efficiency display"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QProgressBar {
                background: #1A1F2E;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                height: 24px;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 3px;
            }
        """)
        self.setTextVisible(True)
        self.setMinimum(0)
        self.setMaximum(100)


class EfficiencyGauge(QWidget):
    """Circular gauge for efficiency display"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)
        self._efficiency = 0.0
        self._label = "Efficiency"

    def setEfficiency(self, value: float):  # noqa: N802
        """Set efficiency value (0-100)"""

    def setLabel(self, label: str):  # noqa: N802
        """Set gauge label"""

    def paintEvent(self, event):  # noqa: N802
        """Paint the gauge"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(center_x, center_y) - 10

        # Background arc
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2D3D4F"))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        # Value arc
        if self._efficiency > 0:
            # Determine color based on efficiency
            if self._efficiency >= 80:
                color = QColor("#2ECC71")  # Green
            elif self._efficiency >= 50:
                color = QColor("#F39C12")  # Orange
            else:
                color = QColor("#E74C3C")  # Red

            gradient = QLinearGradient(
                center_x - radius, center_y - radius, center_x + radius, center_y + radius
            )
            gradient.setColorAt(0, color.lighter(130))
            gradient.setColorAt(1, color)

            painter.setBrush(gradient)

            # Draw arc
            span_angle = int(self._efficiency * 3.6 * 16)  # Convert to angle units
            painter.drawPie(
                center_x - radius,
                center_y - radius,
                radius * 2,
                radius * 2,
                90 * 16,
                -span_angle,  # Start from top, draw clockwise
            )

        # Center text
        painter.setPen(QColor("#E0E1E3"))
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))

        value_text = f"{self._efficiency:.0f}%"
        text_rect = painter.fontMetrics().boundingRect(value_text)
        text_x = center_x - text_rect.width() // 2
        text_y = center_y - text_rect.height() // 2
        painter.drawText(text_x, text_y + text_rect.height(), value_text)


class EfficiencyCard(QFrame):
    """Card showing weapon efficiency metrics"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 8px;
            }
        """)
        self.setFixedHeight(160)

        self.setup_ui()

    def setup_ui(self):
        """Setup card UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Title
        self.title_label = QLabel("Efficiency Analysis")
        self.title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #4A90D9;
        """)
        layout.addWidget(self.title_label)

        # Gauges row
        gauges_layout = QHBoxLayout()
        gauges_layout.setSpacing(20)

        # Efficiency gauge
        self.efficiency_gauge = EfficiencyGauge()
        self.efficiency_gauge.setEfficiency(75)
        gauges_layout.addWidget(self.efficiency_gauge)

        # Metrics grid
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(8)

        self.metrics = {}
        metric_labels = [
            ("dpp", "DPP", "0.00"),
            ("dps", "DPS", "0.00"),
            ("cost", "Cost/PED", "0"),
            ("tt_return", "TT Return", "0%"),
        ]

        for idx, (key, label, default) in enumerate(metric_labels):
            row, col = divmod(idx, 2)

            label_widget = QLabel(label + ":")
            label_widget.setStyleSheet("color: #888; font-size: 11px;")
            metrics_layout.addWidget(label_widget, row, col * 2)

            value_widget = QLabel(default)
            value_widget.setStyleSheet("""
                color: #E0E1E3;
                font-size: 13px;
                font-weight: bold;
            """)
            metrics_layout.addWidget(value_widget, row, col * 2 + 1)

            self.metrics[key] = value_widget

        gauges_layout.addLayout(metrics_layout)
        gauges_layout.addStretch()

        layout.addLayout(gauges_layout)

        # Efficiency bar
        self.efficiency_bar = EfficiencyBar()
        self.efficiency_bar.setValue(75)
        self.efficiency_bar.setFormat("Overall Efficiency: %p%")
        layout.addWidget(self.efficiency_bar)

    def update_metrics(self, dps: float, dpp: float, cost_per_shot: float, tt_return: float = 0):
        """Update efficiency metrics"""
        # Update gauges
        self.metrics["dps"].setText(f"{dps:.2f}")
        self.metrics["dpp"].setText(f"{dpp:.2f}")
        self.metrics["cost"].setText(f"{cost_per_shot:.4f}")
        self.metrics["tt_return"].setText(f"{tt_return:.0f}%")

        # Calculate overall efficiency (normalized DPP)
        # Higher DPP = better efficiency
        if dpp > 0:
            # Normalize to 0-100 scale (arbitrary but useful)
            efficiency = min(100, (dpp / 10) * 100)  # 10 DPP = 100%
            self.efficiency_gauge.setEfficiency(efficiency)
            self.efficiency_bar.setValue(int(efficiency))

            # Update bar color based on efficiency
            if efficiency >= 80:
                bar_color = "#2ECC71"
            elif efficiency >= 50:
                bar_color = "#F39C12"
            else:
                bar_color = "#E74C3C"

            self.efficiency_bar.setStyleSheet(f"""
                QProgressBar {{
                    background: #1A1F2E;
                    border: 1px solid #2D3D4F;
                    border-radius: 4px;
                    height: 24px;
                    text-align: center;
                    color: #E0E1E3;
                }}
                QProgressBar::chunk {{
                    background: {bar_color};
                    border-radius: 3px;
                }}
            """)


class EfficiencyComparison(QWidget):
    """Compare efficiency across multiple weapons"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget {
                background: #1A1F2E;
            }
        """)
        self.setup_ui()
        self._weapons = []

    def setup_ui(self):
        """Setup comparison UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header = QLabel("WEAPON EFFICIENCY COMPARISON")
        header.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #4A90D9;
        """)
        layout.addWidget(header)

        # Scroll area for comparison cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)

        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)

        scroll.setWidget(self.cards_widget)
        layout.addWidget(scroll)

    def add_weapon(self, name: str, weapon_type: str, dps: float, dpp: float, cost: float):
        """Add a weapon to comparison"""
        card = EfficiencyCard()
        card.update_metrics(dps, dpp, cost)

        # Update title with weapon name
        card.title_label.setText(name)

        self.cards_layout.addWidget(card)
        self._weapons.append(
            {"name": name, "type": weapon_type, "dps": dps, "dpp": dpp, "cost": cost}
        )

        logger.debug(f"Added weapon to comparison: {name}")

    def clear(self):
        """Clear all weapons"""
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._weapons = []

    def get_weapons(self) -> list[dict]:
        """Get list of weapons in comparison"""
        return self._weapons

    def sort_by_dpp(self):
        """Sort weapons by DPP (best first)"""
        self._weapons.sort(key=lambda x: x["dpp"], reverse=True)
        self._rebuild_cards()

    def sort_by_dps(self):
        """Sort weapons by DPS (best first)"""
        self._weapons.sort(key=lambda x: x["dps"], reverse=True)
        self._rebuild_cards()

    def _rebuild_cards(self):
        """Rebuild cards in current order"""
        # Remove all cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Re-add cards in sorted order
        for weapon in self._weapons:
            card = EfficiencyCard()
            card.update_metrics(weapon["dps"], weapon["dpp"], weapon["cost"])
            card.title_label.setText(weapon["name"])
            self.cards_layout.addWidget(card)


class EfficiencyWidget(QWidget):
    """Main efficiency dashboard widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = "dark"
        self.setup_ui()

    @property
    def theme(self) -> str:
        """Get current theme"""
        return self._theme

    @theme.setter
    def theme(self, value: str):
        """Set theme and update UI"""
        self._theme = value
        self._apply_theme()

    def setup_ui(self):
        """Setup efficiency dashboard"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Current weapon efficiency
        current_group = QGroupBox("CURRENT WEAPON")
        current_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #4A90D9;
                border: 1px solid #2D3D4F;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        current_layout = QVBoxLayout(current_group)
        current_layout.setContentsMargins(10, 15, 10, 10)

        self.current_card = EfficiencyCard()
        current_layout.addWidget(self.current_card)

        layout.addWidget(current_group)

        # Comparison section
        comparison_group = QGroupBox("COMPARE WEAPONS")
        comparison_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #4A90D9;
                border: 1px solid #2D3D4F;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        comparison_layout = QVBoxLayout(comparison_group)
        comparison_layout.setContentsMargins(10, 15, 10, 10)

        self.comparison = EfficiencyComparison()
        comparison_layout.addWidget(self.comparison)

        layout.addWidget(comparison_group)

        layout.addStretch()

    def _apply_theme(self):
        """Apply theme colors to all UI elements"""
        if self._theme == "dark":
            group_style = """
                QGroupBox {
                    font-weight: bold;
                    color: #4A90D9;
                    border: 1px solid #2D3D4F;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
            """
            card_style = """
                QFrame {
                    background: #1E2A3A;
                    border: 1px solid #2D3D4F;
                    border-radius: 8px;
                }
            """
            widget_bg = "#1A1F2E"
            accent_color = "#4A90D9"
            metric_label_color = "#888"
            metric_value_color = "#E0E1E3"
        else:
            group_style = """
                QGroupBox {
                    font-weight: bold;
                    color: #0066CC;
                    border: 1px solid #CCCCCC;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
            """
            card_style = """
                QFrame {
                    background: #FFFFFF;
                    border: 1px solid #CCCCCC;
                    border-radius: 8px;
                }
            """
            widget_bg = "#F5F5F5"
            accent_color = "#0066CC"
            metric_label_color = "#666666"
            metric_value_color = "#1a1a2e"

        for child in self.findChildren(QGroupBox):
            child.setStyleSheet(group_style)

        for child in self.current_card.findChildren(QFrame):
            child.setStyleSheet(card_style)

        self.setStyleSheet(f"QWidget {{ background: {widget_bg}; }}")

        for label in self.current_card.findChildren(QLabel):
            style = label.styleSheet()
            if "color: #4A90D9" in style:
                label.setStyleSheet(style.replace("#4A90D9", accent_color))
            elif "color: #888" in style:
                label.setStyleSheet(style.replace("#888", metric_label_color))
            elif "color: #E0E1E3" in style:
                label.setStyleSheet(style.replace("#E0E1E3", metric_value_color))

    def update_current_weapon(
        self, name: str, dps: float, dpp: float, cost: float, tt_return: float = 0
    ):
        """Update current weapon metrics"""
        self.current_card.title_label.setText(name)
        self.current_card.update_metrics(dps, dpp, cost, tt_return)

    def add_comparison_weapon(
        self, name: str, weapon_type: str, dps: float, dpp: float, cost: float
    ):
        """Add weapon to comparison"""
        self.comparison.add_weapon(name, weapon_type, dps, dpp, cost)

    def clear_comparison(self):
        """Clear comparison list"""
        self.comparison.clear()

    def sort_comparison(self, by: str = "dpp"):
        """Sort comparison by metric"""
        if by == "dpp":
            self.comparison.sort_by_dpp()
        elif by == "dps":
            self.comparison.sort_by_dps()


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout

    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("Efficiency Test")
    window.resize(400, 600)

    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)

    widget = EfficiencyWidget()
    layout.addWidget(widget)

    # Add test data
    widget.update_current_weapon("ArMatrix BC-100 (L)", 5.0, 6.93, 0.0216, 85)

    widget.add_comparison_weapon("Korss H400 (L)", "Pistol", 9.3, 5.21, 0.036)
    widget.add_comparison_weapon("HL11 (L)", "Rifle", 10.0, 4.82, 0.042)
    widget.add_comparison_weapon("Opalo", "Pistol", 4.3, 7.15, 0.012)

    window.show()
    sys.exit(app.exec())
