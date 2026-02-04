"""Chart utilities for LewtNanny
Simple chart drawing without external dependencies
"""

import asyncio
import logging
from typing import Any

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class SimpleChart(QWidget):
    """Simple bar chart widget for displaying session data"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data: list[dict[str, Any]] = []
        self.title = ""
        self.x_label = ""
        self.y_label = ""
        self.max_value = 0
        self.colors = [
            QColor(0, 150, 136),  # Teal
            QColor(255, 152, 0),  # Orange
            QColor(103, 58, 183),  # Purple
            QColor(76, 175, 80),  # Green
            QColor(244, 67, 54),  # Red
            QColor(33, 150, 243),  # Blue
        ]

        self.setMinimumHeight(200)
        logger.debug("SimpleChart initialized")

    def set_data(
        self, data: list[dict[str, Any]], label_key: str = "label", value_key: str = "value"
    ):
        """Set chart data"""
        self.data = data
        if data:
            self.max_value = max(item.get(value_key, 0) for item in data)
            if self.max_value == 0:
                self.max_value = 1
        self.update()
        logger.debug(f"Chart data updated: {len(data)} items")

    def paintEvent(self, a0):  # noqa: N802
        """Paint the chart"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.data:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data to display")
            return

        margin = 40
        chart_rect = self.rect().adjusted(margin, margin, -margin, -margin)

        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
            return

        bar_width = chart_rect.width() // len(self.data) - 4
        if bar_width < 10:
            bar_width = 10

        for i, item in enumerate(self.data):
            label = str(item.get("label", f"Item {i + 1}"))
            value = float(item.get("value", 0))

            bar_height = (value / self.max_value) * chart_rect.height() if self.max_value > 0 else 0

            x = chart_rect.left() + i * (bar_width + 4) + 2
            y = chart_rect.bottom() - bar_height

            color = self.colors[i % len(self.colors)]
            painter.setPen(QPen(color.darker(150), 1))
            painter.setBrush(QBrush(color))
            painter.drawRect(int(x), int(y), bar_width - 2, int(bar_height))

            painter.setPen(QColor(200, 200, 200))
            painter.setFont(QFont("Arial", 7))
            text_rect = painter.fontMetrics().boundingRect(label)
            painter.drawText(
                int(x + bar_width / 2 - text_rect.width() / 2), chart_rect.bottom() + 5, label
            )

        painter.setPen(QColor(150, 150, 150))
        painter.drawLine(
            chart_rect.left(), chart_rect.bottom(), chart_rect.right(), chart_rect.bottom()
        )

        if self.max_value > 0:
            step = self.max_value / 5
            for i in range(6):
                y = chart_rect.bottom() - (i * chart_rect.height() / 5)
                painter.drawLine(chart_rect.left() - 5, int(y), chart_rect.left(), int(y))
                value = self.max_value - i * step
                painter.drawText(chart_rect.left() - 35, int(y + 5), f"{value:.1f}")


class SessionChartWidget(QWidget):
    """Widget for displaying session-related charts"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = None
        self.session_data: list[dict[str, Any]] = []

        self.setup_ui()
        logger.info("SessionChartWidget initialized")

    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Chart Type:"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(
            [
                "ROI by Session",
                "Profit/Loss by Session",
                "Cost vs Loot by Session",
                "Events per Session",
            ]
        )
        self.chart_type_combo.currentIndexChanged.connect(self.update_chart)
        filter_layout.addWidget(self.chart_type_combo)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        self.chart = SimpleChart()
        self.chart.setStyleSheet("background-color: rgba(30, 30, 40, 200); border-radius: 4px;")
        layout.addWidget(self.chart)

        self.load_timer = QTimer()
        self.load_timer.timeout.connect(self._on_load_timer)
        self.load_timer.setSingleShot(True)
        self.load_timer.start(500)

        layout.addStretch()

    def _on_load_timer(self):
        """Handle load timer timeout"""
        if self.db_manager:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.load_data())
                loop.close()
            except Exception as e:
                logger.debug(f"Chart load error: {e}")

    def set_db_manager(self, db_manager):
        """Set database manager"""
        self.db_manager = db_manager

    def refresh(self):
        """Refresh chart data"""
        if self.db_manager:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.load_data())
                loop.close()
            except Exception as e:
                logger.debug(f"Chart refresh error: {e}")

    async def load_data(self):
        """Load session data"""
        try:
            if self.db_manager:
                self.session_data = await self.db_manager.get_all_sessions()
                logger.info(f"Loaded {len(self.session_data)} sessions for chart")
                self.update_chart()

        except Exception as e:
            logger.error(f"Error loading chart data: {e}")

    def update_chart(self):
        """Update chart based on selected type"""
        try:
            chart_type = self.chart_type_combo.currentText()

            if not self.session_data:
                self.chart.set_data([])
                return

            data = []
            for i, session in enumerate(self.session_data[:20]):
                session_id = session.get("id", f"Session {i + 1}")[:8]
                cost = float(session.get("total_cost", 0))
                return_val = float(session.get("total_return", 0))

                if chart_type == "ROI by Session":
                    roi = ((return_val - cost) / cost * 100) if cost > 0 else 0
                    data.append({"label": session_id, "value": roi})

                elif chart_type == "Profit/Loss by Session":
                    profit = return_val - cost
                    data.append({"label": session_id, "value": profit})

                elif chart_type == "Cost vs Loot by Session":
                    data.append({"label": f"{session_id}\nCost", "value": cost})
                    data.append({"label": f"{session_id}\nLoot", "value": return_val})

                elif chart_type == "Events per Session":
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        stats = loop.run_until_complete(
                            self.db_manager.get_session_stats(session.get("id"))
                        )
                        loop.close()
                        data.append({"label": session_id, "value": stats.get("event_count", 0)})
                    except Exception:
                        data.append({"label": session_id, "value": 0})

            self.chart.set_data(data)
            logger.debug(f"Chart updated: {chart_type}")

        except Exception as e:
            logger.error(f"Error updating chart: {e}")
