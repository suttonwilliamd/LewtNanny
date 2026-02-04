"""Streamer UI tab implementation for LewtNanny
A simplified, high-contrast display suitable for live streaming
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class StreamerTabWidget(QWidget):
    """Streamer-friendly UI with large, readable metrics"""

    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.current_session_id: str | None = None
        self.current_session_start: datetime | None = None
        self._stats = {
            'globals': 0,
            'hofs': 0,
            'items': 0,
            'total_cost': Decimal('0'),
            'total_return': Decimal('0'),
        }

        self.setup_ui()
        self.setup_timer()
        logger.info("StreamerTabWidget initialized")

    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.setStyleSheet("""
            QWidget {
                background-color: #0D1117;
                color: #E6EDF3;
            }
            QLabel {
                color: #E6EDF3;
            }
        """)

        header_section = self.create_header_section()
        layout.addWidget(header_section)

        weapon_section = self.create_weapon_section()
        layout.addWidget(weapon_section)

        metrics_section = self.create_metrics_section()
        layout.addWidget(metrics_section)

        recent_section = self.create_recent_activity_section()
        layout.addWidget(recent_section)

        layout.addStretch()

    def create_header_section(self):
        """Create header with session timer"""
        section = QFrame()
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
            }
        """)

        layout = QHBoxLayout(section)
        layout.setContentsMargins(10, 5, 10, 5)

        self.session_timer_label = QLabel("SESSION TIMER: 00:00:00")
        self.session_timer_label.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
        self.session_timer_label.setStyleSheet("color: #238636;")
        layout.addWidget(self.session_timer_label)

        layout.addStretch()

        self.status_label = QLabel("NO ACTIVE SESSION")
        self.status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #8B949E;")
        layout.addWidget(self.status_label)

        return section

    def create_weapon_section(self):
        """Create weapon loadout section"""
        section = QGroupBox("Active Loadout")
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
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.weapon_combo = QComboBox()
        self.weapon_combo.setFixedHeight(30)
        self.weapon_combo.setStyleSheet("""
            QComboBox {
                background-color: #0D1117;
                color: #E6EDF3;
                border: 1px solid #30363D;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
        """)
        self.weapon_combo.addItems(["No weapon selected", "Select a weapon..."])
        self.weapon_combo.currentIndexChanged.connect(self.on_weapon_changed)
        layout.addWidget(self.weapon_combo)

        weapon_info_layout = QHBoxLayout()

        self.weapon_damage_label = QLabel("Damage: --")
        self.weapon_damage_label.setFont(QFont("Consolas", 10))
        self.weapon_damage_label.setStyleSheet("color: #8B949E;")
        weapon_info_layout.addWidget(self.weapon_damage_label)

        self.weapon_decay_label = QLabel("Decay: -- PED")
        self.weapon_decay_label.setFont(QFont("Consolas", 10))
        self.weapon_decay_label.setStyleSheet("color: #8B949E;")
        weapon_info_layout.addWidget(self.weapon_decay_label)

        self.weapon_eco_label = QLabel("Eco: --")
        self.weapon_eco_label.setFont(QFont("Consolas", 10))
        self.weapon_eco_label.setStyleSheet("color: #8B949E;")
        weapon_info_layout.addWidget(self.weapon_eco_label)

        weapon_info_layout.addStretch()

        layout.addLayout(weapon_info_layout)

        section.setLayout(layout)
        return section

    def on_weapon_changed(self, index):
        """Handle weapon selection change"""
        if index > 0:
            weapon_name = self.weapon_combo.currentText()
            logger.info(f"Weapon selected: {weapon_name}")
            if weapon_name != "Select a weapon...":
                self.load_weapon_details_sync(weapon_name)

    def load_weapon_details_sync(self, weapon_name: str):
        """Load weapon details synchronously"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._load_weapon_async(weapon_name))
            loop.close()
        except Exception as e:
            logger.error(f"Error loading weapon details: {e}")

    async def _load_weapon_async(self, weapon_name: str):
        """Async helper to load weapon details"""
        try:
            db = self.db_manager
            if db is None:
                return
            weapon = await db.get_weapon_by_name(weapon_name)  # type: ignore[union-attr]
            if weapon:
                self.weapon_damage_label.setText(f"Damage: {weapon.damage:.1f}")
                self.weapon_decay_label.setText(f"Decay: {float(weapon.decay):.4f} PED")
                if weapon.eco:
                    self.weapon_eco_label.setText(f"Eco: {float(weapon.eco):.2f}")
        except Exception as e:
            logger.error(f"Error loading weapon details: {e}")

    def set_available_weapons(self, weapons: list):
        """Set available weapons in combo box"""
        self.weapon_combo.clear()
        self.weapon_combo.addItem("No weapon selected")
        for weapon in weapons:
            self.weapon_combo.addItem(weapon if isinstance(weapon, str) else weapon.get('name', str(weapon)))

    def update_weapon_display(self, weapon_name: str):
        """Update weapon display from external source (e.g., loadout)"""
        if weapon_name and weapon_name != "No weapon selected":
            self.weapon_combo.setCurrentText(weapon_name)
            self.load_weapon_details_sync(weapon_name)

    def create_metrics_section(self):
        """Create large metrics display"""
        section = QGroupBox("Key Metrics")
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

        layout = QGridLayout()
        layout.setContentsMargins(4, 28, 4, 4)  # Top margin accounts for title bar
        layout.setSpacing(8)

        self.streamer_metrics = {}

        metrics_items = [
            ("Return %", "100.0%", "#E6EDF3"),
            ("Profit/Loss", "0.00 PED", "#4CAF50"),
            ("Globals", "0", "#FFD700"),
            ("HOFs", "0", "#FF6B6B"),
            ("Items Looted", "0", "#4FC3F7"),
            ("Active Weapon", "None", "#B388FF")
        ]

        for i, (label, default, color) in enumerate(metrics_items):
            row = i // 3
            col = i % 3

            container = QWidget()
            container.setStyleSheet("""
                QWidget {
                    background-color: #0D1117;
                    border: 1px solid #30363D;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(4, 4, 4, 4)
            container_layout.setSpacing(2)

            lbl = QLabel(label)
            lbl.setFont(QFont("Arial", 9))
            lbl.setStyleSheet("color: #8B949E;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            container_layout.addWidget(lbl)

            value_lbl = QLabel(default)
            value_lbl.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
            value_lbl.setStyleSheet(f"color: {color};")
            value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            container_layout.addWidget(value_lbl)

            self.streamer_metrics[label] = value_lbl
            layout.addWidget(container, row, col)

        section.setLayout(layout)
        return section

    def create_recent_activity_section(self):
        """Create recent activity ticker"""
        section = QGroupBox("Recent Activity")
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
        layout.setSpacing(2)

        self.activity_ticker = QLabel("No recent activity")
        self.activity_ticker.setFont(QFont("Consolas", 10))
        self.activity_ticker.setStyleSheet("color: #8B949E;")
        self.activity_ticker.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.activity_ticker.setWordWrap(True)
        layout.addWidget(self.activity_ticker)

        section.setLayout(layout)
        return section

    def setup_timer(self):
        """Setup update timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_timer_display)
        self.update_timer.start(1000)
        logger.debug("Streamer timer started")

    def update_timer_display(self):
        """Update session timer display"""
        if self.current_session_start:
            delta = datetime.now() - self.current_session_start
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.session_timer_label.setText(
                f"SESSION TIMER: {hours:02d}:{minutes:02d}:{seconds:02d}"
            )

    def set_db_manager(self, db_manager):
        """Set database manager"""
        self.db_manager = db_manager
        self.load_available_weapons()

    def load_available_weapons(self):
        """Load available weapons from database"""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._load_weapons_async())
            loop.close()
        except Exception as e:
            logger.error(f"Error loading available weapons: {e}")

    async def _load_weapons_async(self):
        """Async helper to load weapons"""
        try:
            if self.db_manager:
                weapons = await self.db_manager.get_all_weapons()
                weapon_names = [w.name for w in weapons]
                self.set_available_weapons(weapon_names)
        except Exception as e:
            logger.error(f"Error loading weapons async: {e}")

    def start_session(self, session_id: str, activity_type: str):
        """Start a new session"""
        self.current_session_id = session_id
        self.current_session_start = datetime.now()
        self._stats = {
            'globals': 0,
            'hofs': 0,
            'items': 0,
            'total_cost': Decimal('0'),
            'total_return': Decimal('0'),
        }
        self.status_label.setText(f"ACTIVITY: {activity_type.upper()}")
        self.status_label.setStyleSheet("color: #238636;")
        self._update_stats_display()
        logger.info(f"Streamer UI session started: {session_id}")

    def stop_session(self):
        """Stop current session"""
        self.current_session_id = None
        self.current_session_start = None
        self.session_timer_label.setText("SESSION TIMER: 00:00:00")
        self.status_label.setText("NO ACTIVE SESSION")
        self.status_label.setStyleSheet("color: #8B949E;")
        logger.info("Streamer UI session stopped")

    def update_metrics(self, metrics: dict[str, Any]):
        """Update metrics display"""
        for label, value in metrics.items():
            if label in self.streamer_metrics:
                self.streamer_metrics[label].setText(str(value))
        logger.debug("Streamer metrics updated")

    def _update_stats_display(self):
        """Update statistics display with calculated values"""
        cost = self._stats.get('total_cost', Decimal('0'))
        return_val = self._stats.get('total_return', Decimal('0'))

        if cost > 0:
            return_pct = (return_val / cost) * 100
            return_pct_str = f"{float(return_pct):.1f}%"
        else:
            return_pct_str = "100.0%"

        profit = return_val - cost
        if profit >= 0:
            profit_str = f"+{float(profit):.2f} PED"
            profit_color = "#4CAF50"
        else:
            profit_str = f"{float(profit):.2f} PED"
            profit_color = "#FF6B6B"

        if "Return %" in self.streamer_metrics:
            self.streamer_metrics["Return %"].setText(return_pct_str)
        if "Profit/Loss" in self.streamer_metrics:
            self.streamer_metrics["Profit/Loss"].setText(profit_str)
            self.streamer_metrics["Profit/Loss"].setStyleSheet(f"color: {profit_color}; font-weight: bold; font-family: Consolas; font-size: 14px;")
        if "Globals" in self.streamer_metrics:
            self.streamer_metrics["Globals"].setText(str(self._stats.get('globals', 0)))
        if "HOFs" in self.streamer_metrics:
            self.streamer_metrics["HOFs"].setText(str(self._stats.get('hofs', 0)))
        if "Items Looted" in self.streamer_metrics:
            self.streamer_metrics["Items Looted"].setText(str(self._stats.get('items', 0)))

    def add_activity(self, activity: str):
        """Add activity to ticker"""
        current = self.activity_ticker.text()
        if current == "No recent activity":
            current = ""

        timestamp = datetime.now().strftime("%H:%M:%S")
        new_activity = f"[{timestamp}] {activity}"

        lines = current.split("\n") if current else []
        lines.insert(0, new_activity)
        lines = lines[:10]

        self.activity_ticker.setText("\n".join(lines))
        logger.debug(f"Activity added: {activity}")

    def add_event(self, event_data: dict[str, Any]):
        """Add event to streamer UI with formatted output"""
        logger.info("[STREAMER_UI] ===========================================")
        logger.info("[STREAMER_UI] >>> add_event RECEIVED <<<")
        logger.info(f"[STREAMER_UI] Event type: {event_data.get('event_type', 'unknown')}")
        logger.info(f"[STREAMER_UI] Event data: {event_data}")

        event_type = event_data.get('event_type', 'unknown')
        parsed_data = event_data.get('parsed_data', {})

        logger.info(f"[STREAMER_UI] Processing event type: {event_type}")

        activity_str = ""

        if event_type == 'loot':
            item_name = parsed_data.get('item_name', 'Unknown')
            quantity = parsed_data.get('quantity', 1)
            value = parsed_data.get('value', 0)
            activity_str = f"💰 {item_name} x ({quantity}) ({value} PED)"

            self._stats['items'] = self._stats.get('items', 0) + 1
            self._stats['total_return'] = self._stats.get('total_return', Decimal('0')) + Decimal(str(value))

        elif event_type == 'combat':
            damage = parsed_data.get('damage', 0)
            decay = parsed_data.get('decay', 0)
            critical = parsed_data.get('critical', False)
            miss = parsed_data.get('miss', False)
            if miss:
                activity_str = "❌ MISS"
            elif critical:
                activity_str = f"🔥 CRIT: {damage} dmg"
            else:
                activity_str = f"⚔️ {damage} dmg"
            if decay and float(decay) > 0:
                self._stats['total_cost'] = self._stats.get('total_cost', Decimal('0')) + Decimal(str(decay))

        elif event_type == 'skill':
            skill = parsed_data.get('skill', '')
            exp = parsed_data.get('experience', 0)
            activity_str = f"📈 {skill} +{exp} exp"

        elif event_type == 'global':
            player = parsed_data.get('player', '')
            creature = parsed_data.get('creature', '')
            value = parsed_data.get('value', 0)
            activity_str = f"🌟 GLOBAL! {player} → {creature} ({value} PED)"
            self._stats['globals'] = self._stats.get('globals', 0) + 1
            self._stats['total_return'] = self._stats.get('total_return', Decimal('0')) + Decimal(str(value))

        elif event_type == 'hof':
            player = parsed_data.get('player', '')
            creature = parsed_data.get('creature', '')
            value = parsed_data.get('value', 0)
            activity_str = f"🏆 HOF! {player} → {creature} ({value} PED)"
            self._stats['hofs'] = self._stats.get('hofs', 0) + 1
            self._stats['total_return'] = self._stats.get('total_return', Decimal('0')) + Decimal(str(value))

        else:
            raw_message = event_data.get('raw_message', '')
            activity_str = raw_message[:50] if raw_message else event_type

        if activity_str:
            self.add_activity(activity_str)

        self._update_stats_display()
