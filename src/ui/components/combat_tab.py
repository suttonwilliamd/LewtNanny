"""
Combat tab implementation for LewtNanny
Tracks combat statistics including kills, damage, and efficiency
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from decimal import Decimal

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class CombatTabWidget(QWidget):
    """Combat statistics and tracking widget"""
    
    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.combat_data = []
        
        self.setup_ui()
        logger.info("CombatTabWidget initialized")
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        summary_section = self.create_combat_summary()
        layout.addWidget(summary_section)
        
        kills_section = self.create_kills_table()
        layout.addWidget(kills_section, 1)  # Give kills table stretch priority
        
        layout.addStretch()
    
    def create_combat_summary(self):
        """Create combat summary section"""
        section = QGroupBox("Combat Summary")
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
        layout.setContentsMargins(4, 28, 4, 4)  # Top margin accounts for title bar
        layout.setSpacing(4)
        
        summary_items = [
            ("Total Kills", "0"),
            ("Total Damage Dealt", "0.00"),
            ("Total Damage Received", "0.00"),
            ("Kills/Death Ratio", "0.0"),
            ("Critical Hits", "0"),
            ("Misses", "0")
        ]
        
        self.combat_summary_labels = {}
        
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
            
            self.combat_summary_labels[label] = value_lbl
            layout.addWidget(container, row, col)
        
        section.setLayout(layout)
        return section
    
    def create_kills_table(self):
        """Create kills table section"""
        section = QGroupBox("Recent Kills")
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

        self.kills_table = QTableWidget()
        self.kills_table.setColumnCount(5)
        self.kills_table.setHorizontalHeaderLabels([
            "#", "Enemy", "Damage", "Time", "Type"
        ])
        self.kills_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.kills_table.setAlternatingRowColors(True)
        self.kills_table.setSortingEnabled(True)
        self.kills_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.kills_table.setAlternatingRowColors(True)
        self.kills_table.setSortingEnabled(True)
        
        header = self.kills_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.kills_table)
        
        section.setLayout(layout)
        return section
    
    def set_db_manager(self, db_manager):
        """Set database manager"""
        self.db_manager = db_manager
        self.load_combat_data()
    
    def load_combat_data(self):
        """Load combat data from database"""
        logger.debug("Loading combat data")
        self.update_combat_display()
    
    def update_combat_display(self):
        """Update combat statistics display"""
        for label, value_lbl in self.combat_summary_labels.items():
            if "Kills" in label:
                value_lbl.setText("0")
            elif "Damage Dealt" in label:
                value_lbl.setText("0.00")
            elif "Damage Received" in label:
                value_lbl.setText("0.00")
            elif "Ratio" in label:
                value_lbl.setText("0.0")
            elif "Critical" in label:
                value_lbl.setText("0")
            elif "Misses" in label:
                value_lbl.setText("0")
        
        self.kills_table.setRowCount(0)
        logger.debug("Combat display updated")
    
    def add_combat_event(self, event_data: Dict[str, Any]):
        """Add a combat event"""
        logger.info(f"[COMBAT_TAB] ===========================================")
        logger.info(f"[COMBAT_TAB] >>> add_combat_event RECEIVED <<<")
        logger.info(f"[COMBAT_TAB] Event data: {event_data}")

        event_type = event_data.get('event_type', '')
        
        if event_type == 'combat':
            self.combat_data.append(event_data)
            self.update_combat_display()
            logger.debug(f"Combat event added: {event_data}")
    
    def clear_data(self):
        """Clear all combat data"""
        self.combat_data = []
        self.update_combat_display()
        logger.info("Combat data cleared")
