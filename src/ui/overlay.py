"""
Streamer Overlay for LewtNanny
Transparent, always-on-top overlay for live session stats streaming
Modern redesign with accurate data integration
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QFont, QPainter, QColor, QPen

logger = logging.getLogger(__name__)


class StreamerOverlayWidget(QWidget):
    """Draggable, transparent overlay widget for streaming"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        self.dragging = False
        self.drag_position = QPoint()

        self._stats = {
            'globals': 0,
            'hofs': 0,
            'items': 0,
            'total_cost': Decimal('0'),
            'total_return': Decimal('0'),
        }
        self._weapon = {
            'name': '',
            'amp': '',
            'decay': ''
        }

        self.setup_ui()
        self.setup_timers()

        logger.debug("StreamerOverlayWidget initialized")

    def setup_ui(self):
        """Setup the overlay UI with modern design"""
        self.setFixedSize(300, 420)
        self.move(100, 100)

        container = QFrame(self)
        container.setGeometry(0, 0, 300, 420)
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 15, 20, 245);
                border: 1px solid rgba(60, 60, 80, 180);
                border-radius: 12px;
            }
        """)
        self.container = container

        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.create_header(layout)
        self.create_timer(layout)
        self.create_stats_grid(layout)
        self.create_weapon_section(layout)
        self.create_activity_ticker(layout)

        self.session_start_time = None
        self.session_active = False

    def create_header(self, layout):
        """Create header with title"""
        header_layout = QHBoxLayout()

        title_label = QLabel("LEWT NANNY")
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #7ee787; letter-spacing: 2px;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22, 22)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(40, 40, 50, 200);
                color: #8b949e;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(200, 60, 60, 200);
                color: #ffffff;
            }
        """)
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)

        layout.addLayout(header_layout)

    def create_timer(self, layout):
        """Create session timer display"""
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setFont(QFont("Consolas", 28, QFont.Weight.Bold))
        self.timer_label.setStyleSheet("color: #ffffff;")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.timer_label)

    def create_stats_grid(self, layout):
        """Create statistics grid with modern cards"""
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 40, 150);
                border-radius: 8px;
                padding: 8px;
            }
        """)

        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setSpacing(6)

        self.stats_labels = {}

        stats_items = [
            ("Return %", "100.0%", "#58a6ff"),
            ("Profit", "0.00 PED", "#7ee787"),
            ("Globals", "0", "#d29922"),
            ("HOFs", "0", "#f0883e"),
            ("Items", "0", "#a371f7"),
        ]

        for label, default, color in stats_items:
            row_layout = QHBoxLayout()

            lbl = QLabel(label)
            lbl.setFont(QFont("Segoe UI", 9))
            lbl.setStyleSheet("color: #8b949e;")
            row_layout.addWidget(lbl)

            row_layout.addStretch()

            value_lbl = QLabel(default)
            value_lbl.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
            value_lbl.setStyleSheet(f"color: {color};")
            row_layout.addWidget(value_lbl)

            self.stats_labels[label] = value_lbl

            separator = QFrame()
            separator.setStyleSheet("border-bottom: 1px solid rgba(60, 60, 70, 100);")
            separator.setFixedHeight(1)
            stats_layout.addWidget(separator)
            stats_layout.addLayout(row_layout)

        layout.addWidget(stats_frame)

    def create_weapon_section(self, layout):
        """Create weapon loadout section"""
        weapon_frame = QFrame()
        weapon_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 40, 150);
                border-radius: 8px;
                padding: 8px;
            }
        """)

        weapon_layout = QVBoxLayout(weapon_frame)
        weapon_layout.setSpacing(4)

        title = QLabel("LOADOUT")
        title.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        title.setStyleSheet("color: #8b949e; letter-spacing: 1px;")
        weapon_layout.addWidget(title)

        self.weapon_label = QLabel("No weapon selected")
        self.weapon_label.setFont(QFont("Consolas", 10))
        self.weapon_label.setStyleSheet("color: #e6edf3;")
        weapon_layout.addWidget(self.weapon_label)

        weapon_info_layout = QHBoxLayout()

        self.amp_label = QLabel("--")
        self.amp_label.setFont(QFont("Consolas", 9))
        self.amp_label.setStyleSheet("color: #8b949e;")
        weapon_info_layout.addWidget(self.amp_label)

        self.decay_label = QLabel("-- PED/click")
        self.decay_label.setFont(QFont("Consolas", 9))
        self.decay_label.setStyleSheet("color: #8b949e;")
        weapon_info_layout.addWidget(self.decay_label)

        weapon_info_layout.addStretch()
        weapon_layout.addLayout(weapon_info_layout)

        layout.addWidget(weapon_frame)

    def create_activity_ticker(self, layout):
        """Create activity ticker"""
        ticker_frame = QFrame()
        ticker_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(25, 25, 35, 180);
                border-radius: 6px;
            }
        """)

        ticker_layout = QVBoxLayout(ticker_frame)
        ticker_layout.setContentsMargins(6, 4, 6, 4)

        title = QLabel("ACTIVITY")
        title.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        title.setStyleSheet("color: #6e7681; letter-spacing: 1px;")
        ticker_layout.addWidget(title)

        self.activity_label = QLabel("No recent activity")
        self.activity_label.setFont(QFont("Consolas", 9))
        self.activity_label.setStyleSheet("color: #8b949e;")
        self.activity_label.setWordWrap(True)
        ticker_layout.addWidget(self.activity_label)

        layout.addWidget(ticker_frame)

    def setup_timers(self):
        """Setup update timers"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)

    def update_display(self):
        """Update timer display"""
        if self.session_active and self.session_start_time:
            elapsed = datetime.now() - self.session_start_time
            hours = int(elapsed.total_seconds() // 3600)
            minutes = int((elapsed.total_seconds() % 3600) // 60)
            seconds = int(elapsed.total_seconds() % 60)
            self.timer_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def start_session(self, session_id: str, activity_type: str):
        """Start a new session"""
        self.session_start_time = datetime.now()
        self.session_active = True
        self.current_session_id = session_id
        self._stats = {
            'globals': 0,
            'hofs': 0,
            'items': 0,
            'total_cost': Decimal('0'),
            'total_return': Decimal('0'),
        }
        self._weapon = {'name': '', 'amp': '', 'decay': ''}
        self._update_stats_display()
        self.show()
        logger.info(f"Streamer overlay session started: {session_id}")

    def stop_session(self):
        """Stop current session"""
        self.session_active = False
        self.session_start_time = None
        self.timer_label.setText("00:00:00")
        logger.info("Streamer overlay session stopped")

    def _update_stats_display(self):
        """Update statistics display with calculated values"""
        cost = self._stats.get('total_cost', Decimal('0'))
        return_val = self._stats.get('total_return', Decimal('0'))

        if cost > 0:
            return_pct = (return_val / cost) * 100
            return_pct_str = f"{return_pct:.1f}%"
        else:
            return_pct_str = "100.0%"

        profit = return_val - cost
        if profit >= 0:
            profit_str = f"+{float(profit):.2f} PED"
            profit_color = "#7ee787"
        else:
            profit_str = f"{float(profit):.2f} PED"
            profit_color = "#f85149"

        if "Return %" in self.stats_labels:
            self.stats_labels["Return %"].setText(return_pct_str)
        if "Profit" in self.stats_labels:
            self.stats_labels["Profit"].setText(profit_str)
            self.stats_labels["Profit"].setStyleSheet(f"color: {profit_color}; font-weight: bold;")
        if "Globals" in self.stats_labels:
            self.stats_labels["Globals"].setText(str(self._stats.get('globals', 0)))
        if "HOFs" in self.stats_labels:
            self.stats_labels["HOFs"].setText(str(self._stats.get('hofs', 0)))
        if "Items" in self.stats_labels:
            self.stats_labels["Items"].setText(str(self._stats.get('items', 0)))

    def update_stats(self, stats: Dict[str, Any]):
        """Update statistics from external source"""
        for key, value in stats.items():
            if key == 'globals':
                self._stats['globals'] = value
            elif key == 'hofs':
                self._stats['hofs'] = value
            elif key == 'items':
                self._stats['items'] = value
            elif key == 'total_cost':
                self._stats['total_cost'] = Decimal(str(value))
            elif key == 'total_return':
                self._stats['total_return'] = Decimal(str(value))
        self._update_stats_display()

    def update_weapon(self, weapon_name: str, amp: str = "", decay: str = ""):
        """Update weapon display"""
        self._weapon = {
            'name': weapon_name or '',
            'amp': amp or '',
            'decay': decay or ''
        }
        self.weapon_label.setText(weapon_name if weapon_name else "No weapon selected")
        self.amp_label.setText(f"Amp: {amp}" if amp else "Amp: --")
        self.decay_label.setText(f"Decay: {decay}" if decay else "Decay: -- PED/click")

    def add_activity(self, activity: str):
        """Add activity to ticker"""
        current = self.activity_label.text()
        if current == "No recent activity":
            current = ""

        timestamp = datetime.now().strftime("%H:%M:%S")
        new_activity = f"[{timestamp}] {activity}"

        lines = current.split("\n") if current else []
        lines.insert(0, new_activity)
        lines = lines[:5]

        self.activity_label.setText("\n".join(lines))

    def add_event(self, event_data: Dict[str, Any]):
        """Add event to ticker and update stats"""
        logger.info(f"[OVERLAY] ===========================================")
        logger.info(f"[OVERLAY] >>> add_event RECEIVED <<<")
        logger.info(f"[OVERLAY] Event type: {event_data.get('event_type', 'unknown')}")
        logger.info(f"[OVERLAY] Event data: {event_data}")

        event_type = event_data.get('event_type', 'unknown')
        raw_message = event_data.get('raw_message', '')
        parsed_data = event_data.get('parsed_data', {})

        logger.info(f"[OVERLAY] Processing event type: {event_type}")
        logger.info(f"[OVERLAY] Parsed data: {parsed_data}")

        activity_str = ""
        should_add_activity = True

        logger.info(f"[OVERLAY] Processing event type: {event_type}")
        logger.info(f"[OVERLAY] Parsed data: {parsed_data}")

        if event_type == 'loot':
            item_name = parsed_data.get('item_name', 'Unknown')
            quantity = parsed_data.get('quantity', 1)
            value = parsed_data.get('value', 0)
            activity_str = f"💰 {item_name} x ({quantity}) ({value} PED)"
            self._stats['items'] = self._stats.get('items', 0) + 1
            self._stats['total_return'] = self._stats.get('total_return', Decimal('0')) + Decimal(str(value))
            logger.info(f"[OVERLAY] Loot event processed: items={self._stats['items']}, return={self._stats['total_return']}")

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
            logger.info(f"[OVERLAY] Combat event processed: damage={damage}, decay={decay}, critical={critical}")

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
            logger.info(f"[OVERLAY] GLOBAL event processed: globals={self._stats['globals']}")

        elif event_type == 'hof':
            player = parsed_data.get('player', '')
            creature = parsed_data.get('creature', '')
            value = parsed_data.get('value', 0)
            activity_str = f"🏆 HOF! {player} → {creature} ({value} PED)"
            self._stats['hofs'] = self._stats.get('hofs', 0) + 1
            self._stats['total_return'] = self._stats.get('total_return', Decimal('0')) + Decimal(str(value))
            logger.info(f"[OVERLAY] HOF event processed: hofs={self._stats['hofs']}")

        else:
            activity_str = raw_message[:45] if raw_message else event_type

        if should_add_activity and activity_str:
            self.add_activity(activity_str)

        self._update_stats_display()
        logger.info(f"[OVERLAY] <<< add_event complete >>>")
        logger.info(f"[OVERLAY] Current stats: {dict(self._stats)}")

    def mousePressEvent(self, a0):
        """Mouse press for dragging"""
        if a0.button() == Qt.MouseButton.LeftButton:  # type: ignore[union-attr]
            self.dragging = True
            self.drag_position = a0.globalPosition().toPoint() - self.frameGeometry().topLeft()  # type: ignore[union-attr]
            a0.accept()  # type: ignore[union-attr]

    def mouseMoveEvent(self, a0):
        """Mouse move for dragging"""
        if a0.buttons() == Qt.MouseButton.LeftButton and self.dragging:  # type: ignore[union-attr]
            self.move(a0.globalPosition().toPoint() - self.drag_position)  # type: ignore[union-attr]
            a0.accept()  # type: ignore[union-attr]

    def mouseReleaseEvent(self, a0):  # type: ignore[no-untyped-def]
        """Mouse release to stop dragging"""
        self.dragging = False


class SessionOverlay:
    """Session overlay controller"""

    def __init__(self, db_manager, config_manager):
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.overlay_widget: Optional[StreamerOverlayWidget] = None
        self.current_weapon = None
        logger.info("SessionOverlay initialized")

    def show(self):
        """Show the overlay"""
        try:
            if self.overlay_widget is None:
                self.overlay_widget = StreamerOverlayWidget()

            self.overlay_widget.show()
            logger.info("SessionOverlay shown")

        except Exception as e:
            logger.error(f"Error showing overlay: {e}")

    def hide(self):
        """Hide the overlay"""
        if self.overlay_widget:
            self.overlay_widget.hide()
            logger.info("SessionOverlay hidden")

    def close(self):
        """Close the overlay"""
        if self.overlay_widget:
            self.overlay_widget.close()
            self.overlay_widget = None
            logger.info("SessionOverlay closed")

    def start_session(self, session_id: str, activity_type: str):
        """Start a new session"""
        if self.overlay_widget:
            self.overlay_widget.start_session(session_id, activity_type)
        logger.info(f"SessionOverlay started session: {session_id}")

    def stop_session(self):
        """Stop current session"""
        if self.overlay_widget:
            self.overlay_widget.stop_session()
        logger.info("SessionOverlay stopped session")

    def add_event(self, event_data: Dict[str, Any]):
        """Add event to overlay"""
        logger.info(f"[OVERLAY_CONTROLLER] add_event called with type: {event_data.get('event_type', 'unknown')}")
        if self.overlay_widget:
            self.overlay_widget.add_event(event_data)
            logger.info(f"[OVERLAY_CONTROLLER] Forwarded event to widget")
        else:
            logger.warning(f"[OVERLAY_CONTROLLER] No overlay widget available!")

    def update_weapon(self, weapon_name: str, amp: str = "", decay: str = ""):
        """Update weapon display"""
        self.current_weapon = weapon_name
        if self.overlay_widget:
            self.overlay_widget.update_weapon(weapon_name, amp, decay)
