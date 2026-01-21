"""
CLI interface for LewtNanny
Command-line argument parsing and application launcher
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from src.core.app_config import app_config, AppConfig


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="LewtNanny - Entropia Universe Loot Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Start GUI with default settings
  python main.py --debug            # Enable debug mode
  python main.py --no-ocr           # Disable OCR feature
  python main.py --ui tkinter       # Use Tkinter UI instead of PyQt6
  python main.py --window 800x600   # Set window size
        """
    )
    
    # UI Options
    ui_group = parser.add_argument_group('UI Options')
    ui_group.add_argument(
        '--ui', 
        choices=['pyqt6', 'tkinter'], 
        default=app_config.ui_framework,
        help='UI framework to use (default: %(default)s)'
    )
    ui_group.add_argument(
        '--window', 
        type=str, 
        metavar='WxH',
        help=f'Window size (default: {app_config.window_size[0]}x{app_config.window_size[1]})'
    )
    ui_group.add_argument(
        '--dark-theme', 
        action='store_true',
        help='Enable dark theme'
    )
    
    # Feature Flags
    feature_group = parser.add_argument_group('Feature Flags')
    feature_group.add_argument(
        '--no-ocr', 
        action='store_true',
        help='Disable OCR feature'
    )
    feature_group.add_argument(
        '--no-chat', 
        action='store_true',
        help='Disable chat monitoring'
    )
    feature_group.add_argument(
        '--no-weapon-selector', 
        action='store_true',
        help='Disable weapon selector'
    )
    feature_group.add_argument(
        '--no-overlay', 
        action='store_true',
        help='Disable overlay window'
    )
    
    # Development Options
    dev_group = parser.add_argument_group('Development Options')
    dev_group.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug mode'
    )
    dev_group.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    dev_group.add_argument(
        '--profile', 
        action='store_true',
        help='Enable performance profiling'
    )
    
    # Performance Options
    perf_group = parser.add_argument_group('Performance Options')
    perf_group.add_argument(
        '--no-cache', 
        action='store_true',
        help='Disable caching'
    )
    perf_group.add_argument(
        '--max-events', 
        type=int,
        metavar='N',
        help=f'Maximum events to keep in memory (default: {app_config.max_events_memory})'
    )
    
    return parser


def parse_window_size(window_str: Optional[str]) -> Optional[tuple]:
    """Parse window size string like '800x600' into tuple"""
    if not window_str:
        return None
    
    try:
        parts = window_str.lower().split('x')
        if len(parts) == 2:
            width = int(parts[0])
            height = int(parts[1])
            if width > 0 and height > 0:
                return (width, height)
    except (ValueError, AttributeError):
        pass
    
    return None


def create_config_from_args(args: argparse.Namespace) -> AppConfig:
    """Create AppConfig from command-line arguments"""
    config = AppConfig()
    
    # UI settings
    config.ui_framework = args.ui
    if args.dark_theme:
        config.enable_dark_theme = True
    if args.window:
        window_size = parse_window_size(args.window)
        if window_size:
            config.window_size = window_size
    
    # Feature flags
    if args.no_ocr:
        config.enable_ocr = False
    if args.no_chat:
        config.enable_chat_monitoring = False
    if args.no_weapon_selector:
        config.enable_weapon_selector = False
    if args.no_overlay:
        config.enable_overlay = False
    
    # Development settings
    if args.debug:
        config.debug_mode = True
    if args.verbose:
        config.verbose_logging = True
    if args.profile:
        config.enable_profiling = True
    
    # Performance settings
    if args.no_cache:
        config.enable_caching = False
    if args.max_events:
        config.max_events_memory = args.max_events
    
    return config


def main() -> Optional[AppConfig]:
    """Main CLI entry point for GUI launcher"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Create configuration
    config = create_config_from_args(args)
    
    return config


if __name__ == '__main__':
    main()
