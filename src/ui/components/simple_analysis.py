"""
Simplified analysis tab with 2 core charts: Run TT Return % and Cost to Kill vs Return
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from statistics import mean

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QFrame,
    QSlider,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGridLayout,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush

logger = logging.getLogger(__name__)


class SimpleAnalysisChartWidget(QWidget):
    """Simple chart widget for analysis with 2 chart types"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data: List[Dict[str, Any]] = []
        self.chart_type = "return_percentage"
        self.max_runs = 50
        self.show_trend_line = True
        self.colors = {
            "positive": QColor(76, 175, 80),
            "negative": QColor(244, 67, 54),
            "neutral": QColor(33, 150, 243),
            "break_even": QColor(255, 152, 0),
            "grid": QColor(60, 60, 60),
            "text": QColor(200, 200, 200),
            "background": QColor(13, 17, 23),
        }
        self.setMinimumHeight(250)
        logger.debug("SimpleAnalysisChartWidget initialized")

    def set_data(self, data: List[Dict[str, Any]]):
        """Set chart data"""
        self.data = data
        self.update()
        logger.debug(f"Chart data updated: {len(data)} items")

    def set_chart_type(self, chart_type: str):
        """Set the chart type"""
        self.chart_type = chart_type
        self.update()

    def paintEvent(self, a0):
        """Paint the chart"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.data:
            self.draw_empty_state(painter)
            return

        margin = 50
        chart_rect = self.rect().adjusted(margin, margin, -margin, -margin)

        if chart_rect.width() <= 0 or chart_rect.height() <= 0:
            return

        if self.chart_type == "return_percentage":
            self.draw_return_chart(painter, chart_rect)
        elif self.chart_type == "cost_vs_return":
            self.draw_cost_return_scatter(painter, chart_rect)
        else:
            self.draw_empty_state(painter)

    def draw_empty_state(self, painter: QPainter):
        """Draw empty state message"""
        painter.fillRect(self.rect(), self.colors["background"])
        painter.setPen(self.colors["text"])
        painter.setFont(QFont("Arial", 12))
        painter.drawText(
            self.rect(), Qt.AlignmentFlag.AlignCenter, "No data to display"
        )

    def get_filtered_data(self):
        """Get filtered data based on settings"""
        return self.data[: self.max_runs]

    def draw_grid(self, painter: QPainter, chart_rect, num_points, min_y, max_y):
        """Draw chart grid"""
        painter.setPen(QPen(self.colors["grid"], 1))

        if num_points > 0:
            for i in range(num_points + 1):
                x = (
                    chart_rect.left() + (i * chart_rect.width()) / num_points
                    if num_points > 0
                    else chart_rect.center().x()
                )
                painter.drawLine(int(x), chart_rect.top(), int(x), chart_rect.bottom())

        num_y_lines = 5
        for i in range(num_y_lines + 1):
            y = chart_rect.bottom() - (i * chart_rect.height()) / num_y_lines
            painter.drawLine(chart_rect.left(), int(y), chart_rect.right(), int(y))

    def draw_break_even_line(
        self, painter: QPainter, chart_rect, min_y, max_y, value=0
    ):
        """Draw break-even reference line"""
        y_100 = self.value_to_y(value, min_y, max_y, chart_rect)
        if chart_rect.top() <= y_100 <= chart_rect.bottom():
            painter.setPen(QPen(self.colors["break_even"], 2, Qt.PenStyle.DashLine))
            painter.drawLine(
                chart_rect.left(), int(y_100), chart_rect.right(), int(y_100)
            )

            painter.setPen(self.colors["break_even"])
            painter.setFont(QFont("Arial", 8))
            painter.drawText(chart_rect.right() + 5, int(y_100 + 4), f"{value:.0f}")

    def draw_trend_line(self, painter: QPainter, chart_rect, points, min_y, max_y):
        """Draw trend line using linear regression"""
        if len(points) < 2:
            return

        x_coords = list(range(len(points)))
        y_values = [p[1] for p in points]

        n = len(points)
        sum_x = sum(x_coords)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_coords, y_values))
        sum_x2 = sum(x * x for x in x_coords)

        if n * sum_x2 - sum_x * sum_x == 0:
            return

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n

        painter.setPen(QPen(self.colors["break_even"], 2, Qt.PenStyle.DashLine))

        y_start = intercept
        y_end = slope * (n - 1) + intercept

        x1 = chart_rect.left()
        x2 = chart_rect.right()

        y1_chart = self.value_to_y(y_start, min_y, max_y, chart_rect)
        y2_chart = self.value_to_y(y_end, min_y, max_y, chart_rect)

        painter.drawLine(int(x1), int(y1_chart), int(x2), int(y2_chart))

    def draw_data_points(self, painter: QPainter, chart_rect, points, min_y, max_y):
        """Draw data points as line with markers"""
        if len(points) < 2:
            return

        painter.setPen(QPen(self.colors["neutral"], 2))

        for i in range(len(points) - 1):
            x1 = self.index_to_x(i, len(points), chart_rect)
            y1 = self.value_to_y(points[i][1], min_y, max_y, chart_rect)
            x2 = self.index_to_x(i + 1, len(points), chart_rect)
            y2 = self.value_to_y(points[i + 1][1], min_y, max_y, chart_rect)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        for i, (_, value) in enumerate(points):
            x = self.index_to_x(i, len(points), chart_rect)
            y = self.value_to_y(value, min_y, max_y, chart_rect)

            if value >= 0:
                color = self.colors["positive"]
            else:
                color = self.colors["negative"]

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(150), 1))
            radius = 4
            painter.drawEllipse(
                int(x) - radius, int(y) - radius, radius * 2, radius * 2
            )

    def draw_scatter_points(self, painter: QPainter, chart_rect, points, max_val):
        """Draw scatter plot points"""
        for cost, return_val in points:
            x = chart_rect.left() + (cost / max_val) * chart_rect.width()
            y = chart_rect.bottom() - (return_val / max_val) * chart_rect.height()

            if return_val >= cost:
                color = self.colors["positive"]
            else:
                color = self.colors["negative"]

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(150), 1))
            radius = 5
            painter.drawEllipse(
                int(x) - radius, int(y) - radius, radius * 2, radius * 2
            )

    def draw_axis_labels(self, painter: QPainter, chart_rect, num_points, min_y, max_y):
        """Draw axis labels"""
        painter.setPen(self.colors["text"])
        painter.setFont(QFont("Arial", 8))

        for i in range(0, num_points, max(1, num_points // 10)):
            x = self.index_to_x(i, num_points, chart_rect)
            painter.drawText(int(x - 15), chart_rect.bottom() + 15, f"R{i + 1}")

        num_labels = 5
        for i in range(num_labels + 1):
            y = chart_rect.bottom() - (i * chart_rect.height()) / num_labels
            value = max_y - (i * (max_y - min_y) / num_labels)
            painter.drawText(chart_rect.left() - 40, int(y + 4), f"{value:.0f}%")

        painter.drawText(chart_rect.center().x() - 30, chart_rect.bottom() + 35, "Run")

        painter.save()
        painter.translate(chart_rect.left() - 10, chart_rect.center().y() + 30)
        painter.rotate(-90)
        painter.drawText(0, 0, "Return (%)")
        painter.restore()

    def draw_scatter_axis_labels(self, painter: QPainter, chart_rect, max_val):
        """Draw scatter plot axis labels"""
        painter.setPen(self.colors["text"])
        painter.setFont(QFont("Arial", 8))

        painter.drawText(
            chart_rect.center().x() - 30, chart_rect.bottom() + 15, "Cost (PED)"
        )

        painter.save()
        painter.translate(chart_rect.left() - 10, chart_rect.center().y() + 30)
        painter.rotate(-90)
        painter.drawText(0, 0, "Return (PED)")
        painter.restore()

        for i in range(6):
            value = (i / 5) * max_val
            y = chart_rect.bottom() - (i / 5) * chart_rect.height()
            painter.drawText(chart_rect.left() - 35, int(y + 4), f"{value:.1f}")

            x = chart_rect.left() + (i / 5) * chart_rect.width()
            painter.drawText(int(x - 10), chart_rect.bottom() + 15, f"{value:.1f}")

    def draw_title(self, painter: QPainter, title: str):
        """Draw chart title"""
        painter.setPen(self.colors["text"])
        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.drawText(10, 20, title)

    def index_to_x(self, index: int, total: int, chart_rect) -> float:
        """Convert index to x coordinate"""
        if total <= 1:
            return chart_rect.center().x()
        return chart_rect.left() + (index / (total - 1)) * chart_rect.width()

    def value_to_y(
        self, value: float, min_val: float, max_val: float, chart_rect
    ) -> float:
        """Convert value to y coordinate"""
        if max_val == min_val:
            return chart_rect.center().y()
        normalized = (value - min_val) / (max_val - min_val)
        return chart_rect.bottom() - normalized * chart_rect.height()

    def draw_return_chart(self, painter: QPainter, chart_rect):
        """Draw return percentage line chart"""
        painter.fillRect(self.rect(), self.colors["background"])

        filtered_data = self.get_filtered_data()
        if not filtered_data:
            self.draw_empty_state(painter)
            return

        points = []
        for i, item in enumerate(filtered_data):
            cost = float(item.get("total_cost", 0) or 0)
            return_val = float(item.get("total_return", 0) or 0)
            return_pct = ((return_val - cost) / cost * 100) if cost > 0 else 0
            points.append((i, return_pct))

        if not points:
            self.draw_empty_state(painter)
            return

        y_values = [p[1] for p in points]
        min_y = min(y_values)
        max_y = max(y_values)
        y_range = max_y - min_y
        if y_range < 50:
            y_range = 50
        y_padding = y_range * 0.1
        min_y -= y_padding
        max_y += y_padding

        self.draw_grid(painter, chart_rect, len(points), min_y, max_y)
        self.draw_break_even_line(painter, chart_rect, min_y, max_y, 0)

        if len(points) >= 2 and self.show_trend_line:
            self.draw_trend_line(painter, chart_rect, points, min_y, max_y)

        self.draw_data_points(painter, chart_rect, points, min_y, max_y)
        self.draw_axis_labels(painter, chart_rect, len(points), min_y, max_y)
        self.draw_title(painter, "Run TT Return (%)")

    def draw_cost_return_scatter(self, painter: QPainter, chart_rect):
        """Draw cost vs return scatter plot"""
        painter.fillRect(self.rect(), self.colors["background"])

        filtered_data = self.get_filtered_data()
        if not filtered_data:
            self.draw_empty_state(painter)
            return

        points = []
        for item in filtered_data:
            cost = float(item.get("total_cost", 0) or 0)
            return_val = float(item.get("total_return", 0) or 0)
            if cost > 0:
                points.append((cost, return_val))

        if not points:
            self.draw_empty_state(painter)
            return

        costs = [p[0] for p in points]
        returns = [p[1] for p in points]
        max_cost = max(costs) * 1.1
        max_return = max(returns) * 1.1
        max_val = max(max_cost, max_return)

        self.draw_scatter_points(painter, chart_rect, points, max_val)

        painter.setPen(QPen(self.colors["break_even"], 2, Qt.PenStyle.DashLine))
        painter.drawLine(
            chart_rect.left(), chart_rect.bottom(), chart_rect.right(), chart_rect.top()
        )

        self.draw_scatter_axis_labels(painter, chart_rect, max_val)
        self.draw_title(painter, "Cost to Kill vs Return")


class SimpleAnalysisWidget(QWidget):
    """Simplified analysis widget with 2 charts"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = None
        self.session_data: List[Dict[str, Any]] = []
        self.setup_ui()
        logger.info("SimpleAnalysisWidget initialized")

    def setup_ui(self):
        """Setup the simplified analysis UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        stats_bar = self.create_stats_bar()
        layout.addWidget(stats_bar)

        top_chart_frame = self.create_chart_frame(
            "Run TT Return (%)", "return_percentage"
        )
        layout.addWidget(top_chart_frame)

        bottom_chart_frame = self.create_chart_frame(
            "Cost to Kill vs Return", "cost_vs_return"
        )
        layout.addWidget(bottom_chart_frame)

        layout.addStretch()

        load_timer = QTimer()
        load_timer.timeout.connect(self._on_load_timer)
        load_timer.setSingleShot(True)
        load_timer.start(500)

    def create_stats_bar(self):
        """Create stats summary bar"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 4px;
            }
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 5, 10, 5)

        self.avg_return_label = QLabel("Avg Return: --")
        self.avg_return_label.setFont(QFont("Consolas", 10))
        self.avg_return_label.setStyleSheet("color: #8B949E;")
        layout.addWidget(self.avg_return_label)

        self.best_run_label = QLabel("Best: --")
        self.best_run_label.setFont(QFont("Consolas", 10))
        self.best_run_label.setStyleSheet("color: #4CAF50;")
        layout.addWidget(self.best_run_label)

        self.worst_run_label = QLabel("Worst: --")
        self.worst_run_label.setFont(QFont("Consolas", 10))
        self.worst_run_label.setStyleSheet("color: #F44336;")
        layout.addWidget(self.worst_run_label)

        self.hit_rate_label = QLabel("Hit Rate: --")
        self.hit_rate_label.setFont(QFont("Consolas", 10))
        self.hit_rate_label.setStyleSheet("color: #2196F3;")
        layout.addWidget(self.hit_rate_label)

        layout.addStretch()

        return frame

    def create_chart_frame(self, title: str, chart_type: str):
        """Create a chart frame with title and chart"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #8B949E;")
        layout.addWidget(title_label)

        chart = SimpleAnalysisChartWidget()
        chart.setStyleSheet("background-color: #0D1117; border-radius: 4px;")
        chart.set_chart_type(chart_type)
        layout.addWidget(chart)

        if chart_type == "return_percentage":
            self.top_chart = chart
        else:
            self.bottom_chart = chart

        return frame

    def set_db_manager(self, db_manager):
        """Set database manager"""
        self.db_manager = db_manager

    def _on_load_timer(self):
        """Handle load timer timeout"""
        if self.db_manager:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.load_data())
                loop.close()
            except Exception as e:
                logger.debug(f"Analysis load error: {e}")

    async def load_data(self):
        """Load session data"""
        try:
            if self.db_manager:
                self.session_data = await self.db_manager.get_all_sessions()
                logger.info(f"Loaded {len(self.session_data)} sessions for analysis")
                self.top_chart.set_data(self.session_data)
                self.bottom_chart.set_data(self.session_data)
                self.update_stats()
        except Exception as e:
            logger.error(f"Error loading analysis data: {e}")

    def update_with_current_session(self, session_data: dict):
        """Update analysis with current session data in real-time"""
        if not session_data:
            return

        session_id = session_data.get("id", "")

        found_existing = False
        for i, session in enumerate(self.session_data):
            if session.get("id") == session_id:
                self.session_data[i] = session_data
                found_existing = True
                break

        if not found_existing:
            self.session_data.insert(0, session_data)

        self.top_chart.set_data(self.session_data)
        self.bottom_chart.set_data(self.session_data)
        self.update_stats()

    def update_stats(self):
        """Update statistics display"""
        if not self.session_data:
            return

        filtered_data = self.session_data[: self.top_chart.max_runs]

        returns = []
        profit_runs = 0
        total_runs = 0

        for item in filtered_data:
            cost = float(item.get("total_cost", 0) or 0)
            return_val = float(item.get("total_return", 0) or 0)
            if cost > 0:
                return_pct = (return_val - cost) / cost * 100
                returns.append(return_pct)
                total_runs += 1
                if return_val >= cost:
                    profit_runs += 1

        if returns:
            avg = sum(returns) / len(returns)
            best = max(returns)
            worst = min(returns)
            hit_rate = (profit_runs / len(returns) * 100) if returns else 0

            self.avg_return_label.setText(f"Avg Return: {avg:.1f}%")
            self.best_run_label.setText(f"Best: {best:.1f}%")
            self.worst_run_label.setText(f"Worst: {worst:.1f}%")
            self.hit_rate_label.setText(f"Hit Rate: {hit_rate:.1f}%")

    def load_specific_session(self, session_data: Dict[str, Any]):
        """Load analysis for a specific session"""
        # Filter to show only the selected session
        self.session_data = [session_data]
        self.top_chart.set_data(self.session_data)
        self.bottom_chart.set_data(self.session_data)
        self.update_stats()

        # Update title to show this is a single session view
        if hasattr(self, "title_label"):
            session_id = session_data.get("id", "Unknown")[:8]
            self.title_label.setText(f"Analysis - Session {session_id}")

    def update_realtime(self):
        """Update analysis in real-time - wrapper for load_data"""
        try:
            # Skip async loading during real-time updates to avoid event loop issues
            # The analysis will be refreshed when needed via refresh() method
            logger.debug(
                "Skipping real-time analysis update to avoid event loop issues"
            )
        except Exception as e:
            logger.error(f"Error updating analysis in real-time: {e}")

    def refresh(self):
        """Refresh all data"""
        try:
            # Use QTimer to schedule async operation safely in Qt context
            from PyQt6.QtCore import QTimer

            def async_load():
                try:
                    import asyncio

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.load_data())
                finally:
                    loop.close()

            QTimer.singleShot(0, async_load)
        except Exception as e:
            logger.error(f"Error refreshing analysis data: {e}")
