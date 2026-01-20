"""
LewtNanny - Entropia Universe Loot Tracking and Financial Analytics
Main application entry point with feature flags and UI framework selection
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional

# Import configuration
from cli import main as cli_main, AppConfig
from src.core.app_config import app_config as default_config

# Import PyQt6 components
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    import qasync
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    print("PyQt6 not available. Install with: pip install PyQt6 qasync")

# Import Tkinter components (fallback)
try:
    import tkinter as tk
    from tkinter import messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

# Import application components
from src.ui.main_window import MainWindow
from src.core.database import DatabaseManager
from src.services.config_manager import ConfigManager
from src.services.chat_reader import ChatReader
from src.utils.logger import setup_logger


class LewtNannyApp:
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or default_config
        self.app = None
        self.main_window = None
        self.db_manager = None
        self.config_manager = None
        self.chat_reader = None
        
    async def initialize(self):
        """Initialize all application components"""
        # Setup logging
        setup_logger()  # TODO: Update logger to support verbose flag
        
        # Initialize database
        self.db_manager = DatabaseManager()
        await self.db_manager.initialize()
        
        # Initialize configuration
        self.config_manager = ConfigManager()
        await self.config_manager.initialize()
        
        # Initialize UI based on framework choice
        if self.config.ui_framework == "pyqt6" and PYQT6_AVAILABLE:
            await self._initialize_pyqt6()
        elif self.config.ui_framework == "tkinter" and TKINTER_AVAILABLE:
            await self._initialize_tkinter()
        else:
            # Fallback logic
            if PYQT6_AVAILABLE:
                await self._initialize_pyqt6()
            elif TKINTER_AVAILABLE:
                await self._initialize_tkinter()
            else:
                raise RuntimeError("No UI framework available. Install PyQt6 or ensure Tkinter is available.")
        
        # Initialize chat reader if enabled
        if self.config.enable_chat_monitoring:
            self.chat_reader = ChatReader(
                self.db_manager, 
                self.config_manager
            )
            
            # Connect signals
            self.chat_reader.new_event.connect(
                self.main_window.handle_new_event
            )
    
    async def _initialize_pyqt6(self):
        """Initialize PyQt6 UI"""
        # Initialize main window
        self.main_window = MainWindow(
            self.db_manager, 
            self.config_manager
        )
        
        # Apply window size
        if self.config.window_size:
            self.main_window.setGeometry(100, 100, *self.config.window_size)
    
    async def _initialize_tkinter(self):
        """Initialize Tkinter UI (fallback)"""
        # For now, show a message box indicating PyQt6 is preferred
        if PYQT6_AVAILABLE:
            print("PyQt6 is available but Tkinter was selected. Consider using --ui pyqt6 for better experience.")
        
        # Create simple Tkinter interface as fallback
        self.app = tk.Tk()
        self.app.title("LewtNanny - Tkinter Fallback")
        self.app.geometry(f"{self.config.window_size[0]}x{self.config.window_size[1]}")
        
        label = tk.Label(
            self.app, 
            text="LewtNanny\nTkinter Fallback Interface\n\nUse --ui pyqt6 for full features",
            justify=tk.CENTER,
            font=("Arial", 14)
        )
        label.pack(pady=50)
        
        # Simple status display
        status_label = tk.Label(self.app, text="Status: Ready (Limited Functionality)")
        status_label.pack(pady=10)
        
        # Note: Tkinter version has limited functionality
        # Full features available with PyQt6
        
    def run(self):
        """Start the application"""
        if self.config.ui_framework == "pyqt6" and PYQT6_AVAILABLE:
            return self._run_pyqt6()
        elif self.config.ui_framework == "tkinter" or not PYQT6_AVAILABLE:
            return self._run_tkinter()
        else:
            raise RuntimeError(f"UI framework '{self.config.ui_framework}' not available")
    
    def _run_pyqt6(self):
        """Run PyQt6 application"""
        import asyncio
        from pathlib import Path
        
        # Initialize synchronously first
        self.app = QApplication(sys.argv)
        
        # Load theme (default to dark theme)
        theme_name = getattr(self.config, 'theme', 'dark')
        self._load_theme(theme_name)
        
        # Create main window
        self.main_window = MainWindow(
            self.db_manager, 
            self.config_manager
        )
        
        # Apply window size
        if self.config.window_size:
            self.main_window.setGeometry(100, 100, *self.config.window_size)
        
        self.main_window.show()
        
        # Initialize async components synchronously for now
        # asyncio.create_task(self._async_init_components())
        
        return self.app.exec()
    
    def _load_theme(self, theme_name):
        """Load theme stylesheet"""
        try:
            theme_path = Path(__file__).parent / "themes" / f"{theme_name}.qss"
            if theme_path.exists():
                with open(theme_path, 'r') as f:
                    stylesheet = f.read()
                self.app.setStyleSheet(stylesheet)
                print(f"Loaded {theme_name} theme successfully")
            else:
                print(f"Theme file not found: {theme_path}")
        except Exception as e:
            print(f"Error loading theme {theme_name}: {e}")
    
    async def _async_init_components(self):
        """Initialize async components after UI is shown"""
        try:
            # Initialize chat reader if enabled
            if self.config.enable_chat_monitoring:
                from src.core.chat_reader import ChatReader
                self.chat_reader = ChatReader(
                    self.db_manager, 
                    self.config_manager
                )
                
                # Connect signals
                if self.chat_reader and self.main_window:
                    self.chat_reader.new_event.connect(
                        self.main_window.handle_new_event
                    )
        except Exception as e:
            print(f"Error initializing async components: {e}")
    
    def _run_tkinter(self):
        """Run Tkinter application"""
        asyncio.create_task(self.initialize())
        self.app.mainloop()
        return 0


def main():
    """Main entry point"""
    # Parse command line arguments
    config = cli_main()
    if not config:
        sys.exit(1)
    
    # Create and run application
    app = LewtNannyApp(config)
    sys.exit(app.run())


if __name__ == "__main__":
    main()