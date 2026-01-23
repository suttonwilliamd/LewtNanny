"""
Streamer Overlay for LewtNanny
Transparent, always-on-top overlay for live session stats streaming
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QPoint, QThread
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QScreen, QGuiApplication

logger = logging.getLogger(__name__)


class ScreenshotWorker(QThread):
    """Background worker to take screenshot after delay"""

    def __init__(self, delay_ms: int, screenshot_dir: str, event_type: str, value: float, player: str):
        super().__init__()
        self.delay_ms = delay_ms
        self.screenshot_dir = screenshot_dir
        self.event_type = event_type
        self.value = value
        self.player = player

    def run(self):
        import time
        time.sleep(self.delay_ms / 1000.0)
        self.take_screenshot()

    def take_screenshot(self):
        try:
            screen = QGuiApplication.primaryScreen()
            if screen is None:
                logger.error("[OVERLAY] No primary screen found for screenshot")
                return

            os.makedirs(self.screenshot_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.event_type}_{self.player}_{self.value:.2f}ped_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)

            pixmap = screen.grabWindow(0)
            pixmap.save(filepath)
            logger.info(f"[OVERLAY] Screenshot saved: {filepath}")
        except Exception as e:
            logger.error(f"[OVERLAY] Error taking screenshot: {e}")


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
        self.character_name = ""

        self._stats = {
            'globals': 0,
            'hofs': 0,
            'items': 0,
            'kills': 0,
            'wasted_shots': 0,
            'total_cost': Decimal('0'),
            'total_return': Decimal('0'),
        }
        self._shots_taken = 0
        self._cost_per_attack = Decimal('0')

        self.setup_ui()
        self.setup_timers()

        logger.debug("StreamerOverlayWidget initialized")

    def set_character_name(self, name: str):
        """Set the character name for filtering globals/HOFs"""
        self.character_name = name
        logger.debug(f"[OVERLAY] Character name set to: {name}")

    def set_cost_per_attack(self, cost: float):
        """Set the cost per attack for calculating total spent"""
        self._cost_per_attack = Decimal(str(cost))
        logger.debug(f"[OVERLAY] Cost per attack set to: {self._cost_per_attack}")
        self._update_stats_display()

    def setup_ui(self):
        """Setup the overlay UI"""
        self.setFixedSize(350, 280)
        self.move(100, 100)

        container = QFrame(self)
        container.setGeometry(0, 0, 350, 280)
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 15, 20, 245);
                border: 1px solid rgba(60, 60, 80, 180);
                border-radius: 12px;
            }
        """)
        self.container = container

        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        self.create_main_display(layout)

        self.session_start_time = None
        self.session_active = False

    def create_main_display(self, layout):
        """Create main display with all required elements"""
        # Large % Return display
        self.return_percentage_label = QLabel("100.00%")
        self.return_percentage_label.setFont(QFont("Consolas", 36, QFont.Weight.Bold))
        self.return_percentage_label.setStyleSheet("color: #ffffff;")
        self.return_percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.return_percentage_label)

        # Stats grid layout
        stats_layout = QGridLayout()
        stats_layout.setSpacing(8)

        # Kills
        self.kills_label = QLabel("Kills: 0")
        self.kills_label.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        self.kills_label.setStyleSheet("color: #ffa500;")
        self.kills_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        stats_layout.addWidget(self.kills_label, 0, 0)

        # Wasted Shots
        self.wasted_shots_label = QLabel("Wasted: 0")
        self.wasted_shots_label.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        self.wasted_shots_label.setStyleSheet("color: #ff4444;")
        self.wasted_shots_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        stats_layout.addWidget(self.wasted_shots_label, 0, 1)

        # Total Spent
        self.total_spent_label = QLabel("Spent: 0.00 PED")
        self.total_spent_label.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        self.total_spent_label.setStyleSheet("color: #ff6b6b;")
        self.total_spent_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        stats_layout.addWidget(self.total_spent_label, 1, 0)

        # Total Return
        self.total_return_label = QLabel("Return: 0.000 PED")
        self.total_return_label.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        self.total_return_label.setStyleSheet("color: #7ee787;")
        self.total_return_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        stats_layout.addWidget(self.total_return_label, 1, 1)

        layout.addLayout(stats_layout)

        # Session Timer
        timer_layout = QHBoxLayout()
        timer_layout.addStretch()

        self.timer_label = QLabel("Session: 00:00:00")
        self.timer_label.setFont(QFont("Consolas", 12))
        self.timer_label.setStyleSheet("color: #8b949e;")
        timer_layout.addWidget(self.timer_label)

        timer_layout.addStretch()
        layout.addLayout(timer_layout)

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

    def start_session(self, session_id: str, activity_type: str, session_start_time: Optional[datetime] = None):
        """Start a new session"""
        logger.info(f"[OVERLAY] start_session called: session_id={session_id}, activity_type={activity_type}")
        logger.info(f"[OVERLAY] Previous stats before reset: {dict(self._stats)}")
        
        self.session_start_time = session_start_time if session_start_time else datetime.now()
        self.session_active = True
        self.current_session_id = session_id
        self._stats = {
            'globals': 0,
            'hofs': 0,
            'items': 0,
            'kills': 0,
            'wasted_shots': 0,
            'total_cost': Decimal('0'),
            'total_return': Decimal('0'),
        }
        self._shots_taken = 0
        logger.info(f"[OVERLAY] Stats reset to: {dict(self._stats)}")
        
        self._update_stats_display()
        self.show()
        logger.info(f"Streamer overlay session started: {session_id}")

    def stop_session(self):
        """Stop current session"""
        logger.info(f"[OVERLAY] stop_session called, session_active={self.session_active}, current_session_id={self.current_session_id}")
        logger.info(f"[OVERLAY] Stats before stop: {dict(self._stats)}")
        self.session_active = False
        self.session_start_time = None
        self.timer_label.setText("00:00:00")
        logger.info("Streamer overlay session stopped")

    def _get_return_color(self, return_pct: float) -> str:
        """Get color based on return percentage"""
        if return_pct < 10:
            return "#000000"  # Black for single digit returns
        elif return_pct < 50:
            return "#8B0000"  # Dark Red
        elif return_pct < 75:
            return "#FF0000"  # Red
        elif return_pct < 90:
            return "#FF4500"  # Orange Red
        elif return_pct < 100:
            return "#FFA500"  # Orange
        elif return_pct < 110:
            return "#90EE90"  # Light Green
        elif return_pct < 150:
            return "#00FF00"  # Green
        elif return_pct < 200:
            return "#00CED1"  # Dark Turquoise
        elif return_pct < 300:
            return "#FFD700"  # Gold
        elif return_pct < 500:
            return "#FF8C00"  # Dark Orange
        else:
            return "#FF1493"  # Deep Pink for huge returns

    def _update_stats_display(self):
        """Update statistics display with calculated values"""
        cost = self._stats.get('total_cost', Decimal('0'))
        return_val = self._stats.get('total_return', Decimal('0'))
        kills = self._stats.get('kills', 0)
        wasted_shots = self._stats.get('wasted_shots', 0)

        logger.debug(f"[OVERLAY] _update_stats_display: cost={float(cost):.3f}, return={float(return_val):.3f}, kills={kills}, wasted={wasted_shots}")

        if cost > 0:
            return_pct = (return_val / cost) * 100
            return_pct_str = f"{float(return_pct):.2f}%"
        else:
            return_pct = 100.0
            return_pct_str = "100.00%"

        logger.debug(f"[OVERLAY] Display update: {return_pct_str} return, spent={float(cost):.2f} PED, return={float(return_val):.3f} PED, kills={kills}, wasted={wasted_shots}")

        # Update percentage with dynamic color
        self.return_percentage_label.setText(return_pct_str)
        color = self._get_return_color(return_pct)
        self.return_percentage_label.setStyleSheet(f"color: {color};")
        
        self.kills_label.setText(f"Kills: {kills}")
        self.wasted_shots_label.setText(f"Wasted: {wasted_shots}")

        if float(cost) > 0:
            self.total_spent_label.setText(f"Spent: {float(cost):.2f} PED")
        else:
            self.total_spent_label.setText("Spent: 0.00 PED")

        if float(return_val) > 0:
            self.total_return_label.setText(f"Return: {float(return_val):.3f} PED")
        else:
            self.total_return_label.setText("Return: 0.000 PED")

    def _schedule_screenshot(self, event_type: str, value: float, player: str):
        """Schedule a screenshot for global/HOF events"""
        try:
            from src.services.config_manager import ConfigManager
            config = ConfigManager()

            screenshot_enabled = config.get("screenshot.enabled", True)
            if not screenshot_enabled:
                logger.debug(f"[OVERLAY] Screenshots disabled, skipping")
                return

            screenshot_dir = config.get("screenshot.directory", "~/Documents/LewtNanny/")
            screenshot_dir = os.path.expanduser(screenshot_dir)

            delay_ms = int(config.get("screenshot.delay_ms", 500))

            logger.info(f"[OVERLAY] Scheduling screenshot in {delay_ms}ms for {event_type}: {player} got {value} PED")

            worker = ScreenshotWorker(delay_ms, screenshot_dir, event_type, value, player)
            worker.start()

        except Exception as e:
            logger.error(f"[OVERLAY] Error scheduling screenshot: {e}")

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

    def add_activity(self, activity: str):
        pass

    def update_weapon(self, weapon_name: str, amp: str = "", decay: str = ""):
        pass

    def add_event(self, event_data: Dict[str, Any]):
        """Add event to ticker and update stats"""
        logger.debug(f"[OVERLAY] ===========================================")
        logger.debug(f"[OVERLAY] >>> add_event RECEIVED <<<")
        logger.debug(f"[OVERLAY] Event type: {event_data.get('event_type', 'unknown')}")
        logger.debug(f"[OVERLAY] Event data: {event_data}")

        event_type = event_data.get('event_type', 'unknown')
        parsed_data = event_data.get('parsed_data', {})

        logger.debug(f"[OVERLAY] Processing event type: {event_type}")
        logger.debug(f"[OVERLAY] Parsed data: {parsed_data}")

        current_return = float(self._stats.get('total_return', Decimal('0')))
        current_cost = float(self._stats.get('total_cost', Decimal('0')))
        logger.debug(f"[OVERLAY] Before event - total_return: {current_return:.3f}, total_cost: {current_cost:.3f}")

        if event_type == 'loot':
            value = parsed_data.get('value', 0)
            item_name = parsed_data.get('item_name', '')
            logger.debug(f"[OVERLAY] Loot event: value={value}, item={item_name}")
            self._stats['items'] = self._stats.get('items', 0) + 1
            self._stats['total_return'] = self._stats.get('total_return', Decimal('0')) + Decimal(str(value))
            new_return = float(self._stats['total_return'])
            logger.debug(f"[OVERLAY] Loot event processed: items={self._stats['items']}, adding {value} PED to return, new total_return: {new_return:.3f}")

        elif event_type == 'combat':
            damage = parsed_data.get('damage', 0)
            miss = parsed_data.get('miss', False)
            dodge = parsed_data.get('dodged', False)  # When creature dodges your attack
            logger.debug(f"[OVERLAY] Combat event: damage={damage}, miss={miss}, dodge={dodge}")
            
            # Count shots that consume ammo/decay (successful hits + dodged shots)
            should_count_shot = False
            
            if dodge:
                # Track wasted shots (creature dodged your attack)
                self._stats['wasted_shots'] = self._stats.get('wasted_shots', 0) + 1
                should_count_shot = True
                logger.debug(f"[OVERLAY] Dodged shot detected: total wasted={self._stats['wasted_shots']}")
            elif not miss and damage and float(damage) > 0:
                # Successful hit
                should_count_shot = True
                self._stats['kills'] = self._stats.get('kills', 0) + 1
                logger.debug(f"[OVERLAY] Successful hit: kills={self._stats['kills']}")
            else:
                logger.debug(f"[OVERLAY] Combat event skipped (miss or no damage): miss={miss}, damage={damage}")
            
            # Update cost for shots that consume ammo/decay
            if should_count_shot:
                self._shots_taken += 1
                if self._cost_per_attack > 0:
                    self._stats['total_cost'] = Decimal(str(self._shots_taken * float(self._cost_per_attack)))
                new_cost = float(self._stats['total_cost'])
                logger.debug(f"[OVERLAY] Combat event processed: shots={self._shots_taken}, cost_per_attack={float(self._cost_per_attack):.6f}, new total_cost: {new_cost:.3f}")
                
        elif event_type == 'kill':
            # Track successful kills
            self._stats['kills'] = self._stats.get('kills', 0) + 1
            logger.debug(f"[OVERLAY] Kill event: total kills={self._stats['kills']}")

        elif event_type == 'global':
            value = parsed_data.get('value', 0)
            player = parsed_data.get('player', '')
            logger.debug(f"[OVERLAY] GLOBAL event: value={value}, player={player}, my_character_name={self.character_name}")
            if self.character_name and player and player.lower() == self.character_name.lower():
                logger.info(f"[OVERLAY] GLOBAL DETECTED! {player} got {value} PED - scheduling screenshot")
                self._schedule_screenshot("global", value, player)
            else:
                logger.debug(f"[OVERLAY] GLOBAL event skipped (not mine): player={player}, my_character_name={self.character_name}")

        elif event_type == 'hof':
            value = parsed_data.get('value', 0)
            player = parsed_data.get('player', '')
            logger.debug(f"[OVERLAY] HOF event: value={value}, player={player}, my_character_name={self.character_name}")
            if self.character_name and player and player.lower() == self.character_name.lower():
                logger.info(f"[OVERLAY] HOF DETECTED! {player} got {value} PED - scheduling screenshot")
                self._schedule_screenshot("hof", value, player)
            else:
                logger.debug(f"[OVERLAY] HOF event skipped (not mine): player={player}, my_character_name={self.character_name}")

        else:
            logger.debug(f"[OVERLAY] Unknown event type: {event_type}, raw_message: {event_data.get('raw_message', 'N/A')}")

        self._update_stats_display()
        logger.debug(f"[OVERLAY] <<< add_event complete >>>")
        logger.debug(f"[OVERLAY] Current stats: globals={self._stats.get('globals')}, hofs={self._stats.get('hofs')}, items={self._stats.get('items')}, total_cost={float(self._stats.get('total_cost', Decimal('0'))):.3f}, total_return={float(self._stats.get('total_return', Decimal('0'))):.3f}")

    def mousePressEvent(self, a0):
        """Mouse press for dragging"""
        if a0.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = a0.globalPosition().toPoint() - self.frameGeometry().topLeft()
            a0.accept()

    def mouseMoveEvent(self, a0):
        """Mouse move for dragging"""
        if a0.buttons() == Qt.MouseButton.LeftButton and self.dragging:
            self.move(a0.globalPosition().toPoint() - self.drag_position)
            a0.accept()

    def mouseReleaseEvent(self, a0):
        """Mouse release to stop dragging"""
        self.dragging = False





class SessionOverlay:
    """Session overlay controller"""

    def __init__(self, db_manager, config_manager):
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.overlay_widget: Optional[StreamerOverlayWidget] = None
        self.current_weapon = None
        self._stats = {
            'total_cost': Decimal('0'),
            'total_return': Decimal('0')
        }
        logger.info("SessionOverlay initialized")

    def get_character_name(self) -> str:
        """Get the current character name from config"""
        if self.config_manager:
            return self.config_manager.get("character.name", "") or ""
        return ""

    def show(self):
        """Show the overlay"""
        try:
            if self.overlay_widget is None:
                self.overlay_widget = StreamerOverlayWidget()
                self.overlay_widget.set_character_name(self.get_character_name())
            else:
                self.overlay_widget.set_character_name(self.get_character_name())
                self.overlay_widget._update_stats_display()
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

    def start_session(self, session_id: str, activity_type: str, session_start_time: Optional[datetime] = None):
        """Start a new session"""
        logger.info(f"[OVERLAY_CONTROLLER] start_session called: session_id={session_id}, activity_type={activity_type}")
        if self.overlay_widget:
            self.overlay_widget.start_session(session_id, activity_type, session_start_time)
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
        logger.info(f"[OVERLAY_CONTROLLER] Event forwarded to overlay widget")

    def update_weapon(self, weapon_name: str, amp: str = "", decay: str = ""):
        """Update weapon display"""
        self.current_weapon = weapon_name
        if self.overlay_widget:
            self.overlay_widget.update_weapon(weapon_name, amp, decay)

    def set_cost_per_attack(self, cost: float):
        """Set the cost per attack for calculating total spent"""
        if self.overlay_widget:
            self.overlay_widget.set_cost_per_attack(cost)
        logger.info(f"SessionOverlay set cost per attack: {cost}")
