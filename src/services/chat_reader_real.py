"""Real-time chat log reader with patterns from LootNanny"""

import re
import threading
import time
from collections import namedtuple
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

LogLine = namedtuple("LogLine", ["time", "channel", "speaker", "msg"])

LOG_LINE_REGEX = re.compile(r"([\d\-]+ [\d:]+) \[(\w+)\] \[(.*)\] (.*)")

CHAT_PATTERNS = {
    "damage_critical": re.compile(  # noqa: E501
        r"Critical hit - Additional damage! You inflicted (\d+\.\d+) points of damage"
    ),
    "damage_normal": re.compile(r"You inflicted (\d+\.\d+) points of damage"),
    "heal": re.compile(r"You healed yourself (\d+\.\d+) points"),
    "deflect": re.compile(r"Damage deflected!"),
    "evade": re.compile(r"You Evaded the attack"),
    "miss_you": re.compile(r"You missed"),
    "miss_target": re.compile(r"The target (Dodged|Evaded|Jammed) your attack"),
    "damage_taken": re.compile(r"You took (\d+\.\d+) points of damage"),
    "skill_exp": re.compile(r"You have gained (\d+\.\d+) experience in your ([a-zA-Z ]+) skill"),
    "skill_points": re.compile(r"You have gained (\d+\.\d+) ([a-zA-Z ]+)"),
    "skill_improved": re.compile(r"Your ([a-zA-Z ]+) has improved by (\d+\.\d+)"),
    "enhancer_break": re.compile(r"Your enhancer ([a-zA-Z0-9 ]+) on your .* broke."),
    "loot_item": re.compile(r"You received (.*) x \((\d+)\) Value: (\d+\.\d+) PED"),
}

GLOBAL_PATTERNS = {
    "hof_creature": re.compile(  # noqa: E501
        r"([\w\s\'\(\)]+) killed a creature \(([\w\s\(\),]+)\) with a value of "
        r"(\d+) PED! A record has been added to the Hall of Fame!"
    ),
    "global_creature": re.compile(  # noqa: E501
        r"([\w\s\'\(\)]+) killed a creature \(([\w\s\(\),]+)\) with a value of (\d+) PED!"
    ),
    "hof_crafting": re.compile(  # noqa: E501
        r"([\w\s\'\(\)]+) constructed an item \(([\w\s\(\),]+)\) worth (\d+) PED! "
        r"A record has been added to the Hall of Fame!"
    ),
    "global_crafting": re.compile(  # noqa: E501
        r"([\w\s\'\(\)]+) constructed an item \(([\w\s\(\),]+)\) worth (\d+) PED!"
    ),
    "hof_mining": re.compile(  # noqa: E501
        r"([\w\s\'\(\)]+) found a deposit \(([\w\s\(\)]+)\) with a value of (\d+) PED! "
        r"A record has been added to the Hall of Fame!"
    ),
    "global_mining": re.compile(  # noqa: E501
        r"([\w\s\'\(\)]+) found a deposit \(([\w\s\(\)]+)\) with a value of (\d+) PED!"
    ),
    "global_location": re.compile(  # noqa: E501
        r"([\w\s\'\(\)]+) killed a creature \(([\w\s\(\),]+)\) with a value of (\d+) PED at ([\s\w\W]+)!"
    ),
}


class ChatEvent:
    """Base class for chat events"""

    def __init__(self, timestamp: datetime, event_type: str, raw_message: str):
        self.timestamp = timestamp
        self.event_type = event_type
        self.raw_message = raw_message


class CombatEvent(ChatEvent):
    """Combat-related event"""

    def __init__(
        self,
        timestamp: datetime,
        raw_message: str,
        damage: float = 0.0,
        critical: bool = False,
        miss: bool = False,
    ):
        super().__init__(timestamp, "combat", raw_message)
        self.damage = damage
        self.critical = critical
        self.miss = miss


class LootEvent(ChatEvent):
    """Loot event"""

    def __init__(self, timestamp: datetime, raw_message: str, items: list[tuple]):
        super().__init__(timestamp, "loot", raw_message)
        self.items = items  # List of (name, quantity, value)
        self.total_value = sum(float(value) for _, _, value in items)


class SkillEvent(ChatEvent):
    """Skill gain event"""

    def __init__(self, timestamp: datetime, raw_message: str, skill_name: str, amount: float):
        super().__init__(timestamp, "skill", raw_message)
        self.skill_name = skill_name
        self.amount = amount


class GlobalEvent(ChatEvent):
    """Global/HOF event"""

    def __init__(
        self,
        timestamp: datetime,
        raw_message: str,
        player: str,
        target: str,
        value: int,
        hof: bool = False,
        location: str | None = None,
    ):
        super().__init__(timestamp, "global", raw_message)
        self.player = player
        self.target = target
        self.value = value
        self.hof = hof
        self.location = location


class ChatLogReader:
    """Real-time chat log reader with proper event parsing"""

    def __init__(self, log_file_path: str, event_callback: Callable[[ChatEvent], None]):
        self.log_file_path = Path(log_file_path)
        self.event_callback = event_callback
        self.is_running = False
        self.file_position = 0
        self.thread: threading.Thread | None = None

    def start_monitoring(self):
        """Start monitoring the chat log file"""
        if self.is_running:
            return False

        if not self.log_file_path.exists():
            print(f"Chat log file not found: {self.log_file_path}")
            return False

        # Start at end of file
        self.file_position = self.log_file_path.stat().st_size

        self.is_running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

        print(f"Started monitoring: {self.log_file_path}")
        return True

    def stop_monitoring(self):
        """Stop monitoring the chat log"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1)
        print("Stopped monitoring")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                self._check_file_changes()
                time.sleep(0.1)  # Check every 100ms
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(1)  # Wait longer on error

    def _check_file_changes(self):
        """Check for new lines in the log file"""
        try:
            current_size = self.log_file_path.stat().st_size
            if current_size <= self.file_position:
                return  # No new content

            with open(self.log_file_path, encoding="utf-8", errors="ignore") as f:
                f.seek(self.file_position)
                new_lines = f.readlines()
                self.file_position = f.tell()

                for line in new_lines:
                    line = line.strip()
                    if line:
                        self._process_line(line)

        except Exception as e:
            print(f"Error reading log file: {e}")

    def _process_line(self, line: str):
        """Process a single log line"""
        # Parse basic log structure
        log_line = self._parse_log_line(line)
        if not log_line:
            return

        # Process based on channel
        if log_line.channel == "System":
            self._process_system_message(log_line)
        elif log_line.channel == "Globals":
            self._process_global_message(log_line)

    def _parse_log_line(self, line: str) -> LogLine | None:
        """Parse raw log line into components"""
        matched = LOG_LINE_REGEX.match(line)
        if not matched:
            return None

        try:
            timestamp = datetime.strptime(matched.group(1), "%Y-%m-%d %H:%M:%S")
            return LogLine(timestamp, matched.group(2), matched.group(3), matched.group(4))
        except ValueError:
            return None

    def _process_system_message(self, log_line: LogLine):
        """Process system channel messages"""
        event = None

        # Check each pattern
        for pattern_name, pattern in CHAT_PATTERNS.items():
            match = pattern.search(log_line.msg)
            if match:
                event = self._create_event_from_match(
                    pattern_name, match, log_line.time, log_line.msg
                )
                break

        if event:
            self.event_callback(event)

    def _process_global_message(self, log_line: LogLine):
        """Process global channel messages"""
        event = None

        # Check global patterns
        for pattern_name, pattern in GLOBAL_PATTERNS.items():
            match = pattern.search(log_line.msg)
            if match:
                event = self._create_global_event_from_match(
                    pattern_name, match, log_line.time, log_line.msg
                )
                break

        if event:
            self.event_callback(event)

    def _create_event_from_match(
        self, pattern_name: str, match: re.Match, timestamp: datetime, raw_message: str
    ) -> ChatEvent | None:
        """Create event object from pattern match"""
        groups = match.groups()

        if pattern_name.startswith("damage"):
            damage = float(groups[0])
            critical = "critical" in pattern_name
            return CombatEvent(timestamp, raw_message, damage=damage, critical=critical)

        elif pattern_name == "heal":
            return None  # Skip heals for now

        elif pattern_name in ["miss_you", "miss_target", "deflect", "evade"]:
            return CombatEvent(timestamp, raw_message, miss=True)

        elif pattern_name.startswith("skill"):
            if pattern_name == "skill_improved":
                skill_name, amount = groups[0], float(groups[1])
            elif pattern_name == "skill_points":
                amount, skill_name = float(groups[0]), groups[1]
            else:  # skill_exp
                amount, skill_name = float(groups[0]), groups[1]
            return SkillEvent(timestamp, raw_message, skill_name, amount)

        elif pattern_name == "enhancer_break":
            return None  # Skip enhancer breaks for now

        elif pattern_name == "loot_item":
            item_name, quantity, value = groups
            items = [(item_name, int(quantity), float(value))]
            return LootEvent(timestamp, raw_message, items)

        return None

    def _create_global_event_from_match(
        self, pattern_name: str, match: re.Match, timestamp: datetime, raw_message: str
    ) -> GlobalEvent | None:
        """Create global event from pattern match"""
        groups = match.groups()
        player = groups[0]
        target = groups[1]
        value = int(groups[2])

        hof = "hof" in pattern_name
        location: str | None = groups[3] if len(groups) > 3 else None

        return GlobalEvent(timestamp, raw_message, player, target, value, hof, location)
