"""
Tabbed MainWindow for LewtNanny
Implements the detailed UI specification with custom tab bar and persistent bottom control bar
"""

import sys
import asyncio
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from decimal import Decimal

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QTabWidget,
    QTextEdit,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
    QGroupBox,
    QFrame,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QFileDialog,
    QStatusBar,
    QFrame,
    QProgressBar,
    QMessageBox,
    QToolBar,
    QToolButton,
    QDockWidget,
    QStackedWidget,
    QLineEdit,
    QGraphicsDropShadowEffect,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtGui import (
    QFont,
    QAction,
    QIcon,
    QColor,
    QPixmap,
    QPainter,
    QRadialGradient,
)

from src.models.models import ActivityType, EventType
from src.ui.overlay import SessionOverlay
from src.ui.components.config_tab import ConfigTab
from src.ui.components.combat_tab import CombatTabWidget
from src.services.game_data_service import GameDataService
from src.ui.components.crafting_tab import CraftingTabWidget
from src.ui.components.weapon_selector import WeaponSelector
from src.services.cost_calculation_service import CostCalculationService

# Import extracted components
from src.ui.components.status_indicator import StatusIndicator
from src.ui.layout.main_layout_creator import MainLayoutCreator
from src.ui.tabs.loot_tab_creator import LootTabCreator
from src.ui.tabs.skills_tab_creator import SkillsTabCreator
from src.ui.managers.session_manager import SessionManager
from src.ui.managers.cost_manager import CostManager

logger = logging.getLogger(__name__)


class TabbedMainWindow(QMainWindow):
    """Main application window with custom tab bar and persistent bottom control bar"""

    TAB_NAMES = ["Loot", "Analysis", "Skills", "Combat", "Crafting", "Twitch", "Config"]

    def __init__(self, db_manager, config_manager):
        super().__init__()

        self.db_manager = db_manager
        self.config_manager = config_manager
        self.chat_reader = None
        self.overlay: Optional[SessionOverlay] = None
        self.current_session_id: Optional[str] = None
        self.current_session_start: Optional[datetime] = None
        self.current_theme = "dark"
        self.is_logging_paused = False

        # Total cost calculation tracking
        self.total_shots_taken = 0
        self.cost_per_attack = 0.0

        self.setWindowTitle("LewtNanny - Entropia Universe Loot Tracker")
        self.setGeometry(100, 100, 1000, 650)

        logger.info("TabbedMainWindow initializing...")

        # Initialize managers
        self.session_manager = SessionManager(self)
        self.cost_manager = CostManager(self)

        # Initialize UI creators
        self.layout_creator = MainLayoutCreator(self)
        self.loot_tab_creator = LootTabCreator(self)
        self.skills_tab_creator = SkillsTabCreator(self)

        self.setup_ui()
        self.setup_menubar()
        self.setup_status_bar()
        self.setup_timer()

        # Initialize overlay early so it can receive events
        self.overlay = SessionOverlay(self.db_manager, self.config_manager)
        logger.info("TabbedMainWindow initialization complete")

    def setup_ui(self):
        """Setup main UI with custom tab bar and bottom control bar"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Create layout components
        self.tab_bar_frame = self.layout_creator.create_top_tab_bar()
        self.main_layout.addWidget(self.tab_bar_frame)

        self.content_stack = self.create_middle_content_area()
        self.main_layout.addWidget(self.content_stack, 1)

        self.bottom_bar_frame = self.layout_creator.create_bottom_control_bar()
        self.main_layout.addWidget(self.bottom_bar_frame)

        logger.debug("Main UI setup complete")

        QTimer.singleShot(500, self._load_past_runs_on_startup)

    def on_tab_clicked(self, tab_name: str, button: QPushButton):
        """Handle tab button click"""
        self.content_stack.setCurrentIndex(self.TAB_NAMES.index(tab_name))

        for name, btn in self.tab_buttons.items():
            if name == tab_name:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #238636;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 4px 4px 0 0;
                        padding: 6px 16px;
                        font-weight: bold;
                        font-size: 11px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #8B949E;
                        border: none;
                        border-radius: 4px 4px 0 0;
                        padding: 6px 16px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #21262D;
                        color: #E6EDF3;
                    }
                """)

        # Update blueprint dropdown when switching to crafting tab
        if tab_name == "Crafting" and hasattr(self, "crafting_tab"):
            # Use a timer to ensure the widget is fully visible
            QTimer.singleShot(
                100, lambda: self.crafting_tab.update_blueprint_dropdown()
            )

        logger.debug(f"Switched to tab: {tab_name}")

    def create_middle_content_area(self):
        """Create middle content area that changes based on selected tab"""
        self.content_stack = self.layout_creator.create_middle_content_area()

        # Now create all tabs and add them to the content stack
        self.create_loot_tab()
        self.create_analysis_tab()
        self.create_skills_tab()
        self.create_combat_tab()
        self.create_crafting_tab()
        self.create_twitch_tab()
        self.create_config_tab()

        return self.content_stack

    def create_loot_tab(self):
        """Create the Loot tab"""
        loot_widget = self.loot_tab_creator.create_loot_tab()
        self.content_stack.addWidget(loot_widget)
        logger.info("Loot tab created")

    def create_analysis_tab(self):
        """Create the Analysis tab with 2 core charts"""
        from src.ui.components.simple_analysis import SimpleAnalysisWidget

        analysis_widget = SimpleAnalysisWidget()
        analysis_widget.set_db_manager(self.db_manager)
        self.analysis_widget = analysis_widget

        self.content_stack.addWidget(analysis_widget)
        logger.info("Analysis tab created with 2 core charts")

    def create_skills_tab(self):
        """Create the Skills tab with skill gain tracking"""
        skills_widget = self.skills_tab_creator.create_skills_tab()
        self.skills_tab = skills_widget
        self.content_stack.addWidget(skills_widget)
        logger.info("Skills tab created")

    def create_combat_tab(self):
        """Create the Combat tab"""
        combat_widget = CombatTabWidget(self.db_manager)
        self.combat_tab = combat_widget
        self.combat_widget = combat_widget  # Store reference for session management
        self.content_stack.addWidget(combat_widget)
        logger.info("Combat tab created")

    def create_crafting_tab(self):
        """Create the Crafting tab"""
        crafting_widget = CraftingTabWidget(self.db_manager)
        self.crafting_tab = crafting_widget
        self.crafting_widget = crafting_widget  # Store reference for session management
        crafting_widget.add_crafting_cost.connect(self._on_crafting_cost_added)

        # Start with "Add to Session" button disabled (no active session)
        crafting_widget.set_session_active(False)

        self.content_stack.addWidget(crafting_widget)
        logger.info("Crafting tab created")

    def create_twitch_tab(self):
        """Create the Twitch tab"""
        from src.services.twitch_bot import TwitchBotUI

        twitch_widget = QWidget()
        twitch_layout = QVBoxLayout(twitch_widget)
        twitch_layout.setContentsMargins(8, 8, 8, 8)
        twitch_layout.setSpacing(8)

        config_panel = TwitchBotUI.create_config_panel()
        twitch_layout.addWidget(config_panel)

        self.twitch_status_label = QLabel("Twitch Bot: Disconnected")
        self.twitch_status_label.setStyleSheet("color: #8B949E; font-size: 12px;")
        twitch_layout.addWidget(self.twitch_status_label)

        twitch_layout.addStretch()

        self.content_stack.addWidget(twitch_widget)
        logger.info("Twitch tab created")

    def create_config_tab(self):
        """Create the Config tab using the new ConfigTab widget"""
        self.config_widget = ConfigTab(config_manager=self.config_manager)
        self.content_stack.addWidget(self.config_widget)
        self.config_widget.signals.loadout_changed.connect(self._on_loadout_changed)
        self.config_widget.signals.stats_calculated.connect(self._on_stats_calculated)

        # Initialize cost per attack for the current loadout
        self.cost_per_attack = self._calculate_cost_per_attack()
        logger.info(
            f"Config tab created using ConfigTab, initial cost per attack: {self.cost_per_attack:.6f} PED"
        )
        if self.overlay:
            self.overlay.set_cost_per_attack(self.cost_per_attack)

    # Delegate to managers
    def toggle_session(self):
        """Toggle session start/stop"""
        self.session_manager.toggle_session()

    def toggle_pause_logging(self):
        """Pause or resume logging"""
        self.session_manager.toggle_pause_logging()

    def _check_and_update_cost(self):
        """Check if cost per attack needs to be recalculated"""
        self.cost_manager.check_and_update_cost()

    def _calculate_cost_per_attack(self) -> float:
        """Calculate cost per attack from the active loadout"""
        return self.cost_manager.calculate_cost_per_attack()

    def _update_total_cost_display(self):
        """Update the total cost display based on shots taken and cost per attack"""
        self.cost_manager.update_total_cost_display()

    def _on_crafting_cost_added(self, cost: float):
        """Handle crafting cost added"""
        self.cost_manager.on_crafting_cost_added(cost)

    def _on_stats_calculated(self, total_cost: float):
        """Handle stats calculation completion"""
        self.cost_manager.on_stats_calculated(total_cost)

    def add_skill_event(self, event_data: Dict[str, Any]):
        """Add a skill event to the skills tab"""
        self.skills_tab_creator.add_skill_event(event_data)

    def _on_loadout_changed(self):
        """Handle loadout changed"""
        try:
            if hasattr(self, "config_widget") and self.config_widget:
                active_loadout = self.config_widget.active_loadout_combo.currentData()
                if active_loadout:
                    for loadout in self.config_widget._loadouts:
                        if loadout.id == active_loadout:
                            if self.overlay:
                                self.overlay.update_weapon(
                                    loadout.weapon,
                                    loadout.amplifier or "",
                                    f"{loadout.damage_enh * 0.1:.3f}"
                                    if loadout.damage_enh
                                    else "",
                                )
                            logger.info(
                                f"Loadout changed to: {loadout.weapon} - waiting for stats calculation to sync cost"
                            )
                            break
        except Exception as e:
            logger.error(f"Error handling loadout change: {e}")

    # Keep the remaining methods that were not extracted
    def setup_menubar(self):
        """Setup menubar"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #161B22;
                color: #E6EDF3;
                border-bottom: 1px solid #30363D;
            }
            QMenuBar::item:selected {
                background-color: #30363D;
            }
        """)

        file_menu = menubar.addMenu("File")

        export_session_action = QAction("Export Session...", self)
        export_session_action.triggered.connect(self.export_session)
        file_menu.addAction(export_session_action)

        export_all_action = QAction("Export All Sessions...", self)
        export_all_action.triggered.connect(self.export_all_sessions)
        file_menu.addAction(export_all_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        session_menu = menubar.addMenu("Session")

        start_session_action = QAction("Start Session", self)
        start_session_action.triggered.connect(self.start_session)
        session_menu.addAction(start_session_action)

        stop_session_action = QAction("Stop Session", self)
        stop_session_action.triggered.connect(self.stop_session)
        session_menu.addAction(stop_session_action)

        view_menu = menubar.addMenu("View")

        toggle_overlay_action = QAction("Toggle Overlay", self)
        toggle_overlay_action.setShortcut("F12")
        toggle_overlay_action.triggered.connect(self.toggle_overlay)
        view_menu.addAction(toggle_overlay_action)

        theme_action = QAction("Toggle Theme", self)
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)

        view_menu.addSeparator()

        settings_action = QAction("Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        view_menu.addAction(settings_action)

        logger.debug("Menubar setup complete")

    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        logger.debug("Status bar setup complete")

    def setup_timer(self):
        """Setup update timer"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.timeout.connect(self.check_readiness)
        self.update_timer.start(1000)

        # Timer for checking cost per attack calculation
        self.cost_check_timer = QTimer()
        self.cost_check_timer.timeout.connect(self._check_and_update_cost)
        self.cost_check_timer.start(2000)  # Check every 2 seconds

        logger.debug("Timer setup complete")

    def check_readiness(self):
        """Check if all prerequisites are met for starting a run"""
        chat_log_ok = False
        character_name_ok = False
        loadout_ok = False

        chat_path = None
        if hasattr(self, "chat_log_path"):
            chat_path = self.chat_log_path.text().strip()

        if not chat_path:
            try:
                chat_path = self.config_manager.get("chat_monitoring.log_file_path", "")
            except:
                pass

        if not chat_path:
            for i in range(self.content_stack.count()):
                widget = self.content_stack.widget(i)
                if hasattr(widget, "chat_location_text"):
                    chat_path = widget.chat_location_text.text().strip()
                    break

        if chat_path and Path(chat_path).exists():
            chat_log_ok = True

        char_name = None
        for i in range(self.content_stack.count()):
            widget = self.content_stack.widget(i)
            if hasattr(widget, "character_name"):
                char_name = widget.character_name.text().strip()
                break

        if not char_name:
            try:
                char_name = self.config_manager.get("character.name", "")
            except:
                pass

        if char_name:
            character_name_ok = True

        active_loadout = None
        for i in range(self.content_stack.count()):
            widget = self.content_stack.widget(i)
            if hasattr(widget, "active_loadout_combo"):
                active_loadout = widget.active_loadout_combo.currentData()
                break

        if active_loadout:
            loadout_ok = True

        if chat_log_ok and character_name_ok and loadout_ok:
            self.status_indicator.status = "green"
            self.start_run_btn.setEnabled(True)
        elif chat_log_ok and (character_name_ok or loadout_ok):
            self.status_indicator.status = "yellow"
            self.start_run_btn.setEnabled(False)
        else:
            self.status_indicator.status = "red"
            self.start_run_btn.setEnabled(False)

    def update_status(self):
        """Update status periodically"""
        try:
            if self.current_session_id:
                current_time = datetime.now().strftime("%H:%M:%S")
                elapsed = ""
                if self.current_session_start:
                    delta = datetime.now() - self.current_session_start
                    hours, remainder = divmod(int(delta.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    elapsed = f" | Elapsed: {hours:02d}:{minutes:02d}:{seconds:02d}"
                self.status_bar.showMessage(f"Session Active{elapsed}")
            else:
                self.status_bar.showMessage("Ready")

        except Exception as e:
            logger.error(f"Error updating status: {e}")

    def start_session(self):
        """Start a new tracking session"""
        self.session_manager.start_session()

    def stop_session(self):
        """Stop current session"""
        self.session_manager.stop_session()

    def toggle_overlay(self):
        """Toggle overlay visibility"""
        if self.overlay:
            if (
                hasattr(self.overlay, "overlay_widget")
                and self.overlay.overlay_widget
                and self.overlay.overlay_widget.isVisible()
            ):
                self.overlay.hide()
                self.streamer_ui_btn.setText("Show Overlay")
            else:
                self.overlay.show()
                self.streamer_ui_btn.setText("Hide Overlay")

    def toggle_theme(self):
        """Toggle between dark and light theme"""
        if self.current_theme == "dark":
            self.current_theme = "light"
            self.apply_theme("Light")
        else:
            self.current_theme = "dark"
            self.apply_theme("Dark")

    def apply_theme(self, theme_name):
        """Apply the specified theme"""
        logger.info(f"Applying theme: {theme_name}")
        # Theme implementation would go here

    def open_donate(self):
        """Open donation link"""
        import webbrowser

        webbrowser.open("https://example.com/donate")

    def open_settings(self):
        """Open settings dialog"""
        self.content_stack.setCurrentIndex(self.TAB_NAMES.index("Config"))
        tab_button = self.tab_buttons["Config"]
        self.on_tab_clicked("Config", tab_button)

    def export_session(self):
        """Export current session data"""
        if not self.current_session_id:
            QMessageBox.information(self, "Export", "No active session to export.")
            return

        # Export implementation would go here
        logger.info("Export session called")

    def export_all_sessions(self):
        """Export all session data"""
        # Export implementation would go here
        logger.info("Export all sessions called")

    def _load_past_runs_on_startup(self):
        """Load past runs when application starts"""

        def load():
            try:
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    sessions = loop.run_until_complete(
                        self.db_manager.get_all_sessions()
                    )
                    for session in sessions:
                        self._add_run_to_run_log(session)
                    logger.info(f"Loaded {len(sessions)} past runs")
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"Error loading past runs: {e}")

        # Use QTimer to schedule async loading in Qt event loop
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(1000, load)  # Delay 1 second to ensure UI is ready

    def _add_run_to_run_log(self, session: Dict[str, Any]):
        """Add a run entry to run log table"""
        from PyQt6.QtCore import QTimer

        def add_in_gui_thread():
            row = self.run_log_table.rowCount()
            self.run_log_table.insertRow(row)

            start_time = session.get("start_time", "")
            if isinstance(start_time, str):
                try:
                    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    start_time = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass

            duration = ""
            end_time = session.get("end_time")
            if end_time:
                if isinstance(end_time, str):
                    try:
                        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                        start_dt = datetime.fromisoformat(
                            session.get("start_time", "").replace("Z", "+00:00")
                        )
                        delta = end_dt - start_dt
                        hours, remainder = divmod(int(delta.total_seconds()), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    except:
                        duration = "-"
                else:
                    delta = end_time - session.get("start_time", datetime.now())
                    hours, remainder = divmod(int(delta.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                duration = "-"

            total_cost = session.get("total_cost", 0) or 0
            total_return = session.get("total_return", 0) or 0
            roi = (total_return / total_cost * 100) if total_cost > 0 else 0

            self.run_log_table.setItem(row, 0, QTableWidgetItem("Completed"))
            self.run_log_table.setItem(row, 1, QTableWidgetItem(start_time))
            self.run_log_table.setItem(row, 2, QTableWidgetItem(duration))
            self.run_log_table.setItem(row, 3, QTableWidgetItem(f"{total_cost:.2f}"))
            self.run_log_table.setItem(row, 4, QTableWidgetItem(f"{total_return:.2f}"))
            self.run_log_table.setItem(row, 5, QTableWidgetItem(f"{roi:.1f}%"))
            self.run_log_table.setItem(row, 6, QTableWidgetItem("-"))

            self.run_log_table.item(row, 0).setData(
                Qt.ItemDataRole.UserRole, session["id"]
            )

            # Get item count for this session
            def load_item_count():
                try:
                    import asyncio

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        items = loop.run_until_complete(
                            self.db_manager.get_session_loot_items(session["id"])
                        )
                        item_count = len(items)
                        self.run_log_table.setItem(
                            row, 6, QTableWidgetItem(str(item_count))
                        )
                    finally:
                        loop.close()
                except Exception as e:
                    logger.error(
                        f"Error loading item count for session {session['id']}: {e}"
                    )

            QTimer.singleShot(100, load_item_count)

        # Schedule GUI update in main thread
        QTimer.singleShot(0, add_in_gui_thread)

    def _on_run_log_selection_changed(self):
        """Handle run log table selection change"""
        selected_rows = self.run_log_table.selectedItems()
        if not selected_rows:
            self._clear_session_specific_data()
            return

        row = selected_rows[0].row()
        session_id = self.run_log_table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        if not session_id:
            self._clear_session_specific_data()
            return

        if session_id == "current":
            self._update_item_breakdown_current_run()
            self._load_current_session_summary()
            self._update_current_session_tabs()
        else:
            self._load_session_data(session_id)

    def _clear_session_specific_data(self):
        """Clear session-specific displays"""
        self.item_breakdown_table.setRowCount(0)
        if hasattr(self, "skills_table"):
            self.skills_table.setRowCount(0)

        # Clear combat tab
        if hasattr(self, "combat_tab") and self.combat_tab:
            self.combat_tab.load_session_combat_data([])

        # Reset analysis tab to show all sessions
        if hasattr(self, "analysis_widget") and self.analysis_widget:
            # Trigger reload of all session data
            import threading

            def reload_analysis():
                import asyncio

                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.analysis_widget.load_data())
                    loop.close()
                except:
                    pass

            threading.Thread(target=reload_analysis, daemon=True).start()

    def _update_item_breakdown_current_run(self):
        """Current run item breakdown is already live-updated, no need to change"""
        # The item breakdown table is populated in real-time via _process_loot_event
        # For current run selection, just leave it as is
        pass

    def _load_current_session_summary(self):
        """Load current session summary (already displayed)"""
        # Current session summary is already live-upgraded
        pass

    def _update_current_session_tabs(self):
        """Update other tabs to show current session data"""
        # Reset skills tab - current session skills are already being added in real-time
        # So we don't need to reload them

        # Reset combat tab to show live session stats
        if hasattr(self, "combat_tab") and self.combat_tab:
            self.combat_tab.load_combat_data()

        # Reset analysis tab to show all sessions including current
        if hasattr(self, "analysis_widget") and self.analysis_widget:
            # Trigger reload of all session data
            import threading

            def reload_analysis():
                import asyncio

                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.analysis_widget.load_data())
                    loop.close()
                except:
                    pass

            threading.Thread(target=reload_analysis, daemon=True).start()

    def _load_session_data(self, session_id: str):
        """Load all session data: item breakdown and summary"""

        def load_in_background():
            import asyncio

            try:
                # Create new event loop for background thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def load_session_async():
                    self.item_breakdown_table.setRowCount(0)

                    # Load item breakdown
                    items = await self.db_manager.get_session_loot_items(session_id)
                    for item in items:
                        row = self.item_breakdown_table.rowCount()
                        self.item_breakdown_table.insertRow(row)
                        self.item_breakdown_table.setItem(
                            row, 0, QTableWidgetItem(item["item_name"])
                        )
                        self.item_breakdown_table.setItem(
                            row, 1, QTableWidgetItem(str(item["quantity"]))
                        )
                        item_value = (
                            item["total_value"] / item["quantity"]
                            if item["quantity"] > 0
                            else 0
                        )
                        self.item_breakdown_table.setItem(
                            row, 2, QTableWidgetItem(f"{item_value:.4f}")
                        )
                        self.item_breakdown_table.setItem(
                            row, 3, QTableWidgetItem(f"{item['markup_percent']:.0f}%")
                        )
                        self.item_breakdown_table.setItem(
                            row, 4, QTableWidgetItem(f"{item['total_value']:.4f}")
                        )

                    # Load session summary
                    sessions = await self.db_manager.get_all_sessions()
                    session_data = next(
                        (s for s in sessions if s["id"] == session_id), None
                    )
                    if session_data:
                        total_cost = session_data.get("total_cost", 0) or 0
                        total_return = session_data.get("total_return", 0) or 0
                        return_pct = (
                            (total_return / total_cost * 100) if total_cost > 0 else 0
                        )

                        # Update summary labels
                        self.loot_summary_labels["Total Cost"].setText(
                            f"{total_cost:.2f} PED"
                        )
                        self.loot_summary_labels["Total Return"].setText(
                            f"{total_return:.2f} PED"
                        )
                        self.loot_summary_labels["% Return"].setText(
                            f"{return_pct:.1f}%"
                        )

                        # Load and update creatures, globals, and HOFs counts
                        counts = await self.db_manager.get_session_counts(session_id)
                        self.loot_summary_labels["Creatures Looted"].setText(
                            str(counts["creatures"])
                        )
                        self.loot_summary_labels["Globals"].setText(
                            str(counts["globals"])
                        )
                        self.loot_summary_labels["HOFs"].setText(str(counts["hofs"]))

                    # Load skills data
                    skill_events = await self.db_manager.get_session_skills(session_id)
                    self.skills_tab_creator.load_session_skills(skill_events)

                    # Load combat data
                    combat_events = await self.db_manager.get_session_combat_events(
                        session_id
                    )
                    if hasattr(self, "combat_tab") and self.combat_tab:
                        self.combat_tab.load_session_combat_data(combat_events)

                    # Update analysis tab with specific session data
                    if hasattr(self, "analysis_widget") and self.analysis_widget:
                        self.analysis_widget.load_specific_session(session_data)

                # Run the async function in this thread's event loop
                loop.run_until_complete(load_session_async())

            except Exception as e:
                logger.error(f"Error loading session data: {e}")
            finally:
                try:
                    loop.close()
                except:
                    pass

        # Run in background thread to avoid blocking UI
        import threading

        threading.Thread(target=load_in_background, daemon=True).start()

    def on_item_breakdown_header_clicked(self, column):
        """Handle item breakdown header click for sorting"""
        if column == 1:  # Count column
            self.item_breakdown_table.sortItems(column, self.item_breakdown_sort_order)
            self.item_breakdown_sort_order = (
                Qt.SortOrder.DescendingOrder
                if self.item_breakdown_sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )

    def _process_loot_event(self, parsed_data: Dict[str, Any]):
        """Process loot event and add to item breakdown"""
        item_name = parsed_data.get("item_name", "")
        quantity = parsed_data.get("quantity", 1)
        total_value = parsed_data.get("value", 0.0)

        if not item_name:
            return

        # Calculate item value (absolute value for display)
        item_value = abs(total_value) / quantity if quantity > 0 else 0
        markup_percent = 0

        # For spent items (negative total_value), adjust display
        display_value = total_value
        if total_value < 0:
            display_value = -abs(total_value)  # Keep negative for spent items

        found = False
        for row in range(self.item_breakdown_table.rowCount()):
            if self.item_breakdown_table.item(row, 0).text() == item_name:
                current_count = int(self.item_breakdown_table.item(row, 1).text())
                current_total = float(self.item_breakdown_table.item(row, 4).text())

                # For spent items, add to count and adjust total
                new_count = current_count + quantity
                new_total = current_total + display_value

                self.item_breakdown_table.setItem(
                    row, 1, QTableWidgetItem(str(new_count))
                )
                self.item_breakdown_table.setItem(
                    row, 2, QTableWidgetItem(f"{item_value:.4f}")
                )
                self.item_breakdown_table.setItem(
                    row, 4, QTableWidgetItem(f"{new_total:.4f}")
                )
                found = True
                break

        if not found:
            row = self.item_breakdown_table.rowCount()
            self.item_breakdown_table.insertRow(row)
            self.item_breakdown_table.setItem(row, 0, QTableWidgetItem(item_name))
            self.item_breakdown_table.setItem(row, 1, QTableWidgetItem(str(quantity)))
            self.item_breakdown_table.setItem(
                row, 2, QTableWidgetItem(f"{item_value:.4f}")
            )
            self.item_breakdown_table.setItem(
                row, 3, QTableWidgetItem(f"{markup_percent}%")
            )
            self.item_breakdown_table.setItem(
                row, 4, QTableWidgetItem(f"{display_value:.4f}")
            )

        if self.current_session_id:
            self.db_manager.save_session_loot_item_sync(
                self.current_session_id,
                item_name,
                quantity,
                total_value,
                markup_percent,
            )

    def _refresh_analysis_data(self):
        """Refresh analysis data"""
        if hasattr(self, "analysis_widget") and self.analysis_widget:
            self.analysis_widget.refresh()

    def _update_analysis_realtime(self):
        """Update analysis in real-time"""
        if hasattr(self, "analysis_widget") and self.analysis_widget:
            self.analysis_widget.update_realtime()

    def handle_new_event(self, event_data: Dict[str, Any]):
        """Handle new events from chat reader - update all UI components"""
        if not event_data:
            logger.warning("[UI] ERROR: Received empty event data!")
            return

        event_type = event_data.get("event_type", "unknown")
        raw_message = event_data.get("raw_message", "")
        parsed_data = event_data.get("parsed_data", {})
        session_id = event_data.get("session_id", "None")

        # Save event to database if we have an active session
        if self.current_session_id and hasattr(self, "db_manager"):
            # Add session_id to event data if not present
            if (
                not event_data.get("session_id")
                or event_data.get("session_id") == "None"
            ):
                event_data["session_id"] = self.current_session_id

            # Save event asynchronously in background
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create a task
                    asyncio.create_task(self.db_manager.add_event(event_data))
                else:
                    # If no running loop, run in thread
                    import threading

                    def save_event():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            new_loop.run_until_complete(
                                self.db_manager.add_event(event_data)
                            )
                        finally:
                            new_loop.close()

                    threading.Thread(target=save_event, daemon=True).start()
            except Exception as e:
                logger.error(f"Error saving event to database: {e}")

        # Update Overlay
        if self.overlay:
            self.overlay.add_event(event_data)

        # Update Combat Tab
        if hasattr(self, "combat_widget") and self.combat_widget:
            self.combat_widget.add_combat_event(event_data)

        # Update Skills Tab
        if event_type in ["skill_gain", "skill"]:
            self.add_skill_event(event_data)

        # Update Loot Tab
        if event_type in ["loot", "global", "hof"]:
            self._process_event_for_summary(event_type, parsed_data, raw_message)
            if event_type == "loot":
                self._process_loot_event(parsed_data)

        # Update Analysis Tab in real-time
        self._update_analysis_realtime()

    def _process_event_for_summary(
        self, event_type: str, parsed_data: Dict[str, Any], raw_message: str = ""
    ):
        """Process events for the summary section"""
        if event_type == "loot":
            # Update creatures looted count
            current = int(self.loot_summary_labels["Creatures Looted"].text())
            self.loot_summary_labels["Creatures Looted"].setText(str(current + 1))

            # Update total return
            value = parsed_data.get("value", 0)
            current_return = float(
                self.loot_summary_labels["Total Return"]
                .text()
                .replace(",", "")
                .split()[0]
            )
            new_return = current_return + value
            self.loot_summary_labels["Total Return"].setText(f"{new_return:.2f} PED")

            # Update % return
            current_cost = float(
                self.loot_summary_labels["Total Cost"]
                .text()
                .replace(",", "")
                .split()[0]
            )
            if current_cost > 0:
                return_pct = (new_return / current_cost) * 100
                self.loot_summary_labels["% Return"].setText(f"{return_pct:.1f}%")

        elif event_type == "global":
            current = int(self.loot_summary_labels["Globals"].text())
            self.loot_summary_labels["Globals"].setText(str(current + 1))

        elif event_type == "hof":
            current = int(self.loot_summary_labels["HOFs"].text())
            self.loot_summary_labels["HOFs"].setText(str(current + 1))

    # ... (add any missing methods from the original file)
