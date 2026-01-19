#!/usr/bin/env python3
"""
Simplified main application to isolate the issue
"""

import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout

# Add src to path
sys.path.insert(0, 'src')

from ui.main_window import MainWindow
from core.database import DatabaseManager
from services.config_manager import ConfigManager

def test_init():
    """Simplified initialization"""
    print("Initializing components...")
    # Just create a simple window
    app = QApplication([])
    
    window = QWidget()
    layout = QVBoxLayout(window)
    
    label = QLabel("LewtNanny - Simplified Test")
    label.setStyleSheet("font-size: 18px; color: #2E8B57;")
    layout.addWidget(label)
    
    window.setLayout(layout)
    window.setWindowTitle("LewtNanny Test")
    window.resize(400, 300)
    window.show()
    
    print("Application should be visible now")

if __name__ == "__main__":
    print("Starting simplified test...")
    app = QApplication([])
    test_init()
    
    print("Application running - should be visible")
    sys.exit(app.exec())