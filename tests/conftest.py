"""Basic test configuration and utilities for LewtNanny"""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager"""
    manager = Mock()
    manager.initialize = Mock(return_value=None)
    manager.get_weapons = Mock(return_value=[])
    manager.get_events = Mock(return_value=[])
    return manager


@pytest.fixture
def mock_config_manager():
    """Create a mock configuration manager"""
    manager = Mock()
    manager.initialize = Mock(return_value=None)
    manager.get_config = Mock(return_value={})
    manager.set_config = Mock(return_value=None)
    return manager


@pytest.fixture
def sample_weapon_data():
    """Sample weapon data for testing"""
    return {
        "id": "1",
        "name": "Korss H400 (L)",
        "damage": 28,
        "ammo_burn": 11,
        "decay": 0.10,
        "hits": 36,
        "range": 55,
        "reload_time": 3.0,
        "weapon_type": "Pistol",
    }


@pytest.fixture
def sample_attachment_data():
    """Sample attachment data for testing"""
    return {
        "id": "a1",
        "name": "A106 Amplifier",
        "type": "amplifier",
        "damage_bonus": 0.5,
        "ammo_bonus": 0,
        "decay_modifier": 0.25,
    }


@pytest.fixture
def sample_event_data():
    """Sample event data for testing"""
    return {
        "timestamp": "2024-01-19T10:30:00",
        "event_type": "loot",
        "activity_type": "hunting",
        "raw_message": "You looted 10 PED",
        "parsed_data": {"amount": 10, "currency": "PED"},
        "session_id": "test_session_123",
    }


@pytest.fixture
def temp_db_file(tmp_path):
    """Create a temporary database file"""
    db_file = tmp_path / "test.db"
    yield db_file
    # Cleanup is handled automatically by tmp_path


class MockQtApplication:
    """Mock Qt application for testing without GUI"""

    def __init__(self):
        self.exec_called = False
        self.widgets = []

    def exec(self):
        """Mock exec to avoid starting GUI event loop"""
        self.exec_called = True
        return 0

    def quit(self):
        """Mock quit"""
        pass


@pytest.fixture
def mock_qt_app():
    """Mock Qt application for testing"""
    return MockQtApplication()


# Skip UI tests on headless environments
def pytest_configure(config):
    """Configure pytest for UI tests"""
    config.addinivalue_line("markers", "skip_ci: mark test to skip in CI environment")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip UI tests in CI"""
    import os

    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        skip_ui = pytest.mark.skip(reason="UI tests skipped in CI")
        for item in items:
            if "ui" in item.keywords:
                item.add_marker(skip_ui)
