"""
Tabbed MainWindow for LewtNanny
Implements the detailed UI specification with custom tab bar and persistent bottom control bar
"""

import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from decimal import Decimal

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QTextEdit, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QGroupBox, QFrame,
    QComboBox, QSpinBox, QCheckBox, QFileDialog,
    QStatusBar, QFrame, QProgressBar, QMessageBox,
    QToolBar, QToolButton, QDockWidget, QStackedWidget,
    QLineEdit, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QAction, QIcon, QColor, QPixmap, QPainter, QRadialGradient

from src.models.models import ActivityType, EventType
from src.ui.overlay import SessionOverlay
from src.ui.components.config_tab import ConfigTab
from src.ui.components.combat_tab import CombatTabWidget
from src.services.game_data_service import GameDataService
from src.ui.components.crafting_tab import CraftingTabWidget
from src.ui.components.weapon_selector import WeaponSelector

logger = logging.getLogger(__name__)


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
            "green": "Ready"
        }
        self._status_message = messages.get(value, "Unknown")
        self._update_appearance()

    def _update_appearance(self):
        colors = {
            "red": ("#FF4444", "#880000"),
            "yellow": ("#FFAA00", "#884400"),
            "green": ("#44FF44", "#008800")
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

    def leaveEvent(self, event):
        pass


class TabbedMainWindow(QMainWindow):
    """Main application window with custom tab bar and persistent bottom control bar"""

    TAB_NAMES = ["Loot", "Analysis", "Skills", "Combat", "Crafting", "Twitch", "Config"]

    def __init__(self, db_manager, config_manager):
        super().__init__()

        self.db_manager = db_manager
        self.config_manager = config_manager
        self.chat_reader = None
        self.overlay: Optional[SessionOverlay] = None
        self.current_session_id: Optional[str] = None
        self.current_session_start: Optional[datetime] = None
        self.current_theme = 'dark'
        self.is_logging_paused = False
        
        # Total cost calculation tracking
        self.total_shots_taken = 0
        self.cost_per_attack = 0.0

        self.setWindowTitle("LewtNanny - Entropia Universe Loot Tracker")
        self.setGeometry(100, 100, 1200, 800)

        logger.info("TabbedMainWindow initializing...")

        self.setup_ui()
        self.setup_menubar()
        self.setup_status_bar()
        self.setup_timer()
        
        # Initialize overlay early so it can receive events
        self.overlay = SessionOverlay(self.db_manager, self.config_manager)
        logger.info("TabbedMainWindow initialization complete")

    def setup_ui(self):
        """Setup main UI with custom tab bar and bottom control bar"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.create_top_tab_bar()
        self.create_middle_content_area()
        self.create_bottom_control_bar()

        logger.debug("Main UI setup complete")

        QTimer.singleShot(500, self._load_past_runs_on_startup)

    def create_top_tab_bar(self):
        """Create the top tab bar with buttons for all tabs"""
        self.tab_bar_frame = QFrame()
        self.tab_bar_frame.setFixedHeight(40)
        self.tab_bar_frame.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border-bottom: 1px solid #30363D;
            }
        """)

        tab_bar_layout = QHBoxLayout(self.tab_bar_frame)
        tab_bar_layout.setContentsMargins(4, 0, 4, 0)
        tab_bar_layout.setSpacing(2)

        self.tab_buttons = {}

        for i, tab_name in enumerate(self.TAB_NAMES):
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

            btn.clicked.connect(lambda checked, name=tab_name, button=btn: self.on_tab_clicked(name, button))
            self.tab_buttons[tab_name] = btn
            tab_bar_layout.addWidget(btn)

        tab_bar_layout.addStretch()

        self.main_layout.addWidget(self.tab_bar_frame)

    def on_tab_clicked(self, tab_name: str, button: QPushButton):
        """Handle tab button click"""
        self.content_stack.setCurrentIndex(self.TAB_NAMES.index(tab_name))

        for name, btn in self.tab_buttons.items():
            if name == tab_name:
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

        logger.debug(f"Switched to tab: {tab_name}")

    def create_middle_content_area(self):
        """Create the middle content area that changes based on selected tab"""
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("""
            QStackedWidget {
                background-color: #0D1117;
            }
        """)

        self.main_layout.addWidget(self.content_stack, 1)

        self.create_loot_tab()
        self.create_analysis_tab()
        self.create_skills_tab()
        self.create_combat_tab()
        self.create_crafting_tab()
        self.create_twitch_tab()
        self.create_config_tab()

    def create_bottom_control_bar(self):
        """Create the persistent bottom control bar"""
        self.bottom_bar_frame = QFrame()
        self.bottom_bar_frame.setFixedHeight(50)
        self.bottom_bar_frame.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border-top: 1px solid #30363D;
            }
        """)

        bottom_layout = QHBoxLayout(self.bottom_bar_frame)
        bottom_layout.setContentsMargins(10, 4, 10, 4)
        bottom_layout.setSpacing(8)

        left_section = QHBoxLayout()
        left_section.setSpacing(8)

        self.version_label = QLabel("Version: 1.0.0")
        self.version_label.setFont(QFont("Arial", 9))
        self.version_label.setStyleSheet("color: #8B949E;")
        left_section.addWidget(self.version_label)

        self.status_indicator = StatusIndicator()
        self.status_indicator.setStatusTip("Checking readiness...")
        left_section.addWidget(self.status_indicator)

        self.start_run_btn = QPushButton("Start Run")
        self.start_run_btn.setFixedHeight(32)
        self.start_run_btn.setFixedWidth(100)
        self.start_run_btn.setStyleSheet("""
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
        self.start_run_btn.clicked.connect(self.toggle_session)
        left_section.addWidget(self.start_run_btn)

        self.pause_btn = QPushButton("Pause Logging")
        self.pause_btn.setFixedHeight(32)
        self.pause_btn.setFixedWidth(100)
        self.pause_btn.setCheckable(True)
        self.pause_btn.setStyleSheet("""
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
        self.pause_btn.clicked.connect(self.toggle_pause_logging)
        left_section.addWidget(self.pause_btn)

        self.streamer_ui_btn = QPushButton("Show Streamer UI")
        self.streamer_ui_btn.setFixedHeight(32)
        self.streamer_ui_btn.setStyleSheet("""
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
        self.streamer_ui_btn.clicked.connect(self.toggle_streamer_ui)
        left_section.addWidget(self.streamer_ui_btn)

        bottom_layout.addLayout(left_section)
        bottom_layout.addStretch()

        right_section = QHBoxLayout()
        right_section.setSpacing(8)

        self.donate_btn = QPushButton("Donate :)")
        self.donate_btn.setFixedHeight(32)
        self.donate_btn.setFixedWidth(80)
        self.donate_btn.setStyleSheet("""
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
        self.donate_btn.clicked.connect(self.open_donate)
        right_section.addWidget(self.donate_btn)

        self.theme_btn = QPushButton("Toggle Theme")
        self.theme_btn.setFixedHeight(32)
        self.theme_btn.setStyleSheet("""
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
        self.theme_btn.clicked.connect(self.toggle_theme)
        right_section.addWidget(self.theme_btn)

        bottom_layout.addLayout(right_section)

        self.main_layout.addWidget(self.bottom_bar_frame)

    def create_loot_tab(self):
        """Create the Loot tab with summary, run log, and item breakdown"""
        loot_widget = QWidget()
        loot_layout = QVBoxLayout(loot_widget)
        loot_layout.setContentsMargins(8, 8, 8, 8)
        loot_layout.setSpacing(8)

        summary_section = self.create_loot_summary_section()
        loot_layout.addWidget(summary_section)

        run_log_section = self.create_run_log_table_section()
        loot_layout.addWidget(run_log_section, 1)  # Give run log stretch priority

        item_breakdown_section = self.create_item_breakdown_section()
        loot_layout.addWidget(item_breakdown_section, 1)  # Give item breakdown stretch priority

        self.content_stack.addWidget(loot_widget)
        logger.info("Loot tab created")

    def create_loot_summary_section(self):
        """Create the summary information section for Loot tab"""
        section = QGroupBox("Summary")
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #8B949E;
                font-size: 11px;
            }
        """)

        layout = QGridLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        summary_items = [
            ("Creatures Looted", "0"),
            ("Total Cost", "0.00 PED"),
            ("Total Return", "0.00 PED"),
            ("% Return", "0.0%"),
            ("Globals", "0"),
            ("HOFs", "0")
        ]

        self.loot_summary_labels = {}

        for i, (label, default) in enumerate(summary_items):
            row = i // 3
            col = i % 3

            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(2)

            lbl = QLabel(label)
            lbl.setFont(QFont("Arial", 9))
            lbl.setStyleSheet("color: #8B949E;")
            container_layout.addWidget(lbl)

            value_lbl = QLabel(default)
            value_lbl.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
            value_lbl.setStyleSheet("""
                color: #E6EDF3;
                background-color: #0D1117;
                border: 1px solid #30363D;
                border-radius: 4px;
                padding: 4px;
            """)
            container_layout.addWidget(value_lbl)

            self.loot_summary_labels[label] = value_lbl
            layout.addWidget(container, row, col)

        section.setLayout(layout)
        return section

    def create_run_log_table_section(self):
        """Create the run log table section for Loot tab"""
        section = QGroupBox("Run Log")
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #8B949E;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 28, 4, 4)  # Top margin accounts for title bar
        layout.setSpacing(4)

        self.run_log_table = QTableWidget()
        self.run_log_table.setColumnCount(7)
        self.run_log_table.setHorizontalHeaderLabels([
            "Status", "Start Time", "Duration", "Cost", "Return", "ROI", "Items"
        ])
        self.run_log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.run_log_table.setAlternatingRowColors(True)
        self.run_log_table.setSortingEnabled(True)
        self.run_log_table.setShowGrid(True)
        self.run_log_table.itemSelectionChanged.connect(self._on_run_log_selection_changed)

        header = self.run_log_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.run_log_table)

        section.setLayout(layout)
        return section

    def create_item_breakdown_section(self):
        """Create the item breakdown table section for Loot tab"""
        section = QGroupBox("Item Breakdown")
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #8B949E;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 28, 4, 4)  # Top margin accounts for title bar
        layout.setSpacing(4)

        self.item_breakdown_table = QTableWidget()
        self.item_breakdown_table.setColumnCount(5)
        self.item_breakdown_table.setHorizontalHeaderLabels([
            "Item Name", "Count", "Value", "Markup", "Total Value"
        ])
        self.item_breakdown_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.item_breakdown_table.setAlternatingRowColors(True)

        header = self.item_breakdown_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.item_breakdown_table)

        section.setLayout(layout)
        return section

    def create_analysis_tab(self):
        """Create the Analysis tab with 2 core charts"""
        from src.ui.components.simple_analysis import SimpleAnalysisWidget

        analysis_widget = SimpleAnalysisWidget()
        analysis_widget.set_db_manager(self.db_manager)
        self.analysis_widget = analysis_widget

        self.content_stack.addWidget(analysis_widget)
        logger.info("Analysis tab created with 2 core charts")

    def create_skills_tab(self):
        """Create the Skills tab with skill gain tracking"""
        skills_widget = QWidget()
        skills_layout = QVBoxLayout(skills_widget)
        skills_layout.setContentsMargins(8, 8, 8, 8)
        skills_layout.setSpacing(8)

        summary_field = self.create_skills_summary_field()
        skills_layout.addWidget(summary_field)

        skills_table = self.create_skills_table()
        skills_layout.addWidget(skills_table, 1)  # Give skills table stretch priority

        self.skills_tab = skills_widget
        self.content_stack.addWidget(skills_widget)
        logger.info("Skills tab created")

    def create_skills_summary_field(self):
        """Create the skills summary field"""
        section = QGroupBox("")
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        label = QLabel("Total Skill Gain:")
        label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        label.setStyleSheet("color: #8B949E;")
        layout.addWidget(label)

        self.total_skill_gain_value = QLabel("0.00")
        self.total_skill_gain_value.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self.total_skill_gain_value.setStyleSheet("""
            color: #E6EDF3;
            background-color: #0D1117;
            border: 1px solid #30363D;
            border-radius: 4px;
            padding: 4px 12px;
        """)
        layout.addWidget(self.total_skill_gain_value)

        layout.addStretch()

        section.setLayout(layout)
        return section

    def create_skills_table(self):
        """Create the skills table"""
        section = QGroupBox("Skills")
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #8B949E;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 28, 4, 4)
        layout.setSpacing(4)

        self.skills_table = QTableWidget()
        self.skills_table.setColumnCount(5)
        self.skills_table.setHorizontalHeaderLabels([
            "#", "Skill Name", "Value", "Procs", "Proc %"
        ])
        self.skills_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.skills_table.setAlternatingRowColors(True)
        self.skills_table.setSortingEnabled(True)

        header = self.skills_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in range(2, 5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.skills_table)

        section.setLayout(layout)
        return section

    def add_skill_event(self, event_data: Dict[str, Any]):
        """Add a skill event to the skills tab"""
        event_type = event_data.get('event_type', '')
        parsed_data = event_data.get('parsed_data', {})

        if event_type in ['skill_gain', 'skill']:
            skill_name = parsed_data.get('skill', '')
            experience = parsed_data.get('experience', 0)
            improvement = parsed_data.get('improvement', 0)

            logger.info(f"[UI] Adding skill event: {skill_name} +{experience} exp")

            # Update total skill gain
            current_total = float(self.total_skill_gain_value.text())
            new_total = current_total + (experience or improvement)
            self.total_skill_gain_value.setText(f"{new_total:.2f}")

            # Add to skills table
            row = self.skills_table.rowCount()
            self.skills_table.insertRow(row)

            self.skills_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.skills_table.setItem(row, 1, QTableWidgetItem(skill_name))
            self.skills_table.setItem(row, 2, QTableWidgetItem(f"{experience or improvement:.2f}"))
            self.skills_table.setItem(row, 3, QTableWidgetItem("1"))
            self.skills_table.setItem(row, 4, QTableWidgetItem("100%"))

            logger.info(f"[UI] Skill event added to table")

    def create_combat_tab(self):
        """Create the Combat tab"""
        combat_widget = CombatTabWidget(self.db_manager)
        self.combat_tab = combat_widget
        self.content_stack.addWidget(combat_widget)
        logger.info("Combat tab created")

    def create_crafting_tab(self):
        """Create the Crafting tab"""
        crafting_widget = CraftingTabWidget(self.db_manager)
        self.content_stack.addWidget(crafting_widget)
        logger.info("Crafting tab created")

    def create_twitch_tab(self):
        """Create the Twitch tab"""
        from src.services.twitch_bot import TwitchBotUI

        twitch_widget = QWidget()
        twitch_layout = QVBoxLayout(twitch_widget)
        twitch_layout.setContentsMargins(8, 8, 8, 8)
        twitch_layout.setSpacing(8)

        config_panel = TwitchBotUI.create_config_panel()
        twitch_layout.addWidget(config_panel)

        self.twitch_status_label = QLabel("Twitch Bot: Disconnected")
        self.twitch_status_label.setStyleSheet("color: #8B949E; font-size: 12px;")
        twitch_layout.addWidget(self.twitch_status_label)

        twitch_layout.addStretch()

        self.content_stack.addWidget(twitch_widget)
        logger.info("Twitch tab created")

    def create_config_tab(self):
        """Create the Config tab using the new ConfigTab widget"""
        self.config_widget = ConfigTab(config_manager=self.config_manager)
        self.content_stack.addWidget(self.config_widget)
        self.config_widget.signals.loadout_changed.connect(self._on_loadout_changed)
        
        # Initialize cost per attack for the current loadout
        self.cost_per_attack = self._calculate_cost_per_attack()
        logger.info(f"Config tab created using ConfigTab, initial cost per attack: {self.cost_per_attack:.6f} PED")
        if self.overlay:
            self.overlay.set_cost_per_attack(self.cost_per_attack)

    def _on_loadout_changed(self):
        """Handle loadout changed - update overlay with new weapon info"""
        try:
            if hasattr(self, 'config_widget') and self.config_widget:
                active_loadout = self.config_widget.active_loadout_combo.currentData()
                if active_loadout:
                    for loadout in self.config_widget._loadouts:
                        if loadout.id == active_loadout:
                            if self.overlay:
                                self.overlay.update_weapon(
                                    loadout.weapon,
                                    loadout.amplifier or "",
                                    f"{loadout.damage_enh * 0.1:.3f}" if loadout.damage_enh else ""
                                )
                                self.overlay.set_cost_per_attack(self.cost_per_attack)
                            
                            # Update cost per attack for total cost calculation
                            self.cost_per_attack = self._calculate_cost_per_attack()
                            logger.info(f"Loadout changed to: {loadout.weapon}, cost per attack: {self.cost_per_attack:.6f} PED")
                            
                            # Update total cost display with new cost per attack
                            self._update_total_cost_display()
                            break
        except Exception as e:
            logger.error(f"Error handling loadout change: {e}")

    def create_chat_config_panel(self):
        """Create chat monitoring configuration panel"""
        panel = QGroupBox("Chat Monitoring")
        panel.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #8B949E;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        path_layout = QHBoxLayout()

        path_layout.addWidget(QLabel("Log File:"))

        self.chat_log_path = QLineEdit()
        default_path = str(Path.home() / "Documents" / "Entropia Universe" / "chat.log")
        self.chat_log_path.setText(default_path)
        path_layout.addWidget(self.chat_log_path)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_chat_log)
        path_layout.addWidget(browse_btn)

        layout.addLayout(path_layout)

        monitoring_layout = QHBoxLayout()

        self.monitoring_enabled = QCheckBox("Enable Monitoring")
        self.monitoring_enabled.setChecked(True)
        monitoring_layout.addWidget(self.monitoring_enabled)

        start_btn = QPushButton("Start Monitoring")
        start_btn.clicked.connect(self.start_chat_monitoring)
        monitoring_layout.addWidget(start_btn)

        monitoring_layout.addStretch()

        layout.addLayout(monitoring_layout)

        panel.setLayout(layout)
        return panel

    def create_theme_config_panel(self):
        """Create theme configuration panel"""
        panel = QGroupBox("Appearance")
        panel.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #8B949E;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        theme_layout = QHBoxLayout()

        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText("Dark" if self.current_theme == 'dark' else "Light")
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        theme_layout.addWidget(self.theme_combo)

        theme_layout.addStretch()

        layout.addLayout(theme_layout)

        panel.setLayout(layout)
        return panel

    def create_database_config_panel(self):
        """Create database configuration panel"""
        panel = QGroupBox("Database")
        panel.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #8B949E;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        button_layout = QHBoxLayout()

        backup_btn = QPushButton("Backup Database")
        backup_btn.clicked.connect(self.backup_database)
        button_layout.addWidget(backup_btn)

        reset_btn = QPushButton("Reset Sessions")
        reset_btn.clicked.connect(self.reset_sessions)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        self.db_status_label = QLabel("Loading...")
        layout.addWidget(self.db_status_label)

        QTimer.singleShot(100, self._run_update_db_status)

        panel.setLayout(layout)
        return panel

    def setup_menubar(self):
        """Setup menubar"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #161B22;
                color: #E6EDF3;
                border-bottom: 1px solid #30363D;
            }
            QMenuBar::item:selected {
                background-color: #30363D;
            }
        """)

        file_menu = menubar.addMenu("File")

        export_session_action = QAction("Export Session...", self)
        export_session_action.triggered.connect(self.export_session)
        file_menu.addAction(export_session_action)

        export_all_action = QAction("Export All Sessions...", self)
        export_all_action.triggered.connect(self.export_all_sessions)
        file_menu.addAction(export_all_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        session_menu = menubar.addMenu("Session")

        start_session_action = QAction("Start Session", self)
        start_session_action.triggered.connect(self.start_session)
        session_menu.addAction(start_session_action)

        stop_session_action = QAction("Stop Session", self)
        stop_session_action.triggered.connect(self.stop_session)
        session_menu.addAction(stop_session_action)

        view_menu = menubar.addMenu("View")

        toggle_overlay_action = QAction("Toggle Overlay", self)
        toggle_overlay_action.setShortcut("F12")
        toggle_overlay_action.triggered.connect(self.toggle_overlay)
        view_menu.addAction(toggle_overlay_action)

        theme_action = QAction("Toggle Theme", self)
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)

        view_menu.addSeparator()

        settings_action = QAction("Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        view_menu.addAction(settings_action)

        logger.debug("Menubar setup complete")

    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        logger.debug("Status bar setup complete")

    def setup_timer(self):
        """Setup update timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.timeout.connect(self.check_readiness)
        self.update_timer.start(1000)
        
        # Timer for checking cost per attack calculation
        self.cost_check_timer = QTimer()
        self.cost_check_timer.timeout.connect(self._check_and_update_cost)
        self.cost_check_timer.start(2000)  # Check every 2 seconds
        
        logger.debug("Timer setup complete")
    
    def _check_and_update_cost(self):
        """Check if cost per attack needs to be recalculated"""
        if self.cost_per_attack <= 0:
            new_cost = self._calculate_cost_per_attack()
            if new_cost > 0:
                self.cost_per_attack = new_cost
                logger.info(f"Cost per attack calculated: {self.cost_per_attack:.6f} PED")
                if self.overlay:
                    self.overlay.set_cost_per_attack(self.cost_per_attack)
                self._update_total_cost_display()

    def _calculate_cost_per_attack(self) -> float:
        """Calculate cost per attack from the active loadout"""
        try:
            if not hasattr(self, 'config_widget') or not self.config_widget:
                return 0.0
                
            active_loadout = self.config_widget.active_loadout_combo.currentData()
            if not active_loadout:
                return 0.0
                
            # Try to get cost from config_tab's calculated stats
            if hasattr(self.config_widget, 'ammo_burn_text') and hasattr(self.config_widget, 'weapon_decay_text'):
                try:
                    ammo_burn = float(self.config_widget.ammo_burn_text.text())
                    decay = float(self.config_widget.weapon_decay_text.text())
                    ammo_cost = ammo_burn / 10000.0
                    return decay + ammo_cost
                except (ValueError, AttributeError) as e:
                    logger.debug(f"Could not get cost from config_tab: {e}")
            
            # Fallback: calculate using loadout data
            selected_loadout = None
            for loadout in self.config_widget._loadouts:
                if loadout.id == active_loadout:
                    selected_loadout = loadout
                    break
                    
            if not selected_loadout:
                return 0.0
                
            # Calculate cost per attack using similar logic to config_tab._async_calculate_stats
            async def calc_cost():
                data_service = GameDataService()
                weapon = await data_service.get_weapon_by_name(selected_loadout.weapon)
                if not weapon:
                    return 0.0
                    
                base_decay = float(weapon.decay) if weapon.decay else 0.0
                base_ammo = weapon.ammo if weapon.ammo else 0
                
                damage_mult = 1.0 + (selected_loadout.damage_enh * 0.1)
                economy_mult = 1.0 - (selected_loadout.economy_enh * 0.05)
                
                enhanced_decay = base_decay * damage_mult * economy_mult
                enhanced_ammo = base_ammo * damage_mult
                
                # Add amplifier decay
                if selected_loadout.amplifier:
                    amp = await data_service.get_attachment_by_name(selected_loadout.amplifier)
                    if amp:
                        enhanced_decay += float(amp.decay) if amp.decay else 0
                        enhanced_ammo += amp.ammo if amp.ammo else 0
                
                # Add scope decay
                if selected_loadout.scope:
                    scope = await data_service.get_attachment_by_name(selected_loadout.scope)
                    if scope:
                        enhanced_decay += float(scope.decay) if scope.decay else 0
                        enhanced_ammo += scope.ammo if scope.ammo else 0
                
                # Add sight 1 decay
                if selected_loadout.sight_1:
                    sight = await data_service.get_attachment_by_name(selected_loadout.sight_1)
                    if sight:
                        enhanced_decay += float(sight.decay) if sight.decay else 0
                        enhanced_ammo += sight.ammo if sight.ammo else 0
                
                # Add sight 2 decay
                if selected_loadout.sight_2:
                    sight = await data_service.get_attachment_by_name(selected_loadout.sight_2)
                    if sight:
                        enhanced_decay += float(sight.decay) if sight.decay else 0
                        enhanced_ammo += sight.ammo if sight.ammo else 0
                
                # Calculate ammo cost (ammo is in PEC, divide by 10000 to get PED)
                ammo_cost = enhanced_ammo / 10000.0
                
                return enhanced_decay + ammo_cost
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                cost = loop.run_until_complete(calc_cost())
                return cost
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error calculating cost per attack: {e}")
            return 0.0

    def _update_total_cost_display(self):
        """Update the total cost display based on shots taken and cost per attack"""
        try:
            if self.cost_per_attack <= 0:
                self.cost_per_attack = self._calculate_cost_per_attack()
                logger.debug(f"Calculated cost_per_attack: {self.cost_per_attack}")
                if self.overlay:
                    self.overlay.set_cost_per_attack(self.cost_per_attack)
            
            if self.cost_per_attack <= 0:
                logger.debug("Cannot update total cost: cost_per_attack is still 0")
                return
                
            total_cost = self.total_shots_taken * self.cost_per_attack
            logger.debug(f"Updating total cost: {total_cost:.2f} PED (shots={self.total_shots_taken}, cpa={self.cost_per_attack})")
            self.loot_summary_labels["Total Cost"].setText(f"{total_cost:.2f} PED")
            
            if self.overlay:
                self.overlay._shots_taken = self.total_shots_taken
                self.overlay._stats['total_cost'] = Decimal(str(total_cost))
                self.overlay._update_stats_display()
            
            total_return_str = self.loot_summary_labels["Total Return"].text().replace(",", "").split()[0]
            total_return = float(total_return_str)
            
            if total_cost > 0:
                return_pct = (total_return / total_cost) * 100
                self.loot_summary_labels["% Return"].setText(f"{return_pct:.1f}%")
            elif total_return > 0:
                self.loot_summary_labels["% Return"].setText("100.0%")
            
            self._update_analysis_realtime()
                
        except Exception as e:
            logger.error(f"Error updating total cost display: {e}")

    def check_readiness(self):
        """Check if all prerequisites are met for starting a run"""
        chat_log_ok = False
        character_name_ok = False
        loadout_ok = False

        chat_path = None
        if hasattr(self, 'chat_log_path'):
            chat_path = self.chat_log_path.text().strip()

        if not chat_path:
            try:
                chat_path = self.config_manager.get("chat_monitoring.log_file_path", "")
            except:
                pass

        if not chat_path:
            for i in range(self.content_stack.count()):
                widget = self.content_stack.widget(i)
                if hasattr(widget, 'chat_location_text'):
                    chat_path = widget.chat_location_text.text().strip()
                    break

        if chat_path and Path(chat_path).exists():
            chat_log_ok = True

        char_name = None
        for i in range(self.content_stack.count()):
            widget = self.content_stack.widget(i)
            if hasattr(widget, 'character_name'):
                char_name = widget.character_name.text().strip()
                break

        if not char_name:
            try:
                char_name = self.config_manager.get("character.name", "")
            except:
                pass

        if char_name:
            character_name_ok = True

        active_loadout = None
        for i in range(self.content_stack.count()):
            widget = self.content_stack.widget(i)
            if hasattr(widget, 'active_loadout_combo'):
                active_loadout = widget.active_loadout_combo.currentData()
                break

        if active_loadout:
            loadout_ok = True

        if chat_log_ok and character_name_ok and loadout_ok:
            self.status_indicator.status = "green"
            self.start_run_btn.setEnabled(True)
        elif chat_log_ok and (character_name_ok or loadout_ok):
            self.status_indicator.status = "yellow"
            self.start_run_btn.setEnabled(False)
        else:
            self.status_indicator.status = "red"
            self.start_run_btn.setEnabled(False)

    def update_status(self):
        """Update status periodically"""
        try:
            if self.current_session_id:
                current_time = datetime.now().strftime("%H:%M:%S")
                elapsed = ""
                if self.current_session_start:
                    delta = datetime.now() - self.current_session_start
                    hours, remainder = divmod(int(delta.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    elapsed = f" | Elapsed: {hours:02d}:{minutes:02d}:{seconds:02d}"
                self.status_bar.showMessage(f"Session Active{elapsed}")
            else:
                self.status_bar.showMessage("Ready")

        except Exception as e:
            logger.error(f"Error updating status: {e}")

    def toggle_session(self):
        """Toggle session start/stop"""
        if self.current_session_id:
            self.stop_session()
        else:
            self.start_session()

    def start_session(self):
        """Start a new tracking session"""
        try:
            from datetime import datetime

            self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.current_session_start = datetime.now()

            self.start_run_btn.setText("Stop Run")
            self.start_run_btn.setStyleSheet("""
                QPushButton {
                    background-color: #DA3633;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #F04028;
                }
            """)

            self.db_manager.create_session_sync(self.current_session_id, "hunting")

            self._add_current_run_entry()

            self.item_breakdown_table.setRowCount(0)

            self.loot_summary_labels["Creatures Looted"].setText("0")
            self.loot_summary_labels["Total Cost"].setText("0.00 PED")
            self.loot_summary_labels["Total Return"].setText("0.00 PED")
            self.loot_summary_labels["% Return"].setText("0.0%")
            self.loot_summary_labels["Globals"].setText("0")
            self.loot_summary_labels["HOFs"].setText("0")

            if hasattr(self, 'chat_reader') and self.chat_reader:
                chat_path = None
                if hasattr(self, 'config_widget') and self.config_widget:
                    if hasattr(self.config_widget, 'chat_location_text'):
                        chat_path = self.config_widget.chat_location_text.text().strip()
                elif hasattr(self, 'chat_log_path') and self.chat_log_path:
                    chat_path = self.chat_log_path.text().strip()
                
                if chat_path and Path(chat_path).exists():
                    success = self.chat_reader.start_monitoring(chat_path)
                    if success:
                        self.status_bar.showMessage(f"Session started - Monitoring: {chat_path}")
                    else:
                        self.status_bar.showMessage(f"Session started - Failed to start monitoring")
                else:
                    self.status_bar.showMessage("Session started - No valid chat.log path")
            else:
                self.status_bar.showMessage("Session started - Chat reader not available")

            if self.overlay:
                self.overlay.start_session(self.current_session_id, "hunting", self.current_session_start)
                self.overlay.set_cost_per_attack(self.cost_per_attack)

            self._refresh_analysis_data()

            logger.info(f"Session started: {self.current_session_id}")
            self.status_bar.showMessage(f"Session started: {self.current_session_id}")

        except Exception as e:
            logger.error(f"Error starting session: {e}", exc_info=True)
            self.status_bar.showMessage(f"Error starting session: {e}")

    def _add_current_run_entry(self):
        """Add a (Current run) entry to the run log"""
        row = 0
        self.run_log_table.insertRow(row)

        start_time = self.current_session_start.strftime("%Y-%m-%d %H:%M")

        self.run_log_table.setItem(row, 0, QTableWidgetItem("(Current run)"))
        self.run_log_table.setItem(row, 1, QTableWidgetItem(start_time))
        self.run_log_table.setItem(row, 2, QTableWidgetItem("-"))
        self.run_log_table.setItem(row, 3, QTableWidgetItem("0.00"))
        self.run_log_table.setItem(row, 4, QTableWidgetItem("0.00"))
        self.run_log_table.setItem(row, 5, QTableWidgetItem("0.0%"))
        self.run_log_table.setItem(row, 6, QTableWidgetItem("0"))

        self.run_log_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, "current")
        self.run_log_table.item(row, 0).setForeground(QColor("#3FB950"))

    def stop_session(self):
        """Stop current session"""
        try:
            if self.current_session_id:
                session_id = self.current_session_id

                if hasattr(self, 'chat_reader') and self.chat_reader:
                    self.chat_reader.stop_monitoring()

                if self.overlay:
                    self.overlay.stop_session()

                total_cost = float(self.loot_summary_labels["Total Cost"].text().replace(",", "").split()[0])
                total_return = float(self.loot_summary_labels["Total Return"].text().replace(",", "").split()[0])

                asyncio.run(self.db_manager.update_session_totals(session_id, total_cost, total_return, 0))

                self._convert_current_run_to_completed(session_id, total_cost, total_return)

                self.current_session_id = None
                self.current_session_start = None

                self.start_run_btn.setText("Start Run")
                self.start_run_btn.setStyleSheet("""
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

                self.status_bar.showMessage(f"Session stopped")
                logger.info(f"Session stopped: {session_id}")

        except Exception as e:
            logger.error(f"Error stopping session: {e}", exc_info=True)
            self.status_bar.showMessage(f"Error stopping session: {e}")

    def _convert_current_run_to_completed(self, session_id: str, total_cost: float, total_return: float):
        """Convert the (Current run) entry to a completed run entry"""
        for row in range(self.run_log_table.rowCount()):
            item = self.run_log_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == "current":
                end_time = datetime.now()
                delta = end_time - self.current_session_start
                hours, remainder = divmod(int(delta.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                roi = (total_return / total_cost * 100) if total_cost > 0 else 0

                self.run_log_table.setItem(row, 0, QTableWidgetItem("Completed"))
                self.run_log_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, session_id)
                self.run_log_table.item(row, 0).setForeground(QColor("#E6EDF3"))

                start_time_str = self.run_log_table.item(row, 1).text()
                self.run_log_table.setItem(row, 2, QTableWidgetItem(duration))
                self.run_log_table.setItem(row, 3, QTableWidgetItem(f"{total_cost:.2f}"))
                self.run_log_table.setItem(row, 4, QTableWidgetItem(f"{total_return:.2f}"))
                self.run_log_table.setItem(row, 5, QTableWidgetItem(f"{roi:.1f}%"))

                item_count = self.item_breakdown_table.rowCount()
                self.run_log_table.setItem(row, 6, QTableWidgetItem(str(item_count)))
                break

        self.run_log_table.sortItems(1, Qt.SortOrder.DescendingOrder)

        if hasattr(self, 'analysis_widget') and self.analysis_widget:
            self.analysis_widget.refresh()

    def toggle_pause_logging(self):
        """Pause or resume logging"""
        self.is_logging_paused = not self.is_logging_paused
        if self.is_logging_paused:
            self.pause_btn.setText("Resume Logging")
            self.status_bar.showMessage("Logging paused")
        else:
            self.pause_btn.setText("Pause Logging")
            self.status_bar.showMessage("Logging resumed")
        logger.info(f"Logging paused: {self.is_logging_paused}")

    def toggle_streamer_ui(self):
        """Toggle streamer UI overlay"""
        if self.overlay.overlay_widget is None or not self.overlay.overlay_widget.isVisible():
            self.overlay.show()
            self.overlay.set_cost_per_attack(self.cost_per_attack)
            if self.current_session_id:
                self.overlay.start_session(self.current_session_id, "hunting", self.current_session_start)
            logger.info("Streamer overlay shown")
        else:
            self.overlay.hide()
            logger.info("Streamer overlay hidden")

    def open_donate(self):
        """Open donation link"""
        logger.info("Donate button clicked")

    def toggle_theme(self):
        """Toggle between dark and light themes"""
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.theme_combo.setCurrentText(new_theme.capitalize())

    def apply_theme(self, theme_name: str):
        """Apply theme"""
        self.current_theme = theme_name.lower()

        try:
            theme_file = f"themes/{self.current_theme}.qss"
            with open(theme_file, 'r', encoding='utf-8') as f:
                style = f.read()
            self.setStyleSheet(style)
        except FileNotFoundError:
            logger.warning(f"Theme file not found: themes/{self.current_theme}.qss")

        logger.info(f"Theme applied: {theme_name}")

    def _refresh_analysis_data(self):
        """Refresh analysis tab data"""
        if hasattr(self, 'analysis_widget') and self.analysis_widget and self.db_manager:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.analysis_widget.load_data())
                loop.close()
                logger.debug("Analysis data refreshed")
            except Exception as e:
                logger.debug(f"Error refreshing analysis data: {e}")

    def _update_analysis_realtime(self):
        """Update analysis tab with current session data in real-time"""
        if not hasattr(self, 'analysis_widget') or not self.analysis_widget:
            return

        if not self.current_session_id:
            return

        total_cost = float(self.loot_summary_labels["Total Cost"].text().replace(",", "").split()[0])
        total_return = float(self.loot_summary_labels["Total Return"].text().replace(",", "").split()[0])
        total_markup = 0

        current_session_data = {
            'id': self.current_session_id,
            'start_time': self.current_session_start.strftime("%Y-%m-%d %H:%M:%S") if self.current_session_start else '',
            'end_time': '',
            'activity_type': 'hunting',
            'total_cost': total_cost,
            'total_return': total_return,
            'total_markup': total_markup
        }

        self.analysis_widget.update_with_current_session(current_session_data)

    def open_settings(self):
        """Open settings dialog"""
        from src.ui.settings_dialog import SettingsDialog

        current_settings = {
            'theme': self.current_theme,
            'font_family': 'Segoe UI',
            'font_size': 10,
        }

        dialog = SettingsDialog(self, current_settings)
        dialog.settingsApplied.connect(self._on_settings_applied)

        if dialog.exec() == dialog.Accepted:
            settings = dialog.get_settings()
            self._on_settings_applied(settings)

        logger.info("Settings dialog closed")

    def _on_settings_applied(self, settings: dict):
        """Handle settings applied"""
        logger.info(f"Settings applied: {settings}")

        if 'theme' in settings:
            theme_name = settings['theme']
            self.current_theme = theme_name
            self.theme_combo.setCurrentText(theme_name.capitalize())
            self.apply_theme(theme_name)

        self.status_bar.showMessage("Settings applied")

    def toggle_overlay(self, checked: bool = False):
        """Toggle overlay window"""
        try:
            if checked:
                self.overlay.show()
                self.overlay.set_cost_per_attack(self.cost_per_attack)
                logger.info("Overlay shown")
            else:
                self.overlay.hide()
                logger.info("Overlay hidden")

        except Exception as e:
            logger.error(f"Error toggling overlay: {e}")

    def backup_database(self):
        """Backup the database"""
        try:
            import shutil
            from pathlib import Path

            db_path = Path("data/lewtnanny.db")
            if db_path.exists():
                backup_path = f"data/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy(db_path, backup_path)
                logger.info(f"Database backed up to: {backup_path}")
                self.status_bar.showMessage(f"Database backed up")
            else:
                self.status_bar.showMessage("No database file found")

        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            self.status_bar.showMessage(f"Backup error: {e}")

    def _run_update_db_status(self):
        """Wrapper to run update_db_status"""
        import asyncio

        async def _do_update():
            try:
                weapon_count = await self.db_manager.get_weapon_count()
                session_count = await self.db_manager.get_session_count()
                self.db_status_label.setText(f"Weapons: {weapon_count} | Sessions: {session_count}")
            except Exception as e:
                logger.error(f"Error updating DB status: {e}")

        asyncio.run(_do_update())

    def reset_sessions(self):
        """Reset all sessions"""
        from PyQt6.QtWidgets import QMessageBox
        import asyncio

        reply = QMessageBox.question(
            self, "Confirm Reset",
            "Are you sure you want to delete all sessions? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.db_manager.delete_all_sessions())
                loop.close()
                
                # Reset session tracking variables
                self.total_shots_taken = 0
                self.cost_per_attack = self._calculate_cost_per_attack()
                if self.overlay:
                    self.overlay.set_cost_per_attack(self.cost_per_attack)
                self._update_total_cost_display()
                
                logger.warning("All sessions have been reset")
                self.status_bar.showMessage("All sessions have been reset")
            except Exception as e:
                logger.error(f"Error resetting sessions: {e}")
                self.status_bar.showMessage(f"Reset error: {e}")

    def browse_chat_log(self):
        """Browse for chat log file"""
        from PyQt6.QtWidgets import QFileDialog
        from pathlib import Path

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Chat Log", str(Path.home()),
            "Text Files (*.txt);;All Files (*.*)"
        )
        if file_path:
            self.chat_log_path.setText(file_path)
            logger.info(f"Chat log path set: {file_path}")

    def start_chat_monitoring(self):
        """Start or restart chat monitoring"""
        import asyncio

        logger.info("[UI] start_chat_monitoring called")

        log_path = None

        if hasattr(self, 'chat_log_path'):
            log_path = self.chat_log_path.text().strip()
            logger.info(f"[UI] Got path from main window chat_log_path: {log_path}")

        if not log_path:
            try:
                log_path = self.config_manager.get("chat_monitoring.log_file_path", "")
                logger.info(f"[UI] Got path from config_manager: {log_path}")
            except Exception as e:
                logger.error(f"[UI] Error reading from config_manager: {e}")

        if not log_path:
            try:
                config_tab = None
                for i in range(self.content_stack.count()):
                    widget = self.content_stack.widget(i)
                    if hasattr(widget, 'chat_location_text'):
                        config_tab = widget
                        break

                if config_tab:
                    log_path = config_tab.chat_location_text.text().strip()
                    logger.info(f"[UI] Got path from ConfigTab: {log_path}")
            except Exception as e:
                logger.error(f"[UI] Error reading from ConfigTab: {e}")

        if not log_path:
            from pathlib import Path
            log_path = str(Path.home() / "Documents" / "Entropia Universe" / "chat.log")
            logger.info(f"[UI] Using default path: {log_path}")

        logger.info(f"[UI] Final chat log path: {log_path}")

        if hasattr(self, 'chat_reader') and self.chat_reader:
            logger.info("[UI] Chat reader exists, starting monitoring...")
            loop = asyncio.get_event_loop()
            success = loop.run_until_complete(self.chat_reader.start_monitoring(log_path))
            if success:
                self.status_bar.showMessage(f"Monitoring: {log_path}")
                logger.info(f"[UI] Chat monitoring started successfully: {log_path}")
            else:
                self.status_bar.showMessage(f"Failed to start monitoring")
                logger.error(f"[UI] Failed to start monitoring")
        else:
            self.status_bar.showMessage("Chat reader not initialized")
            logger.error("[UI] Chat reader not available!")

    def export_session(self):
        """Export current session"""
        logger.info("Export session requested")
        QMessageBox.information(self, "Export", "Export functionality coming soon")

    def export_all_sessions(self):
        """Export all sessions"""
        logger.info("Export all sessions requested")
        QMessageBox.information(self, "Export", "Export all functionality coming soon")

    def handle_new_event(self, event_data: Dict[str, Any]):
        """Handle new events from chat reader - update all UI components"""
        print(f"[UI DEBUG] handle_new_event called with: {event_data.get('event_type', 'unknown')}")
        print(f"[UI DEBUG] Full event data: {event_data}")
        
        if not event_data:
            logger.warning("[UI] ERROR: Received empty event data!")
            return

        event_type = event_data.get('event_type', 'unknown')
        raw_message = event_data.get('raw_message', '')
        parsed_data = event_data.get('parsed_data', {})
        session_id = event_data.get('session_id', 'None')

        print(f"[UI DEBUG] Processing event type: {event_type}")

        # Update Overlay
        logger.info(f"[UI] ===========================================")
        logger.info(f"[UI] Updating OVERLAY...")
        if self.overlay:
            logger.info(f"[UI] Calling overlay.add_event({event_type})...")
            self.overlay.add_event(event_data)
            logger.info(f"[UI] Overlay updated successfully")
        else:
            logger.warning(f"[UI] ERROR: No overlay available!")

        # Update Streamer Tab
        logger.info(f"[UI] ===========================================")
        # Update Combat Tab
        logger.info(f"[UI] ===========================================")
        logger.info(f"[UI] Updating COMBAT TAB...")
        if hasattr(self, 'combat_tab') and self.combat_tab:
            logger.info(f"[UI] Calling combat_tab.add_combat_event({event_type})...")
            try:
                self.combat_tab.add_combat_event(event_data)
                logger.info(f"[UI] Combat tab updated successfully")
            except AttributeError as e:
                logger.error(f"[UI] ERROR: Combat tab missing add_combat_event: {e}")
        else:
            logger.warning(f"[UI] WARNING: No combat tab available")

        # Update Skills Tab
        logger.info(f"[UI] ===========================================")
        logger.info(f"[UI] Updating SKILLS TAB...")
        if hasattr(self, 'skills_tab') and self.skills_tab:
            logger.info(f"[UI] Calling add_skill_event({event_type})...")
            try:
                self.add_skill_event(event_data)
                logger.info(f"[UI] Skills tab updated successfully")
            except Exception as e:
                logger.error(f"[UI] ERROR updating skills tab: {e}")
        else:
            logger.warning(f"[UI] WARNING: No skills tab available")

        # Update Loot Summary
        logger.info(f"[UI] ===========================================")
        logger.info(f"[UI] Updating LOOT SUMMARY...")
        try:
            self._process_event_for_summary(event_type, parsed_data)
            logger.info(f"[UI] Loot summary updated")
        except Exception as e:
            logger.error(f"[UI] ERROR updating loot summary: {e}", exc_info=True)

        # Process loot event
        if event_type == 'loot':
            logger.info(f"[UI] ===========================================")
            logger.info(f"[UI] Processing LOOT EVENT...")
            try:
                self._process_loot_event(parsed_data)
                logger.info(f"[UI] Loot event processed")
            except Exception as e:
                logger.error(f"[UI] ERROR processing loot event: {e}", exc_info=True)

        self._update_analysis_realtime()

        logger.info(f"[UI] ===========================================")
        logger.info(f"[UI] <<< Event handling complete: {event_type} >>>")

    def _process_event_for_summary(self, event_type: str, parsed_data: Dict[str, Any]):
        """Update loot summary stats based on event type"""
        if event_type == 'loot':
            value = parsed_data.get('value', 0)
            current = float(self.loot_summary_labels["Total Return"].text().replace(",", "").split()[0])
            new_total = current + value
            self.loot_summary_labels["Total Return"].setText(f"{new_total:.2f} PED")

            raw = parsed_data.get('raw_message', '')
            if 'Hall of Fame' in raw or 'HOF' in raw:
                hof_count = int(self.loot_summary_labels["HOFs"].text()) + 1
                self.loot_summary_labels["HOFs"].setText(str(hof_count))
            elif 'killed a creature' in raw:
                globals_count = int(self.loot_summary_labels["Globals"].text()) + 1
                self.loot_summary_labels["Globals"].setText(str(globals_count))

                creatures = int(self.loot_summary_labels["Creatures Looted"].text()) + 1
                self.loot_summary_labels["Creatures Looted"].setText(str(creatures))

        elif event_type == 'combat':
            damage = parsed_data.get('damage', 0)
            critical = parsed_data.get('critical', False)
            miss = parsed_data.get('miss', False)
            
            if miss:
                pass
            elif damage and damage > 0:
                self.total_shots_taken += 1
                logger.debug(f"Combat hit: damage={damage}, total_shots={self.total_shots_taken}, cost_per_attack={self.cost_per_attack}")
                self._update_total_cost_display()

        elif event_type == 'skill':
            pass

        total_return = float(self.loot_summary_labels["Total Return"].text().replace(",", "").split()[0])
        total_cost = float(self.loot_summary_labels["Total Cost"].text().replace(",", "").split()[0])

        if total_cost > 0:
            return_pct = (total_return / total_cost) * 100
            self.loot_summary_labels["% Return"].setText(f"{return_pct:.1f}%")
        elif total_return > 0:
            self.loot_summary_labels["% Return"].setText("100.0%")

        self._update_current_run_entry(total_cost, total_return)

        if self.overlay:
            self.overlay._stats['total_return'] = Decimal(str(total_return))
            self.overlay._stats['total_cost'] = Decimal(str(total_cost))
            self.overlay._update_stats_display()

        self._update_analysis_realtime()

    def _update_current_run_entry(self, total_cost: float, total_return: float):
        """Update the current run entry in the run log table"""
        if not self.current_session_id:
            return

        for row in range(self.run_log_table.rowCount()):
            item = self.run_log_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == "current":
                roi = (total_return / total_cost * 100) if total_cost > 0 else 0

                self.run_log_table.setItem(row, 3, QTableWidgetItem(f"{total_cost:.2f}"))
                self.run_log_table.setItem(row, 4, QTableWidgetItem(f"{total_return:.2f}"))
                self.run_log_table.setItem(row, 5, QTableWidgetItem(f"{roi:.1f}%"))

                item_count = self.item_breakdown_table.rowCount()
                self.run_log_table.setItem(row, 6, QTableWidgetItem(str(item_count)))
                break

    def _process_loot_event(self, parsed_data: Dict[str, Any]):
        """Process loot event and add to item breakdown"""
        item_name = parsed_data.get('item_name', '')
        quantity = parsed_data.get('quantity', 1)
        total_value = parsed_data.get('value', 0.0)
        
        if not item_name:
            return

        item_value = total_value / quantity if quantity > 0 else 0
        markup_percent = 0

        found = False
        for row in range(self.item_breakdown_table.rowCount()):
            if self.item_breakdown_table.item(row, 0).text() == item_name:
                count = int(self.item_breakdown_table.item(row, 1).text()) + quantity
                self.item_breakdown_table.setItem(row, 1, QTableWidgetItem(str(count)))
                existing_total = float(self.item_breakdown_table.item(row, 4).text())
                new_total = existing_total + total_value
                self.item_breakdown_table.setItem(row, 4, QTableWidgetItem(f"{new_total:.4f}"))
                found = True
                break

        if not found:
            row = self.item_breakdown_table.rowCount()
            self.item_breakdown_table.insertRow(row)
            self.item_breakdown_table.setItem(row, 0, QTableWidgetItem(item_name))
            self.item_breakdown_table.setItem(row, 1, QTableWidgetItem(str(quantity)))
            self.item_breakdown_table.setItem(row, 2, QTableWidgetItem(f"{item_value:.4f}"))
            self.item_breakdown_table.setItem(row, 3, QTableWidgetItem(f"{markup_percent}%"))
            self.item_breakdown_table.setItem(row, 4, QTableWidgetItem(f"{total_value:.4f}"))

        if self.current_session_id:
            asyncio.create_task(self.db_manager.save_session_loot_item(
                self.current_session_id, item_name, quantity, total_value, markup_percent
            ))

    def _on_run_log_selection_changed(self):
        """Handle run log row selection - update item breakdown"""
        selected_rows = self.run_log_table.selectedItems()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        session_id = self.run_log_table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        if not session_id:
            return

        if session_id == "current":
            self._update_item_breakdown_current_run()
        else:
            self._load_item_breakdown_for_session(session_id)

    def _update_item_breakdown_current_run(self):
        """Update item breakdown with current run data from the table"""
        self.item_breakdown_table.setRowCount(0)

    def _load_item_breakdown_for_session(self, session_id: str):
        """Load item breakdown for a specific session"""
        self.item_breakdown_table.setRowCount(0)

        def load_items():
            async def inner():
                items = await self.db_manager.get_session_loot_items(session_id)
                for item in items:
                    row = self.item_breakdown_table.rowCount()
                    self.item_breakdown_table.insertRow(row)
                    self.item_breakdown_table.setItem(row, 0, QTableWidgetItem(item['item_name']))
                    self.item_breakdown_table.setItem(row, 1, QTableWidgetItem(str(item['quantity'])))
                    item_value = item['total_value'] / item['quantity'] if item['quantity'] > 0 else 0
                    self.item_breakdown_table.setItem(row, 2, QTableWidgetItem(f"{item_value:.4f}"))
                    self.item_breakdown_table.setItem(row, 3, QTableWidgetItem(f"{item['markup_percent']:.0f}%"))
                    self.item_breakdown_table.setItem(row, 4, QTableWidgetItem(f"{item['total_value']:.4f}"))

            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(inner())
                loop.close()
            except Exception as e:
                logger.error(f"Error loading item breakdown: {e}")

    async def _load_past_runs(self):
        """Load past runs from database into run log table"""
        sessions = await self.db_manager.get_all_sessions()

        for session in sessions:
            self._add_run_to_run_log(session)

    def _load_past_runs_on_startup(self):
        """Load past runs when application starts"""
        import threading

        def load():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    sessions = loop.run_until_complete(self.db_manager.get_all_sessions())
                    for session in sessions:
                        self._add_run_to_run_log(session)
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"Error loading past runs: {e}")

        threading.Thread(target=load, daemon=True).start()

    def _add_run_to_run_log(self, session: Dict[str, Any]):
        """Add a run entry to the run log table"""
        row = self.run_log_table.rowCount()
        self.run_log_table.insertRow(row)

        start_time = session.get('start_time', '')
        if isinstance(start_time, str):
            try:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                start_time = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass

        duration = ""
        end_time = session.get('end_time')
        if end_time:
            if isinstance(end_time, str):
                try:
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    start_dt = datetime.fromisoformat(session.get('start_time', '').replace('Z', '+00:00'))
                    delta = end_dt - start_dt
                    hours, remainder = divmod(int(delta.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                except:
                    duration = "-"
            else:
                delta = end_time - session.get('start_time', datetime.now())
                hours, remainder = divmod(int(delta.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            duration = "-"

        total_cost = session.get('total_cost', 0) or 0
        total_return = session.get('total_return', 0) or 0
        roi = (total_return / total_cost * 100) if total_cost > 0 else 0

        self.run_log_table.setItem(row, 0, QTableWidgetItem("Completed"))
        self.run_log_table.setItem(row, 1, QTableWidgetItem(start_time))
        self.run_log_table.setItem(row, 2, QTableWidgetItem(duration))
        self.run_log_table.setItem(row, 3, QTableWidgetItem(f"{total_cost:.2f}"))
        self.run_log_table.setItem(row, 4, QTableWidgetItem(f"{total_return:.2f}"))
        self.run_log_table.setItem(row, 5, QTableWidgetItem(f"{roi:.1f}%"))
        self.run_log_table.setItem(row, 6, QTableWidgetItem("-"))

        self.run_log_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, session['id'])
