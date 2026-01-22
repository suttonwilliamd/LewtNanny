#!/usr/bin/env python3
"""
Test script for the new WeaponSelector component
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.ui.components.weapon_selector import WeaponSelector
from src.core.database import DatabaseManager


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weapon Selector Test")
        self.setMinimumSize(1200, 800)
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background: #1A1F2E;
            }
            QWidget {
                background: #1A1F2E;
                color: #E0E1E3;
            }
        """)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create weapon selector
        self.db_manager = DatabaseManager("data/lewtnanny.db")
        
        self.weapon_selector = WeaponSelector(
            parent=central,
            db_manager=self.db_manager
        )
        layout.addWidget(self.weapon_selector)
        
        # Connect signals for testing
        self.weapon_selector.signals.weapon_selected.connect(self._on_weapon_selected)
        self.weapon_selector.signals.cost_calculated.connect(self._on_cost_calculated)
        
        print("Test window created successfully!")
        print("Features to test:")
        print("  - Weapon table with filtering")
        print("  - Attachment selectors (Amp, Scope, Sight 1, Sight 2)")
        print("  - Enhancement sliders (Damage, Accuracy, Economy) 0-20")
        print("  - Cost analysis with animated values")
        print("  - Cost breakdown bar")
        print("  - Session stats bar")
        print("  - Loadout save/load/reset buttons")
    
    def _on_weapon_selected(self, data):
        print(f"Selected: {data}")
    
    def _on_cost_calculated(self, data):
        print(f"Cost calculated: {data}")


async def init_database():
    """Initialize database and load data"""
    db = DatabaseManager("data/lewtnanny.db")
    await db.initialize()
    return db


def main():
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Initialize database
    print("Initializing database...")
    db = asyncio.run(init_database())
    weapon_count = asyncio.run(db.get_weapon_count())
    print(f"Database initialized with {weapon_count} weapons")
    
    # Create and show window
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
