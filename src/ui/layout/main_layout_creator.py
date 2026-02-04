"""Main window UI layout creation methods
"""

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
)

from ..components.status_indicator import StatusIndicator

logger = logging.getLogger(__name__)


class MainLayoutCreator:
    """Handles creation of the main window layout components"""

    def __init__(self, parent_window):
        self.parent = parent_window

    def create_top_tab_bar(self):
        """Create the top tab bar with buttons for all tabs"""
        self.parent.tab_bar_frame = QFrame()
        self.parent.tab_bar_frame.setFixedHeight(30)
        self.parent.tab_bar_frame.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border-bottom: 1px solid #30363D;
            }
        """)

        tab_bar_layout = QHBoxLayout(self.parent.tab_bar_frame)
        tab_bar_layout.setContentsMargins(4, 0, 4, 0)
        tab_bar_layout.setSpacing(2)

        self.parent.tab_buttons = {}

        for i, tab_name in enumerate(self.parent.TAB_NAMES):
            btn = QPushButton(tab_name)
            btn.setFixedHeight(36)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            if i == 0:
                btn.setChecked(True)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #238636;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 4px 4px 0 0;
                        padding: 6px 16px;
                        font-weight: bold;
                        font-size: 11px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #8B949E;
                        border: none;
                        border-radius: 4px 4px 0 0;
                        padding: 6px 16px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #21262D;
                        color: #E6EDF3;
                    }
                """)

            btn.clicked.connect(
                lambda checked, name=tab_name, button=btn: self.parent.on_tab_clicked(
                    name, button
                )
            )
            self.parent.tab_buttons[tab_name] = btn
            tab_bar_layout.addWidget(btn)

        tab_bar_layout.addStretch()

        return self.parent.tab_bar_frame

    def create_middle_content_area(self):
        """Create the middle content area that changes based on selected tab"""
        self.parent.content_stack = QStackedWidget()
        self.parent.content_stack.setStyleSheet("""
            QStackedWidget {
                background-color: #0D1117;
            }
        """)

        return self.parent.content_stack

    def create_bottom_control_bar(self):
        """Create the persistent bottom control bar"""
        self.parent.bottom_bar_frame = QFrame()
        self.parent.bottom_bar_frame.setFixedHeight(40)
        self.parent.bottom_bar_frame.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border-top: 1px solid #30363D;
            }
        """)

        bottom_layout = QHBoxLayout(self.parent.bottom_bar_frame)
        bottom_layout.setContentsMargins(10, 4, 10, 4)
        bottom_layout.setSpacing(8)

        left_section = QHBoxLayout()
        left_section.setSpacing(8)

        self.parent.version_label = QLabel("Version: 1.0.0")
        self.parent.version_label.setFont(QFont("Arial", 9))
        self.parent.version_label.setStyleSheet("color: #8B949E;")
        left_section.addWidget(self.parent.version_label)

        self.parent.status_indicator = StatusIndicator()
        self.parent.status_indicator.setStatusTip("Checking readiness...")
        left_section.addWidget(self.parent.status_indicator)

        self.parent.start_run_btn = QPushButton("Start Run")
        self.parent.start_run_btn.setFixedHeight(32)
        self.parent.start_run_btn.setFixedWidth(100)
        self.parent.start_run_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2EA043;
            }
            QPushButton:disabled {
                background-color: #3D444D;
                color: #6A737D;
            }
        """)
        self.parent.start_run_btn.clicked.connect(self.parent.toggle_session)
        left_section.addWidget(self.parent.start_run_btn)

        self.parent.pause_btn = QPushButton("Pause Logging")
        self.parent.pause_btn.setFixedHeight(32)
        self.parent.pause_btn.setFixedWidth(100)
        self.parent.pause_btn.setCheckable(True)
        self.parent.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #1F6FEB;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #388BFD;
            }
            QPushButton:checked {
                background-color: #F0A100;
            }
        """)
        self.parent.pause_btn.clicked.connect(self.parent.toggle_pause_logging)
        left_section.addWidget(self.parent.pause_btn)

        self.parent.streamer_ui_btn = QPushButton("Show Overlay")
        self.parent.streamer_ui_btn.setFixedHeight(32)
        self.parent.streamer_ui_btn.setStyleSheet("""
            QPushButton {
                background-color: #6E7681;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #8B949E;
            }
        """)
        self.parent.streamer_ui_btn.setCheckable(True)
        self.parent.streamer_ui_btn.toggled.connect(self.parent.toggle_overlay)
        left_section.addWidget(self.parent.streamer_ui_btn)

        bottom_layout.addLayout(left_section)
        bottom_layout.addStretch()

        right_section = QHBoxLayout()
        right_section.setSpacing(8)

        self.parent.donate_btn = QPushButton("Donate :)")
        self.parent.donate_btn.setFixedHeight(32)
        self.parent.donate_btn.setFixedWidth(80)
        self.parent.donate_btn.setStyleSheet("""
            QPushButton {
                background-color: #A371F7;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #B088F9;
            }
        """)
        self.parent.donate_btn.clicked.connect(self.parent.open_donate)
        right_section.addWidget(self.parent.donate_btn)

        self.parent.theme_btn = QPushButton("Toggle Theme")
        self.parent.theme_btn.setFixedHeight(32)
        self.parent.theme_btn.setStyleSheet("""
            QPushButton {
                background-color: #6E7681;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #8B949E;
            }
        """)
        self.parent.theme_btn.clicked.connect(self.parent.toggle_theme)
        right_section.addWidget(self.parent.theme_btn)

        bottom_layout.addLayout(right_section)

        return self.parent.bottom_bar_frame
