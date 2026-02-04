"""Streamlined Dashboard Tab for LewtNanny
Clean, focused interface with essential controls and metrics
"""

import logging
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.models.models import ActivityType

logger = logging.getLogger(__name__)


class StreamlinedDashboard(QWidget):
    """Streamlined dashboard with unified interface"""

    event_selected = pyqtSignal(dict)
    session_export_requested = pyqtSignal()
    session_clear_requested = pyqtSignal()
    monitoring_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_activity = None
        self.is_monitoring = False
        self.setup_ui()
        logger.info("Streamlined dashboard initialized")

    def setup_ui(self):
        """Setup streamlined UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        # Create unified header section
        header_section = self._create_header_section()
        layout.addWidget(header_section)

        # Create unified content area
        content_area = self._create_content_area()
        layout.addWidget(content_area)

        self.setStyleSheet("""
            QWidget {
                background-color: #0D1117;
                color: #E6EDF3;
            }
            QLabel {
                color: #E6EDF3;
                font-family: Arial;
                font-size: 12px;
                font-weight: bold;
            }
            QLabel[class="metric-icon"] {
                font-size: 16px;
            }
            QLabel[class="metric-label"] {
                color: #8B949E;
                font-weight: bold;
                font-size: 10px;
            }
            QLabel[class="metric-value"] {
                color: #21262D;
                background-color: #161B22;
                border: 1px solid #21262D;
                border-radius: 3px;
                padding: 2px 4px;
                font-family: Consolas;
                font-size: 10px;
                font-weight: bold;
            }
            QComboBox {
                background-color: #0D1117;
                border: 1px solid #21262D;
                border-radius: 4px;
                padding: 4px;
                color: #E6EDF3;
                font-size: 11px;
                selection-background-color: #0969DA;
            }
            QPushButton {
                background-color: #43A047;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 8px;
                font-weight: 600;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #45A047;
            }
            QFrame[class="panel"] {
                background-color: #161B22;
                border: 1px solid #21262D;
                border-radius: 6px;
                padding: 6px;
                margin-top: 6px;
            }
            QFrame[class="content-panel"] {
                border: none;
                background-color: #161B22;
                padding: 8px;
                border-radius: 8px;
            }
            QTableWidget {
                background-color: #161B22;
                gridline-color: #21262D;
                color: #E6EDF3;
                selection-background-color: #0969DA;
                alternate-background-color: #1B5E76;
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #0969DA;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #21262D;
                color: #8B949E;
                font-weight: 600;
                font-size: 11px;
                padding: 8px 4px;
                border-bottom: 1px solid #21262D;
                border-left: 1px solid #21262D;
                border-right: 1px solid #21262D;
            }
        """)

        # Setup signals
        self.event_selected.connect(self._on_event_selected)
        self.session_export_requested.connect(self._on_session_export)
        self.session_clear_requested.connect(self._on_session_clear)
        self.monitoring_toggled.connect(self._on_monitoring_toggled)

        logger.debug("Streamlined dashboard setup complete")

    def _create_header_section(self):
        """Create unified header section"""
        header_frame = QFrame()
        header_frame.setProperty("class", "header")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        # Title
        title = QLabel("LewtNanny Monitor")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #43A047;")
        header_layout.addWidget(title)

        # Controls row
        controls_row = QWidget()
        controls_layout = QHBoxLayout(controls_row)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)

        # Session label
        session_label = QLabel("Session: Inactive")
        session_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        session_label.setProperty("class", "session-label")

        # Activity selector
        activity_combo = QComboBox()
        activity_combo.addItems([t.value for t in ActivityType])
        activity_combo.setMaximumWidth(100)
        activity_combo.setMinimumWidth(80)
        activity_combo.setStyleSheet("""
            QComboBox {
                background-color: #0D1117;
                border: 1px solid #21262D;
                border-radius: 4px;
                padding: 4px;
                color: #E6EDF3;
                font-size: 11px;
            }
        """)

        # Monitor toggle button
        self.monitor_btn = QPushButton("Start Monitoring")
        self.monitor_btn.setProperty("class", "monitor-btn")
        self.monitor_btn.clicked.connect(self.toggle_monitoring)

        # Assemble controls row
        controls_layout.addWidget(session_label)
        controls_layout.addStretch()
        controls_layout.addWidget(QLabel("Activity:"))
        controls_layout.addWidget(activity_combo)
        controls_layout.addWidget(self.monitor_btn)
        header_layout.addLayout(controls_layout)

        header_layout.addStretch()
        header_frame.setLayout(header_layout)

        return header_frame

    def _create_content_area(self):
        """Create unified content area with stats and events"""
        content_frame = QFrame()
        content_frame.setProperty("class", "content-panel")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)

        # Metrics panel
        metrics_panel = self._create_metrics_panel()
        content_layout.addWidget(metrics_panel)

        # Events panel
        events_panel = self._create_events_panel()
        content_layout.addWidget(events_panel)

        content_frame.setLayout(content_layout)

        return content_frame

    def _create_metrics_panel(self):
        """Create metrics panel with essential info only"""
        panel = QFrame()
        panel.setProperty("class", "panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(8, 8, 8, 8)
        panel_layout.setSpacing(6)

        # Key metrics title
        title_label = QLabel("Key Metrics")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setProperty("class", "metric-label")
        title_label.setStyleSheet("color: #8B949E;")
        panel_layout.addWidget(title_label)

        # Metrics grid - 2x2 layout for clean look
        grid_layout = QGridLayout()
        grid_layout.setSpacing(4)
        grid_layout.setContentsMargins(4, 4, 4, 4)

        self.metrics = {}
        key_configs = [
            ("cost", "💰", "0.00", "#43A047"),
            ("loot", "📦", "0.00", "#43A047"),
            ("profit", "📊", "0.00", "#E53935"),
        ]

        for _, (icon, key, default, color) in enumerate(key_configs):
            # Create metric container
            metric_widget = QWidget()
            metric_layout = QVBoxLayout(metric_widget)
            metric_layout.setSpacing(2)

            # Icon and label row
            icon_label = QLabel(icon)
            icon_label.setProperty("class", "metric-icon")
            icon_label.setFont(QFont("Arial", 12))
            icon_label.setStyleSheet(f"color: {color};")

            text_label = QLabel(f"{key.title()}:")
            text_label.setProperty("class", "metric-label")
            text_label.setStyleSheet("color: #8B949E;")

            label_row = QHBoxLayout()
            label_row.addWidget(icon_label)
            label_row.addStretch()
            label_row.addWidget(text_label)
            label_row.setContentsMargins(0, 0, 0, 0)

            metric_layout.addLayout(label_row)

            # Value display
            value_label = QLabel(default)
            value_label.setProperty("class", "metric-value")
            value_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
            value_label.setStyleSheet(
                f"color: {color}; background-color: #161B22; border: 1px solid #21262D; border-radius: 3px; padding: 2px 4px;"
            )
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            metric_layout.addLayout(value_label)
            metric_layout.setContentsMargins(0, 0, 0, 0, 0)

            # Store widget reference
            metric_layout.addWidget(metric_widget)
            self.metrics[key] = value_label

        # Arrange metrics in grid
        for i, _ in enumerate(key_configs[:4]):
            row, col = divmod(i, 2)
            widget = panel_layout.itemAtPosition(i)
            widget.setStyleSheet("font-size: 10px;")

            widget.setProperty("class", "metric-card")
            widget.setProperty("row", str(row))
            grid_layout.addWidget(widget, row, col)

        panel_layout.addLayout(grid_layout)

        panel.setLayout(panel_layout)
        return panel

    def _create_events_panel(self):
        """Create events panel with clean design"""
        panel = QFrame()
        panel.setProperty("class", "content-panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(8, 8, 8, 8)
        panel_layout.setSpacing(6)

        # Header
        header_label = QLabel("Recent Activity")
        header_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        header_label.setStyleSheet("color: #8B949E;")
        panel_layout.addWidget(header_label)

        # Events table
        self.event_table = QTableWidget()
        self.event_table.setColumnCount(3)
        self.event_table.setHorizontalHeaderLabels(["Time", "Type", "Details"])
        self.event_table.setMaximumHeight(120)
        self.event_table.setShowGrid(False)
        self.event_table.setAlternatingRowColors(True)

        header = self.event_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setDefaultSectionSize(0, 60)  # type: ignore[call-overload]
            header.setDefaultSectionSize(1, 120)  # type: ignore[call-overload]

        panel_layout.addWidget(self.event_table)
        panel.setLayout(panel_layout)

        return panel

    def _on_event_selected(self, event_data: dict):
        """Handle event selection"""
        self.event_selected.emit(event_data)

    def _on_session_export(self):
        """Handle session export"""
        self.session_export_requested.emit()

    def _on_session_clear(self):
        """Handle session clear"""
        self.session_clear_requested.emit()

    def _on_monitoring_toggled(self, checked: bool):
        """Toggle monitoring state"""
        self.is_monitoring = checked
        self.monitor_toggled.emit(checked)  # type: ignore[attr-defined]

        # Update button text and style
        if hasattr(self, "monitor_btn"):
            self.monitor_btn.setText("Stop Monitoring" if checked else "Start Monitoring")
            self.monitor_btn.setProperty(
                "class", "monitor-btn-active" if checked else "monitor-btn"
            )

    def handle_new_event(self, event_data: dict):
        """Add new event to table"""
        # Limit to last 20 events
        if self.event_table.rowCount() > 20:
            self.event_table.removeRow(0)

        row = self.event_table.rowCount()
        self.event_table.insertRow(row)

        # Format event data
        event_type = event_data.get("event_type", "Unknown")
        event_data.get("parsed_data", {})

        # Time
        time_item = QTableWidgetItem(datetime.now().strftime("%H:%M:%S"))
        time_item.setFont(QFont("Consolas", 9))
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

        # Type with color coding
        type_item = QTableWidgetItem(event_type.replace("_", " ").title())
        if "loot" in event_type:
            type_item.setStyleSheet("color: #43A047;")
        elif "combat" in event_type:
            type_item.setStyleSheet("color: #E6EDF3;")
        elif "global" in event_type:
            type_item.setStyleSheet("color: #FFB300;")

        type_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

        # Details
        details = self._format_event_details(event_data)
        details_item = QTableWidgetItem(details)
        details_item.setFont(QFont("Arial", 9))

        # Add to table
        self.event_table.setItem(row, 0, time_item)
        self.event_table.setItem(row, 1, type_item)
        self.event_table.setItem(row, 2, details_item)

        # Auto-scroll to latest
        self.event_table.scrollToBottom()

        logger.debug(f"Added event: {event_type}")

    def _format_event_details(self, event_data: dict) -> str:
        """Format event details for display"""
        event_type = event_data.get("event_type", "")
        parsed_data = event_data.get("parsed_data", {})

        if event_type == "loot":
            item_name = parsed_data.get("item_name", "Unknown")
            quantity = parsed_data.get("quantity", 1)
            value = parsed_data.get("value", 0)
            return f"{item_name} x ({quantity}) ({value} PED)"
        elif event_type == "combat":
            damage = parsed_data.get("damage", 0)
            if parsed_data.get("critical", False):
                return f"Hit: {damage}"
            elif parsed_data.get("miss", False):
                return "Miss"
            else:
                return f"Hit: {damage}"
        elif event_type == "skill":
            skill = parsed_data.get("skill", "")
            exp = parsed_data.get("experience", 0)
            return f"{skill} +{exp}"
        elif event_type == "global":
            player = parsed_data.get("player", "Unknown")
            value = parsed_data.get("value", 0)
            return f"{player} killed creature for {value:.0f} PED"
        else:
            return str(event_data.get("raw_message", "Unknown"))[:50]

    def update_metrics(self, metrics_data: dict):
        """Update key metrics display"""
        for key, _label in self.metrics.items():
            if key in metrics_data:
                value = metrics_data.get(key, 0)
                if key == "total_cost":
                    self.metrics[key].setText(f"💰 {value:.2f}")
                elif key == "total_loot":
                    self.metrics[key].setText(f"📦 {value:.2f}")
                elif key == "net_profit":
                    profit = value
                    self.metrics[key].setText(
                        f"📊 {profit:+.2f}" if profit >= 0 else f"📊 {profit:.2f}"
                    )
                else:
                    self.metrics[key].setText(f"{value:.2f}")

                # Add glow effect for profit
                if key == "net_profit":
                    self.metrics[key].setProperty(
                        "class", "profit-positive" if value >= 0 else "profit-negative"
                    )

    def set_activity(self, activity_type: ActivityType):
        """Set current activity type"""
        self.current_activity = activity_type

        if hasattr(self, "activity_combo"):
            # Find matching activity
            for i, t in enumerate(ActivityType):
                if t.value == activity_type:
                    self.activity_combo.setCurrentIndex(i)
                    break

    def add_sample_events(self):
        """Add sample events for testing"""
        sample_events = [
            {
                "event_type": "loot",
                "activity_type": "hunting",
                "parsed_data": {"items": "Animal Oil x (5)", "value": 1.25},
            },
            {"event_type": "combat", "activity_type": "hunting", "parsed_data": {"damage": 25.5}},
            {
                "event_type": "skill",
                "activity_type": "hunting",
                "parsed_data": {"skill": "Rifle", "experience": 0.5},
            },
        ]

        for event in sample_events:
            self.handle_new_event(event)
