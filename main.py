"""
LewtNanny - Entropia Universe Loot Tracking and Financial Analytics
Main application entry point
"""

import sys
import asyncio
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import qasync

from src.ui.main_window import MainWindow
from src.core.database import DatabaseManager
from src.services.config_manager import ConfigManager
from src.services.chat_reader import ChatReader
from src.utils.logger import setup_logger


class LewtNannyApp:
    def __init__(self):
        self.app = None
        self.main_window = None
        self.db_manager = None
        self.config_manager = None
        self.chat_reader = None
        
    async def initialize(self):
        """Initialize all application components"""
        # Setup logging
        setup_logger()
        
        # Initialize database
        self.db_manager = DatabaseManager()
        await self.db_manager.initialize()
        
        # Initialize configuration
        self.config_manager = ConfigManager()
        await self.config_manager.initialize()
        
        # Initialize main window
        self.main_window = MainWindow(
            self.db_manager, 
            self.config_manager
        )
        
        # Initialize chat reader
        self.chat_reader = ChatReader(
            self.db_manager, 
            self.config_manager
        )
        
        # Connect signals
        self.chat_reader.new_event.connect(
            self.main_window.handle_new_event
        )
        
    def run(self):
        """Start the application"""
        self.app = qasync.QApplication(sys.argv)
        
        # Schedule async initialization
        QTimer.singleShot(0, lambda: asyncio.create_task(self.initialize()))
        
        self.main_window.show()
        return self.app.exec()


def main():
    """Main entry point"""
    app = LewtNannyApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()