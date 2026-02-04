"""Chat log reader for real-time game event parsing
Uses QTimer for Qt event loop integration
"""

import logging
import re
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from src.models.models import ActivityType, EventType

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
        self.is_paused = False

        # Thread-safe queue for file modification events
        self._file_change_queue = []

        # Regex patterns for parsing - updated for Entropia Universe format
        self.patterns = {
            "loot": re.compile(r"You\s+received\s+(.+?)\s+x\s*\((\d+)\)\s+Value:\s*([\d.]+)\s+PED"),
            "damage": re.compile(r"You\s+inflicted\s+([\d.]+)\s+points\s+of\s+damage"),
            "damage_taken": re.compile(r"You\s+took\s+([\d.]+)\s+points\s+of\s+damage"),
            "critical": re.compile(  # noqa: E501
                r"Critical\s+hit\s+-\s+Additional\s+damage!\s+You\s+inflicted\s+([\d.]+)\s+points\s+of\s+damage"
            ),
            "critical_armor": re.compile(  # noqa: E501
                r"Critical\s+hit\s+-\s+Armor\s+penetration!\s+You\s+took\s+([\d.]+)\s+points\s+of\s+damage"
            ),
            "miss": re.compile(r"The attack missed you"),
            "dodge": re.compile(r".*Dodged.*your\s+attack"),
            "evade": re.compile(r"You\s+Evaded\s+the\s+attack"),
            "heal": re.compile(r"You\s+healed\s+yourself\s+([\d.]+)\s+points"),
            "weapon": re.compile(r"You\s+equipped\s+(.+)"),
            "global": re.compile(
                r"(\w*)\s+killed\s+a\s+creature\s+\((.+?)\)\s+with\s+a\s+value\s+of\s+(\d+)\s+PED!?"
            ),
            "global_team": re.compile(  # noqa: E501
                r'Team\s+"([^"]+)"\s+killed\s+a\s+creature\s+\((.+?)\)\s+with\s+a\s+value\s+of\s+(\d+)\s+PED!?'
            ),
            "global_craft": re.compile(
                r"(\w+)\s+constructed\s+an\s+item\s+\((.+?)\)\s+worth\s+(\d+)\s+PED!"
            ),
            "global_craft_team": re.compile(  # noqa: E501
                r'Team\s+"([^"]+)"\s+constructed\s+an\s+item\s+\((.+?)\)\s+worth\s+(\d+)\s+PED!'
            ),
            "global_mine": re.compile(
                r"(\w+)\s+found\s+a\s+deposit\s+\((.+?)\)\s+with\s+a\s+value\s+of\s+(\d+)\s+PED!"
            ),
            "global_mine_team": re.compile(  # noqa: E501
                r'Team\s+"([^"]+)"\s+found\s+a\s+deposit\s+\((.+?)\)\s+with\s+a\s+value\s+of\s+(\d+)\s+PED!'
            ),
            "global_hof": re.compile(
                r"A\s+record\s+has\s+been\s+added\s+to\s+the\s+Hall\s+of\s+Fame!"
            ),
            "global_spawn": re.compile(r"\[\]\s+(.+?)\s+has\s+been\s+challenged!"),
            "global_spawn_team": re.compile(r'Team\s+"([^"]+)"\s+has\s+been\s+challenged!'),
            "hof": re.compile(r"A\s+record\s+has\s+been\s+added\s+to\s+the\s+Hall\s+of\s+Fame!"),
            "craft_success": re.compile(r"You\s+successfully\s+crafted\s+(.+)"),
            "craft_fail": re.compile(r"You\s+failed\s+to\s+craft\s+(.+)"),
            "skill": re.compile(  # noqa: E501
                r"You\s+(?:have\s+)?gained\s+([\d.]+)\s+experience\s+in\s+your\s+(.+?)\s+skill"
            ),
            "picked_up": re.compile(r"Picked up (.+?)(?: \((\d+)\))?$"),
            "trade": re.compile(r"\[#\]"),  # Trade channel messages start with [#]
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
                logger.info(
                    f"[CHAT_READER] File modification detected (size: {current_size}, last_pos: {self.last_position})"
                )
                self.process_file_changes(str(file_path))

        except Exception as e:
            logger.debug(f"[CHAT_READER] Error in poll timer: {e}")

    def process_file_changes(self, file_path: str):
        """Process new lines in chat log file (synchronous)"""
        logger.info("[CHAT_READER] >>> process_file_changes START <<<")
        logger.info(f"[CHAT_READER] File: {file_path}")
        logger.info(f"[CHAT_READER] Last position: {self.last_position}")
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
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
                        logger.debug("[CHAT_READER] Skipping empty line")

        except Exception as e:
            logger.error(f"[CHAT_READER] Error processing file changes: {e}", exc_info=True)

    def parse_line(self, line: str):
        """Parse a single chat line for game events (synchronous)"""
        logger.debug(f"[CHAT_READER] parse_line: {line[:80]}...")
        event_data = None

        # Check if logging is paused
        if self.is_paused:
            # Check if this is a trade message - trade messages should still be processed
            trade_match = self.patterns["trade"].search(line)
            if not trade_match:
                logger.debug(  # noqa: E501
                    f"[CHAT_READER] Skipping non-trade message due to pause: {line[:50]}..."
                )
                return None
            logger.debug(f"[CHAT_READER] Processing trade message during pause: {line[:50]}...")

        # Check for loot events
        loot_match = self.patterns["loot"].search(line)
        if loot_match:
            loot_info = loot_match.groups()
            logger.debug(f"[CHAT_READER] Loot match found: {loot_info}")
            logger.debug(f"[CHAT_READER] Full line: {line}")

            # Exclude Universal Ammo (not actual loot, appears when converting shrapnel at 101%)
            if loot_info[0] == "Universal Ammo":
                logger.info("[CHAT_READER] Skipping Universal Ammo (shrapnel conversion)")
                return None

            # Only process loot messages that are actually from you, not from chat channels
            # Personal loot messages either have no character name bracket or have your
            # character name in the last bracket before "You received"
            before_received = line.split("You received")[0]
            logger.debug(f"[CHAT_READER] Text before 'You received': '{before_received}'")

            # Find the LAST bracket content before "You received" - this should be the character name
            import re

            last_bracket_match = None
            for match in re.finditer(r"\[(.*?)\]", before_received):
                last_bracket_match = match

            if last_bracket_match:
                bracket_content = last_bracket_match.group(1).strip()
                logger.debug(  # noqa: E501
                    f"[CHAT_READER] Last bracket content before 'You received': '{bracket_content}'"
                )

                # If the last bracket is not "[You]", it's someone else's loot
                if bracket_content and bracket_content != "You":
                    # This is someone else's loot message in a chat channel
                    logger.info(  # noqa: E501
                        f"[CHAT_READER] Skipping other player's loot message: {line[:80]}..."
                    )
                    return None
                # "[You]" or empty bracket indicates this is personal loot
                logger.debug("[CHAT_READER] Processing personal loot")

            logger.info(f"[CHAT_READER] Detected LOOT event: {loot_info}")
            event_data = {
                "event_type": EventType.LOOT.value,
                "activity_type": self.current_activity.value,
                "raw_message": line,
                "parsed_data": {
                    "item_name": loot_info[0],
                    "quantity": int(loot_info[1]),
                    "value": float(loot_info[2]),
                    "timestamp": datetime.now().isoformat(),
                },
                "session_id": self.current_session_id,
            }

        # Check for damage taken events
        damage_taken_match = self.patterns["damage_taken"].search(line)
        if damage_taken_match and not event_data:
            damage = float(damage_taken_match.group(1))
            logger.info(f"[CHAT_READER] Detected DAMAGE_TAKEN event: {damage}")
            event_data = {
                "event_type": EventType.COMBAT.value,
                "activity_type": self.current_activity.value,
                "raw_message": line,
                "parsed_data": {"damage_taken": damage, "timestamp": datetime.now().isoformat()},
                "session_id": self.current_session_id,
            }

        # Check for miss events
        miss_match = self.patterns["miss"].search(line)
        if miss_match and not event_data:
            logger.info("[CHAT_READER] Detected MISS event")
            event_data = {
                "event_type": EventType.COMBAT.value,
                "activity_type": self.current_activity.value,
                "raw_message": line,
                "parsed_data": {"damage": 0, "miss": True, "timestamp": datetime.now().isoformat()},
                "session_id": self.current_session_id,
            }

        # Check for dodge events
        dodge_match = self.patterns["dodge"].search(line)
        if dodge_match and not event_data:
            logger.info("[CHAT_READER] Detected DODGE event")
            event_data = {
                "event_type": EventType.COMBAT.value,
                "activity_type": self.current_activity.value,
                "raw_message": line,
                "parsed_data": {
                    "damage": 0,
                    "dodged": True,
                    "timestamp": datetime.now().isoformat(),
                },
                "session_id": self.current_session_id,
            }

        # Check for evade events
        evade_match = self.patterns["evade"].search(line)
        if evade_match and not event_data:
            logger.info("[CHAT_READER] Detected EVADE event")
            event_data = {
                "event_type": EventType.COMBAT.value,
                "activity_type": self.current_activity.value,
                "raw_message": line,
                "parsed_data": {
                    "damage": 0,
                    "evaded": True,
                    "timestamp": datetime.now().isoformat(),
                },
                "session_id": self.current_session_id,
            }

        # Check for critical hit events
        critical_match = self.patterns["critical"].search(line)
        if critical_match and not event_data:
            damage = float(critical_match.group(1))
            logger.info(f"[CHAT_READER] Detected CRITICAL event: {damage}")
            event_data = {
                "event_type": EventType.COMBAT.value,
                "activity_type": self.current_activity.value,
                "raw_message": line,
                "parsed_data": {
                    "damage": damage,
                    "critical": True,
                    "timestamp": datetime.now().isoformat(),
                },
                "session_id": self.current_session_id,
            }

        # Check for damage events
        damage_match = self.patterns["damage"].search(line)
        if damage_match and not event_data:
            damage = float(damage_match.group(1))
            logger.info(f"[CHAT_READER] Detected DAMAGE event: {damage}")
            event_data = {
                "event_type": EventType.COMBAT.value,
                "activity_type": self.current_activity.value,
                "raw_message": line,
                "parsed_data": {
                    "damage": damage,
                    "critical": False,
                    "timestamp": datetime.now().isoformat(),
                },
                "session_id": self.current_session_id,
            }

        # Check for skill gain events
        skill_match = self.patterns["skill"].search(line)
        if skill_match and not event_data:
            experience = float(skill_match.group(1))
            skill = skill_match.group(2)
            logger.info(f"[CHAT_READER] Detected SKILL event: {experience} in {skill}")
            event_data = {
                "event_type": EventType.SKILL_GAIN.value,
                "activity_type": self.current_activity.value,
                "raw_message": line,
                "parsed_data": {
                    "experience": experience,
                    "skill": skill,
                    "timestamp": datetime.now().isoformat(),
                },
                "session_id": self.current_session_id,
            }

        # Check for global/HOF events
        global_match = self.patterns["global"].search(line)
        if global_match and not event_data:
            groups = global_match.groups()
            logger.info(f"[CHAT_READER] Detected GLOBAL event: {groups}")
            is_hof = "Hall of Fame" in line or "HOF" in line
            player = groups[0] if groups[0] else "Unknown"
            creature = groups[1] if len(groups) > 1 else "Unknown"
            value = float(groups[2]) if len(groups) > 2 else 0

            event_data = {
                "event_type": EventType.GLOBAL.value,
                "activity_type": self.current_activity.value,
                "raw_message": line,
                "parsed_data": {
                    "type": "kill",
                    "player": player,
                    "creature": creature,
                    "value": value,
                    "hof": is_hof,
                    "timestamp": datetime.now().isoformat(),
                },
                "session_id": self.current_session_id,
            }

        # Check for team global events
        global_team_match = self.patterns["global_team"].search(line)
        if global_team_match and not event_data:
            groups = global_team_match.groups()
            logger.info(f"[CHAT_READER] Detected TEAM GLOBAL event: {groups}")
            is_hof = "Hall of Fame" in line or "HOF" in line
            player = groups[0] if groups[0] else "Unknown"
            creature = groups[1] if len(groups) > 1 else "Unknown"
            value = float(groups[2]) if len(groups) > 2 else 0

            event_data = {
                "event_type": EventType.GLOBAL.value,
                "activity_type": self.current_activity.value,
                "raw_message": line,
                "parsed_data": {
                    "type": "team_kill",
                    "player": player,
                    "creature": creature,
                    "value": value,
                    "hof": is_hof,
                    "timestamp": datetime.now().isoformat(),
                },
                "session_id": self.current_session_id,
            }

        # Check for crafting global events
        craft_global_match = self.patterns["global_craft"].search(line)
        if craft_global_match and not event_data:
            groups = craft_global_match.groups()
            logger.info(f"[CHAT_READER] Detected CRAFTING GLOBAL event: {groups}")
            is_hof = "Hall of Fame" in line or "HOF" in line
            player = groups[0] if groups[0] else "Unknown"
            item = groups[1] if len(groups) > 1 else "Unknown"
            value = float(groups[2]) if len(groups) > 2 else 0

            event_data = {
                "event_type": EventType.GLOBAL.value,
                "activity_type": self.current_activity.value,
                "raw_message": line,
                "parsed_data": {
                    "type": "crafting",
                    "player": player,
                    "item": item,
                    "value": value,
                    "hof": is_hof,
                    "timestamp": datetime.now().isoformat(),
                },
                "session_id": self.current_session_id,
            }

        # Check for mining global events
        mine_global_match = self.patterns["global_mine"].search(line)
        if mine_global_match and not event_data:
            groups = mine_global_match.groups()
            logger.info(f"[CHAT_READER] Detected MINING GLOBAL event: {groups}")
            is_hof = "Hall of Fame" in line or "HOF" in line
            player = groups[0] if groups[0] else "Unknown"
            deposit = groups[1] if len(groups) > 1 else "Unknown"
            value = float(groups[2]) if len(groups) > 2 else 0

            event_data = {
                "event_type": EventType.GLOBAL.value,
                "activity_type": self.current_activity.value,
                "raw_message": line,
                "parsed_data": {
                    "type": "mining",
                    "player": player,
                    "deposit": deposit,
                    "value": value,
                    "hof": is_hof,
                    "timestamp": datetime.now().isoformat(),
                },
                "session_id": self.current_session_id,
            }

        # Check for picked up items
        picked_up_match = self.patterns["picked_up"].search(line)
        if picked_up_match and not event_data:
            item_name = picked_up_match.group(1).strip()
            quantity = int(picked_up_match.group(2)) if picked_up_match.group(2) else 1

            # Only calculate value for crude oil, skip other items since they should have
            # been processed by the loot message with actual values
            if item_name == "Crude Oil":
                # Crude oil is worth 1 PEC (0.01 PED) per unit
                value_ped = quantity * 0.01
                logger.info(f"[CHAT_READER] Detected PICKED_UP event: {item_name} x{quantity}")
                event_data = {
                    "event_type": EventType.LOOT.value,
                    "activity_type": self.current_activity.value,
                    "raw_message": line,
                    "parsed_data": {
                        "item_name": item_name,
                        "quantity": quantity,
                        "value": value_ped,
                        "timestamp": datetime.now().isoformat(),
                    },
                    "session_id": self.current_session_id,
                }
            else:
                # Skip picked up processing for non-crude oil items since they should
                # have been processed by the corresponding loot message with actual values
                logger.info(  # noqa: E501
                    f"[CHAT_READER] Skipping PICKED_UP event for {item_name} (should be processed by loot message)"
                )
                return None

        # Check for trade channel messages
        trade_match = self.patterns["trade"].search(line)
        if trade_match and not event_data:
            logger.info("[CHAT_READER] Detected TRADE event")
            event_data = {
                "event_type": EventType.TRADE.value,
                "activity_type": ActivityType.TRADING.value,
                "raw_message": line,
                "parsed_data": {"message": line, "timestamp": datetime.now().isoformat()},
                "session_id": self.current_session_id,
            }

        if event_data:
            logger.info(f"[CHAT_READER] >>> EVENT DETECTED: {event_data['event_type']} <<<")
            logger.info(f"[CHAT_READER] Event data: {event_data.get('parsed_data', {})}")
            logger.info(f"[CHAT_READER] Session ID: {self.current_session_id}")

            # Save to database (synchronous)
            try:
                logger.info("[CHAT_READER] About to save to DB...")
                self.db_manager.add_event_sync(event_data)
                logger.info("[CHAT_READER] Event saved to DB")
            except Exception as e:
                logger.error(f"[CHAT_READER] Error saving event to DB: {e}", exc_info=True)

            # Emit signal
            logger.info("[CHAT_READER] About to emit new_event signal...")
            self.new_event.emit(event_data)
            logger.info(f"[CHAT_READER] >>> SIGNAL EMITTED: {event_data['event_type']} <<<")

        return event_data

    def start_monitoring(self, log_file_path: str):
        """Start monitoring chat log file (synchronous, for use with Qt event loop)"""
        logger.info("[CHAT_READER] ===========================================")
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
            with open(log_path, encoding="utf-8", errors="ignore") as f:
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
            self.db_manager.create_session_sync(  # noqa: E501
                self.current_session_id, self.current_activity.value
            )

            logger.info(f"[CHAT_READER] Monitoring started successfully: {log_file_path}")
            logger.info(f"[CHAT_READER] Session ID: {self.current_session_id}")
            logger.info(f"[CHAT_READER] Current activity: {self.current_activity.value}")
            logger.info("[CHAT_READER] ===========================================")
            return True

        except Exception as e:
            logger.error(f"[CHAT_READER] Error starting chat monitoring: {e}", exc_info=True)
            return False

    def stop_monitoring(self):
        """Stop monitoring chat log file"""
        logger.info("[CHAT_READER] Stopping monitoring...")
        self._polling = False

        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer = None

        logger.info("[CHAT_READER] Polling stopped")
