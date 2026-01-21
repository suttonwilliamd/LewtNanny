"""
Crafting tab implementation for LewtNanny
Tracks crafting statistics including success rates and material usage
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


class CraftingTabWidget(QWidget):
    """Crafting statistics and tracking widget"""
    
    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.crafting_data = []
        
        self.setup_ui()
        logger.info("CraftingTabWidget initialized")
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        summary_section = self.create_crafting_summary()
        layout.addWidget(summary_section)
        
        crafts_section = self.create_crafts_table()
        layout.addWidget(crafts_section, 1)  # Give crafts table stretch priority
        
        layout.addStretch()
    
    def create_crafting_summary(self):
        """Create crafting summary section"""
        section = QGroupBox("Crafting Summary")
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
            ("Total Crafts", "0"),
            ("Successes", "0"),
            ("Failures", "0"),
            ("Success Rate", "0.0%"),
            ("Total Cost", "0.00 PED"),
            ("Total Return", "0.00 PED")
        ]
        
        self.crafting_summary_labels = {}
        
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
            
            self.crafting_summary_labels[label] = value_lbl
            layout.addWidget(container, row, col)
        
        section.setLayout(layout)
        return section
    
    def create_crafts_table(self):
        """Create crafts table section"""
        section = QGroupBox("Crafting Log")
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

        self.crafts_table = QTableWidget()
        self.crafts_table.setColumnCount(6)
        self.crafts_table.setHorizontalHeaderLabels([
            "#", "Blueprint", "Result", "Cost", "Return", "Time"
        ])
        self.crafts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.crafts_table.setAlternatingRowColors(True)
        self.crafts_table.setSortingEnabled(True)
        self.crafts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.crafts_table.setAlternatingRowColors(True)
        self.crafts_table.setSortingEnabled(True)
        
        header = self.crafts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.crafts_table)
        
        section.setLayout(layout)
        return section
    
    def set_db_manager(self, db_manager):
        """Set database manager"""
        self.db_manager = db_manager
        self.load_crafting_data()
    
    def load_crafting_data(self):
        """Load crafting data from database"""
        logger.debug("Loading crafting data")
        self.update_crafting_display()
    
    def update_crafting_display(self):
        """Update crafting statistics display"""
        for label, value_lbl in self.crafting_summary_labels.items():
            if "Crafts" in label:
                value_lbl.setText("0")
            elif "Successes" in label:
                value_lbl.setText("0")
            elif "Failures" in label:
                value_lbl.setText("0")
            elif "Rate" in label:
                value_lbl.setText("0.0%")
            elif "Cost" in label:
                value_lbl.setText("0.00 PED")
            elif "Return" in label:
                value_lbl.setText("0.00 PED")
        
        self.crafts_table.setRowCount(0)
        logger.debug("Crafting display updated")
    
    def add_crafting_event(self, event_data: Dict[str, Any]):
        """Add a crafting event"""
        event_type = event_data.get('event_type', '')
        
        if event_type == 'crafting':
            self.crafting_data.append(event_data)
            self.update_crafting_display()
            logger.debug(f"Crafting event added: {event_data}")
    
    def clear_data(self):
        """Clear all crafting data"""
        self.crafting_data = []
        self.update_crafting_display()
        logger.info("Crafting data cleared")
