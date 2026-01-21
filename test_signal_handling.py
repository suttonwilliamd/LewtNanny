#!/usr/bin/env python3
"""Test UI signal handling"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

# Create a mock signal emitter
class MockChatReader(QObject):
    new_event = pyqtSignal(dict)

# Create a mock receiver
class MockMainWindow:
    def __init__(self):
        self.events_received = []

    def handle_new_event(self, event_data):
        print(f"[MOCK UI] Received event: {event_data.get('event_type')}")
        self.events_received.append(event_data)

def test_signal_handling():
    print("=" * 60)
    print("TESTING UI SIGNAL HANDLING")
    print("=" * 60)

    # Create mock objects
    chat_reader = MockChatReader()
    main_window = MockMainWindow()

    # Connect signal
    print("\n1. Connecting signal...")
    chat_reader.new_event.connect(main_window.handle_new_event)
    print("   Signal connected!")

    # Emit a loot event
    print("\n2. Emitting loot event...")
    loot_event = {
        'event_type': 'loot',
        'parsed_data': {
            'items': 'Shrapnel x (999)',
            'value': 0.0999
        }
    }
    chat_reader.new_event.emit(loot_event)

    print(f"\n3. Events received: {len(main_window.events_received)}")

    if main_window.events_received:
        print("SUCCESS: Signal handling works!")
    else:
        print("FAILURE: Signal was not received!")

    print("=" * 60)

# Run test
test_signal_handling()
