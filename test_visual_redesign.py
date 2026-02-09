#!/usr/bin/env python3
"""Quick test to verify overlay visual redesign"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from src.ui.overlay import SessionOverlay
from src.core.multi_database_manager import MultiDatabaseManager
from src.services.config_manager import ConfigManager
from datetime import datetime


def test_overlay_visuals():
    """Test the visual redesign of the overlay"""
    app = QApplication(sys.argv)

    # Create overlay
    db_manager = MultiDatabaseManager()
    config_manager = ConfigManager()
    overlay = SessionOverlay(db_manager, config_manager)

    # Show overlay
    overlay.show()

    # Start session
    overlay.start_session("visual_test_session", "hunting")

    # Test various events to see visual changes
    test_events = [
        {
            "event_type": "combat",
            "parsed_data": {
                "damage": 15.5,
                "miss": False,
                "dodged": False,
            },
        },
        {
            "event_type": "loot",
            "parsed_data": {
                "value": 25.75,
                "item_name": "Test Loot 1",
                "timestamp": datetime.now().isoformat(),
            },
        },
        {
            "event_type": "combat",
            "parsed_data": {
                "damage": 22.3,
                "miss": False,
                "dodged": False,
            },
        },
        {
            "event_type": "loot",
            "parsed_data": {
                "value": 45.20,
                "item_name": "Test Loot 2",
                "timestamp": datetime.now().isoformat(),
            },
        },
    ]

    print("Testing visual redesign with events...")

    # Send test events
    for i, event in enumerate(test_events):
        print(f"Sending event {i + 1}: {event['event_type']}")
        overlay.add_event(event)
        # Small delay to see changes
        app.processEvents()

    print("Visual redesign test complete!")
    print("The overlay should now show:")
    print("- Modern glass-morphism design")
    print("- Rounded corners and gradients")
    print("- Improved typography with Segoe UI")
    print("- Enhanced color scheme")
    print("- Better visual hierarchy")
    print("- Container-based layouts")

    # Keep window open for visual inspection
    overlay.overlay_widget.show()
    return app.exec()


if __name__ == "__main__":
    test_overlay_visuals()
