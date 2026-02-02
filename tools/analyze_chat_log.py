#!/usr/bin/env python3
"""
Chat.log Analysis Tool
Reads the real chat.log for 5 minutes and compares each line against regex patterns
"""

import asyncio
import sys
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import re

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from src.services.chat_reader import ChatReader
from src.core.multi_database_manager import MultiDatabaseManager
from src.services.config_manager import ConfigManager
from src.models.models import ActivityType, EventType


class ChatLogAnalyzer:
    def __init__(self):
        self.db_manager = None
        self.config_manager = None
        self.chat_reader = None
        self.lines_captured = []
        self.lines_matched = []
        self.lines_missed = []
        self.start_time = None

        # Pattern statistics
        self.pattern_stats = defaultdict(int)

    async def initialize(self):
        """Initialize services"""
        self.db_manager = MultiDatabaseManager()
        await self.db_manager.initialize_all()

        self.config_manager = ConfigManager()
        await self.config_manager.initialize()

        self.chat_reader = ChatReader(self.db_manager, self.config_manager)

        # Create session
        self.session_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        await self.db_manager.create_session(
            self.session_id, ActivityType.HUNTING.value
        )
        self.chat_reader.current_session_id = self.session_id
        self.chat_reader.current_activity = ActivityType.HUNTING

        logger.info("Services initialized")

    async def capture_lines(self, duration_seconds=300):
        """Capture all lines from chat.log for specified duration"""
        # Get chat.log path
        default_path = str(Path.home() / "Documents" / "Entropia Universe" / "chat.log")

        if not Path(default_path).exists():
            logger.error(f"chat.log not found at: {default_path}")
            logger.info("Please set the correct path in the Config tab first")
            return False

        log_path = default_path

        # Read existing content first
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, 2)  # Go to end
            initial_position = f.tell()

        logger.info(
            f"Starting 5-minute analysis at {datetime.now().strftime('%H:%M:%S')}"
        )
        logger.info(f"Monitoring: {log_path}")
        logger.info(f"Initial file size: {initial_position} bytes")

        self.start_time = datetime.now()
        end_time = self.start_time + timedelta(seconds=duration_seconds)

        # Start monitoring
        self.chat_reader.last_position = initial_position
        await self.chat_reader.start_monitoring(log_path)

        # Capture loop
        logger.info(f"Reading until {end_time.strftime('%H:%M:%S')}...")

        while datetime.now() < end_time:
            # Read new lines
            try:
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(self.chat_reader.last_position)
                    new_lines = f.readlines()
                    self.chat_reader.last_position = f.tell()

                    for line in new_lines:
                        line = line.strip()
                        if line:
                            self.lines_captured.append(
                                {"timestamp": datetime.now(), "line": line}
                            )

                await asyncio.sleep(0.5)  # Poll every 500ms

            except Exception as e:
                logger.error(f"Error reading file: {e}")
                await asyncio.sleep(1)

        # Stop monitoring
        await self.chat_reader.stop_monitoring()

        elapsed = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"\nCapture complete! Elapsed: {elapsed:.1f} seconds")
        logger.info(f"Lines captured: {len(self.lines_captured)}")

        return True

    def analyze_lines(self):
        """Analyze captured lines against patterns"""
        logger.info("\n" + "=" * 60)
        logger.info("ANALYZING CAPTURED LINES")
        logger.info("=" * 60)

        # Get patterns from chat_reader
        patterns = self.chat_reader.patterns

        # Category patterns
        category_patterns = {
            "SYSTEM": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[System\]",
            "GLOBALS": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[Globals\]",
            "TRADE": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[#\w+\]",
            "ROOKIE": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[Rookie\]",
            "OTHER": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \[",
        }

        category_counts = defaultdict(int)

        for item in self.lines_captured:
            line = item["line"]
            matched = False
            matched_pattern = None

            # Check each pattern
            for pattern_name, pattern_regex in patterns.items():
                if pattern_regex.search(line):
                    matched = True
                    matched_pattern = pattern_name
                    self.pattern_stats[pattern_name] += 1
                    break

            # Also categorize by message type
            for cat_name, cat_regex in category_patterns.items():
                if re.search(cat_regex, line):
                    category_counts[cat_name] += 1
                    break

            if matched:
                self.lines_matched.append({"line": line, "pattern": matched_pattern})
            else:
                self.lines_missed.append({"line": line, "reason": "No pattern matched"})

        return category_counts

    def print_report(self, category_counts):
        """Print detailed analysis report"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        print("\n" + "=" * 70)
        print(" CHAT.LOG ANALYSIS REPORT")
        print("=" * 70)
        print(f"\nDuration: {elapsed:.1f} seconds (5 minutes)")
        print(f"Total lines captured: {len(self.lines_captured)}")
        print(
            f"Lines matched: {len(self.lines_matched)} ({100 * len(self.lines_matched) / max(1, len(self.lines_captured)):.1f}%)"
        )
        print(
            f"Lines missed: {len(self.lines_missed)} ({100 * len(self.lines_missed) / max(1, len(self.lines_captured)):.1f}%)"
        )

        print("\n" + "-" * 70)
        print(" MESSAGE CATEGORIES")
        print("-" * 70)
        for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            pct = 100 * count / max(1, len(self.lines_captured))
            print(f"  {cat:15} {count:6} lines ({pct:5.1f}%)")

        print("\n" + "-" * 70)
        print(" PATTERN MATCH STATISTICS")
        print("-" * 70)
        total_matches = sum(self.pattern_stats.values())
        for pattern, count in sorted(self.pattern_stats.items(), key=lambda x: -x[1]):
            pct = 100 * count / max(1, total_matches)
            print(f"  {pattern:20} {count:6} matches ({pct:5.1f}%)")

        print("\n" + "-" * 70)
        print(" MISSED LINES (first 50)")
        print("-" * 70)

        # Show unique missed lines (grouped by similarity)
        missed_lines = {}
        for item in self.lines_missed:
            line = item["line"]
            # Create a simplified key for grouping
            if "[Globals]" in line:
                key = line.split("[Globals]")[1].strip()[:60]
            elif "[System]" in line:
                key = line.split("[System]")[1].strip()[:60]
            elif "[#" in line:
                key = line.split("]", 2)[-1].strip()[:60] if "]" in line else line[:60]
            else:
                key = line[:60]

            if key not in missed_lines:
                missed_lines[key] = []
            missed_lines[key].append(line)

        for i, (key, examples) in enumerate(list(missed_lines.items())[:50]):
            count = len(examples)
            prefix = f"[{count}x]" if count > 1 else "      "
            print(f"  {prefix} {key}")

        print("\n" + "-" * 70)
        print(" MISSED LINE BREAKDOWN")
        print("-" * 70)

        # Categorize missed lines
        missed_categories = defaultdict(int)
        for item in self.lines_missed:
            line = item["line"]

            if "[#" in line:
                missed_categories["Trade channels"] += 1
            elif "[Rookie]" in line:
                missed_categories["Rookie chat"] += 1
            elif "[Globals]" in line:
                if "killed a creature" in line:
                    missed_categories["Global kills (no match)"] += 1
                elif "found a deposit" in line:
                    missed_categories["Global mining (no match)"] += 1
                elif "constructed an item" in line:
                    missed_categories["Global crafting (no match)"] += 1
                elif "A record has been added" in line:
                    missed_categories["Global HOF (no match)"] += 1
                else:
                    missed_categories["Other globals"] += 1
            elif "[System]" in line:
                if "You inflicted" in line:
                    missed_categories["Damage dealt (no match)"] += 1
                elif "Critical hit" in line:
                    missed_categories["Critical hits (no match)"] += 1
                elif "The attack missed" in line:
                    missed_categories["Misses (no match)"] += 1
                elif "You Evaded" in line:
                    missed_categories["Evades (no match)"] += 1
                elif "You took" in line:
                    missed_categories["Damage taken (no match)"] += 1
                elif "You received" in line:
                    missed_categories["Loot (no match)"] += 1
                elif "experience" in line:
                    missed_categories["Skill XP (no match)"] += 1
                elif "improved" in line:
                    missed_categories["Skill improved (no match)"] += 1
                else:
                    missed_categories["Other system messages"] += 1
            else:
                missed_categories["Other"] += 1

        for cat, count in sorted(missed_categories.items(), key=lambda x: -x[1]):
            pct = 100 * count / max(1, len(self.lines_missed))
            print(f"  {cat:35} {count:6} ({pct:5.1f}%)")

        print("\n" + "=" * 70)
        print(" RECOMMENDATIONS")
        print("=" * 70)

        if missed_categories["Trade channels"] > 0:
            print(
                f"\n  • Add patterns for trade channel messages ({missed_categories['Trade channels']} missed)"
            )

        if missed_categories["Rookie chat"] > 0:
            print(
                f"\n  • Add patterns for rookie chat ({missed_categories['Rookie chat']} missed)"
            )

        if missed_categories["Damage dealt (no match)"] > 0:
            print(
                f"\n  • Check damage pattern - {missed_categories['Damage dealt (no match)']} lines not matched"
            )

        if missed_categories["Loot (no match)"] > 0:
            print(
                f"\n  • Check loot pattern - {missed_categories['Loot (no match)']} lines not matched"
            )

        print("\n")

    async def save_results(self):
        """Save results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"chat_analysis_{timestamp}.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Chat.log Analysis Results\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Duration: 5 minutes\n\n")

            f.write(f"Total lines captured: {len(self.lines_captured)}\n")
            f.write(f"Lines matched: {len(self.lines_matched)}\n")
            f.write(f"Lines missed: {len(self.lines_missed)}\n\n")

            f.write("MISSED LINES:\n")
            f.write("-" * 70 + "\n")
            for item in self.lines_missed[:100]:  # Save first 100
                f.write(f"{item['line']}\n")

        logger.info(f"Results saved to: {output_file}")

    async def cleanup(self):
        """Cleanup resources"""
        if self.db_manager:
            await self.db_manager.close()


async def main():
    print("\n" + "=" * 70)
    print(" CHAT.LOG ANALYSIS TOOL")
    print(" Monitoring for 5 minutes to capture and analyze all chat.log lines")
    print("=" * 70)

    analyzer = ChatLogAnalyzer()

    try:
        await analyzer.initialize()

        # Run 5-minute capture
        success = await analyzer.capture_lines(duration_seconds=300)

        if success:
            # Analyze results
            category_counts = analyzer.analyze_lines()
            analyzer.print_report(category_counts)

            # Save to file
            await analyzer.save_results()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        await analyzer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
