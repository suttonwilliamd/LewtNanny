#!/usr/bin/env python3
"""
Final working test based on our successful test pattern
"""

import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout

# Add src to path
sys.path.insert(0, 'src')

def main():
    print("Creating PyQt6 application...")
    
    app = QApplication([])
    window = QWidget()
    layout = QVBoxLayout(window)
    
    label = QLabel("LewtNanny - Working Test!")
    label.setStyleSheet("font-size: 18px; color: #2E8B57; padding: 20px;")
    layout.addWidget(label)
    
    window.setLayout(layout)
    window.setWindowTitle("LewtNanny - SUCCESS")
    window.resize(600, 400)
    
    window.show()
    print("Window created and shown")
    
    return app.exec()

if __name__ == "__main__":
    print("Starting final test...")
    sys.exit(main())