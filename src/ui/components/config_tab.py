"""Configuration tab for LewtNanny - Weapon Loadout System
Adapted from LootNanny's ConfigTab with similar functionality
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.services.config_manager import ConfigManager
from src.services.cost_calculation_service import CostCalculationService
from src.services.game_data_service import GameDataService
from src.services.loadout_service import LoadoutService, WeaponLoadout


def get_default_chat_log_path() -> str:
    """Get the default Entropia Universe chat log path"""
    documents_path = Path.home() / "Documents"
    chat_log_path = documents_path / "Entropia Universe" / "chat.log"
    return str(chat_log_path)


def chat_log_exists() -> bool:
    """Check if the default chat log file exists"""
    return Path(get_default_chat_log_path()).exists()


class ConfigSignals(QObject):
    """Signals for config tab"""

    config_changed = pyqtSignal(str, object)
    loadout_changed = pyqtSignal()
    stats_calculated = pyqtSignal(float)  # Signal when stats calculation completes with total cost


class ConfigTab(QWidget):
    """Configuration tab with weapon loadout management - LootNanny style"""

    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.signals = ConfigSignals()
        self._theme = "dark"

        from src.core.multi_database_manager import MultiDatabaseManager

        self.db_manager = MultiDatabaseManager()
        self._loadouts: list[WeaponLoadout] = []
        self._selected_loadout_index: int | None = None

        # Use provided config_manager or create a new one
        if config_manager is not None:
            self._config = config_manager
        else:
            self._config = ConfigManager()
            self._config.load()  # Load synchronously

        self.setup_ui()
        self.connect_signals()

        QTimer.singleShot(100, self._delayed_load)

    @property
    def theme(self) -> str:
        return self._theme

    @theme.setter
    def theme(self, value: str):
        self._theme = value
        self._apply_theme()

    def setup_ui(self):
        """Setup the configuration UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #2D3D4F;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #4A90D9;
                color: #1A1F2E;
            }
        """)

        tab_widget.addTab(self._create_general_tab(), "General")
        tab_widget.addTab(self._create_weapons_tab(), "Weapons")
        tab_widget.addTab(self._create_screenshots_tab(), "Screenshots")
        tab_widget.addTab(self._create_advanced_tab(), "Advanced")

        layout.addWidget(tab_widget)

    def _create_general_tab(self) -> QWidget:
        """Create the general settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        self._config.load()

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(10)

        default_chat_path = get_default_chat_log_path()
        default_chat_exists = chat_log_exists()

        self.chat_location_text = QLineEdit()
        self.chat_location_text.setPlaceholderText("Path to chat log file...")
        saved_chat_path = self._config.get("chat_monitoring.log_file_path", "")

        if default_chat_exists:
            self.chat_location_text.setText(default_chat_path)
            self._save_chat_location(default_chat_path)
        elif saved_chat_path:
            self.chat_location_text.setText(saved_chat_path)
        else:
            self.chat_location_text.setText("")

        self.chat_location_text.setStyleSheet("""
            QLineEdit {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 8px 12px;
                color: #E0E1E3;
                min-width: 300px;
            }
        """)
        form_layout.addRow("Chat Location:", self.chat_location_text)

        self.find_file_btn = QPushButton("Find File")
        self.find_file_btn.setStyleSheet("""
            QPushButton {
                background: #2D3D4F;
                border: 1px solid #4A90D9;
                border-radius: 4px;
                padding: 8px 16px;
                color: #4A90D9;
            }
            QPushButton:hover {
                background: #4A90D9;
                color: #1A1F2E;
            }
        """)
        self.find_file_btn.clicked.connect(self._open_chat_file)
        self.find_file_btn.setVisible(not default_chat_exists)
        form_layout.addRow("", self.find_file_btn)

        self.character_name = QLineEdit()
        self.character_name.setPlaceholderText("Character name...")
        char_name = self._config.get("character.name", "")
        self.character_name.setText(char_name if char_name else "")
        self.character_name.setStyleSheet("""
            QLineEdit {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 8px 12px;
                color: #E0E1E3;
                min-width: 300px;
            }
        """)
        self.character_name.editingFinished.connect(self._on_name_changed)
        form_layout.addRow("Character Name:", self.character_name)

        layout.addLayout(form_layout)
        layout.addStretch()
        return widget

    def _create_weapons_tab(self) -> QWidget:
        """Create the weapons and loadouts tab - LootNanny style"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header = QLabel("WEAPON LOADOUTS")
        header.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #4A90D9;
            letter-spacing: 1px;
        """)
        layout.addWidget(header)

        self.loadout_table = QTableWidget()
        self.loadout_table.setColumnCount(9)
        self.loadout_table.setHorizontalHeaderLabels(
            [
                "Name",
                "Weapon",
                "Amp",
                "Scope",
                "Sight 1",
                "Sight 2",
                "Damage",
                "Accuracy",
                "Economy",
            ]
        )
        self.loadout_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.loadout_table.setSortingEnabled(True)
        self.loadout_table.itemSelectionChanged.connect(self._on_loadout_selected)
        self.loadout_table.setAlternatingRowColors(True)
        self.loadout_table.setStyleSheet("""
            QTableWidget {
                background: #1A1F2E;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                gridline-color: #2D3D4F;
            }
            QTableWidget::item:selected {
                background: #4A90D944;
            }
            QHeaderView::section {
                background: #2D3D4F;
                color: #E0E1E3;
                padding: 8px;
                font-weight: bold;
            }
        """)

        header: QHeaderView = self.loadout_table.horizontalHeader()
        if header is not None:
            try:
                if hasattr(QHeaderView, "setSectionResizeMode"):
                    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
                    for i in range(1, 9):
                        header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            except (AttributeError, TypeError):
                pass

        layout.addWidget(self.loadout_table)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.select_loadout_btn = QPushButton("Select Loadout")
        self.select_loadout_btn.setStyleSheet("""
            QPushButton {
                background: #2D3D4F;
                border: 1px solid #3498DB;
                border-radius: 6px;
                padding: 8px 16px;
                color: #3498DB;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #3498DB;
                color: #1A1F2E;
            }
        """)
        self.select_loadout_btn.clicked.connect(self._select_loadout)
        self.select_loadout_btn.hide()
        button_layout.addWidget(self.select_loadout_btn)

        self.delete_weapon_btn = QPushButton("Delete Loadout")
        self.delete_weapon_btn.setStyleSheet("""
            QPushButton {
                background: #2D3D4F;
                border: 1px solid #E74C3C;
                border-radius: 6px;
                padding: 8px 16px;
                color: #E74C3C;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #E74C3C;
                color: #1A1F2E;
            }
        """)
        self.delete_weapon_btn.clicked.connect(self._delete_loadout)
        self.delete_weapon_btn.hide()
        button_layout.addWidget(self.delete_weapon_btn)

        self.add_weapon_btn = QPushButton("Add Weapon Loadout")
        self.add_weapon_btn.setStyleSheet("""
            QPushButton {
                background: #2D3D4F;
                border: 1px solid #2ECC71;
                border-radius: 6px;
                padding: 8px 16px;
                color: #2ECC71;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2ECC71;
                color: #1A1F2E;
            }
        """)
        self.add_weapon_btn.clicked.connect(self._add_new_weapon)
        button_layout.addWidget(self.add_weapon_btn)

        self.create_weapon_btn = QPushButton("Create Weapon")
        self.create_weapon_btn.setStyleSheet("""
            QPushButton {
                background: #2D3D4F;
                border: 1px solid #9B59B6;
                border-radius: 6px;
                padding: 8px 16px;
                color: #9B59B6;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #9B59B6;
                color: #1A1F2E;
            }
        """)
        self.create_weapon_btn.clicked.connect(self._create_custom_weapon)
        button_layout.addWidget(self.create_weapon_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        active_group = QGroupBox("ACTIVE LOADOUT")
        active_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #4A90D9;
                border: 1px solid #2D3D4F;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        active_layout = QFormLayout(active_group)
        active_layout.setContentsMargins(10, 15, 10, 10)

        self.active_loadout_combo = QComboBox()
        self.active_loadout_combo.setStyleSheet("""
            QComboBox {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 8px 12px;
                color: #E0E1E3;
                min-width: 250px;
            }
        """)
        self.active_loadout_combo.currentIndexChanged.connect(self._on_active_loadout_changed)
        active_layout.addRow("Active Loadout:", self.active_loadout_combo)

        self.active_loadout_info = QLabel("No loadout selected")
        self.active_loadout_info.setStyleSheet("color: #888; font-size: 12px;")
        active_layout.addRow("Info:", self.active_loadout_info)

        layout.addWidget(active_group)

        stats_group = QGroupBox("CALCULATED STATS")
        stats_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #4A90D9;
                border: 1px solid #2D3D4F;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        stats_layout = QGridLayout(stats_group)
        stats_layout.setContentsMargins(10, 15, 10, 10)
        stats_layout.setSpacing(10)

        stats_layout.addWidget(QLabel("Ammo Burn/shot:"), 0, 0)
        self.ammo_burn_text = QLineEdit("0")
        self.ammo_burn_text.setEnabled(False)
        self.ammo_burn_text.setStyleSheet("""
            QLineEdit {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 6px 10px;
                color: #E0E1E3;
            }
        """)
        stats_layout.addWidget(self.ammo_burn_text, 0, 1)

        stats_layout.addWidget(QLabel("Decay/shot (PED):"), 1, 0)
        self.weapon_decay_text = QLineEdit("0.000000")
        self.weapon_decay_text.setEnabled(False)
        self.weapon_decay_text.setStyleSheet("""
            QLineEdit {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 6px 10px;
                color: #E0E1E3;
            }
        """)
        stats_layout.addWidget(self.weapon_decay_text, 1, 1)

        layout.addWidget(stats_group)

        layout.addStretch()
        return widget

    def _create_screenshots_tab(self) -> QWidget:
        """Create the screenshots settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(10)

        self.screenshots_checkbox = QCheckBox("Enable screenshots on loot/HOF")
        screenshot_enabled = self._config.get("screenshot.enabled", True)
        self.screenshots_checkbox.setChecked(screenshot_enabled if screenshot_enabled else False)
        self.screenshots_checkbox.setStyleSheet("color: #E0E1E3;")
        form_layout.addRow("", self.screenshots_checkbox)

        self.screenshots_directory_text = QLineEdit()
        self.screenshots_directory_text.setPlaceholderText("Screenshot directory...")
        screenshot_dir = self._config.get("screenshot.directory", "~/Documents/LewtNanny/")
        self.screenshots_directory_text.setText(screenshot_dir if screenshot_dir else "")
        self.screenshots_directory_text.setStyleSheet("""
            QLineEdit {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 8px 12px;
                color: #E0E1E3;
                min-width: 300px;
            }
        """)
        form_layout.addRow("Screenshot Directory:", self.screenshots_directory_text)

        self.screenshots_delay = QSpinBox()
        self.screenshots_delay.setRange(0, 5000)
        screenshot_delay = self._config.get("screenshot.delay_ms", 500)
        self.screenshots_delay.setValue(int(screenshot_delay) if screenshot_delay else 500)
        self.screenshots_delay.setStyleSheet("""
            QSpinBox {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 6px 10px;
                color: #E0E1E3;
            }
        """)
        form_layout.addRow("Screenshot Delay (ms):", self.screenshots_delay)

        self.screenshot_threshold = QLineEdit()
        self.screenshot_threshold.setPlaceholderText("Minimum PED value for screenshot...")
        threshold = self._config.get("screenshot.threshold_ped", 10)
        self.screenshot_threshold.setText(str(threshold) if threshold else "10")
        self.screenshot_threshold.setStyleSheet("""
            QLineEdit {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 8px 12px;
                color: #E0E1E3;
                min-width: 100px;
            }
        """)
        form_layout.addRow("Screenshot Threshold (PED):", self.screenshot_threshold)

        layout.addLayout(form_layout)
        layout.addStretch()
        return widget

    def _create_advanced_tab(self) -> QWidget:
        """Create the advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(10)

        self.debug_checkbox = QCheckBox("Enable debug mode")
        debug_mode = self._config.get("debug_mode", False)
        self.debug_checkbox.setChecked(bool(debug_mode))
        self.debug_checkbox.setStyleSheet("color: #E0E1E3;")
        form_layout.addRow("", self.debug_checkbox)

        self.verbose_checkbox = QCheckBox("Verbose logging")
        verbose = self._config.get("verbose_logging", False)
        self.verbose_checkbox.setChecked(bool(verbose))
        self.verbose_checkbox.setStyleSheet("color: #E0E1E3;")
        form_layout.addRow("", self.verbose_checkbox)

        self.ocr_checkbox = QCheckBox("Enable OCR")
        ocr = self._config.get("enable_ocr", True)
        self.ocr_checkbox.setChecked(bool(ocr))
        self.ocr_checkbox.setStyleSheet("color: #E0E1E3;")
        form_layout.addRow("", self.ocr_checkbox)

        self.overlay_checkbox = QCheckBox("Enable overlay")
        overlay = self._config.get("enable_overlay", True)
        self.overlay_checkbox.setChecked(bool(overlay))
        self.overlay_checkbox.setStyleSheet("color: #E0E1E3;")
        form_layout.addRow("", self.overlay_checkbox)

        layout.addLayout(form_layout)

        layout.addStretch()
        return widget

    def connect_signals(self):
        """Connect signals and slots"""
        pass

    def _delayed_load(self):
        """Delayed data loading"""
        asyncio.run(self._load_data())

    async def _load_data(self):
        """Load loadouts from database"""
        try:
            service = LoadoutService()
            self._loadouts = await service.get_all_loadouts()
            self._refresh_loadout_table()
            self.active_loadout_combo.blockSignals(True)
            try:
                self._refresh_active_loadout_combo()
                self._restore_active_loadout()
            finally:
                self.active_loadout_combo.blockSignals(False)
        except Exception as e:
            print(f"Error loading loadouts: {e}")
            self._loadouts = []

    def _restore_active_loadout(self):
        """Restore the saved active loadout selection"""
        saved_id = self._config.get("loadouts.active_loadout_id")
        if saved_id:
            for i in range(self.active_loadout_combo.count()):
                if self.active_loadout_combo.itemData(i) == saved_id:
                    self.active_loadout_combo.setCurrentIndex(i)
                    self._on_active_loadout_changed(i)
                    break

            for idx, loadout in enumerate(self._loadouts):
                if loadout.id == saved_id:
                    self._selected_loadout_index = idx
                    self.loadout_table.selectRow(idx)
                    self.select_loadout_btn.show()
                    self.delete_weapon_btn.show()
                    break

    def _refresh_loadout_table(self):
        """Refresh the loadout table"""
        self.loadout_table.setRowCount(0)

        for loadout in self._loadouts:
            row = self.loadout_table.rowCount()
            self.loadout_table.insertRow(row)

            self.loadout_table.setItem(row, 0, QTableWidgetItem(loadout.name))
            self.loadout_table.setItem(row, 1, QTableWidgetItem(loadout.weapon))
            self.loadout_table.setItem(row, 2, QTableWidgetItem(loadout.amplifier or "None"))
            self.loadout_table.setItem(row, 3, QTableWidgetItem(loadout.scope or "None"))
            self.loadout_table.setItem(row, 4, QTableWidgetItem(loadout.sight_1 or "None"))
            self.loadout_table.setItem(row, 5, QTableWidgetItem(loadout.sight_2 or "None"))
            self.loadout_table.setItem(row, 6, QTableWidgetItem(str(loadout.damage_enh)))
            self.loadout_table.setItem(row, 7, QTableWidgetItem(str(loadout.accuracy_enh)))
            self.loadout_table.setItem(row, 8, QTableWidgetItem(str(loadout.economy_enh)))

    def _refresh_active_loadout_combo(self):
        """Refresh the active loadout combo box"""
        self.active_loadout_combo.clear()
        self.active_loadout_combo.addItem("None", None)

        for loadout in self._loadouts:
            self.active_loadout_combo.addItem(loadout.name, loadout.id)

    def _on_loadout_selected(self):
        """Handle loadout selection from table"""
        selected = self.loadout_table.selectedItems()
        if not selected:
            self.select_loadout_btn.hide()
            self.delete_weapon_btn.hide()
            self._selected_loadout_index = None
            return

        row = selected[0].row()
        self._selected_loadout_index = row
        self.select_loadout_btn.show()
        self.delete_weapon_btn.show()

    def _add_new_weapon(self):
        """Add a new weapon loadout"""
        dialog = LoadoutDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            loadout = dialog.get_loadout()
            if loadout:
                asyncio.run(self._save_loadout(loadout))
                self.signals.loadout_changed.emit()

    def _delete_loadout(self):
        """Delete the selected loadout"""
        if self._selected_loadout_index is None:
            return

        loadout = self._loadouts[self._selected_loadout_index]
        reply = QMessageBox.question(
            self,
            "Delete Loadout",
            f"Are you sure you want to delete '{loadout.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if loadout.id:
                asyncio.run(self._delete_loadout_by_id(loadout.id))
            self._selected_loadout_index = None
            self.select_loadout_btn.hide()
            self.delete_weapon_btn.hide()
            self.signals.loadout_changed.emit()

    def _select_loadout(self):
        """Select the highlighted loadout as active"""
        if self._selected_loadout_index is None:
            return

        loadout = self._loadouts[self._selected_loadout_index]
        self.active_loadout_combo.setCurrentText(loadout.name)
        self._update_active_loadout_info(loadout)

    async def _save_loadout(self, loadout: WeaponLoadout):
        """Save a new loadout"""
        try:
            service = LoadoutService()
            await service.create_loadout(loadout)
            self._loadouts = await service.get_all_loadouts()
            self._refresh_loadout_table()
            self._refresh_active_loadout_combo()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save loadout: {e}")

    async def _update_loadout(self, loadout: WeaponLoadout):
        """Update an existing loadout"""
        try:
            service = LoadoutService()
            await service.update_loadout(loadout)
            self._loadouts = await service.get_all_loadouts()
            self._refresh_loadout_table()
            self._refresh_active_loadout_combo()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update loadout: {e}")

    async def _delete_loadout_by_id(self, loadout_id: int):
        """Delete a loadout by ID"""
        try:
            service = LoadoutService()
            await service.delete_loadout(loadout_id)
            self._loadouts = await service.get_all_loadouts()
            self._refresh_loadout_table()
            self._refresh_active_loadout_combo()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete loadout: {e}")

    def _create_custom_weapon(self):
        """Create a custom weapon"""
        dialog = CreateWeaponDialog(self)
        dialog.exec()

    def _on_active_loadout_changed(self, index: int):
        """Handle active loadout change"""
        loadout_id = self.active_loadout_combo.currentData()
        if loadout_id:
            for loadout in self._loadouts:
                if loadout.id == loadout_id:
                    self._update_active_loadout_info(loadout)
                    self._config.set_sync("loadouts.active_loadout_id", loadout_id)
                    self.signals.loadout_changed.emit()
                    return
        self.active_loadout_info.setText("No loadout selected")
        self.ammo_burn_text.setText("0")
        self.weapon_decay_text.setText("0.000000")
        self._config.set_sync("loadouts.active_loadout_id", None)
        self.signals.loadout_changed.emit()

    def _update_active_loadout_info(self, loadout: WeaponLoadout):
        """Update the active loadout info display"""
        self.active_loadout_info.setText(
            f"{loadout.weapon} | {loadout.amplifier or 'No Amp'} | "
            f"Dmg: {loadout.damage_enh} | Acc: {loadout.accuracy_enh} | "
            f"Eco: {loadout.economy_enh}"
        )
        self._calculate_loadout_stats(loadout)

    def _calculate_loadout_stats(self, loadout: WeaponLoadout):
        """Calculate ammo burn and decay for a loadout"""

        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._async_calculate_stats(loadout))
            finally:
                loop.close()

        import threading

        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

    async def _async_calculate_stats(self, loadout: WeaponLoadout):
        """Async calculation of loadout stats using centralized cost calculation service"""
        logger = logging.getLogger(__name__)
        logger.info("===== CONFIG TAB STATS CALCULATION START =====")
        logger.info(f"Loadout: {loadout.name} - Weapon: {loadout.weapon}")
        logger.info(
            f"Loadout components: amp={loadout.amplifier}, scope={loadout.scope}, sight1={loadout.sight_1}, sight2={loadout.sight_2}"
        )
        logger.info(
            f"Enhancers: dmg={loadout.damage_enh}, acc={loadout.accuracy_enh}, eco={loadout.economy_enh}"
        )

        try:
            # Use the centralized cost calculation service
            total_cost_ped = await CostCalculationService.calculate_cost_per_attack(loadout)

            logger.info(f"TOTAL COST PER ATTACK: {total_cost_ped:.6f} PED")
            logger.info("===== CONFIG TAB STATS CALCULATION END =====")

            # For UI display, we need to calculate the individual components
            data_service = GameDataService()
            weapon = await data_service.get_weapon_by_name(loadout.weapon)
            if not weapon:
                logger.error(f"Weapon not found in database: {loadout.weapon}")
                return

            base_decay = float(weapon.decay) if weapon.decay else 0.0
            base_ammo = weapon.ammo if weapon.ammo else 0

            damage_mult = 1.0 + (loadout.damage_enh * 0.1)
            economy_mult = 1.0 - (loadout.economy_enh * 0.05)

            enhanced_decay = base_decay * damage_mult * economy_mult
            enhanced_ammo = base_ammo * damage_mult

            # Add attachment contributions for display
            if loadout.amplifier:
                amp = await data_service.get_attachment_by_name(loadout.amplifier)
                if amp:
                    enhanced_decay += float(amp.decay) if amp.decay else 0
                    enhanced_ammo += amp.ammo if amp.ammo else 0

            if loadout.scope:
                scope = await data_service.get_attachment_by_name(loadout.scope)
                if scope:
                    enhanced_decay += float(scope.decay) if scope.decay else 0
                    enhanced_ammo += scope.ammo if scope.ammo else 0

            if loadout.sight_1:
                sight = await data_service.get_attachment_by_name(loadout.sight_1)
                if sight:
                    enhanced_decay += float(sight.decay) if sight.decay else 0
                    enhanced_ammo += sight.ammo if sight.ammo else 0

            if loadout.sight_2:
                sight = await data_service.get_attachment_by_name(loadout.sight_2)
                if sight:
                    enhanced_decay += float(sight.decay) if sight.decay else 0
                    enhanced_ammo += sight.ammo if sight.ammo else 0

            # Update UI components
            self.ammo_burn_text.setText(str(int(enhanced_ammo)))
            self.weapon_decay_text.setText(f"{enhanced_decay:.6f}")

            # Emit signal with synchronized total cost
            self.signals.stats_calculated.emit(total_cost_ped)

        except Exception as e:
            logger.error(
                f"Error calculating stats for loadout {loadout.weapon}: {e}",
                exc_info=True,
            )

    def _open_chat_file(self):
        """Open file dialog for chat location"""
        path, _ = QFileDialog.getOpenFileName(self, "Open Chat Log", "", "All Files (*.*)")
        if path:
            self.chat_location_text.setText(path)
            self._save_chat_location(path)
            self.find_file_btn.setVisible(False)

    def _save_chat_location(self, path: str):
        """Save chat location to config"""
        asyncio.run(self._config.set("chat_monitoring.log_file_path", path))

    def _on_name_changed(self):
        """Handle character name change"""
        name = self.character_name.text()
        asyncio.run(self._config.set("character.name", name))

    def _apply_theme(self):
        """Apply theme to all UI elements"""
        if self._theme == "dark":
            bg_color = "#1A1F2E"
            fg_color = "#E0E1E3"
            border_color = "#2D3D4F"
            accent_color = "#4A90D9"
        else:
            bg_color = "#FFFFFF"
            fg_color = "#19232D"
            border_color = "#D1D5DB"
            accent_color = "#2563EB"

        self.setStyleSheet(f"""
            QWidget {{
                background: {bg_color};
                color: {fg_color};
            }}
            QGroupBox {{
                font-weight: bold;
                color: {accent_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            QLabel {{
                color: {fg_color};
            }}
        """)


class LoadoutDialog(QDialog):
    """Dialog for adding/editing weapon loadouts"""

    def __init__(self, parent=None, loadout: WeaponLoadout | None = None):
        super().__init__(parent)
        self._loadout = loadout
        self._weapons: list[str] = []
        self._amplifiers: list[str] = []
        self._scopes: list[str] = []
        self._sights: list[str] = []

        self.setWindowTitle("Edit Loadout" if loadout else "Add Loadout")
        self.setMinimumWidth(400)

        self.setup_ui()
        asyncio.run(self.load_data())

        if loadout:
            self._populate_from_loadout(loadout)

    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Loadout name...")
        form_layout.addRow("Name:", self.name_edit)

        self.weapon_combo = QComboBox()
        self.weapon_combo.setStyleSheet("""
            QComboBox {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 8px 12px;
                color: #E0E1E3;
            }
        """)
        form_layout.addRow("Weapon:", self.weapon_combo)

        self.amp_combo = QComboBox()
        self.amp_combo.setStyleSheet("""
            QComboBox {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 8px 12px;
                color: #E0E1E3;
            }
        """)
        form_layout.addRow("Amplifier:", self.amp_combo)

        self.scope_combo = QComboBox()
        self.scope_combo.setStyleSheet("""
            QComboBox {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 8px 12px;
                color: #E0E1E3;
            }
        """)
        form_layout.addRow("Scope:", self.scope_combo)

        self.sight1_combo = QComboBox()
        self.sight1_combo.setStyleSheet("""
            QComboBox {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 8px 12px;
                color: #E0E1E3;
            }
        """)
        form_layout.addRow("Sight 1:", self.sight1_combo)

        self.sight2_combo = QComboBox()
        self.sight2_combo.setStyleSheet("""
            QComboBox {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 8px 12px;
                color: #E0E1E3;
            }
        """)
        form_layout.addRow("Sight 2:", self.sight2_combo)

        self.damage_spin = QSpinBox()
        self.damage_spin.setRange(0, 20)
        self.damage_spin.setStyleSheet("""
            QSpinBox {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 6px 10px;
                color: #E0E1E3;
            }
        """)
        form_layout.addRow("Damage Enh:", self.damage_spin)

        self.accuracy_spin = QSpinBox()
        self.accuracy_spin.setRange(0, 20)
        self.accuracy_spin.setStyleSheet("""
            QSpinBox {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 6px 10px;
                color: #E0E1E3;
            }
        """)
        form_layout.addRow("Accuracy Enh:", self.accuracy_spin)

        self.economy_spin = QSpinBox()
        self.economy_spin.setRange(0, 20)
        self.economy_spin.setStyleSheet("""
            QSpinBox {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 6px 10px;
                color: #E0E1E3;
            }
        """)
        form_layout.addRow("Economy Enh:", self.economy_spin)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    async def load_data(self):
        """Load weapon and attachment data"""
        try:
            data_service = GameDataService()

            weapons = await data_service.get_all_weapons()
            self._weapons = [w.name for w in sorted(weapons, key=lambda x: x.name)]

            loadout_service = LoadoutService()
            custom_weapons = await loadout_service.get_all_custom_weapons()
            for cw in custom_weapons:
                self._weapons.append(f"!CUSTOM - {cw.name}")

            self.weapon_combo.addItems(self._weapons)

            attachments = await data_service.get_all_attachments()

            self._amplifiers = ["None"]
            self._scopes = ["None"]
            self._sights = ["None"]

            for att in attachments:
                if att.attachment_type in [
                    "BLP Amp",
                    "Laser Amp",
                    "Energy Amp",
                    "Melee Amp",
                    "MF Amp",
                ]:
                    self._amplifiers.append(att.name)
                elif att.attachment_type == "Scope":
                    self._scopes.append(att.name)
                elif att.attachment_type == "Sight":
                    self._sights.append(att.name)

            self.amp_combo.addItems(sorted(set(self._amplifiers)))
            self.scope_combo.addItems(sorted(set(self._scopes)))
            self.sight1_combo.addItems(sorted(set(self._sights)))
            self.sight2_combo.addItems(sorted(set(self._sights)))

            # Default to "None" for all optional fields
            none_idx = self.amp_combo.findText("None")
            if none_idx >= 0:
                self.amp_combo.setCurrentIndex(none_idx)
            none_idx = self.scope_combo.findText("None")
            if none_idx >= 0:
                self.scope_combo.setCurrentIndex(none_idx)
            none_idx = self.sight1_combo.findText("None")
            if none_idx >= 0:
                self.sight1_combo.setCurrentIndex(none_idx)
            none_idx = self.sight2_combo.findText("None")
            if none_idx >= 0:
                self.sight2_combo.setCurrentIndex(none_idx)

        except Exception as e:
            print(f"Error loading data: {e}")

    def _populate_from_loadout(self, loadout: WeaponLoadout):
        """Populate dialog from existing loadout"""
        self.name_edit.setText(loadout.name)

        idx = self.weapon_combo.findText(loadout.weapon)
        if idx >= 0:
            self.weapon_combo.setCurrentIndex(idx)

        if loadout.amplifier:
            idx = self.amp_combo.findText(loadout.amplifier)
            if idx >= 0:
                self.amp_combo.setCurrentIndex(idx)

        if loadout.scope:
            idx = self.scope_combo.findText(loadout.scope)
            if idx >= 0:
                self.scope_combo.setCurrentIndex(idx)

        if loadout.sight_1:
            idx = self.sight1_combo.findText(loadout.sight_1)
            if idx >= 0:
                self.sight1_combo.setCurrentIndex(idx)

        if loadout.sight_2:
            idx = self.sight2_combo.findText(loadout.sight_2)
            if idx >= 0:
                self.sight2_combo.setCurrentIndex(idx)

        self.damage_spin.setValue(loadout.damage_enh)
        self.accuracy_spin.setValue(loadout.accuracy_enh)
        self.economy_spin.setValue(loadout.economy_enh)

    def get_loadout(self) -> WeaponLoadout | None:
        """Get the loadout from dialog"""
        name: str = self.name_edit.text()
        if not name:
            name = f"Loadout {1}"

        weapon: str = self.weapon_combo.currentText()
        if not weapon:
            return None

        amp: Optional[str] = self.amp_combo.currentText()
        if amp == "None":
            amp = None

        scope: Optional[str] = self.scope_combo.currentText()
        if scope == "None":
            scope = None

        sight_1: Optional[str] = self.sight1_combo.currentText()
        if sight_1 == "None":
            sight_1 = None

        sight_2: Optional[str] = self.sight2_combo.currentText()
        if sight_2 == "None":
            sight_2 = None

        return WeaponLoadout(
            name=name,
            weapon=weapon,
            amplifier=amp,
            scope=scope,
            sight_1=sight_1,
            sight_2=sight_2,
            damage_enh=self.damage_spin.value(),
            accuracy_enh=self.accuracy_spin.value(),
            economy_enh=self.economy_spin.value(),
        )


class CreateWeaponDialog(QDialog):
    """Dialog for creating custom weapons"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Custom Weapon")
        self.setMinimumWidth(350)

        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Weapon name...")
        form_layout.addRow("Weapon Name:", self.name_edit)

        self.ammo_burn_spin = QSpinBox()
        self.ammo_burn_spin.setRange(0, 1000)
        self.ammo_burn_spin.setValue(10)
        self.ammo_burn_spin.setSuffix(" ammo/shot")
        self.ammo_burn_spin.setStyleSheet("""
            QSpinBox {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 6px 10px;
                color: #E0E1E3;
            }
        """)
        form_layout.addRow("Ammo Burn:", self.ammo_burn_spin)

        self.decay_edit = QLineEdit()
        self.decay_edit.setPlaceholderText("0.00")
        self.decay_edit.setText("0.10")
        form_layout.addRow("Decay (PED):", self.decay_edit)

        self.dps_edit = QLineEdit()
        self.dps_edit.setPlaceholderText("0.00")
        self.dps_edit.setText("15.00")
        form_layout.addRow("DPS:", self.dps_edit)

        layout.addLayout(form_layout)

        info_label = QLabel("Custom weapons are saved locally and added to the weapon list.")
        info_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_ok(self):
        """Handle OK button click"""
        self.accept()

    def get_weapon_data(self) -> dict[str, Any] | None:
        """Get the weapon data from dialog"""
        name = self.name_edit.text()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a weapon name")
            return None

        try:
            decay = float(self.decay_edit.text())
            dps = float(self.dps_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid decay or DPS value")
            return None

        return {
            "name": name,
            "ammo": self.ammo_burn_spin.value(),
            "decay": decay,
            "dps": dps,
        }

    def accept(self):
        """Override accept to validate before closing"""
        if not self.get_weapon_data():
            return
        super().accept()
