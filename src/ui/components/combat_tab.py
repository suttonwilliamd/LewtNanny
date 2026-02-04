"""Combat tab implementation for LewtNanny
Tracks combat statistics including kills, damage, and efficiency
"""

import logging
from datetime import datetime
from typing import Any

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class CombatTabWidget(QWidget):
    """Combat statistics and tracking widget"""

    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.combat_data = []
        self.session_stats = {
            "total_kills": 0,
            "total_damage_dealt": 0.0,
            "total_damage_received": 0.0,
            "deaths": 0,
            "critical_hits": 0,
            "misses": 0,
            "hits": 0,
            "session_start": None,
        }

        self.setup_ui()
        logger.info("CombatTabWidget initialized")

    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        summary_section = self.create_combat_summary()
        layout.addWidget(summary_section)

        kills_section = self.create_kills_table()
        layout.addWidget(kills_section, 1)  # Give kills table stretch priority

        layout.addStretch()

    def create_combat_summary(self):
        """Create combat summary section"""
        self.session_info_label = QLabel("No active session")
        self.session_info_label.setFont(QFont("Arial", 9))
        self.session_info_label.setStyleSheet("color: #8B949E; padding: 4px;")

        section = QGroupBox("Combat Summary")
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #8B949E;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 28, 4, 4)  # Top margin accounts for title bar
        layout.setSpacing(4)

        layout.addWidget(self.session_info_label)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(4)

        summary_items = [
            ("Total Kills", "0"),
            ("Total Damage Dealt", "0.00"),
            ("Total Damage Received", "0.00"),
            ("Kills/Death Ratio", "0.0"),
            ("Critical Hits", "0"),
            ("Misses", "0"),
        ]

        self.combat_summary_labels = {}

        for i, (label, default) in enumerate(summary_items):
            row = i // 3
            col = i % 3

            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(2)

            lbl = QLabel(label)
            lbl.setFont(QFont("Arial", 9))
            lbl.setStyleSheet("color: #8B949E;")
            container_layout.addWidget(lbl)

            value_lbl = QLabel(default)
            value_lbl.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
            value_lbl.setStyleSheet("""
                color: #E6EDF3;
                background-color: #0D1117;
                border: 1px solid #30363D;
                border-radius: 4px;
                padding: 4px;
            """)
            container_layout.addWidget(value_lbl)

            self.combat_summary_labels[label] = value_lbl
            grid_layout.addWidget(container, row, col)

        layout.addLayout(grid_layout)
        section.setLayout(layout)
        return section

    def create_kills_table(self):
        """Create kills table section"""
        section = QGroupBox("Recent Kills")
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #8B949E;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 28, 4, 4)
        layout.setSpacing(4)

        self.kills_table = QTableWidget()
        self.kills_table.setColumnCount(5)
        self.kills_table.setHorizontalHeaderLabels(
            ["#", "Enemy", "Damage", "Time", "Type"]
        )
        self.kills_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.kills_table.setAlternatingRowColors(True)
        self.kills_table.setSortingEnabled(True)
        self.kills_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.kills_table.setAlternatingRowColors(True)
        self.kills_table.setSortingEnabled(True)

        header = self.kills_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.kills_table)

        section.setLayout(layout)
        return section

    def set_db_manager(self, db_manager):
        """Set database manager"""
        self.db_manager = db_manager
        self.load_combat_data()

    def load_combat_data(self):
        """Load combat data from database"""
        logger.debug("Loading combat data")
        self.update_combat_display()

    def update_combat_display(self):
        """Update combat statistics display"""
        for label, value_lbl in self.combat_summary_labels.items():
            if "Kills" in label:
                value_lbl.setText(str(self.session_stats["total_kills"]))
            elif "Damage Dealt" in label:
                value_lbl.setText(f"{self.session_stats['total_damage_dealt']:.2f}")
            elif "Damage Received" in label:
                value_lbl.setText(f"{self.session_stats['total_damage_received']:.2f}")
            elif "Ratio" in label:
                if self.session_stats["deaths"] > 0:
                    ratio = (
                        self.session_stats["total_kills"] / self.session_stats["deaths"]
                    )
                    value_lbl.setText(f"{ratio:.1f}")
                else:
                    ratio = (
                        self.session_stats["total_kills"]
                        if self.session_stats["total_kills"] > 0
                        else 0
                    )
                    value_lbl.setText(f"{ratio:.1f}")
            elif "Critical" in label:
                value_lbl.setText(str(self.session_stats["critical_hits"]))
            elif "Misses" in label:
                value_lbl.setText(str(self.session_stats["misses"]))

        self.update_kills_table()
        logger.debug("Combat display updated")

    def add_combat_event(self, event_data: dict[str, Any]):
        """Add a combat event"""
        logger.info("[COMBAT_TAB] >>> add_combat_event RECEIVED <<<")
        logger.info(f"[COMBAT_TAB] Event data: {event_data}")

        event_type = event_data.get("event_type", "")

        if event_type == "combat":
            self.combat_data.append(event_data)
            self.process_combat_event(event_data)
            self.update_combat_display()
            logger.debug(f"Combat event added: {event_data}")
        elif event_type == "global":
            # Check if this is a kill event
            parsed_data = event_data.get("parsed_data", {})
            if parsed_data.get("type") in ["kill", "team_kill"]:
                # Convert global kill to combat event format
                kill_event = {
                    "event_type": "combat",
                    "action": "kill",
                    "enemy": parsed_data.get("creature", "Unknown"),
                    "damage": parsed_data.get("value", 0),
                    "timestamp": parsed_data.get(
                        "timestamp", datetime.now().isoformat()
                    ),
                    "type": "Global" if parsed_data.get("hof") else "Kill",
                }
                self.combat_data.append(kill_event)
                self.process_combat_event(kill_event)
                self.update_combat_display()
                logger.info(f"Global kill processed: {parsed_data.get('creature')}")
        elif event_type == "loot":
            # Regular kills are tracked through loot events
            parsed_data = event_data.get("parsed_data", {})
            kill_event = {
                "event_type": "combat",
                "action": "kill",
                "enemy": parsed_data.get("item_name", "Unknown"),
                "damage": parsed_data.get("value", 0),
                "timestamp": parsed_data.get("timestamp", datetime.now().isoformat()),
                "type": "Loot",
            }
            self.combat_data.append(kill_event)
            self.process_combat_event(kill_event)
            self.update_combat_display()
            logger.info(f"Loot kill processed: {parsed_data.get('item_name')}")
        else:
            logger.debug(f"Ignoring non-combat event: {event_type}")

    def process_combat_event(self, event_data: dict[str, Any]):
        """Process a combat event and update session stats"""
        if not self.session_stats["session_start"]:
            from datetime import datetime

            self.session_stats["session_start"] = datetime.now()

        # Check for explicit action first (for converted global/loot events)
        action = event_data.get("action", "").lower()
        parsed_data = event_data.get("parsed_data", {})

        if action == "kill":
            self.session_stats["total_kills"] += 1
            logger.debug(
                f"Processed kill. Total kills: {self.session_stats['total_kills']}"
            )
        elif "damage_taken" in parsed_data:
            damage = parsed_data.get("damage_taken", 0)
            self.session_stats["total_damage_received"] += float(damage)
            logger.debug(f"Processed damage_received: {damage}")
        elif "miss" in parsed_data and parsed_data["miss"]:
            self.session_stats["misses"] += 1
            logger.debug("Processed miss")
        elif "dodged" in parsed_data and parsed_data["dodged"]:
            self.session_stats["misses"] += 1  # Treat dodge as miss
            logger.debug("Processed dodge as miss")
        elif "evaded" in parsed_data and parsed_data["evaded"]:
            self.session_stats["misses"] += 1  # Treat evade as miss
            logger.debug("Processed evade as miss")
        elif "critical_hit" in parsed_data:
            damage = parsed_data.get("critical_hit", 0)
            self.session_stats["critical_hits"] += 1
            self.session_stats["total_damage_dealt"] += float(damage)
            self.session_stats["hits"] += 1
            logger.debug(f"Processed critical_hit: {damage}")
        elif "damage" in parsed_data and action == "":
            # This could be damage dealt or other damage event
            damage = parsed_data.get("damage", 0)
            if damage > 0:
                self.session_stats["total_damage_dealt"] += float(damage)
                self.session_stats["hits"] += 1
                logger.debug(f"Processed damage_dealt: {damage}")

        logger.debug(f"Updated session stats: {self.session_stats}")

    def update_kills_table(self):
        """Update the kills table with recent combat data"""
        kills_data = [
            event
            for event in self.combat_data
            if event.get("action", "").lower() == "kill"
        ]
        kills_data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        self.kills_table.setRowCount(len(kills_data[:20]))  # Show last 20 kills

        for row, kill_event in enumerate(kills_data[:20]):
            # Kill number
            self.kills_table.setItem(
                row, 0, QTableWidgetItem(str(len(kills_data) - row))
            )

            # Enemy name
            enemy = kill_event.get("enemy", kill_event.get("target", "Unknown"))
            self.kills_table.setItem(row, 1, QTableWidgetItem(enemy))

            # Damage
            damage = kill_event.get("damage", 0)
            self.kills_table.setItem(row, 2, QTableWidgetItem(f"{float(damage):.2f}"))

            # Time
            timestamp = kill_event.get("timestamp", "")
            if timestamp:
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M:%S")
                except (ValueError, TypeError):
                    time_str = timestamp[:8]
            else:
                time_str = "Unknown"
            self.kills_table.setItem(row, 3, QTableWidgetItem(time_str))

            # Type
            kill_type = kill_event.get("kill_type", kill_event.get("type", "Normal"))
            self.kills_table.setItem(row, 4, QTableWidgetItem(kill_type))

    def clear_data(self):
        """Clear all combat data"""
        self.combat_data = []
        self.session_stats = {
            "total_kills": 0,
            "total_damage_dealt": 0.0,
            "total_damage_received": 0.0,
            "deaths": 0,
            "critical_hits": 0,
            "misses": 0,
            "hits": 0,
            "session_start": None,
        }
        self.update_combat_display()
        logger.info("Combat data cleared")

    def start_new_session(self):
        """Start a new combat session"""
        self.clear_data()
        from datetime import datetime

        self.session_stats["session_start"] = datetime.now()
        logger.info("New combat session started")

    def update_session_info(
        self, session_id: str | None = None, session_start: datetime | None = None
    ):
        """Update session information display"""
        if session_id and session_start:
            session_time = session_start.strftime("%Y-%m-%d %H:%M:%S")
            self.session_info_label.setText(
                f"Active Session: {session_id[:8]} (Started: {session_time})"
            )
        else:
            self.session_info_label.setText("No active session")

    def get_session_summary(self) -> dict[str, Any]:
        """Get session summary data"""
        duration = None
        if self.session_stats["session_start"]:
            from datetime import datetime

            duration = datetime.now() - self.session_stats["session_start"]

        accuracy = 0
        total_attempts = self.session_stats["hits"] + self.session_stats["misses"]
        if total_attempts > 0:
            accuracy = (self.session_stats["hits"] / total_attempts) * 100

        return {
            "total_kills": self.session_stats["total_kills"],
            "total_damage_dealt": self.session_stats["total_damage_dealt"],
            "total_damage_received": self.session_stats["total_damage_received"],
            "deaths": self.session_stats["deaths"],
            "critical_hits": self.session_stats["critical_hits"],
            "misses": self.session_stats["misses"],
            "hits": self.session_stats["hits"],
            "accuracy": accuracy,
            "session_duration": duration,
            "session_start": self.session_stats["session_start"],
        }

    def load_session_combat_data(self, combat_events: list[dict[str, Any]]):
        """Load combat events for a specific session"""
        # Reset session stats
        self.session_stats = {
            "total_kills": 0,
            "total_damage_dealt": 0.0,
            "total_damage_received": 0.0,
            "deaths": 0,
            "critical_hits": 0,
            "misses": 0,
            "hits": 0,
            "session_start": None,
        }

        # Clear kills table
        if hasattr(self, "kills_table"):
            self.kills_table.setRowCount(0)

        # Process each combat event
        for event_data in combat_events:
            self._process_combat_event(event_data)

        # Update displays
        self.update_combat_display()
        if hasattr(self, "kills_table"):
            self.update_kills_table()

    def _process_combat_event(self, event_data: dict[str, Any]):
        """Process a single combat event (from historical data)"""
        event_type = event_data.get("event_type", "")

        if event_type == "kill":
            self.session_stats["total_kills"] += 1

            # Add to kills table
            if hasattr(self, "kills_table"):
                creature_name = event_data.get("creature_name", "Unknown")
                damage = event_data.get("damage", 0)

                row = self.kills_table.rowCount()
                self.kills_table.insertRow(row)
                self.kills_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
                self.kills_table.setItem(row, 1, QTableWidgetItem(creature_name))
                self.kills_table.setItem(row, 2, QTableWidgetItem(f"{damage:.2f}"))

        elif event_type == "damage_dealt":
            self.session_stats["total_damage_dealt"] += float(
                event_data.get("damage", 0)
            )
            self.session_stats["hits"] += 1

        elif event_type == "damage_received":
            self.session_stats["total_damage_received"] += float(
                event_data.get("damage", 0)
            )

        elif event_type == "death":
            self.session_stats["deaths"] += 1

        elif event_type == "critical_hit":
            self.session_stats["critical_hits"] += 1

        elif event_type == "miss":
            self.session_stats["misses"] += 1
