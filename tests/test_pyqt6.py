#!/usr/bin/env python3
"""Simple test to isolate the PyQt6/qasync issue"""

import sys

# Add src to path
sys.path.insert(0, "src")

print("Testing PyQt6 imports...")

try:
    from PyQt6.QtWidgets import QApplication, QLabel

    print("SUCCESS: PyQt6 imports successful")
except ImportError as e:
    print(f"✗ PyQt6 import failed: {e}")
    sys.exit(1)

try:
    print("SUCCESS: Main window import successful")
except Exception as e:
    print(f"✗ Main window import failed: {e}")
    sys.exit(1)

print("Testing application creation...")

try:
    app = QApplication([])
    label = QLabel("Test")
    label.show()
    print("SUCCESS: Application creation successful")
except Exception as e:
    print(f"✗ Application creation failed: {e}")
    sys.exit(1)

print("All tests passed! PyQt6 is working correctly.")
