"""
Main window for LewtNanny PyQt6 GUI
"""

import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import json

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QTextEdit, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QGroupBox, QGridLayout, QLineEdit,
    QComboBox, QSpinBox, QCheckBox, QFileDialog,
    QStatusBar, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QTextCursor

from src.models.models import ActivityType, EventType


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, db_manager, config_manager):
        super().__init__()
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.chat_reader = None
        
        self.setWindowTitle("LewtNanny - Entropia Universe Loot Tracker")
        self.setGeometry(100, 100, 1200, 800)
        
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with proper margins
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Setup toolbar area
        self.setup_toolbar()
        
        # Setup weapon configuration panel
        self.setup_weapon_config()
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_loot_tab()
        self.create_analysis_tab()
        self.create_config_tab()
        
        # Setup proper status bar
        self.setup_status_bar()
        
    def setup_toolbar(self):
        """Setup toolbar area"""
        toolbar_widget = QFrame()
        toolbar_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        toolbar_layout.setSpacing(10)
        
        # Initialize theme state
        self.current_theme = 'dark'
        
        # Session controls
        self.session_label = QLabel("No active session")
        self.session_label.setProperty("class", "session-label")
        
        self.start_session_btn = QPushButton("Start Session")
        self.start_session_btn.clicked.connect(self.start_session)
        self.start_session_btn.setMinimumWidth(120)
        
        # Activity selector
        activity_label = QLabel("Activity:")
        self.activity_combo = QComboBox()
        self.activity_combo.addItems([t.value for t in ActivityType])
        self.activity_combo.currentTextChanged.connect(self.change_activity)
        self.activity_combo.setMinimumWidth(150)
        
        # Weapon config toggle button
        self.weapon_config_btn = QPushButton("⚙️ Weapon Config")
        self.weapon_config_btn.clicked.connect(self.toggle_weapon_config)
        self.weapon_config_btn.setMinimumWidth(120)
        
        # Current weapon display
        self.current_weapon_label = QLabel("No Weapon Selected")
        self.current_weapon_label.setProperty("class", "weapon-label")
        
        toolbar_layout.addWidget(self.session_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(activity_label)
        toolbar_layout.addWidget(self.activity_combo)
        toolbar_layout.addWidget(self.current_weapon_label)
        toolbar_layout.addWidget(self.weapon_config_btn)
        toolbar_layout.addWidget(self.start_session_btn)
        
        # Theme toggle
        self.theme_toggle_btn = QPushButton("🌓 Theme")
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        self.theme_toggle_btn.setMinimumWidth(80)
        toolbar_layout.addWidget(self.theme_toggle_btn)
        
        # Overlay toggle
        self.overlay_btn = QPushButton("Toggle Overlay")
        self.overlay_btn.clicked.connect(self.toggle_overlay)
        self.overlay_btn.setMinimumWidth(120)
        toolbar_layout.addWidget(self.overlay_btn)
        
        self.main_layout.addWidget(toolbar_widget)
        
    def setup_weapon_config(self):
        """Setup comprehensive weapon configuration panel"""
        # Create collapsible weapon config widget
        self.weapon_config_widget = QFrame()
        self.weapon_config_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        self.weapon_config_widget.setVisible(False)  # Initially hidden
        
        config_layout = QVBoxLayout(self.weapon_config_widget)
        config_layout.setContentsMargins(15, 10, 15, 10)
        config_layout.setSpacing(10)
        
        # Title
        title_label = QLabel("⚙️ Weapon Configuration")
        title_label.setProperty("class", "config-title")
        config_layout.addWidget(title_label)
        
        # Create form layout for weapon components
        from PyQt6.QtWidgets import QFormLayout, QDoubleSpinBox, QSpinBox
        
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        
        # Weapon selector
        self.weapon_combo = QComboBox()
        self.weapon_combo.setEditable(True)
        self.weapon_combo.setMinimumWidth(200)
        self.weapon_combo.setPlaceholderText("Select or type weapon...")
        self.load_weapons()
        self.weapon_combo.currentTextChanged.connect(self.update_weapon_display)
        form_layout.addRow("Weapon:", self.weapon_combo)
        
        # Attachments
        self.attachment_combo = QComboBox()
        self.attachment_combo.setEditable(True)
        self.attachment_combo.addItems(["None", "A206 Amplifier", "A204 Amplifier", "A203 Amplifier", "Beast Amplifier", "Wolf Amplifier"])
        form_layout.addRow("Attachment:", self.attachment_combo)
        
        # Scope
        self.scope_combo = QComboBox()
        self.scope_combo.setEditable(True)
        self.scope_combo.addItems(["None", "Laser Sight", "Illumination", "Holographic Sight", "AIO Sight", "Force Sight"])
        form_layout.addRow("Scope:", self.scope_combo)
        
        # Enhancers section
        enhancer_group = QGroupBox("Enhancers")
        enhancer_layout = QGridLayout(enhancer_group)
        
        # Different enhancer types with numerical inputs
        enhancer_types = [
            ("Damage", "dmg_enh"),
            ("Range", "range_enh"), 
            ("Accuracy", "acc_enh"),
            ("Economy", "eco_enh")
        ]
        
        self.enhancer_inputs = {}
        for i, (label, key) in enumerate(enhancer_types):
            enh_label = QLabel(f"{label}:")
            enh_spinbox = QSpinBox()
            enh_spinbox.setMinimum(0)
            enh_spinbox.setMaximum(10)
            enh_spinbox.setValue(0)
            enh_spinbox.setSuffix(" units")
            self.enhancer_inputs[key] = enh_spinbox
            enhancer_layout.addWidget(enh_label, i, 0)
            enhancer_layout.addWidget(enh_spinbox, i, 1)
        
        form_layout.addRow(enhancer_group)
        
        # Additional stats
        self.dmg_spinbox = QDoubleSpinBox()
        self.dmg_spinbox.setRange(0.0, 999.9)
        self.dmg_spinbox.setSingleStep(0.1)
        self.dmg_spinbox.setDecimals(1)
        self.dmg_spinbox.setSuffix(" dmg")
        form_layout.addRow("Damage:", self.dmg_spinbox)
        
        self.ammo_spinbox = QDoubleSpinBox()
        self.ammo_spinbox.setRange(0.0, 99.9)
        self.ammo_spinbox.setSingleStep(0.01)
        self.ammo_spinbox.setDecimals(2)
        self.ammo_spinbox.setSuffix(" ammo")
        form_layout.addRow("Ammo/shot:", self.ammo_spinbox)
        
        config_layout.addLayout(form_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_weapon_config)
        save_btn.setProperty("class", "save-btn")
        
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_weapon_config)
        reset_btn.setProperty("class", "reset-btn")
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        
        config_layout.addLayout(button_layout)
        
        # Add to main layout
        self.main_layout.addWidget(self.weapon_config_widget)
        
    def toggle_weapon_config(self):
        """Toggle weapon configuration panel visibility"""
        self.weapon_config_widget.setVisible(not self.weapon_config_widget.isVisible())
        if self.weapon_config_widget.isVisible():
            self.weapon_config_btn.setText("⚙️ Hide Config")
        else:
            self.weapon_config_btn.setText("⚙️ Weapon Config")
    
    def update_weapon_display(self):
        """Update the current weapon display in toolbar"""
        weapon = self.get_selected_weapon()
        if weapon:
            self.current_weapon_label.setText(f"Weapon: {weapon}")
            self.current_weapon_label.setProperty("class", "weapon-label-active")
        else:
            self.current_weapon_label.setText("No Weapon Selected")
            self.current_weapon_label.setProperty("class", "weapon-label")
        # Trigger style update - let theme handle styling
    
    def save_weapon_config(self):
        """Save weapon configuration"""
        config = {
            'weapon': self.get_selected_weapon(),
            'attachment': self.attachment_combo.currentText(),
            'scope': self.scope_combo.currentText(),
            'dmg_enh': self.enhancer_inputs['dmg_enh'].value(),
            'range_enh': self.enhancer_inputs['range_enh'].value(),
            'acc_enh': self.enhancer_inputs['acc_enh'].value(),
            'eco_enh': self.enhancer_inputs['eco_enh'].value(),
            'damage': self.dmg_spinbox.value(),
            'ammo': self.ammo_spinbox.value()
        }
        print(f"Saved weapon config: {config}")
        self.update_weapon_display()
    
    def reset_weapon_config(self):
        """Reset weapon configuration"""
        self.weapon_combo.setCurrentIndex(0)
        self.attachment_combo.setCurrentIndex(0)
        self.scope_combo.setCurrentIndex(0)
        for spinbox in self.enhancer_inputs.values():
            spinbox.setValue(0)
        self.dmg_spinbox.setValue(0.0)
        self.ammo_spinbox.setValue(0.0)
        self.update_weapon_display()
    
    def toggle_theme(self):
        """Toggle between dark and light themes"""
        from pathlib import Path
        
        # Switch theme
        if self.current_theme == 'dark':
            self.current_theme = 'light'
            self.theme_toggle_btn.setText("☀️ Theme")
        else:
            self.current_theme = 'dark'
            self.theme_toggle_btn.setText("🌙 Theme")
        
        # Load new theme
        try:
            theme_path = Path(__file__).parent.parent.parent / "themes" / f"{self.current_theme}.qss"
            if theme_path.exists():
                with open(theme_path, 'r') as f:
                    stylesheet = f.read()
                self.setStyleSheet(stylesheet)
                print(f"Switched to {self.current_theme} theme")
            else:
                print(f"Theme file not found: {theme_path}")
        except Exception as e:
            print(f"Error switching theme: {e}")
        
    def setup_status_bar(self):
        """Setup proper status bar"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Add permanent widgets to status bar
        self.status_label = QLabel("Ready")
        status_bar.addWidget(self.status_label)
        
        # Add stretch to push other info to the right
        status_bar.addPermanentWidget(QLabel("LewtNanny v1.0"))
        
    def setup_timer(self):
        """Setup update timer"""
        # Don't start timer automatically to avoid hanging
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        # self.update_timer.start(5000)  # Temporarily disabled
        
    def create_loot_tab(self):
        """Create loot tracking tab"""
        loot_widget = QWidget()
        loot_layout = QVBoxLayout(loot_widget)
        loot_layout.setContentsMargins(5, 5, 5, 5)
        loot_layout.setSpacing(5)
        
        # Splitter for loot feed and stats
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # Loot feed (left side)
        loot_group = QGroupBox("Recent Loot")
        loot_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        loot_feed_layout = QVBoxLayout(loot_group)
        loot_feed_layout.setContentsMargins(10, 20, 10, 10)
        
        self.loot_feed = QTextEdit()
        self.loot_feed.setReadOnly(True)
        self.loot_feed.setFont(QFont("Consolas, Monaco, monospace", 9))
        self.loot_feed.setStyleSheet("""
            QTextEdit {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        loot_feed_layout.addWidget(self.loot_feed)
        
        splitter.addWidget(loot_group)
        splitter.setStretchFactor(0, 2)  # Give loot feed more space
        
        # Quick stats (right side)
        stats_group = QGroupBox("Session Stats")
        stats_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        stats_layout = QGridLayout(stats_group)
        stats_layout.setContentsMargins(10, 20, 10, 10)
        stats_layout.setSpacing(8)
        
        # Create stat labels with theming
        def create_stat_label(text, is_header=False):
            label = QLabel(text)
            if is_header:
                label.setProperty("class", "stat-header")
            else:
                label.setProperty("class", "stat-value")
            return label
        
        self.total_cost_label = create_stat_label("Cost: 0.00 PED")
        self.total_return_label = create_stat_label("Return: 0.00 PED")
        self.profit_label = create_stat_label("Profit: 0.00 PED")
        self.dpp_label = create_stat_label("DPP: N/A")
        self.events_count_label = create_stat_label("Events: 0")
        
        stats_layout.addWidget(create_stat_label("Cost:", True), 0, 0)
        stats_layout.addWidget(create_stat_label("Return:", True), 0, 1)
        stats_layout.addWidget(create_stat_label("Profit:", True), 1, 0)
        stats_layout.addWidget(create_stat_label("DPP:", True), 1, 1)
        stats_layout.addWidget(self.total_cost_label, 2, 0)
        stats_layout.addWidget(self.total_return_label, 2, 1)
        stats_layout.addWidget(self.profit_label, 3, 0)
        stats_layout.addWidget(self.dpp_label, 3, 1)
        stats_layout.addWidget(create_stat_label("Events:", True), 4, 0, 1, 2)
        stats_layout.addWidget(self.events_count_label, 5, 0, 1, 2)
        stats_layout.setRowStretch(6, 1)  # Add stretch at bottom
        
        splitter.addWidget(stats_group)
        splitter.setStretchFactor(1, 1)  # Give stats less space
        
        # Set initial splitter sizes (60% loot feed, 40% stats)
        splitter.setSizes([600, 400])
        
        loot_layout.addWidget(splitter)
        self.tab_widget.addTab(loot_widget, "Loot")
        
    def create_analysis_tab(self):
        """Create analysis tab"""
        analysis_widget = QWidget()
        analysis_layout = QVBoxLayout(analysis_widget)
        analysis_layout.setContentsMargins(5, 5, 5, 5)
        analysis_layout.setSpacing(5)
        
        # Event history table
        history_group = QGroupBox("Event History")
        history_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        history_layout = QVBoxLayout(history_group)
        history_layout.setContentsMargins(10, 20, 10, 10)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Time", "Type", "Activity", "Details", "Session"])
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setSortingEnabled(True)
        
        # Better column sizing
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Time
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Activity
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)            # Details
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Session
        
        self.history_table.setProperty("class", "history-table")
        
        history_layout.addWidget(self.history_table)
        analysis_layout.addWidget(history_group)
        
        self.tab_widget.addTab(analysis_widget, "Analysis")
        
    def create_config_tab(self):
        """Create configuration tab"""
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        config_layout.setContentsMargins(5, 5, 5, 5)
        config_layout.setSpacing(10)
        
        # Chat monitoring settings
        chat_group = QGroupBox("Chat Monitoring")
        chat_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        chat_layout = QGridLayout(chat_group)
        chat_layout.setContentsMargins(10, 20, 10, 10)
        chat_layout.setSpacing(10)
        
        self.log_file_edit = QLineEdit()
        self.log_file_edit.setPlaceholderText("Path to Entropia Universe chat log file")
        self.log_file_edit.setProperty("class", "input-field")
        
        self.browse_log_btn = QPushButton("Browse...")
        self.browse_log_btn.clicked.connect(self.browse_log_file)
        self.browse_log_btn.setMinimumWidth(80)
        
        self.monitoring_checkbox = QCheckBox("Enable real-time monitoring")
        self.monitoring_checkbox.setChecked(True)
        self.monitoring_checkbox.setStyleSheet("spacing: 5px;")
        
        chat_layout.addWidget(QLabel("Log File:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        chat_layout.addWidget(self.log_file_edit, 0, 1)
        chat_layout.addWidget(self.browse_log_btn, 0, 2)
        chat_layout.addWidget(self.monitoring_checkbox, 1, 0, 1, 3)
        chat_layout.setColumnStretch(1, 1)  # Make the file path field expand
        
        config_layout.addWidget(chat_group)
        
        # OCR settings
        ocr_group = QGroupBox("OCR Settings")
        ocr_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        ocr_layout = QGridLayout(ocr_group)
        ocr_layout.setContentsMargins(10, 20, 10, 10)
        ocr_layout.setSpacing(10)
        
        self.ocr_enabled_checkbox = QCheckBox("Enable OCR for screenshots")
        self.ocr_enabled_checkbox.setChecked(True)
        self.ocr_enabled_checkbox.setStyleSheet("spacing: 5px;")
        
        self.screenshot_hotkey_edit = QLineEdit("F12")
        self.screenshot_hotkey_edit.setProperty("class", "input-field")
        
        self.auto_screenshot_checkbox = QCheckBox("Auto-screenshot on events")
        self.auto_screenshot_checkbox.setStyleSheet("spacing: 5px;")
        
        ocr_layout.addWidget(self.ocr_enabled_checkbox, 0, 0, 1, 3)
        ocr_layout.addWidget(QLabel("Screenshot Hotkey:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        ocr_layout.addWidget(self.screenshot_hotkey_edit, 1, 1)
        ocr_layout.addWidget(self.auto_screenshot_checkbox, 2, 0, 1, 3)
        ocr_layout.setColumnStretch(1, 1)
        
        config_layout.addWidget(ocr_group)
        
        # Save button
        self.save_config_btn = QPushButton("Save Configuration")
        self.save_config_btn.clicked.connect(self.save_config)
        self.save_config_btn.setMinimumHeight(40)
        self.save_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        config_layout.addWidget(self.save_config_btn)
        
        config_layout.addStretch()
        self.tab_widget.addTab(config_widget, "Config")
        
    @pyqtSlot()
    def start_session(self):
        """Start a new tracking session"""
        self.start_session_btn.setText("Stop Session")
        self.start_session_btn.clicked.disconnect()
        self.start_session_btn.clicked.connect(self.stop_session)
        
        # Update status
        activity = self.activity_combo.currentText()
        self.session_label.setText(f"Session Active - {activity}")
        
        # Update overlay with full weapon info
        if hasattr(self, 'overlay_window') and self.overlay_window:
            import uuid
            session_id = str(uuid.uuid4())
            weapon_config = self.get_full_weapon_config()
            weapon_display = weapon_config['weapon'] or 'None'
            self.overlay_window.update_session_info(session_id, activity, weapon=weapon_display)
        
    @pyqtSlot()
    def stop_session(self):
        """Stop the current tracking session"""
        self.start_session_btn.setText("Start Session")
        self.start_session_btn.clicked.disconnect()
        self.start_session_btn.clicked.connect(self.start_session)
        
        # Update status
        self.session_label.setText("No active session")
        
        # Update overlay
        if hasattr(self, 'overlay_window') and self.overlay_window:
            self.overlay_window.update_session_info("", "None")
        
    @pyqtSlot()
    def change_activity(self, activity_text):
        """Change current activity type"""
        if hasattr(self, 'chat_reader') and self.chat_reader:
            for activity in ActivityType:
                if activity.value == activity_text:
                    self.chat_reader.set_activity_type(activity)
                    break
                    
    @pyqtSlot()
    def browse_log_file(self):
        """Browse for chat log file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Chat Log File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.log_file_edit.setText(file_path)
            
    @pyqtSlot()
    def save_config(self):
        """Save configuration"""
        config_updates = {
            "chat_monitoring": {
                "log_file_path": self.log_file_edit.text(),
                "monitoring_enabled": self.monitoring_checkbox.isChecked()
            },
            "ocr": {
                "enabled": self.ocr_enabled_checkbox.isChecked(),
                "screenshot_hotkey": self.screenshot_hotkey_edit.text(),
                "auto_screenshot": self.auto_screenshot_checkbox.isChecked()
            }
        }
        
        # This would be implemented with async in the full version
        # asyncio.create_task(self.config_manager.update(config_updates))
        
    @pyqtSlot(dict)
    def handle_new_event(self, event_data):
        """Handle new event from chat reader"""
        # Add to loot feed
        timestamp = datetime.fromisoformat(event_data['parsed_data']['timestamp']).strftime("%H:%M:%S")
        event_type = event_data['event_type']
        message = f"[{timestamp}] {event_type.upper()}: {event_data['raw_message']}"
        
        self.loot_feed.append(message)
        self.loot_feed.moveCursor(QTextCursor.MoveOperation.End)
        
        # Add to history table
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)
        
        self.history_table.setItem(row, 0, QTableWidgetItem(timestamp))
        self.history_table.setItem(row, 1, QTableWidgetItem(event_type))
        self.history_table.setItem(row, 2, QTableWidgetItem(event_data['activity_type']))
        self.history_table.setItem(row, 3, QTableWidgetItem(event_data['raw_message'][:50] + "..."))
        self.history_table.setItem(row, 4, QTableWidgetItem(event_data.get('session_id', 'Unknown')[:8]))
        
        # Update overlay if it exists
        if hasattr(self, 'overlay_window') and self.overlay_window:
            session_id = event_data.get('session_id', '')
            activity_type = event_data.get('activity_type', 'Unknown')
            weapon = self.get_selected_weapon()
            self.overlay_window.update_session_info(session_id, activity_type, event_data, weapon)
        
    def update_stats(self):
        """Update statistics display"""
        try:
            # Update status bar with timestamp
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"Last updated: {current_time}")
            
            # This would query the database in the full version
            # For now, we'll just update the status bar
        except Exception as e:
            print(f"Error updating stats: {e}")
    
    def toggle_overlay(self):
        """Toggle overlay window"""
        try:
            if not hasattr(self, 'overlay_window') or not self.overlay_window:
                # Create overlay window with proper background and dragging
                from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
                from PyQt6.QtCore import Qt, QPoint, pyqtSignal
                from PyQt6.QtGui import QMouseEvent, QPainter, QColor, QBrush
                
                class DraggableOverlay(QWidget):
                    def __init__(self):
                        super().__init__()
                        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
                        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
                        self.setGeometry(100, 100, 350, 200)
                        
                        # Dragging variables
                        self.drag_pos = QPoint()
                        
                        # Create main frame with themed background
                        self.main_frame = QFrame()
                        self.main_frame.setProperty("class", "overlay-frame")
                        
                        # Create layout
                        layout = QVBoxLayout(self.main_frame)
                        layout.setContentsMargins(15, 10, 15, 10)
                        layout.setSpacing(8)
                        
                        # Title
                        title = QLabel("🎯 LewtNanny Overlay")
                        title.setProperty("class", "overlay-title")
                        layout.addWidget(title)
                        
                        # Session info
                        self.session_label = QLabel("Session: Not Started")
                        self.session_label.setProperty("class", "overlay-info")
                        layout.addWidget(self.session_label)
                        
                        # Activity info
                        self.activity_label = QLabel("Activity: None")
                        self.activity_label.setProperty("class", "overlay-accent")
                        layout.addWidget(self.activity_label)
                        
                        # Weapon info
                        self.weapon_label = QLabel("Weapon: None")
                        self.weapon_label.setProperty("class", "overlay-info")
                        layout.addWidget(self.weapon_label)
                        
                        # Stats info
                        self.stats_label = QLabel("Events: 0 | Duration: 00:00:00")
                        self.stats_label.setProperty("class", "overlay-stats")
                        layout.addWidget(self.stats_label)
                        
                        # Last event
                        self.last_event_label = QLabel("Last: --")
                        self.last_event_label.setProperty("class", "overlay-info")
                        layout.addWidget(self.last_event_label)
                        
                        # Main layout
                        main_layout = QVBoxLayout(self)
                        main_layout.setContentsMargins(0, 0, 0, 0)
                        main_layout.addWidget(self.main_frame)
                        
                        self.event_count = 0
                        self.session_start = None
                
                    def mousePressEvent(self, event: QMouseEvent):
                        if event.button() == Qt.MouseButton.LeftButton:
                            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                            event.accept()
                    
                    def mouseMoveEvent(self, event: QMouseEvent):
                        if event.buttons() == Qt.MouseButton.LeftButton:
                            self.move(event.globalPosition().toPoint() - self.drag_pos)
                            event.accept()
                    
                    def update_session_info(self, session_id, activity_type, event_data=None, weapon=None):
                        if session_id:
                            self.session_label.setText(f"Session: {session_id[:8]}")
                            if not self.session_start:
                                from datetime import datetime
                                self.session_start = datetime.now()
                        else:
                            self.session_label.setText("Session: Not Started")
                            self.session_start = None
                        
                        self.activity_label.setText(f"Activity: {activity_type or 'None'}")
                        self.weapon_label.setText(f"Weapon: {weapon or 'None'}")
                        
                        if event_data:
                            self.event_count += 1
                            event_type = event_data.get('event_type', 'Unknown')
                            self.last_event_label.setText(f"Last: {event_type}")
                
                    def update_stats(self):
                        if self.session_start:
                            from datetime import datetime
                            duration = datetime.now() - self.session_start
                            hours, remainder = divmod(duration.total_seconds(), 3600)
                            minutes, seconds = divmod(remainder, 60)
                            self.stats_label.setText(f"Events: {self.event_count} | Duration: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
                        else:
                            self.stats_label.setText(f"Events: {self.event_count} | Duration: 00:00:00")
                
                self.overlay_window = DraggableOverlay()
                self.overlay_window.show()
                self.overlay_btn.setText("Hide Overlay")
                
                # Connect overlay updates
                self.overlay_timer = QTimer()
                self.overlay_timer.timeout.connect(self.overlay_window.update_stats)
                self.overlay_timer.start(1000)  # Update every second
                
                print("Overlay window created with draggable background")
            else:
                if self.overlay_window.isVisible():
                    self.overlay_window.hide()
                    if hasattr(self, 'overlay_timer'):
                        self.overlay_timer.stop()
                    self.overlay_btn.setText("Show Overlay")
                else:
                    self.overlay_window.show()
                    if hasattr(self, 'overlay_timer'):
                        self.overlay_timer.start()
                    self.overlay_btn.setText("Hide Overlay")
        except Exception as e:
            print(f"Error toggling overlay: {e}")
    
    def load_weapons(self):
        """Load weapons from database"""
        from pathlib import Path
        import json
        from typing import Dict, Any
        
        # Clear existing items
        self.weapon_combo.clear()
        
        # Add placeholder
        self.weapon_combo.addItem("Select Weapon...", None)
        
        # Load weapons from weapons.json database
        weapons_data: Dict[str, Any] = {}
        try:
            weapons_path = Path(__file__).parent.parent / "weapons.json"
            if weapons_path.exists():
                with open(weapons_path, 'r') as f:
                    weapons_data = json.load(f)
                    print(f"Loaded weapons database with {len(weapons_data.get('data', {}))} weapons")
                
        except Exception as e:
            print(f"Error loading weapons database: {e}")
            weapons_data = {'data': {}}
        
        # Add weapons to combo box with real stats
        added_weapons = []
        for weapon_name, stats in weapons_data.get('data', {}).items():
            self.weapon_combo.addItem(weapon_name, weapon_name)
            added_weapons.append(weapon_name)
            
        # Add fallback weapons if database is empty
        if not added_weapons:
            fallback_weapons = [
                "Korss H400 (L)",
                "P5a (L)", 
                "H400 (L)",
                "ME(L)",
                "Karwapak (L)",
                "Adj. M107a",
                "ML-35"
            ]
            
            for weapon in fallback_weapons:
                self.weapon_combo.addItem(weapon, weapon)
                
        self.weapon_combo.addItem("Custom...", None)
        self.weapon_combo.currentTextChanged.connect(self.update_weapon_display)
            
        self.weapon_combo.addItem("Custom...", None)
        self.weapon_combo.currentTextChanged.connect(self.update_weapon_display)
        
        # Update overlay if it exists and session is active
        if hasattr(self, 'overlay_window') and self.overlay_window:
            # Get current session info
            session_active = "Session Active" in self.session_label.text()
            if session_active:
                activity = self.activity_combo.currentText()
                self.overlay_window.update_session_info("active", activity, weapon=weapon)
    
    def get_selected_weapon(self):
        """Get the currently selected weapon"""
        if not hasattr(self, 'weapon_combo'):
            return None
            
        current_data = self.weapon_combo.currentData()
        current_text = self.weapon_combo.currentText()
        
        if current_data is None:
            if current_text == "Select Weapon...":
                return None
            elif current_text == "Custom...":
                return None  # Could open dialog for custom weapon
            else:
                return current_text  # Custom typed weapon
        else:
            return current_data
    
    def get_weapon_stats(self, weapon_name):
        """Get detailed stats for selected weapon"""
        if not weapon_name:
            weapon_name = self.get_selected_weapon()
            if not weapon_name:
                return {}
        
        from pathlib import Path
        import json
        
        try:
            weapons_path = Path(__file__).parent.parent / "weapons.json"
            if weapons_path.exists():
                with open(weapons_path, 'r') as f:
                    weapons_data = json.load(f)
                    return weapons_data.get('data', {}).get(weapon_name, {})
        except Exception:
            return {}
        
    def get_full_weapon_config(self):
        """Get complete weapon configuration for calculations"""
        weapon_name = self.get_selected_weapon()
        base_stats = self.get_weapon_stats(weapon_name)
        
        # Add configuration panel values
        config_stats = {
            'attachment': getattr(self, 'attachment_combo', type('', (), {'currentText': lambda: 'None'})).currentText(),
            'scope': getattr(self, 'scope_combo', type('', (), {'currentText': lambda: 'None'})).currentText(),
            'enhancers': {
                'damage': getattr(self, 'enhancer_inputs', {}).get('dmg_enh', type('', (), {'value': lambda: 0})).value(),
                'range': getattr(self, 'enhancer_inputs', {}).get('range_enh', type('', (), {'value': lambda: 0})).value(),
                'accuracy': getattr(self, 'enhancer_inputs', {}).get('acc_enh', type('', (), {'value': lambda: 0})).value(),
                'economy': getattr(self, 'enhancer_inputs', {}).get('eco_enh', type('', (), {'value': lambda: 0})).value()
            },
            'damage_input': getattr(self, 'dmg_spinbox', type('', (), {'value': lambda: 0.0})).value(),
            'ammo_input': getattr(self, 'ammo_spinbox', type('', (), {'value': lambda: 0.0})).value()
        }
        
        return {**base_stats, **config_stats}
    
    def get_full_weapon_config(self):
        """Get complete weapon configuration for calculations"""
        config = {
            'weapon': self.get_selected_weapon(),
            'attachment': 'None',
            'scope': 'None',
            'enhancers': {'damage': 0, 'range': 0, 'accuracy': 0, 'economy': 0},
            'stats': {'damage': 0.0, 'ammo': 0.0}
        }
        
        if hasattr(self, 'attachment_combo') and hasattr(self.attachment_combo, 'currentText'):
            config['attachment'] = self.attachment_combo.currentText()
        if hasattr(self, 'scope_combo') and hasattr(self.scope_combo, 'currentText'):
            config['scope'] = self.scope_combo.currentText()
        if hasattr(self, 'enhancer_inputs'):
            def get_enhancer_value(key):
                enhancer = self.enhancer_inputs.get(key)
                return enhancer.value() if enhancer and hasattr(enhancer, 'value') else 0
            
            config['enhancers'] = {
                'damage': get_enhancer_value('dmg_enh'),
                'range': get_enhancer_value('range_enh'),
                'accuracy': get_enhancer_value('acc_enh'),
                'economy': get_enhancer_value('eco_enh')
            }
        if hasattr(self, 'dmg_spinbox') and hasattr(self.dmg_spinbox, 'value'):
            config['stats']['damage'] = self.dmg_spinbox.value()
        if hasattr(self, 'ammo_spinbox') and hasattr(self.ammo_spinbox, 'value'):
            config['stats']['ammo'] = self.ammo_spinbox.value()
            
        return config