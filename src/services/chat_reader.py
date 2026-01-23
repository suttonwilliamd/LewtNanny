"""
Chat log reader for real-time game event parsing
Uses QTimer for Qt event loop integration
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from src.models.models import EventType, ActivityType

logger = logging.getLogger(__name__)


class ChatReader(QObject):
    """Reads Entropia Universe chat log and emits events for game actions"""

    new_event = pyqtSignal(dict)

    def __init__(self, db_manager, config_manager):
        super().__init__()
        self.db_manager = db_manager
        self.config_manager = config_manager

        self.monitoring_file_path = None
        self.last_position = 0
        self._polling = False
        self._poll_timer = None

        # Thread-safe queue for file modification events
        self._file_change_queue = []

        # Regex patterns for parsing - updated for Entropia Universe format
        import re
        self.patterns = {
            'loot': re.compile(r'You\s+received\s+(.+?)\s+x\s*\((\d+)\)\s+Value:\s*([\d.]+)\s+PED'),
            'damage': re.compile(r'You\s+inflicted\s+([\d.]+)\s+points\s+of\s+damage'),
            'damage_taken': re.compile(r'You\s+took\s+([\d.]+)\s+points\s+of\s+damage'),
            'critical': re.compile(r'Critical\s+hit\s+-\s+Additional\s+damage!\s+You\s+inflicted\s+([\d.]+)\s+points\s+of\s+damage'),
            'critical_armor': re.compile(r'Critical\s+hit\s+-\s+Armor\s+penetration!\s+You\s+took\s+([\d.]+)\s+points\s+of\s+damage'),
            'miss': re.compile(r'The attack missed you'),
            'dodge': re.compile(r'.*Dodged.*your\s+attack'),
            'evade': re.compile(r'You\s+Evaded\s+the\s+attack'),
            'heal': re.compile(r'You\s+healed\s+yourself\s+([\d.]+)\s+points'),
            'weapon': re.compile(r'You\s+equipped\s+(.+)'),
            'global': re.compile(r'(\w*)\s+killed\s+a\s+creature\s+\((.+?)\)\s+with\s+a\s+value\s+of\s+(\d+)\s+PED!?'),
            'global_team': re.compile(r'Team\s+"([^"]+)"\s+killed\s+a\s+creature\s+\((.+?)\)\s+with\s+a\s+value\s+of\s+(\d+)\s+PED!?'),
            'global_craft': re.compile(r'(\w+)\s+constructed\s+an\s+item\s+\((.+?)\)\s+worth\s+(\d+)\s+PED!'),
            'global_craft_team': re.compile(r'Team\s+"([^"]+)"\s+constructed\s+an\s+item\s+\((.+?)\)\s+worth\s+(\d+)\s+PED!'),
            'global_mine': re.compile(r'(\w+)\s+found\s+a\s+deposit\s+\((.+?)\)\s+with\s+a\s+value\s+of\s+(\d+)\s+PED!'),
            'global_mine_team': re.compile(r'Team\s+"([^"]+)"\s+found\s+a\s+deposit\s+\((.+?)\)\s+with\s+a\s+value\s+of\s+(\d+)\s+PED!'),
            'global_hof': re.compile(r'A\s+record\s+has\s+been\s+added\s+to\s+the\s+Hall\s+of\s+Fame!'),
            'global_spawn': re.compile(r'\[\]\s+(.+?)\s+has\s+been\s+challenged!'),
            'global_spawn_team': re.compile(r'Team\s+"([^"]+)"\s+has\s+been\s+challenged!'),
            'hof': re.compile(r'A\s+record\s+has\s+been\s+added\s+to\s+the\s+Hall\s+of\s+Fame!'),
            'craft_success': re.compile(r'You\s+successfully\s+crafted\s+(.+)'),
            'craft_fail': re.compile(r'You\s+failed\s+to\s+craft\s+(.+)'),
            'skill': re.compile(r'You\s+(?:have\s+)?gained\s+([\d.]+)\s+experience\s+in\s+your\s+(.+?)\s+skill'),
        }

        self.current_session_id = None
        self.current_activity = ActivityType.HUNTING

    def _poll_timer_timeout(self):
        """Called by QTimer - checks for file changes (synchronous)"""
        if not self._polling or not self.monitoring_file_path:
            return

        try:
            file_path = Path(self.monitoring_file_path)
            if not file_path.exists():
                return

            current_size = file_path.stat().st_size

            # Only process if size has actually increased
            if current_size > self.last_position:
                logger.info(f"[CHAT_READER] File modification detected (size: {current_size}, last_pos: {self.last_position})")
                self.process_file_changes(str(file_path))

        except Exception as e:
            logger.debug(f"[CHAT_READER] Error in poll timer: {e}")

    def process_file_changes(self, file_path: str):
        """Process new lines in chat log file (synchronous)"""
        logger.info(f"[CHAT_READER] >>> process_file_changes START <<<")
        logger.info(f"[CHAT_READER] File: {file_path}")
        logger.info(f"[CHAT_READER] Last position: {self.last_position}")
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, 2)
                current_pos = f.tell()
                logger.info(f"[CHAT_READER] File size: {current_pos}")

                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()

                logger.info(f"[CHAT_READER] Found {len(new_lines)} new lines")

                for line in new_lines:
                    line = line.strip()
                    if line:
                        self.parse_line(line)
                    else:
                        logger.debug(f"[CHAT_READER] Skipping empty line")

        except Exception as e:
            logger.error(f"[CHAT_READER] Error processing file changes: {e}", exc_info=True)

    def parse_line(self, line: str):
        """Parse a single chat line for game events (synchronous)"""
        logger.debug(f"[CHAT_READER] parse_line: {line[:80]}...")
        event_data = None

        # Check for loot events
        loot_match = self.patterns['loot'].search(line)
        if loot_match:
            loot_info = loot_match.groups()
            # Exclude Universal Ammo (not actual loot, appears when converting shrapnel at 101%)
            if loot_info[0] == 'Universal Ammo':
                logger.info(f"[CHAT_READER] Skipping Universal Ammo (shrapnel conversion)")
                return None
            
            # Only process loot messages that are actually from you, not from chat channels
            # Personal loot messages either have no brackets or have your character name, not channel names
            before_received = line.split('You received')[0]
            if ']' in before_received:
                # Check if this is a chat channel (not empty brackets or your character name)
                # Look for patterns like [Channel], [Player Name], etc.
                import re
                # Match any non-empty content in brackets
                bracket_content = re.search(r'\[(.*?)\]', before_received)
                if bracket_content and bracket_content.group(1).strip():
                    # This is someone else's loot message in a chat channel
                    logger.info(f"[CHAT_READER] Skipping other player's loot message: {line[:80]}...")
                    return None
                # Empty brackets [] are ok to process (personal loot)
                
            logger.info(f"[CHAT_READER] Detected LOOT event: {loot_info}")
            event_data = {
                'event_type': EventType.LOOT.value,
                'activity_type': self.current_activity.value,
                'raw_message': line,
                'parsed_data': {
                    'item_name': loot_info[0],
                    'quantity': int(loot_info[1]),
                    'value': float(loot_info[2]),
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }

        # Check for damage taken events
        damage_taken_match = self.patterns['damage_taken'].search(line)
        if damage_taken_match and not event_data:
            damage = float(damage_taken_match.group(1))
            logger.info(f"[CHAT_READER] Detected DAMAGE_TAKEN event: {damage}")
            event_data = {
                'event_type': EventType.COMBAT.value,
                'activity_type': self.current_activity.value,
                'raw_message': line,
                'parsed_data': {
                    'damage_taken': damage,
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }

        # Check for miss events
        miss_match = self.patterns['miss'].search(line)
        if miss_match and not event_data:
            logger.info(f"[CHAT_READER] Detected MISS event")
            event_data = {
                'event_type': EventType.COMBAT.value,
                'activity_type': self.current_activity.value,
                'raw_message': line,
                'parsed_data': {
                    'damage': 0,
                    'miss': True,
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }

        # Check for dodge events
        dodge_match = self.patterns['dodge'].search(line)
        if dodge_match and not event_data:
            logger.info(f"[CHAT_READER] Detected DODGE event")
            event_data = {
                'event_type': EventType.COMBAT.value,
                'activity_type': self.current_activity.value,
                'raw_message': line,
                'parsed_data': {
                    'damage': 0,
                    'dodged': True,
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }

        # Check for evade events
        evade_match = self.patterns['evade'].search(line)
        if evade_match and not event_data:
            logger.info(f"[CHAT_READER] Detected EVADE event")
            event_data = {
                'event_type': EventType.COMBAT.value,
                'activity_type': self.current_activity.value,
                'raw_message': line,
                'parsed_data': {
                    'damage': 0,
                    'evaded': True,
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }

        # Check for critical hit events
        critical_match = self.patterns['critical'].search(line)
        if critical_match and not event_data:
            damage = float(critical_match.group(1))
            logger.info(f"[CHAT_READER] Detected CRITICAL event: {damage}")
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

        # Check for damage events
        damage_match = self.patterns['damage'].search(line)
        if damage_match and not event_data:
            damage = float(damage_match.group(1))
            logger.info(f"[CHAT_READER] Detected DAMAGE event: {damage}")
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

        # Check for skill gain events
        skill_match = self.patterns['skill'].search(line)
        if skill_match and not event_data:
            experience = float(skill_match.group(1))
            skill = skill_match.group(2)
            logger.info(f"[CHAT_READER] Detected SKILL event: {experience} in {skill}")
            event_data = {
                'event_type': EventType.SKILL_GAIN.value,
                'activity_type': self.current_activity.value,
                'raw_message': line,
                'parsed_data': {
                    'experience': experience,
                    'skill': skill,
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }

        # Check for global/HOF events
        global_match = self.patterns['global'].search(line)
        if global_match and not event_data:
            groups = global_match.groups()
            logger.info(f"[CHAT_READER] Detected GLOBAL event: {groups}")
            is_hof = 'Hall of Fame' in line or 'HOF' in line
            player = groups[0] if groups[0] else 'Unknown'
            creature = groups[1] if len(groups) > 1 else 'Unknown'
            value = float(groups[2]) if len(groups) > 2 else 0

            event_data = {
                'event_type': EventType.GLOBAL.value,
                'activity_type': self.current_activity.value,
                'raw_message': line,
                'parsed_data': {
                    'type': 'kill',
                    'player': player,
                    'creature': creature,
                    'value': value,
                    'hof': is_hof,
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }

        # Check for team global events
        global_team_match = self.patterns['global_team'].search(line)
        if global_team_match and not event_data:
            groups = global_team_match.groups()
            logger.info(f"[CHAT_READER] Detected TEAM GLOBAL event: {groups}")
            is_hof = 'Hall of Fame' in line or 'HOF' in line
            player = groups[0] if groups[0] else 'Unknown'
            creature = groups[1] if len(groups) > 1 else 'Unknown'
            value = float(groups[2]) if len(groups) > 2 else 0

            event_data = {
                'event_type': EventType.GLOBAL.value,
                'activity_type': self.current_activity.value,
                'raw_message': line,
                'parsed_data': {
                    'type': 'team_kill',
                    'player': player,
                    'creature': creature,
                    'value': value,
                    'hof': is_hof,
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }

        # Check for crafting global events
        craft_global_match = self.patterns['global_craft'].search(line)
        if craft_global_match and not event_data:
            groups = craft_global_match.groups()
            logger.info(f"[CHAT_READER] Detected CRAFTING GLOBAL event: {groups}")
            is_hof = 'Hall of Fame' in line or 'HOF' in line
            player = groups[0] if groups[0] else 'Unknown'
            item = groups[1] if len(groups) > 1 else 'Unknown'
            value = float(groups[2]) if len(groups) > 2 else 0

            event_data = {
                'event_type': EventType.GLOBAL.value,
                'activity_type': self.current_activity.value,
                'raw_message': line,
                'parsed_data': {
                    'type': 'crafting',
                    'player': player,
                    'item': item,
                    'value': value,
                    'hof': is_hof,
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }

        # Check for mining global events
        mine_global_match = self.patterns['global_mine'].search(line)
        if mine_global_match and not event_data:
            groups = mine_global_match.groups()
            logger.info(f"[CHAT_READER] Detected MINING GLOBAL event: {groups}")
            is_hof = 'Hall of Fame' in line or 'HOF' in line
            player = groups[0] if groups[0] else 'Unknown'
            deposit = groups[1] if len(groups) > 1 else 'Unknown'
            value = float(groups[2]) if len(groups) > 2 else 0

            event_data = {
                'event_type': EventType.GLOBAL.value,
                'activity_type': self.current_activity.value,
                'raw_message': line,
                'parsed_data': {
                    'type': 'mining',
                    'player': player,
                    'deposit': deposit,
                    'value': value,
                    'hof': is_hof,
                    'timestamp': datetime.now().isoformat()
                },
                'session_id': self.current_session_id
            }

        if event_data:
            logger.info(f"[CHAT_READER] >>> EVENT DETECTED: {event_data['event_type']} <<<")
            logger.info(f"[CHAT_READER] Event data: {event_data.get('parsed_data', {})}")
            logger.info(f"[CHAT_READER] Session ID: {self.current_session_id}")

            # Save to database (synchronous)
            try:
                logger.info(f"[CHAT_READER] About to save to DB...")
                self.db_manager.add_event_sync(event_data)
                logger.info(f"[CHAT_READER] Event saved to DB")
            except Exception as e:
                logger.error(f"[CHAT_READER] Error saving event to DB: {e}", exc_info=True)

            # Emit signal
            logger.info(f"[CHAT_READER] About to emit new_event signal...")
            self.new_event.emit(event_data)
            logger.info(f"[CHAT_READER] >>> SIGNAL EMITTED: {event_data['event_type']} <<<")

        return event_data

    def start_monitoring(self, log_file_path: str):
        """Start monitoring chat log file (synchronous, for use with Qt event loop)"""
        logger.info(f"[CHAT_READER] ===========================================")
        logger.info(f"[CHAT_READER] start_monitoring called with: {log_file_path}")

        try:
            # Stop existing monitoring
            self.stop_monitoring()

            log_path = Path(log_file_path)

            logger.info(f"[CHAT_READER] Checking if log file exists: {log_path}")
            if not log_path.exists():
                logger.error(f"[CHAT_READER] Chat log file not found: {log_file_path}")
                return False

            self.monitoring_file_path = str(log_path)

            # Set last_position to end of file to read only NEW loot going forward
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, 2)  # Seek to end
                self.last_position = f.tell()
            logger.info(f"[CHAT_READER] Set last_position to end of file: {self.last_position}")

            # Start polling with QTimer (integrates with Qt event loop)
            self._polling = True
            self._poll_timer = QTimer()
            self._poll_timer.timeout.connect(self._poll_timer_timeout)
            self._poll_timer.start(500)  # Poll every 500ms

            logger.info(f"[CHAT_READER] Polling started for: {log_path}")

            # Create initial session (synchronous)
            self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.db_manager.create_session_sync(self.current_session_id, self.current_activity.value)

            logger.info(f"[CHAT_READER] Monitoring started successfully: {log_file_path}")
            logger.info(f"[CHAT_READER] Session ID: {self.current_session_id}")
            logger.info(f"[CHAT_READER] Current activity: {self.current_activity.value}")
            logger.info(f"[CHAT_READER] ===========================================")
            return True

        except Exception as e:
            logger.error(f"[CHAT_READER] Error starting chat monitoring: {e}", exc_info=True)
            return False

    def stop_monitoring(self):
        """Stop monitoring chat log file"""
        logger.info(f"[CHAT_READER] Stopping monitoring...")
        self._polling = False

        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer = None

        logger.info(f"[CHAT_READER] Polling stopped")
