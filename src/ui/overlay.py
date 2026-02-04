"""Streamer Overlay for LewtNanny
Transparent, always-on-top overlay for live session stats streaming
"""

import logging
import os
from datetime import datetime
from decimal import Decimal
from typing import Any

from PyQt6.QtCore import QPoint, Qt, QThread, QTimer
from PyQt6.QtGui import (
    QFont,
    QGuiApplication,
    QPainter,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class BorderlessLabel(QLabel):
    """Custom QLabel with guaranteed no borders"""

    def __init__(self, text=""):
        super().__init__(text)
        self.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                outline: none;
                padding: 0px;
                margin: 0px;
            }
        """)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFrameStyle(QFrame.Shape.NoFrame | QFrame.Shadow.Plain)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, a0):
        # Override to ensure no borders are drawn
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(Qt.GlobalColor.transparent))
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)

        # Draw text
        painter.setPen(QPen(self.palette().color(self.palette().ColorRole.Text)))
        painter.drawText(self.rect(), self.alignment(), self.text())
        painter.end()


class ScreenshotWorker(QThread):
    """Background worker to take screenshot after delay"""

    def __init__(
        self,
        delay_ms: int,
        screenshot_dir: str,
        event_type: str,
        value: float,
        player: str,
    ):
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
            filename = (
                f"{self.event_type}_{self.player}_{self.value:.2f}ped_{timestamp}.png"
            )
            filepath = os.path.join(self.screenshot_dir, filename)

            pixmap = screen.grabWindow(0)
            pixmap.save(filepath)
            logger.info(f"[OVERLAY] Screenshot saved: {filepath}")
        except Exception as e:
            logger.error(f"[OVERLAY] Error taking screenshot: {e}")


class DraggableLogoLabel(QLabel):
    """Custom QLabel that can drag the overlay window"""

    def __init__(self, overlay_widget):
        super().__init__(None)
        self.overlay_widget = overlay_widget
        self.dragging = False
        self.drag_position = QPoint()

    def mousePressEvent(self, ev):
        """Logo mouse press - acts as drag handle"""
        if ev.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = (
                ev.globalPosition().toPoint() - self.overlay_widget.pos()
            )
            ev.accept()

    def mouseMoveEvent(self, ev):
        """Logo mouse move - dragging functionality"""
        if ev.buttons() == Qt.MouseButton.LeftButton and self.dragging:
            new_pos = ev.globalPosition().toPoint() - self.drag_position
            self.overlay_widget.move(new_pos)
            self.overlay_widget.update_logo_position()
            ev.accept()

    def mouseReleaseEvent(self, ev):
        """Logo mouse release - stop dragging"""
        if ev.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            ev.accept()


class StreamerOverlayWidget(QWidget):
    """Draggable, transparent overlay widget for streaming"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        self.dragging = False
        self.drag_position = QPoint()
        self.resizing = False
        self.resize_start_pos = QPoint()
        self.resize_start_size = None
        self.character_name = ""

        self._stats = {
            "globals": 0,
            "hofs": 0,
            "items": 0,
            "kills": 0,
            "wasted_shots": 0,
            "total_cost": Decimal("0"),
            "total_return": Decimal("0"),
        }
        self._shots_taken = 0
        self._cost_per_attack = Decimal("0")
        self._recent_loot_times = []  # Track timestamps of recent loot events for grouping

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
        self.resize(210, 420)  # Use resize instead of setFixedSize to allow resizing
        self.move(100, 100)

        # Create resize handle
        self.resize_handle = QLabel(self)
        self.resize_handle.setText("⋮")
        self.resize_handle.setFixedSize(15, 15)
        self.resize_handle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.resize_handle.setStyleSheet("""
            QLabel {
                color: rgba(200, 200, 200, 150);
                background: rgba(100, 100, 100, 100);
                border: 1px solid rgba(150, 150, 150, 100);
                border-radius: 3px;
            }
            QLabel:hover {
                color: rgba(255, 255, 255, 200);
                background: rgba(150, 150, 150, 150);
            }
        """)
        self.resize_handle.setCursor(Qt.CursorShape.SizeFDiagCursor)

        # Position resize handle at bottom right corner
        self.update_resize_handle_position()

        # Create the container box
        container = QFrame(self)
        container.setGeometry(0, 110, 210, 240)  # Set to 110 as requested
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 20, 30, 200);
                border: 1px solid rgba(60, 60, 80, 180);
            }
        """)
        self.container = container

        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.create_main_display(layout)

        # Add logo on top of the container
        self.create_logo_display()

        self.session_start_time = None
        self.session_active = False

    def showEvent(self, a0):
        """Handle show event to show logo"""
        super().showEvent(a0)
        if hasattr(self, "logo_label"):
            self.logo_label.show()

    def hideEvent(self, a0):
        """Handle hide event to hide logo"""
        super().hideEvent(a0)
        if hasattr(self, "logo_label"):
            self.logo_label.hide()

    def closeEvent(self, a0):
        """Handle close event to close logo"""
        if hasattr(self, "logo_label"):
            self.logo_label.close()
        super().closeEvent(a0)

    def update_resize_handle_position(self):
        """Update resize handle position to bottom right corner"""
        if hasattr(self, "resize_handle"):
            handle_size = 15
            window_size = self.size()
            x = window_size.width() - handle_size - 2
            y = window_size.height() - handle_size - 2
            self.resize_handle.move(x, y)

    def create_logo_display(self):
        """Create logo display on top of the container"""
        import os

        # Get the path to the logo image
        logo_path = r"C:\Users\sutto\LewtNanny\LewtNanny.png"

        # Create logo as independent draggable widget
        self.logo_label = DraggableLogoLabel(self)
        self.logo_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.logo_label.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.logo_label.setStyleSheet("border: none; background: transparent;")
        self.logo_label.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        # Store logo dimensions and position
        self.logo_width = 250
        self.logo_height = 160
        logo_y = 20  # Position at the top

        # Set logo geometry relative to main window
        main_pos = self.pos()
        self.logo_label.setGeometry(
            main_pos.x() + 0, main_pos.y() + logo_y, self.logo_width, self.logo_height
        )

        if os.path.exists(logo_path):
            logger.debug(f"[OVERLAY] Loading logo from: {logo_path}")
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.logo_width,
                    self.logo_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                scaled_pixmap.setMask(scaled_pixmap.createHeuristicMask())
                self.logo_label.setPixmap(scaled_pixmap)
                logger.debug("[OVERLAY] Logo loaded successfully")
            else:
                logger.error(f"[OVERLAY] Failed to load pixmap from: {logo_path}")
        else:
            logger.error(f"[OVERLAY] Logo file not found at: {logo_path}")

        # Show logo initially
        if hasattr(self, "logo_label"):
            self.logo_label.show()

    def create_main_display(self, layout):
        """Create main display with improved hierarchy and design"""
        # Header with context
        header_layout = QHBoxLayout()
        header_layout.addStretch()

        self.live_label = QLabel("● LIVE SESSION")
        self.live_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self.live_label.setStyleSheet("color: #00ff00;")
        self.live_label.setVisible(False)
        header_layout.addWidget(self.live_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Primary metric: large return percentage
        self.return_percentage_label = BorderlessLabel("100.00%")
        self.return_percentage_label.setFont(QFont("Consolas", 28))
        self.return_percentage_label.setStyleSheet("color: #00ff00;")
        self.return_percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.return_percentage_label)

        # Kills stat
        self.kills_label = QLabel("Loots: 0")
        self.kills_label.setFont(QFont("Consolas", 12))
        self.kills_label.setStyleSheet("color: #ffffff; border: none;")
        self.kills_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.kills_label)

        # Financial stats vertically
        self.total_return_label = QLabel("Return: 0.000 PED")
        self.total_return_label.setFont(QFont("Consolas", 10))
        self.total_return_label.setStyleSheet("color: #00ff00; border: none;")
        self.total_return_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.total_return_label)

        self.total_spent_label = QLabel("Spent: 0.00 PED")
        self.total_spent_label.setFont(QFont("Consolas", 10))
        self.total_spent_label.setStyleSheet("color: #ff6b6b; border: none;")
        self.total_spent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.total_spent_label)

        # Session Timer at bottom
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setFont(QFont("Consolas", 9))
        self.timer_label.setStyleSheet("color: #888888; border: none;")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.timer_label)

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

    def start_session(
        self,
        session_id: str,
        activity_type: str,
        session_start_time: datetime | None = None,
    ):
        """Start a new session"""
        logger.info(
            f"[OVERLAY] start_session called: session_id={session_id}, activity_type={activity_type}"
        )
        logger.info(f"[OVERLAY] Previous stats before reset: {dict(self._stats)}")

        self.session_start_time = (
            session_start_time if session_start_time else datetime.now()
        )

        # Only reset stats if this is a new session (not already active)
        if not self.session_active:
            self._stats = {
                "globals": 0,
                "hofs": 0,
                "items": 0,
                "kills": 0,
                "wasted_shots": 0,
                "total_cost": Decimal("0"),
                "total_return": Decimal("0"),
            }
            self._shots_taken = 0
            self._recent_loot_times = []
            logger.info(f"[OVERLAY] Stats reset to: {dict(self._stats)}")

        self.session_active = True
        self.current_session_id = session_id
        self.live_label.setText("● LIVE SESSION")

        self._update_stats_display()
        self.show()
        logger.info(f"Streamer overlay session started: {session_id}")

    def stop_session(self):
        """Stop current session"""
        current_session_id = getattr(self, "current_session_id", None)
        logger.info(
            f"[OVERLAY] stop_session called, session_active={self.session_active}, current_session_id={current_session_id}"
        )
        logger.info(f"[OVERLAY] Stats before stop: {dict(self._stats)}")
        self.session_active = False
        self.session_start_time = None
        self.timer_label.setText("00:00:00")
        self.live_label.setVisible(False)
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
        cost = self._stats.get("total_cost", Decimal("0"))
        return_val = self._stats.get("total_return", Decimal("0"))
        kills = self._stats.get("kills", 0)

        if cost > 0:
            return_pct = (return_val / cost) * 100
            return_pct_str = f"{float(return_pct):.2f}%"
        else:
            return_pct = 100.0
            return_pct_str = "100.00%"

        logger.debug(
            f"[OVERLAY] Display update: {return_pct_str} return, spent={float(cost):.2f} PED, return={float(return_val):.3f} PED, kills={kills}"
        )

        # Update percentage with dynamic color
        self.return_percentage_label.setText(return_pct_str)
        color = self._get_return_color(return_pct)
        self.return_percentage_label.setStyleSheet(f"color: {color};")

        self.kills_label.setText(f"Loots: {kills}")

        if float(cost) > 0:
            self.total_spent_label.setText(f"Spent: {float(cost):.2f} PED")
        else:
            self.total_spent_label.setText("Spent: 0.00 PED")

        if float(return_val) > 0:
            self.total_return_label.setText(f"Return: {float(return_val):.2f} PED")
        else:
            self.total_return_label.setText("Return: 0.000 PED")

    def _schedule_screenshot(self, event_type: str, value: float, player: str):
        """Schedule a screenshot for global/HOF events"""
        try:
            from src.services.config_manager import ConfigManager

            config = ConfigManager()

            screenshot_enabled = config.get("screenshot.enabled", True)
            if not screenshot_enabled:
                logger.debug("[OVERLAY] Screenshots disabled, skipping")
                return

            screenshot_dir = config.get(
                "screenshot.directory", "~/Documents/LewtNanny/"
            )
            screenshot_dir = os.path.expanduser(screenshot_dir)

            delay_ms = int(config.get("screenshot.delay_ms", 500))

            logger.info(
                f"[OVERLAY] Scheduling screenshot in {delay_ms}ms for {event_type}: {player} got {value} PED"
            )

            worker = ScreenshotWorker(
                delay_ms, screenshot_dir, event_type, value, player
            )
            worker.start()

        except Exception as e:
            logger.error(f"[OVERLAY] Error scheduling screenshot: {e}")

    def update_stats(self, stats: dict[str, Any]):
        """Update statistics from external source"""
        for key, value in stats.items():
            if key == "globals":
                self._stats["globals"] = value
            elif key == "hofs":
                self._stats["hofs"] = value
            elif key == "items":
                self._stats["items"] = value
            elif key == "total_cost":
                self._stats["total_cost"] = Decimal(str(value))
            elif key == "total_return":
                self._stats["total_return"] = Decimal(str(value))
        self._update_stats_display()

    def add_activity(self, activity: str):
        pass

    def update_weapon(self, weapon_name: str, amp: str = "", decay: str = ""):
        pass

    def add_event(self, event_data: dict[str, Any]):
        """Add event to ticker and update stats"""
        logger.debug("[OVERLAY] ===========================================")
        logger.debug("[OVERLAY] >>> add_event RECEIVED <<<")
        logger.debug(f"[OVERLAY] Event type: {event_data.get('event_type', 'unknown')}")
        logger.debug(f"[OVERLAY] Event data: {event_data}")

        event_type = event_data.get("event_type", "unknown")
        parsed_data = event_data.get("parsed_data", {})

        logger.debug(f"[OVERLAY] Processing event type: {event_type}")
        logger.debug(f"[OVERLAY] Parsed data: {parsed_data}")

        current_return = float(self._stats.get("total_return", Decimal("0")))
        current_cost = float(self._stats.get("total_cost", Decimal("0")))
        logger.debug(
            f"[OVERLAY] Before event - total_return: {current_return:.3f}, total_cost: {current_cost:.3f}"
        )

        if event_type == "loot":
            value = parsed_data.get("value", 0)
            item_name = parsed_data.get("item_name", "")
            timestamp_str = parsed_data.get("timestamp", datetime.now().isoformat())
            loot_time = datetime.fromisoformat(timestamp_str)
            logger.debug(
                f"[OVERLAY] Loot event: value={value}, item={item_name}, time={loot_time}"
            )

            # Check if this loot event is part of a new kill (not within 2 seconds of last loot)
            is_new_kill = True
            current_time = datetime.now()
            # Clean up old loot times (older than 10 seconds)
            self._recent_loot_times = [
                t
                for t in self._recent_loot_times
                if (current_time - t).total_seconds() < 10
            ]
            if self._recent_loot_times:
                time_since_last_loot = (
                    loot_time - self._recent_loot_times[-1]
                ).total_seconds()
                if time_since_last_loot < 0.6:  # Within 0.6 seconds, consider same kill
                    is_new_kill = False
            if is_new_kill:
                self._stats["kills"] = self._stats.get("kills", 0) + 1
                logger.debug(
                    f"[OVERLAY] New kill detected from loot: total kills={self._stats['kills']}"
                )
            self._recent_loot_times.append(loot_time)

            self._stats["items"] = self._stats.get("items", 0) + 1
            self._stats["total_return"] = self._stats.get(
                "total_return", Decimal("0")
            ) + Decimal(str(value))
            new_return = float(self._stats["total_return"])
            logger.debug(
                f"[OVERLAY] Loot event processed: items={self._stats['items']}, adding {value} PED to return, new total_return: {new_return:.3f}"
            )

        elif event_type == "combat":
            damage = parsed_data.get("damage", 0)
            miss = parsed_data.get("miss", False)
            dodge = parsed_data.get("dodged", False)  # When creature dodges your attack
            logger.debug(
                f"[OVERLAY] Combat event: damage={damage}, miss={miss}, dodge={dodge}"
            )

            # Count shots that consume ammo/decay (successful hits + dodged shots)
            should_count_shot = False

            if dodge:
                # Track wasted shots (creature dodged your attack)
                self._stats["wasted_shots"] = self._stats.get("wasted_shots", 0) + 1
                should_count_shot = True
                logger.debug(
                    f"[OVERLAY] Dodged shot detected: total wasted={self._stats['wasted_shots']}"
                )
            elif not miss and damage and float(damage) > 0:
                # Successful hit
                should_count_shot = True
                logger.debug("[OVERLAY] Successful hit")
            else:
                logger.debug(
                    f"[OVERLAY] Combat event skipped (miss or no damage): miss={miss}, damage={damage}"
                )

            # Update cost for shots that consume ammo/decay
            if should_count_shot:
                self._shots_taken += 1
                if self._cost_per_attack > 0:
                    # Add shot cost to existing total (preserves crafting costs)
                    current_cost = float(self._stats.get("total_cost", Decimal("0")))
                    shot_cost_increment = float(self._cost_per_attack)
                    new_total_cost = current_cost + shot_cost_increment
                    self._stats["total_cost"] = Decimal(str(new_total_cost))
                    new_cost = float(self._stats["total_cost"])
                    logger.debug(
                        f"[OVERLAY] Combat event processed: shots={self._shots_taken}, cost_per_attack={float(self._cost_per_attack):.6f}, current_cost={current_cost:.3f}, added_shot_cost={shot_cost_increment:.6f}, new total_cost: {new_cost:.3f}"
                    )
                else:
                    new_cost = float(self._stats.get("total_cost", Decimal("0")))
                    logger.debug(
                        f"[OVERLAY] Combat event processed: shots={self._shots_taken}, cost_per_attack={float(self._cost_per_attack):.6f}, no cost increment, new total_cost: {new_cost:.3f}"
                    )

        elif event_type == "kill":
            # Track successful kills
            self._stats["kills"] = self._stats.get("kills", 0) + 1
            logger.debug(f"[OVERLAY] Kill event: total kills={self._stats['kills']}")

        elif event_type == "global":
            value = parsed_data.get("value", 0)
            player = parsed_data.get("player", "")
            logger.debug(
                f"[OVERLAY] GLOBAL event: value={value}, player={player}, my_character_name={self.character_name}"
            )
            if (
                self.character_name
                and player
                and player.lower() == self.character_name.lower()
            ):
                logger.info(
                    f"[OVERLAY] GLOBAL DETECTED! {player} got {value} PED - scheduling screenshot"
                )
                self._schedule_screenshot("global", value, player)
            else:
                logger.debug(
                    f"[OVERLAY] GLOBAL event skipped (not mine): player={player}, my_character_name={self.character_name}"
                )

        elif event_type == "hof":
            value = parsed_data.get("value", 0)
            player = parsed_data.get("player", "")
            logger.debug(
                f"[OVERLAY] HOF event: value={value}, player={player}, my_character_name={self.character_name}"
            )
            if (
                self.character_name
                and player
                and player.lower() == self.character_name.lower()
            ):
                logger.info(
                    f"[OVERLAY] HOF DETECTED! {player} got {value} PED - scheduling screenshot"
                )
                self._schedule_screenshot("hof", value, player)
            else:
                logger.debug(
                    f"[OVERLAY] HOF event skipped (not mine): player={player}, my_character_name={self.character_name}"
                )

        else:
            logger.debug(
                f"[OVERLAY] Unknown event type: {event_type}, raw_message: {event_data.get('raw_message', 'N/A')}"
            )

        self._update_stats_display()
        logger.debug("[OVERLAY] <<< add_event complete >>>")
        logger.debug(
            f"[OVERLAY] Current stats: globals={self._stats.get('globals')}, hofs={self._stats.get('hofs')}, items={self._stats.get('items')}, total_cost={float(self._stats.get('total_cost', Decimal('0'))):.3f}, total_return={float(self._stats.get('total_return', Decimal('0'))):.3f}"
        )

    def mousePressEvent(self, a0):
        """Mouse press for dragging or resizing"""
        if a0.button() == Qt.MouseButton.LeftButton:
            pos = a0.position().toPoint()

            # Check if click is on resize handle
            if hasattr(
                self, "resize_handle"
            ) and self.resize_handle.geometry().contains(pos):
                self.resizing = True
                self.resize_start_pos = a0.globalPosition().toPoint()
                self.resize_start_size = self.size()
                a0.accept()
            else:
                # Start dragging from anywhere on overlay
                self.dragging = True
                self.drag_position = (
                    a0.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )
                a0.accept()

    def mouseMoveEvent(self, a0):
        """Mouse move for dragging or resizing"""
        if a0.buttons() == Qt.MouseButton.LeftButton:
            if self.resizing:
                # Handle resizing
                global_pos = a0.globalPosition().toPoint()
                delta = global_pos - self.resize_start_pos

                # Allow small resizing - minimum is just for usability
                min_width = 100  # Allow very small width
                min_height = 200  # Allow small height but still usable

                current_size = self.resize_start_size or self.size()
                new_width = max(min_width, current_size.width() + delta.x())
                new_height = max(min_height, current_size.height() + delta.y())

                self.resize(new_width, new_height)
                self.update_resize_handle_position()
                a0.accept()
            elif self.dragging:
                # Handle dragging
                new_pos = a0.globalPosition().toPoint() - self.drag_position
                self.move(new_pos)
                self.update_logo_position()
                a0.accept()

    def mouseReleaseEvent(self, a0):
        """Mouse release to stop dragging or resizing"""
        if a0.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.dragging = False
            a0.accept()

    def update_logo_position(self):
        """Update logo position relative to main window"""
        if hasattr(self, "logo_label") and hasattr(self, "logo_width"):
            window_width = self.size().width()
            logo_x = (window_width - self.logo_width) // 2
            self.logo_label.move(self.pos().x() + logo_x, self.pos().y() + 20)

    def mouseReleaseEvent(self, a0):
        """Mouse release to stop dragging or resizing"""
        if a0.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.resizing = False
            a0.accept()

    def resizeEvent(self, a0):
        """Handle resize event to update container and handle positions"""
        super().resizeEvent(a0)

        # Update container geometry
        if hasattr(self, "container"):
            window_size = self.size()
            self.container.setGeometry(
                0, 110, window_size.width(), window_size.height() - 110
            )

        # Update resize handle position
        self.update_resize_handle_position()

        # Update logo position - always center and maintain full size
        if hasattr(self, "logo_label") and hasattr(self, "logo_width"):
            window_width = self.size().width()
            main_pos = self.pos()

            # Always center the logo, even if it extends beyond window boundaries
            logo_x = (window_width - self.logo_width) // 2

            # Position the logo window independently
            self.logo_label.setGeometry(
                main_pos.x() + logo_x,
                main_pos.y() + 20,
                self.logo_width,
                self.logo_height,
            )


class SessionOverlay:
    """Session overlay controller"""

    def __init__(self, db_manager, config_manager):
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.overlay_widget: StreamerOverlayWidget | None = None
        self.current_weapon = None
        self._stats = {"total_cost": Decimal("0"), "total_return": Decimal("0")}
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

    def start_session(
        self,
        session_id: str,
        activity_type: str,
        session_start_time: datetime | None = None,
    ):
        """Start a new session"""
        logger.info(
            f"[OVERLAY_CONTROLLER] start_session called: session_id={session_id}, activity_type={activity_type}"
        )
        if self.overlay_widget:
            self.overlay_widget.start_session(
                session_id, activity_type, session_start_time
            )
        logger.info(f"SessionOverlay started session: {session_id}")

    def stop_session(self):
        """Stop current session"""
        if self.overlay_widget:
            self.overlay_widget.stop_session()
        logger.info("SessionOverlay stopped session")

    def add_event(self, event_data: dict[str, Any]):
        """Add event to overlay"""
        logger.info(
            f"[OVERLAY_CONTROLLER] add_event called with type: {event_data.get('event_type', 'unknown')}"
        )
        if self.overlay_widget:
            self.overlay_widget.add_event(event_data)
        logger.info("[OVERLAY_CONTROLLER] Event forwarded to overlay widget")

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
