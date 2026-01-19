"""
Chat log reader for real-time game event parsing
"""

import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyQt6.QtCore import QObject, pyqtSignal

from src.models.models import EventType, ActivityType


class ChatFileHandler(FileSystemEventHandler):
    """Handle file system events for chat log monitoring"""
    
    def __init__(self, chat_reader):
        self.chat_reader = chat_reader
        self.last_position = 0
        
    def on_modified(self, event):
        """Called when file is modified"""
        if not event.is_directory and str(event.src_path).endswith('.txt'):
            asyncio.create_task(self.chat_reader.process_file_changes(event.src_path))


class ChatReader(QObject):
    """Real-time chat log reader and parser"""
    
    new_event = pyqtSignal(dict)  # Signal for new parsed events
    
    def __init__(self, db_manager, config_manager):
        super().__init__()
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.observer = None
        self.current_session_id = None
        self.current_activity = ActivityType.HUNTING
        
        # Regex patterns for parsing
        self.patterns = {
            'loot': re.compile(r'You\s+looted\s+(.+?)\s+from\s+(.+)'),
            'damage': re.compile(r'You\s+dealt\s+(\d+)\s+points\s+of\s+damage'),
            'critical': re.compile(r'Critical\s+hit!\s+(\d+)\s+points\s+of\s+damage'),
            'miss': re.compile(r'You\s+missed\s+(.+)'),
            'weapon': re.compile(r'You\s+equipped\s+(.+)'),
            'global': re.compile(r'GLOBAL\s+HOF!\s+(.+?)\s+looted\s+(.+?)\s+PED'),
            'hof': re.compile(r'HOF!\s+(.+?)\s+looted\s+(.+?)\s+PED'),
            'craft_success': re.compile(r'You\s+successfully\s+crafted\s+(.+)'),
            'craft_fail': re.compile(r'You\s+failed\s+to\s+craft\s+(.+)'),
            'skill': re.compile(r'You\s+gained\s+(.+?)\s+in\s+(.+)')
        }
        
    async def start_monitoring(self, log_file_path: str):
        """Start monitoring chat log file"""
        try:
            # Stop existing monitoring
            await self.stop_monitoring()
            
            # Setup file observer
            self.observer = Observer()
            log_path = Path(log_file_path)
            
            if not log_path.exists():
                print(f"Chat log file not found: {log_file_path}")
                return False
                
            # Create file handler
            handler = ChatFileHandler(self)
            self.observer.schedule(handler, str(log_path.parent), recursive=False)
            self.observer.start()
            
            # Create initial session
            self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            await self.db_manager.create_session(self.current_session_id, self.current_activity.value)
            
            print(f"Started monitoring: {log_file_path}")
            return True
            
        except Exception as e:
            print(f"Error starting chat monitoring: {e}")
            return False
    
    async def stop_monitoring(self):
        """Stop monitoring chat log file"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.current_session_id = None
    
    async def process_file_changes(self, file_path: str):
        """Process new lines in chat log file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, 2)  # Go to end of file
                new_lines = f.readlines()
                
                for line in new_lines:
                    line = line.strip()
                    if line:
                        await self.parse_line(line)
                        
        except Exception as e:
            print(f"Error processing file changes: {e}")
    
    async def parse_line(self, line: str):
        """Parse a single chat line for game events"""
        event_data = None
        
        # Check for loot events
        loot_match = self.patterns['loot'].search(line)
        if loot_match:
            loot_info = loot_match.groups()
            event_data = {
                'event_type': EventType.LOOT.value,
                'activity_type': self.current_activity.value,
                'raw_message': line,
                'parsed_data': {
                    'items': loot_info[0],
                    'creature': loot_info[1],
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }
        
        # Check for damage events
        elif self.patterns['damage'].search(line):
            damage = int(self.patterns['damage'].search(line).group(1))
            event_data = {
                'event_type': EventType.COMBAT.value,
                'activity_type': self.current_activity.value,
                'raw_message': line,
                'parsed_data': {
                    'damage': damage,
                    'critical': False,
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }
        
        # Check for critical hits
        elif self.patterns['critical'].search(line):
            damage = int(self.patterns['critical'].search(line).group(1))
            event_data = {
                'event_type': EventType.COMBAT.value,
                'activity_type': self.current_activity.value,
                'raw_message': line,
                'parsed_data': {
                    'damage': damage,
                    'critical': True,
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }
        
        # Check for global/HOF events
        elif self.patterns['global'].search(line) or self.patterns['hof'].search(line):
            event_data = {
                'event_type': EventType.GLOBAL.value,
                'activity_type': self.current_activity.value,
                'raw_message': line,
                'parsed_data': {
                    'type': 'hof' if 'HOF!' in line else 'global',
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }
        
        # Check for crafting events
        elif self.patterns['craft_success'].search(line):
            result = self.patterns['craft_success'].search(line).group(1)
            event_data = {
                'event_type': EventType.CRAFTING.value,
                'activity_type': ActivityType.CRAFTING.value,
                'raw_message': line,
                'parsed_data': {
                    'result': result,
                    'success': True,
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }
        
        elif self.patterns['craft_fail'].search(line):
            result = self.patterns['craft_fail'].search(line).group(1)
            event_data = {
                'event_type': EventType.CRAFTING.value,
                'activity_type': ActivityType.CRAFTING.value,
                'raw_message': line,
                'parsed_data': {
                    'result': result,
                    'success': False,
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }
        
        # If we found an event, save it and emit signal
        if event_data:
            await self.db_manager.add_event(event_data)
            self.new_event.emit(event_data)
    
    def set_activity_type(self, activity_type: ActivityType):
        """Set current activity type"""
        self.current_activity = activity_type
    
    async def create_new_session(self, activity_type: ActivityType):
        """Create a new session with specified activity"""
        self.current_activity = activity_type
        self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        await self.db_manager.create_session(self.current_session_id, activity_type.value)