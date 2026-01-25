"""
LewtNanny - Entropia Universe Loot Tracking and Financial Analytics
Main application entry point with PyQt6 UI
"""

import sys
import logging
import asyncio

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from cli import main as cli_main, AppConfig
from src.core.app_config import app_config as default_config

from src.ui.main_window_tabbed import TabbedMainWindow as MainWindow
from src.core.database import DatabaseManager
from src.services.config_manager import ConfigManager
from src.services.chat_reader import ChatReader
from src.utils.logger import setup_logger

logger = logging.getLogger(__name__)


class LewtNannyApp:
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or default_config
        self.app = None
        self.main_window = None
        self.db_manager = None
        self.config_manager = None
        self.chat_reader = None
        
        logger.info("LewtNannyApp initialized")
    
    def _get_icon_path(self) -> Optional[Path]:
        """Get the path to the application icon, works both in dev and PyInstaller"""
        import sys
        
        # Try PyInstaller bundled path first
        if hasattr(sys, '_MEIPASS'):
            # Running in PyInstaller bundle
            bundle_dir = Path(sys._MEIPASS)
            icon_path = bundle_dir / 'LewtNanny.ico'
            if icon_path.exists():
                logger.info(f"Found icon in PyInstaller bundle: {icon_path}")
                return icon_path
        
        # Fallback to development paths
        # Try current working directory
        icon_path = Path.cwd() / 'LewtNanny.ico'
        if icon_path.exists():
            logger.info(f"Found icon in current directory: {icon_path}")
            return icon_path
        
        # Try relative to this file (development)
        try:
            icon_path = Path(__file__).parent / 'LewtNanny.ico'
            if icon_path.exists():
                logger.info(f"Found icon relative to script: {icon_path}")
                return icon_path
        except:
            pass
            
        logger.warning("Could not find LewtNanny.ico icon file")
        return None
    
    async def initialize_db(self):
        """Initialize database and config (can run before QApplication)"""
        logger.info("Initializing database and config...")
        
        setup_logger()
        
        self.db_manager = DatabaseManager()
        await self.db_manager.initialize()
        logger.info("Database initialized")
        
        self.config_manager = ConfigManager()
        await self.config_manager.initialize()
        logger.info("Config manager initialized")
    
    def initialize_ui(self):
        """Initialize UI components (must run after QApplication)"""
        logger.info("Initializing UI components...")
        
        self.main_window = MainWindow(self.db_manager, self.config_manager)
        logger.info("Main window created")
        
        self._init_chat_reader()
        
        logger.info("UI initialization complete")
    
    def _init_chat_reader(self):
        """Initialize chat reader"""
        logger.info("[MAIN] _init_chat_reader called")
        try:
            chat_reader = ChatReader(
                self.db_manager, 
                self.config_manager
            )
            
            logger.info("[MAIN] Connecting chat_reader.new_event to main_window.handle_new_event")
            chat_reader.new_event.connect(
                self.main_window.handle_new_event
            )
            
            # Pass chat_reader to main_window for session management
            self.main_window.chat_reader = chat_reader
            
            logger.info("[MAIN] Chat reader initialized and connected successfully")
        
        except Exception as e:
            logger.error(f"[MAIN] Error initializing chat reader: {e}", exc_info=True)
    
    def run(self):
        """Start the application"""
        logger.info("Starting LewtNanny application...")
        
        self.app = QApplication(sys.argv)
        
        self.app.setStyle('Fusion')
        
        # Set application icon
        icon_path = self._get_icon_path()
        if icon_path and icon_path.exists():
            self.app.setWindowIcon(QIcon(str(icon_path)))
            logger.info(f"Application icon set from: {icon_path}")
        else:
            logger.warning("Could not load application icon")
        
        self.initialize_ui()
        
        self.main_window.show()
        
        logger.info("Application window shown")
        
        return self.app.exec()


def main():
    """Main entry point"""
    logger.info("LewtNanny starting...")
    
    config = cli_main()
    if not config:
        logger.error("Failed to parse command line arguments")
        sys.exit(1)
    
    app = LewtNannyApp(config)
    
    try:
        asyncio.run(app.initialize_db())
        exit_code = app.run()
        logger.info(f"Application exited with code: {exit_code}")
        sys.exit(exit_code)
    
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        QMessageBox.critical(None, "Error", f"Application error:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
