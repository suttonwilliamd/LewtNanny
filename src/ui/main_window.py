"""
Main window for LewtNanny PyQt6 GUI
"""

import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QTextEdit, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QGroupBox, QGridLayout, QLineEdit,
    QComboBox, QSpinBox, QCheckBox, QFileDialog
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
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Status bar
        self.setup_status_bar()
        
        # Tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_loot_tab()
        self.create_analysis_tab()
        self.create_config_tab()
        
    def setup_status_bar(self):
        """Setup status bar"""
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        
        # Session controls
        self.session_label = QLabel("No active session")
        self.start_session_btn = QPushButton("Start Session")
        self.start_session_btn.clicked.connect(self.start_session)
        
        # Activity selector
        self.activity_combo = QComboBox()
        self.activity_combo.addItems([t.value for t in ActivityType])
        self.activity_combo.currentTextChanged.connect(self.change_activity)
        
        status_layout.addWidget(self.session_label)
        status_layout.addWidget(self.start_session_btn)
        status_layout.addWidget(QLabel("Activity:"))
        status_layout.addWidget(self.activity_combo)
        status_layout.addStretch()
        
        self.layout().addWidget(status_widget)
        
    def setup_timer(self):
        """Setup update timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)  # Update every second
        
    def create_loot_tab(self):
        """Create loot tracking tab"""
        loot_widget = QWidget()
        loot_layout = QVBoxLayout(loot_widget)
        
        # Splitter for loot feed and stats
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Loot feed
        loot_group = QGroupBox("Recent Loot")
        loot_feed_layout = QVBoxLayout(loot_group)
        
        self.loot_feed = QTextEdit()
        self.loot_feed.setReadOnly(True)
        self.loot_feed.setFont(QFont("Courier", 9))
        loot_feed_layout.addWidget(self.loot_feed)
        
        splitter.addWidget(loot_group)
        
        # Quick stats
        stats_group = QGroupBox("Session Stats")
        stats_layout = QGridLayout(stats_group)
        
        self.total_cost_label = QLabel("Cost: 0.00 PED")
        self.total_return_label = QLabel("Return: 0.00 PED")
        self.profit_label = QLabel("Profit: 0.00 PED")
        self.dpp_label = QLabel("DPP: N/A")
        self.events_count_label = QLabel("Events: 0")
        
        stats_layout.addWidget(self.total_cost_label, 0, 0)
        stats_layout.addWidget(self.total_return_label, 0, 1)
        stats_layout.addWidget(self.profit_label, 1, 0)
        stats_layout.addWidget(self.dpp_label, 1, 1)
        stats_layout.addWidget(self.events_count_label, 2, 0, 1, 2)
        
        splitter.addWidget(stats_group)
        
        loot_layout.addWidget(splitter)
        self.tab_widget.addTab(loot_widget, "Loot")
        
    def create_analysis_tab(self):
        """Create analysis tab"""
        analysis_widget = QWidget()
        analysis_layout = QVBoxLayout(analysis_widget)
        
        # Event history table
        history_group = QGroupBox("Event History")
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Time", "Type", "Activity", "Details", "Session"])
        
        # Auto-resize columns
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        history_layout.addWidget(self.history_table)
        analysis_layout.addWidget(history_group)
        
        self.tab_widget.addTab(analysis_widget, "Analysis")
        
    def create_config_tab(self):
        """Create configuration tab"""
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        
        # Chat monitoring settings
        chat_group = QGroupBox("Chat Monitoring")
        chat_layout = QGridLayout(chat_group)
        
        self.log_file_edit = QLineEdit()
        self.log_file_edit.setPlaceholderText("Path to Entropia Universe chat log file")
        self.browse_log_btn = QPushButton("Browse...")
        self.browse_log_btn.clicked.connect(self.browse_log_file)
        
        self.monitoring_checkbox = QCheckBox("Enable real-time monitoring")
        self.monitoring_checkbox.setChecked(True)
        
        chat_layout.addWidget(QLabel("Log File:"), 0, 0)
        chat_layout.addWidget(self.log_file_edit, 0, 1)
        chat_layout.addWidget(self.browse_log_btn, 0, 2)
        chat_layout.addWidget(self.monitoring_checkbox, 1, 0, 1, 3)
        
        config_layout.addWidget(chat_group)
        
        # OCR settings
        ocr_group = QGroupBox("OCR Settings")
        ocr_layout = QGridLayout(ocr_group)
        
        self.ocr_enabled_checkbox = QCheckBox("Enable OCR for screenshots")
        self.ocr_enabled_checkbox.setChecked(True)
        
        self.screenshot_hotkey_edit = QLineEdit("F12")
        self.auto_screenshot_checkbox = QCheckBox("Auto-screenshot on events")
        
        ocr_layout.addWidget(self.ocr_enabled_checkbox, 0, 0, 1, 3)
        ocr_layout.addWidget(QLabel("Screenshot Hotkey:"), 1, 0)
        ocr_layout.addWidget(self.screenshot_hotkey_edit, 1, 1)
        ocr_layout.addWidget(self.auto_screenshot_checkbox, 2, 0, 1, 3)
        
        config_layout.addWidget(ocr_group)
        
        # Save button
        self.save_config_btn = QPushButton("Save Configuration")
        self.save_config_btn.clicked.connect(self.save_config)
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
        
    @pyqtSlot()
    def stop_session(self):
        """Stop the current tracking session"""
        self.start_session_btn.setText("Start Session")
        self.start_session_btn.clicked.disconnect()
        self.start_session_btn.clicked.connect(self.start_session)
        
        # Update status
        self.session_label.setText("No active session")
        
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
        
    def update_stats(self):
        """Update statistics display"""
        # This would query the database in the full version
        pass