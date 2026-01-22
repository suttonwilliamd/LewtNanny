"""
Settings Dialog
Configuration panel for application preferences
"""

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QComboBox, QSpinBox,
    QCheckBox, QPushButton, QTabWidget, QTabBar,
    QFileDialog, QSlider, QColorDialog, QFontComboBox,
    QListWidget, QListWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from src.utils.paths import get_user_data_dir

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Settings and preferences dialog"""
    
    settingsApplied = pyqtSignal(dict)
    
    def __init__(self, parent=None, current_settings: Optional[dict] = None):
        super().__init__(parent)
        
        self.current_settings = current_settings or self._get_default_settings()
        
        self.setWindowTitle("Settings - LewtNanny")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.setup_ui()
        self.load_settings()
        
        logger.info("SettingsDialog initialized")
    
    def _get_default_settings(self) -> dict:
        """Get default settings"""
        return {
            'theme': 'dark',
            'font_family': 'Segoe UI',
            'font_size': 10,
            'auto_save': True,
            'auto_save_interval': 30,
            'show_overlay': True,
            'decimal_places': 4,
            'default_enhancement_damage': 0,
            'default_enhancement_accuracy': 0,
            'default_enhancement_economy': 0,
            'weapon_sort': 'dps',
            'confirm_delete': True,
            'animations_enabled': True
        }
    
    def setup_ui(self):
        """Setup the settings UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Appearance tab
        appearance_tab = self._create_appearance_tab()
        self.tabs.addTab(appearance_tab, "Appearance")
        
        # Defaults tab
        defaults_tab = self._create_defaults_tab()
        self.tabs.addTab(defaults_tab, "Defaults")
        
        # Data tab
        data_tab = self._create_data_tab()
        self.tabs.addTab(data_tab, "Data")
        
        # Behavior tab
        behavior_tab = self._create_behavior_tab()
        self.tabs.addTab(behavior_tab, "Behavior")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_appearance_tab(self) -> QWidget:
        """Create appearance settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Theme
        theme_group = QGroupBox("Theme")
        theme_layout = QHBoxLayout(theme_group)
        theme_layout.setContentsMargins(10, 15, 10, 10)
        
        theme_layout.addWidget(QLabel("Color Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "System"])
        self.theme_combo.setToolTip("Choose the application color scheme")
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        
        layout.addWidget(theme_group)
        
        # Font
        font_group = QGroupBox("Font")
        font_layout = QGridLayout(font_group)
        font_layout.setContentsMargins(10, 15, 10, 10)
        font_layout.setSpacing(10)
        
        font_layout.addWidget(QLabel("Font Family:"), 0, 0)
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Segoe UI"))
        font_layout.addWidget(self.font_combo, 0, 1)
        
        font_layout.addWidget(QLabel("Font Size:"), 1, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(10)
        font_layout.addWidget(self.font_size_spin, 1, 1)
        
        layout.addWidget(font_group)
        
        # Accent color
        color_group = QGroupBox("Accent Color")
        color_layout = QHBoxLayout(color_group)
        color_layout.setContentsMargins(10, 15, 10, 10)
        
        color_layout.addWidget(QLabel("Accent:"))
        self.accent_color_btn = QPushButton()
        self.accent_color_btn.setFixedSize(60, 30)
        self.accent_color_btn.clicked.connect(self._pick_accent_color)
        color_layout.addWidget(self.accent_color_btn)
        
        self.accent_color = QColor("#4A90D9")
        self._update_accent_button()
        
        color_layout.addStretch()
        
        layout.addWidget(color_group)
        
        layout.addStretch()
        
        return tab
    
    def _create_defaults_tab(self) -> QWidget:
        """Create default settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Default enhancements
        enh_group = QGroupBox("Default Enhancement Levels")
        enh_layout = QGridLayout(enh_group)
        enh_layout.setContentsMargins(10, 15, 10, 10)
        enh_layout.setSpacing(10)
        
        enh_layout.addWidget(QLabel("Default Damage Enhancement:"), 0, 0)
        self.default_damage_enh = QSpinBox()
        self.default_damage_enh.setRange(0, 20)
        self.default_damage_enh.setToolTip("Default damage enhancer level (0-20)")
        enh_layout.addWidget(self.default_damage_enh, 0, 1)
        
        enh_layout.addWidget(QLabel("Default Accuracy Enhancement:"), 1, 0)
        self.default_accuracy_enh = QSpinBox()
        self.default_accuracy_enh.setRange(0, 20)
        self.default_accuracy_enh.setToolTip("Default accuracy enhancer level (0-20)")
        enh_layout.addWidget(self.default_accuracy_enh, 1, 1)
        
        enh_layout.addWidget(QLabel("Default Economy Enhancement:"), 2, 0)
        self.default_economy_enh = QSpinBox()
        self.default_economy_enh.setRange(0, 20)
        self.default_economy_enh.setToolTip("Default economy enhancer level (0-20)")
        enh_layout.addWidget(self.default_economy_enh, 2, 1)
        
        layout.addWidget(enh_group)
        
        # Weapon sorting
        sort_group = QGroupBox("Weapon List")
        sort_layout = QVBoxLayout(sort_group)
        sort_layout.setContentsMargins(10, 15, 10, 10)
        
        sort_layout.addWidget(QLabel("Default Sort By:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            ("DPS", "dps"),
            ("Economy", "eco"),
            ("Name", "name"),
            ("Cost", "cost")
        ])
        self.sort_combo.setToolTip("Default sorting for weapon lists")
        sort_layout.addWidget(self.sort_combo)
        
        layout.addWidget(sort_group)
        
        # Decimal places
        decimal_group = QGroupBox("Number Display")
        decimal_layout = QVBoxLayout(decimal_group)
        decimal_layout.setContentsMargins(10, 15, 10, 10)
        
        decimal_layout.addWidget(QLabel("Decimal Places for PED Values:"))
        self.decimal_places = QSpinBox()
        self.decimal_places.setRange(2, 6)
        self.decimal_places.setToolTip("How many decimal places to show for PED values")
        decimal_layout.addWidget(self.decimal_places)
        
        layout.addWidget(decimal_group)
        
        layout.addStretch()
        
        return tab
    
    def _create_data_tab(self) -> QWidget:
        """Create data settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Auto-save
        autosave_group = QGroupBox("Auto-Save")
        autosave_layout = QVBoxLayout(autosave_group)
        autosave_layout.setContentsMargins(10, 15, 10, 10)
        
        self.auto_save_check = QCheckBox("Enable Auto-Save")
        self.auto_save_check.setToolTip("Automatically save data at regular intervals")
        autosave_layout.addWidget(self.auto_save_check)
        
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Interval (seconds):"))
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(10, 300)
        self.auto_save_interval.setToolTip("How often to auto-save (10-300 seconds)")
        interval_layout.addWidget(self.auto_save_interval)
        interval_layout.addStretch()
        autosave_layout.addLayout(interval_layout)
        
        layout.addWidget(autosave_group)
        
        # Data paths
        paths_group = QGroupBox("Data Locations")
        paths_layout = QGridLayout(paths_group)
        paths_layout.setContentsMargins(10, 15, 10, 10)
        paths_layout.setSpacing(10)
        
        paths_layout.addWidget(QLabel("Database:"), 0, 0)
        self.database_path = QLineEdit()
        self.database_path.setReadOnly(True)
        paths_layout.addWidget(self.database_path, 0, 1)
        
        browse_db_btn = QPushButton("Browse...")
        browse_db_btn.clicked.connect(self._browse_database)
        paths_layout.addWidget(browse_db_btn, 0, 2)
        
        paths_layout.addWidget(QLabel("Export Folder:"), 1, 0)
        self.export_path = QLineEdit()
        paths_layout.addWidget(self.export_path, 1, 1)
        
        browse_export_btn = QPushButton("Browse...")
        browse_export_btn.clicked.connect(self._browse_export)
        paths_layout.addWidget(browse_export_btn, 1, 2)
        
        layout.addWidget(paths_group)
        
        # Export options
        export_group = QGroupBox("Export Options")
        export_layout = QVBoxLayout(export_group)
        export_layout.setContentsMargins(10, 15, 10, 10)
        
        self.export_csv_check = QCheckBox("Include CSV export option")
        self.export_csv_check.setToolTip("Add CSV format to export options")
        export_layout.addWidget(self.export_csv_check)
        
        self.export_json_check = QCheckBox("Include JSON export option")
        self.export_json_check.setToolTip("Add JSON format to export options")
        export_layout.addWidget(self.export_json_check)
        
        layout.addWidget(export_group)
        
        layout.addStretch()
        
        return tab
    
    def _create_behavior_tab(self) -> QWidget:
        """Create behavior settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Confirmations
        confirm_group = QGroupBox("Confirmations")
        confirm_layout = QVBoxLayout(confirm_group)
        confirm_layout.setContentsMargins(10, 15, 10, 10)
        
        self.confirm_delete_check = QCheckBox("Confirm before deleting sessions")
        self.confirm_delete_check.setToolTip("Show confirmation dialog when deleting sessions")
        confirm_layout.addWidget(self.confirm_delete_check)
        
        self.confirm_clear_check = QCheckBox("Confirm before clearing data")
        self.confirm_clear_check.setToolTip("Show confirmation dialog when clearing session data")
        confirm_layout.addWidget(self.confirm_clear_check)
        
        layout.addWidget(confirm_group)
        
        # Overlay
        overlay_group = QGroupBox("Session Overlay")
        overlay_layout = QVBoxLayout(overlay_group)
        overlay_layout.setContentsMargins(10, 15, 10, 10)
        
        self.show_overlay_check = QCheckBox("Show overlay on session start")
        self.show_overlay_check.setToolTip("Display floating overlay when hunting session begins")
        overlay_layout.addWidget(self.show_overlay_check)
        
        self.animations_check = QCheckBox("Enable animations")
        self.animations_check.setToolTip("Use animated transitions and effects")
        overlay_layout.addWidget(self.animations_check)
        
        layout.addWidget(overlay_group)
        
        # Notifications
        notify_group = QGroupBox("Notifications")
        notify_layout = QVBoxLayout(notify_group)
        notify_layout.setContentsMargins(10, 15, 10, 10)
        
        self.sound_notify_check = QCheckBox("Play sound on loot events")
        self.sound_notify_check.setToolTip("Play a sound when valuable loot is received")
        notify_layout.addWidget(self.sound_notify_check)
        
        layout.addWidget(notify_group)
        
        layout.addStretch()
        
        return tab
    
    def _pick_accent_color(self):
        """Pick accent color"""
        color = QColorDialog.getColor(self.accent_color, self, "Choose Accent Color")
        if color.isValid():
            self.accent_color = color
            self._update_accent_button()
    
    def _update_accent_button(self):
        """Update accent color button"""
        self.accent_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent_color.name()};
                border: 1px solid #888;
                border-radius: 4px;
            }}
        """)
    
    def _browse_database(self):
        """Browse for database file"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Database File",
            str(Path.cwd()),
            "SQLite Database (*.db)"
        )
        if path:
            self.database_path.setText(path)
    
    def _browse_export(self):
        """Browse for export folder"""
        path = QFileDialog.getExistingDirectory(
            self, "Select Export Folder",
            str(Path.home())
        )
        if path:
            self.export_path.setText(path)
    
    def load_settings(self):
        """Load current settings into dialog"""
        settings = self.current_settings
        
        # Appearance
        theme_map = {"dark": "Dark", "light": "Light", "system": "System"}
        self.theme_combo.setCurrentText(theme_map.get(settings.get('theme', 'dark'), "Dark"))
        
        font_family = settings.get('font_family', 'Segoe UI')
        font = QFont(font_family)
        self.font_combo.setCurrentFont(font)
        
        self.font_size_spin.setValue(settings.get('font_size', 10))
        
        # Defaults
        self.default_damage_enh.setValue(settings.get('default_enhancement_damage', 0))
        self.default_accuracy_enh.setValue(settings.get('default_enhancement_accuracy', 0))
        self.default_economy_enh.setValue(settings.get('default_enhancement_economy', 0))
        
        sort_map = {"dps": "DPS", "eco": "Economy", "name": "Name", "cost": "Cost"}
        self.sort_combo.setCurrentText(sort_map.get(settings.get('weapon_sort', 'dps'), "DPS"))
        
        self.decimal_places.setValue(settings.get('decimal_places', 4))
        
        # Data
        self.auto_save_check.setChecked(settings.get('auto_save', True))
        self.auto_save_interval.setValue(settings.get('auto_save_interval', 30))

        db_path = settings.get('database_path', str(get_user_data_dir() / 'lewtnanny.db'))
        self.database_path.setText(str(Path(db_path).absolute()))
        
        export_path = settings.get('export_path', str(Path.home()))
        self.export_path.setText(export_path)
        
        self.export_csv_check.setChecked(settings.get('export_csv', True))
        self.export_json_check.setChecked(settings.get('export_json', True))
        
        # Behavior
        self.confirm_delete_check.setChecked(settings.get('confirm_delete', True))
        self.confirm_clear_check.setChecked(settings.get('confirm_clear', True))
        self.show_overlay_check.setChecked(settings.get('show_overlay', True))
        self.animations_check.setChecked(settings.get('animations_enabled', True))
        self.sound_notify_check.setChecked(settings.get('sound_notify', False))
    
    def get_settings(self) -> dict:
        """Get current settings from dialog"""
        theme_map = {"Dark": "dark", "Light": "light", "System": "system"}
        
        return {
            'theme': theme_map.get(self.theme_combo.currentText(), 'dark'),
            'font_family': self.font_combo.currentFont().family(),
            'font_size': self.font_size_spin.value(),
            'accent_color': self.accent_color.name(),
            'default_enhancement_damage': self.default_damage_enh.value(),
            'default_enhancement_accuracy': self.default_accuracy_enh.value(),
            'default_enhancement_economy': self.default_economy_enh.value(),
            'weapon_sort': ["dps", "eco", "name", "cost"][self.sort_combo.currentIndex()],
            'decimal_places': self.decimal_places.value(),
            'auto_save': self.auto_save_check.isChecked(),
            'auto_save_interval': self.auto_save_interval.value(),
            'database_path': self.database_path.text(),
            'export_path': self.export_path.text(),
            'export_csv': self.export_csv_check.isChecked(),
            'export_json': self.export_json_check.isChecked(),
            'confirm_delete': self.confirm_delete_check.isChecked(),
            'confirm_clear': self.confirm_clear_check.isChecked(),
            'show_overlay': self.show_overlay_check.isChecked(),
            'animations_enabled': self.animations_check.isChecked(),
            'sound_notify': self.sound_notify_check.isChecked()
        }
    
    def apply_settings(self):
        """Apply settings and emit signal"""
        settings = self.get_settings()
        self.settingsApplied.emit(settings)
        logger.info("Settings applied")
    
    def accept(self):
        """OK button clicked"""
        self.apply_settings()
        super().accept()
    
    def reject(self):
        """Cancel button clicked"""
        super().reject()


def show_settings_dialog(parent=None, current_settings: dict = None) -> Optional[dict]:
    """Show settings dialog and return new settings"""
    dialog = SettingsDialog(parent, current_settings)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_settings()
    return None


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    settings = {
        'theme': 'dark',
        'font_family': 'Segoe UI',
        'font_size': 10,
        'auto_save': True,
        'auto_save_interval': 30,
        'show_overlay': True,
        'decimal_places': 4
    }
    
    result = show_settings_dialog(None, settings)
    if result:
        print("New settings:", result)
