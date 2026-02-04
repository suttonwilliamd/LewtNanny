"""Session management logic for the main window"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QTableWidgetItem

logger = logging.getLogger(__name__)


class SessionManager:
    """Handles session management for the main window"""

    def __init__(self, parent_window):
        self.parent = parent_window

    def toggle_session(self):
        """Toggle session start/stop"""
        if self.parent.current_session_id:
            self.stop_session()
        else:
            self.start_session()

    def start_session(self):
        """Start a new tracking session"""
        try:
            self.parent.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.parent.current_session_start = datetime.now()

            self.parent.start_run_btn.setText("Stop Run")
            self.parent.start_run_btn.setStyleSheet("""
                QPushButton {
                    background-color: #DA3633;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #F04028;
                }
            """)

            self.parent.db_manager.create_session_sync(self.parent.current_session_id, "hunting")

            self._add_current_run_entry()

            self.parent.item_breakdown_table.setRowCount(0)

            self.parent.skills_table.setRowCount(0)
            self.parent.total_skill_gain_value.setText("0.00")

            self.parent.loot_summary_labels["Creatures Looted"].setText("0")
            self.parent.loot_summary_labels["Total Cost"].setText("0.00 PED")
            self.parent.loot_summary_labels["Total Return"].setText("0.00 PED")
            self.parent.loot_summary_labels["% Return"].setText("0.0%")
            self.parent.loot_summary_labels["Globals"].setText("0")
            self.parent.loot_summary_labels["HOFs"].setText("0")

            # Reset shot cost tracking for new session
            self.parent._last_shot_cost = 0

            # Enable crafting "Add to Session" button
            if hasattr(self.parent, "crafting_widget") and self.parent.crafting_widget:
                self.parent.crafting_widget.set_session_active(True)

            # Update combat tab with session info
            if hasattr(self.parent, "combat_widget") and self.parent.combat_widget:
                self.parent.combat_widget.update_session_info(
                    self.parent.current_session_id, self.parent.current_session_start
                )
                self.parent.combat_widget.start_new_session()

            if hasattr(self.parent, "chat_reader") and self.parent.chat_reader:
                chat_path = None
                if hasattr(self.parent, "config_widget") and self.parent.config_widget:
                    if hasattr(self.parent.config_widget, "chat_location_text"):
                        chat_path = self.parent.config_widget.chat_location_text.text().strip()
                elif hasattr(self.parent, "chat_log_path") and self.parent.chat_log_path:
                    chat_path = self.parent.chat_log_path.text().strip()

                if chat_path and Path(chat_path).exists():
                    success = self.parent.chat_reader.start_monitoring(chat_path)
                    if success:
                        self.parent.status_bar.showMessage(
                            f"Session started - Monitoring: {chat_path}"
                        )
                    else:
                        self.parent.status_bar.showMessage(
                            "Session started - Failed to start monitoring"
                        )
                else:
                    self.parent.status_bar.showMessage("Session started - No valid chat.log path")
            else:
                self.parent.status_bar.showMessage("Session started - Chat reader not available")

            if self.parent.overlay:
                self.parent.overlay.start_session(
                    self.parent.current_session_id,
                    "hunting",
                    self.parent.current_session_start,
                )
                self.parent.overlay.set_cost_per_attack(self.parent.cost_per_attack)

            self.parent._refresh_analysis_data()

            logger.info(f"Session started: {self.parent.current_session_id}")
            self.parent.status_bar.showMessage(f"Session started: {self.parent.current_session_id}")

        except Exception as e:
            logger.error(f"Error starting session: {e}", exc_info=True)
            self.parent.status_bar.showMessage(f"Error starting session: {e}")

    def _add_current_run_entry(self):
        """Add a (Current run) entry to the run log"""
        row = 0
        self.parent.run_log_table.insertRow(row)

        start_time = self.parent.current_session_start.strftime("%Y-%m-%d %H:%M")

        self.parent.run_log_table.setItem(row, 0, QTableWidgetItem("(Current run)"))
        self.parent.run_log_table.setItem(row, 1, QTableWidgetItem(start_time))
        self.parent.run_log_table.setItem(row, 2, QTableWidgetItem("-"))
        self.parent.run_log_table.setItem(row, 3, QTableWidgetItem("0.00"))
        self.parent.run_log_table.setItem(row, 4, QTableWidgetItem("0.00"))
        self.parent.run_log_table.setItem(row, 5, QTableWidgetItem("0.0%"))
        self.parent.run_log_table.setItem(row, 6, QTableWidgetItem("0"))

        self.parent.run_log_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, "current")
        self.parent.run_log_table.item(row, 0).setForeground(QColor("#3FB950"))

    def stop_session(self):
        """Stop current session"""
        try:
            if self.parent.current_session_id:
                session_id = self.parent.current_session_id

                if hasattr(self.parent, "chat_reader") and self.parent.chat_reader:
                    self.parent.chat_reader.stop_monitoring()

                if self.parent.overlay:
                    self.parent.overlay.stop_session()

                total_cost = float(
                    self.parent.loot_summary_labels["Total Cost"].text().replace(",", "").split()[0]
                )
                total_return = float(
                    self.parent.loot_summary_labels["Total Return"]
                    .text()
                    .replace(",", "")
                    .split()[0]
                )

                asyncio.run(
                    self.parent.db_manager.update_session_totals(
                        session_id, total_cost, total_return, 0
                    )
                )

                self._convert_current_run_to_completed(session_id, total_cost, total_return)

                self.parent.current_session_id = None
                self.parent.current_session_start = None

                self.parent.start_run_btn.setText("Start Run")
                self.parent.start_run_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #238636;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 4px;
                        padding: 4px 12px;
                        font-weight: bold;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #2EA043;
                    }
                    QPushButton:disabled {
                        background-color: #3D444D;
                        color: #6A737D;
                    }
                """)

                # Disable crafting "Add to Session" button
                if hasattr(self.parent, "crafting_widget") and self.parent.crafting_widget:
                    self.parent.crafting_widget.set_session_active(False)

                # Update combat tab to show no active session
                if hasattr(self.parent, "combat_widget") and self.parent.combat_widget:
                    self.parent.combat_widget.update_session_info(None, None)

                self.parent.status_bar.showMessage("Session stopped")
                logger.info(f"Session stopped: {session_id}")

        except Exception as e:
            logger.error(f"Error stopping session: {e}", exc_info=True)
            self.parent.status_bar.showMessage(f"Error stopping session: {e}")

    def _convert_current_run_to_completed(
        self, session_id: str, total_cost: float, total_return: float
    ):
        """Convert (Current run) entry to a completed run entry"""
        for row in range(self.parent.run_log_table.rowCount()):
            item = self.parent.run_log_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == "current":
                end_time = datetime.now()
                delta = end_time - self.parent.current_session_start
                hours, remainder = divmod(int(delta.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                roi = (total_return / total_cost * 100) if total_cost > 0 else 0

                self.parent.run_log_table.setItem(row, 0, QTableWidgetItem("Completed"))
                self.parent.run_log_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, session_id)
                self.parent.run_log_table.item(row, 0).setForeground(QColor("#E6EDF3"))

                self.parent.run_log_table.item(row, 1).text()
                self.parent.run_log_table.setItem(row, 2, QTableWidgetItem(duration))
                self.parent.run_log_table.setItem(row, 3, QTableWidgetItem(f"{total_cost:.2f}"))
                self.parent.run_log_table.setItem(row, 4, QTableWidgetItem(f"{total_return:.2f}"))
                self.parent.run_log_table.setItem(row, 5, QTableWidgetItem(f"{roi:.1f}%"))

                item_count = self.parent.item_breakdown_table.rowCount()
                self.parent.run_log_table.setItem(row, 6, QTableWidgetItem(str(item_count)))
                break

        self.parent.run_log_table.sortItems(1, Qt.SortOrder.DescendingOrder)

        if hasattr(self.parent, "analysis_widget") and self.parent.analysis_widget:
            self.parent.analysis_widget.refresh()

    def toggle_pause_logging(self):
        """Pause or resume logging"""
        self.parent.is_logging_paused = not self.parent.is_logging_paused
        if self.parent.is_logging_paused:
            self.parent.pause_btn.setText("Resume Logging")
            self.parent.status_bar.showMessage("Logging paused")
            if hasattr(self.parent, "chat_reader") and self.parent.chat_reader:
                self.parent.chat_reader.pause_monitoring()
        else:
            self.parent.pause_btn.setText("Pause Logging")
            self.parent.status_bar.showMessage("Logging resumed")
            if hasattr(self.parent, "chat_reader") and self.parent.chat_reader:
                self.parent.chat_reader.resume_monitoring()
