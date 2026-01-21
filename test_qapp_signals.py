#!/usr/bin/env python3
"""Test signal handling in the context of an async event loop"""

import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

# Create a signal emitter
class ChatReaderSimulator(QObject):
    new_event = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._running = False

    def start(self):
        self._running = True
        # Simulate async polling
        async def poll():
            count = 0
            while self._running and count < 3:
                await asyncio.sleep(0.5)
                count += 1
                # Emit signal from the async context
                self.new_event.emit({
                    'event_type': 'loot',
                    'parsed_data': {
                        'items': f'Shimmering Patch x ({count})',
                        'value': 0.01 * count
                    }
                })
                print(f"[SIMULATOR] Emitted signal #{count}")
        asyncio.create_task(poll())

    def stop(self):
        self._running = False

# Create a mock UI
class MockMainWindow:
    def __init__(self, app):
        self.app = app
        self.events = []
        self.chat_reader = None

    def connect_chat_reader(self, chat_reader):
        print("[MOCK UI] Connecting chat_reader.new_event to handle_new_event")
        chat_reader.new_event.connect(self.handle_new_event)
        self.chat_reader = chat_reader

    def handle_new_event(self, event_data):
        print(f"[MOCK UI] handle_new_event called with: {event_data.get('event_type')}")
        self.events.append(event_data)

def test_with_qapp():
    print("=" * 60)
    print("TESTING SIGNAL HANDLING WITH QAPPLICATION")
    print("=" * 60)

    app = QApplication([])

    # Create mock UI
    main_window = MockMainWindow(app)

    # Create chat reader simulator
    chat_reader = ChatReaderSimulator()

    # Connect signal
    main_window.connect_chat_reader(chat_reader)
    print("Signal connected!")

    # Start chat reader (simulates clicking Start Run)
    print("\nStarting chat reader...")
    chat_reader.start()

    # Process events
    print("\nProcessing events (3 seconds)...")
    deadline = asyncio.get_event_loop().time() + 3

    def check_done():
        if asyncio.get_event_loop().time() < deadline:
            QTimer.singleShot(100, check_done)
        else:
            print(f"\nEvents received: {len(main_window.events)}")
            if main_window.events:
                print("SUCCESS: Signals were received!")
            else:
                print("FAILURE: No signals received!")
            print("=" * 60)
            chat_reader.stop()
            app.quit()

    QTimer.singleShot(100, check_done)

    return app.exec()

# Run test
result = test_with_qapp()
print(f"App exit code: {result}")
