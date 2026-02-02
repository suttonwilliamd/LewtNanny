"""
Weapon Loadout Component - PyQt6 Version
Complete weapon selection, attachment configuration, and cost analysis
"""

import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from pathlib import Path
import asyncio

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSpinBox,
    QSlider,
    QProgressBar,
    QFrame,
    QSplitter,
    QInputDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont

from src.models.models import Weapon

logger = logging.getLogger(__name__)


class SimpleValueLabel(QLabel):
    """Simple value label for stats"""

    def __init__(self, text: str = "--", parent=None):
        super().__init__(text, parent)
        self._value = 0.0
        self.setStyleSheet("font-weight: bold; font-size: 14px; color: #4A90D9;")

    def setValue(self, new_value: float):
        """Set value without animation"""
        self._value = new_value
        display = (
            f"{new_value:.5f}"
            if new_value < 0.01
            else f"{new_value:.4f}"
            if new_value < 1
            else f"{new_value:.2f}"
        )
        self.setText(display)


class EnhancementSlider(QWidget):
    """Enhancement level slider with visual feedback"""

    valueChanged = pyqtSignal(int)

    def __init__(self, name: str, icon: str, color: str, parent=None):
        super().__init__(parent)
        self._value = 0
        self._color = color
        self._max = 20

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Icon and name
        label_layout = QHBoxLayout()
        label_layout.setSpacing(5)
        self.icon_label = QLabel(icon)
        self.icon_label.setFixedWidth(24)
        self.name_label = QLabel(name)
        self.name_label.setFixedWidth(80)
        self.name_label.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 12px;"
        )
        label_layout.addWidget(self.icon_label)
        label_layout.addWidget(self.name_label)
        layout.addLayout(label_layout)

        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self._max)
        self.slider.setValue(0)
        self.slider.setFixedWidth(120)
        self.slider.setStyleSheet(f"""
            QSlider {{
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                background: #2D3D4F;
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {color};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {color};
                border-radius: 3px;
            }}
        """)
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider)

        # Value display
        self.value_label = QLabel("0")
        self.value_label.setFixedWidth(24)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet(f"""
            background: {color}33;
            border: 1px solid {color};
            border-radius: 4px;
            color: {color};
            font-weight: bold;
            font-size: 12px;
        """)
        layout.addWidget(self.value_label)

        layout.addStretch()

    def _on_value_changed(self, value: int):
        self._value = value
        self.value_label.setText(str(value))
        self.valueChanged.emit(value)

    def value(self) -> int:
        return self._value

    def setValue(self, value: int):
        self.slider.setValue(max(0, min(self._max, value)))

    def setTheme(self, theme: str):
        """Update slider colors based on theme"""
        if theme == "dark":
            groove_color = "#2D3D4F"
        else:
            groove_color = "#D1D5DB"

        self.slider.setStyleSheet(f"""
            QSlider {{
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                background: {groove_color};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {self._color};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {self._color};
                border-radius: 3px;
            }}
        """)


class AttachmentComboBox(QComboBox):
    """Enhanced combo box for attachments with stat preview"""

    def __init__(self, placeholder: str = "None", parent=None):
        super().__init__(parent)
        self._stats_data = {}
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QComboBox {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 6px;
                padding: 8px 12px;
                color: #E0E1E3;
                font-size: 12px;
                min-width: 150px;
            }
            QComboBox:hover {
                border-color: #4A90D9;
            }
            QComboBox:focus {
                border-color: #4A90D9;
            }
        """)

    def setStatsData(self, data: Dict[str, Dict]):
        """Set attachment statistics data"""
        self._stats_data = data

    def currentStats(self) -> Optional[Dict]:
        """Get stats for currently selected item"""
        name = self.currentText()
        if name and name != "None":
            return self._stats_data.get(name)
        return None


class WeaponSelectorSignals(QObject):
    """Signals for weapon selector component"""

    weapon_selected = pyqtSignal(dict)
    cost_calculated = pyqtSignal(dict)
    loadout_changed = pyqtSignal(dict)


class WeaponSelector(QWidget):
    """Complete weapon loadout selector with all attachments and enhancements"""

    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.signals = WeaponSelectorSignals()
        self._theme = "dark"  # Default theme

        self.weapons: Dict[str, Weapon] = {}
        self.attachments: Dict[str, Any] = {}
        self.scopes: Dict[str, Any] = {}
        self.sights: Dict[str, Any] = {}
        self.current_weapon: Optional[Weapon] = None

        # Loadout state
        self._amplifier: Optional[str] = None
        self._scope: Optional[str] = None
        self._sight_1: Optional[str] = None
        self._sight_2: Optional[str] = None
        self._damage_enh: int = 0
        self._accuracy_enh: int = 0
        self._economy_enh: int = 0

        self.session_ammo_used = Decimal("0")
        self.session_decay = Decimal("0")
        self.session_shots = 0

        logger.info("WeaponSelector initializing...")

        self.setup_ui()
        self.connect_signals()

        QTimer.singleShot(50, self._delayed_load)

        logger.info("WeaponSelector initialization complete")

    @property
    def theme(self) -> str:
        """Get current theme"""
        return self._theme

    @theme.setter
    def theme(self, value: str):
        """Set theme and update UI"""
        self._theme = value
        self._apply_theme()

    def setup_ui(self):
        """Setup the complete user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header = QLabel("WEAPON LOADOUT CONFIGURATOR")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #4A90D9;
            letter-spacing: 1px;
        """)
        layout.addWidget(header)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setSizes([550, 450])
        splitter.setChildrenCollapsible(False)

        # Left panel - Selection
        left_panel = self._create_selection_panel()
        splitter.addWidget(left_panel)

        # Right panel - Analysis
        right_panel = self._create_analysis_panel()
        splitter.addWidget(right_panel)

        layout.addWidget(splitter)

        # Bottom - Session stats
        session_bar = self._create_session_bar()
        layout.addWidget(session_bar)

    def _create_selection_panel(self) -> QWidget:
        """Create the weapon and attachment selection panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Weapon filter and search
        filter_group = QGroupBox("WEAPON SELECTION")
        filter_group.setStyleSheet("""
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
        filter_layout = QVBoxLayout(filter_group)
        filter_layout.setContentsMargins(10, 15, 10, 10)

        # Type filter and search row
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)

        # Weapon type filter
        type_label = QLabel("Type:")
        type_label.setStyleSheet("color: #888; font-size: 12px;")
        row_layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItem("All Types", None)
        self.type_combo.addItem("Pistol", "Pistol")
        self.type_combo.addItem("Rifle", "Rifle")
        self.type_combo.addItem("Carbine", "Carbine")
        self.type_combo.addItem("Shotgun", "Shotgun")
        self.type_combo.addItem("Melee", "Melee")
        self.type_combo.addItem("Power Fist", "Power Fist")
        self.type_combo.addItem("Flamethrower", "Flamethrower")
        self.type_combo.addItem("Mindforce", "Mindforce")
        self.type_combo.setStyleSheet("""
            QComboBox {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 6px 10px;
                color: #E0E1E3;
                min-width: 120px;
            }
        """)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        row_layout.addWidget(self.type_combo)

        # Search
        search_label = QLabel("Search:")
        search_label.setStyleSheet("color: #888; font-size: 12px;")
        row_layout.addWidget(search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter weapons...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                padding: 6px 10px;
                color: #E0E1E3;
            }
            QLineEdit:focus {
                border-color: #4A90D9;
            }
        """)
        self.search_edit.textChanged.connect(self._on_search_changed)
        row_layout.addWidget(self.search_edit)

        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #2D3D4F;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                color: #E0E1E3;
            }
            QPushButton:hover {
                background: #3D4D5F;
            }
        """)
        clear_btn.clicked.connect(self._clear_search)
        row_layout.addWidget(clear_btn)

        filter_layout.addLayout(row_layout)

        # Weapon table
        self.weapon_table = QTableWidget()
        self.weapon_table.setColumnCount(5)
        self.weapon_table.setHorizontalHeaderLabels(
            ["Name", "Type", "Ammo", "Decay", "DPS"]
        )
        self.weapon_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.weapon_table.setSortingEnabled(True)
        self.weapon_table.itemSelectionChanged.connect(self._on_weapon_selected)
        self.weapon_table.setAlternatingRowColors(True)
        self.weapon_table.setStyleSheet("""
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

        header = self.weapon_table.horizontalHeader()
        try:
            # Try PyQt6 standard approach
            if hasattr(QHeaderView, "ResizeMode"):
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
                for i in range(1, 5):
                    header.setSectionResizeMode(
                        i, QHeaderView.ResizeMode.ResizeToContents
                    )
            else:
                # PyQt6 with older style enums
                header.setSectionResizeMode(0, 3)  # Stretch
                for i in range(1, 5):
                    header.setSectionResizeMode(i, 1)  # ResizeToContents
        except (AttributeError, TypeError):
            # If all else fails, just let Qt use defaults
            pass

        filter_layout.addWidget(self.weapon_table)

        layout.addWidget(filter_group)

        # Attachments group
        attach_group = QGroupBox("ATTACHMENTS & ENHANCERS")
        attach_group.setStyleSheet("""
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
        attach_layout = QVBoxLayout(attach_group)
        attach_layout.setContentsMargins(10, 15, 10, 10)
        attach_layout.setSpacing(12)

        # Attachment combos row
        combo_row = QHBoxLayout()
        combo_row.setSpacing(10)

        # Amplifier
        amp_layout = QVBoxLayout()
        amp_layout.setSpacing(4)
        amp_label = QLabel("AMPLIFIER")
        amp_label.setStyleSheet("color: #666; font-size: 10px; font-weight: bold;")
        amp_layout.addWidget(amp_label)
        self.amplifier_combo = AttachmentComboBox("No Amplifier")
        self.amplifier_combo.currentTextChanged.connect(self._on_attachment_changed)
        amp_layout.addWidget(self.amplifier_combo)
        combo_row.addLayout(amp_layout)

        # Scope
        scope_layout = QVBoxLayout()
        scope_layout.setSpacing(4)
        scope_label = QLabel("SCOPE")
        scope_label.setStyleSheet("color: #666; font-size: 10px; font-weight: bold;")
        scope_layout.addWidget(scope_label)
        self.scope_combo = AttachmentComboBox("No Scope")
        self.scope_combo.currentTextChanged.connect(self._on_attachment_changed)
        scope_layout.addWidget(self.scope_combo)
        combo_row.addLayout(scope_layout)

        attach_layout.addLayout(combo_row)

        # Second attachment row
        combo_row2 = QHBoxLayout()
        combo_row2.setSpacing(10)

        # Sight 1
        sight1_layout = QVBoxLayout()
        sight1_layout.setSpacing(4)
        sight1_label = QLabel("SIGHT 1")
        sight1_label.setStyleSheet("color: #666; font-size: 10px; font-weight: bold;")
        sight1_layout.addWidget(sight1_label)
        self.sight1_combo = AttachmentComboBox("No Sight")
        self.sight1_combo.currentTextChanged.connect(self._on_attachment_changed)
        sight1_layout.addWidget(self.sight1_combo)
        combo_row2.addLayout(sight1_layout)

        # Sight 2
        sight2_layout = QVBoxLayout()
        sight2_layout.setSpacing(4)
        sight2_label = QLabel("SIGHT 2")
        sight2_label.setStyleSheet("color: #666; font-size: 10px; font-weight: bold;")
        sight2_layout.addWidget(sight2_label)
        self.sight2_combo = AttachmentComboBox("No Sight")
        self.sight2_combo.currentTextChanged.connect(self._on_attachment_changed)
        sight2_layout.addWidget(self.sight2_combo)
        combo_row2.addLayout(sight2_layout)

        attach_layout.addLayout(combo_row2)

        # Enhancement sliders
        enh_group = QGroupBox("ENHANCEMENTS (0-20)")
        enh_group.setStyleSheet("""
            QGroupBox {
                background: #1A1F2E;
                border: 1px solid #2D3D4F;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        enh_layout = QVBoxLayout(enh_group)
        enh_layout.setSpacing(8)

        self.damage_slider = EnhancementSlider("DAMAGE", "⚔️", "#E74C3C")
        self.damage_slider.valueChanged.connect(self._on_enhancement_changed)
        enh_layout.addWidget(self.damage_slider)

        self.accuracy_slider = EnhancementSlider("ACCURACY", "🎯", "#3498DB")
        self.accuracy_slider.valueChanged.connect(self._on_enhancement_changed)
        enh_layout.addWidget(self.accuracy_slider)

        self.economy_slider = EnhancementSlider("ECONOMY", "💰", "#2ECC71")
        self.economy_slider.valueChanged.connect(self._on_enhancement_changed)
        enh_layout.addWidget(self.economy_slider)

        attach_layout.addWidget(enh_group)

        # Loadout preset buttons
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(8)

        save_btn = QPushButton("💾 Save Loadout")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #2D3D4F;
                border: 1px solid #4A90D9;
                border-radius: 6px;
                padding: 8px 16px;
                color: #4A90D9;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4A90D9;
                color: #1A1F2E;
            }
        """)
        save_btn.clicked.connect(self._save_loadout)
        preset_layout.addWidget(save_btn)

        load_btn = QPushButton("📂 Load Loadout")
        load_btn.setStyleSheet("""
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
        load_btn.clicked.connect(self._load_loadout)
        preset_layout.addWidget(load_btn)

        preset_layout.addStretch()

        reset_btn = QPushButton("🔄 Reset")
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #2D3D4F;
                border: 1px solid #E74C3C;
                border-radius: 6px;
                padding: 8px 16px;
                color: #E74C3C;
            }
            QPushButton:hover {
                background: #E74C3C;
                color: #1A1F2E;
            }
        """)
        reset_btn.clicked.connect(self._reset_loadout)
        preset_layout.addWidget(reset_btn)

        attach_layout.addLayout(preset_layout)

        layout.addWidget(attach_group)
        layout.addStretch()

        return widget

    def _create_analysis_panel(self) -> QWidget:
        """Create the cost and performance analysis panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Weapon info card
        info_group = QGroupBox("WEAPON INFO")
        info_group.setStyleSheet("""
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
        info_layout = QGridLayout(info_group)
        info_layout.setContentsMargins(10, 15, 10, 10)

        # Weapon name (large)
        self.weapon_name_label = QLabel("Select a weapon")
        self.weapon_name_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #E0E1E3;
        """)
        info_layout.addWidget(self.weapon_name_label, 0, 0, 1, 2)

        # Weapon type
        self.weapon_type_label = QLabel("Type: --")
        self.weapon_type_label.setStyleSheet("color: #888; font-size: 12px;")
        info_layout.addWidget(self.weapon_type_label, 1, 0)

        # Weapon range
        self.weapon_range_label = QLabel("Range: --")
        self.weapon_range_label.setStyleSheet("color: #888; font-size: 12px;")
        info_layout.addWidget(self.weapon_range_label, 1, 1)

        info_layout.setRowMinimumHeight(2, 15)

        layout.addWidget(info_group)

        # Cost analysis
        cost_group = QGroupBox("COST ANALYSIS")
        cost_group.setStyleSheet("""
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
        cost_layout = QGridLayout(cost_group)
        cost_layout.setContentsMargins(10, 15, 10, 10)
        cost_layout.setSpacing(8)

        # Row labels
        cost_layout.addWidget(QLabel("Base Cost:"), 0, 0)
        cost_layout.addWidget(QLabel("Attachment Cost:"), 1, 0)
        cost_layout.addWidget(QLabel("Enhancement Cost:"), 2, 0)
        cost_layout.addWidget(QLabel("───"), 3, 0)
        cost_layout.addWidget(QLabel("TOTAL COST/SHOT:"), 4, 0)

        # Animated value displays
        self.base_cost_label = SimpleValueLabel("--")
        self.base_cost_label.setStyleSheet("color: #E0E1E3; font-weight: bold;")
        cost_layout.addWidget(self.base_cost_label, 0, 1)

        self.attachment_cost_label = SimpleValueLabel("--")
        self.attachment_cost_label.setStyleSheet("color: #E0E1E3;")
        cost_layout.addWidget(self.attachment_cost_label, 1, 1)

        self.enhancement_cost_label = SimpleValueLabel("--")
        self.enhancement_cost_label.setStyleSheet("color: #E0E1E3;")
        cost_layout.addWidget(self.enhancement_cost_label, 2, 1)

        cost_layout.addWidget(QLabel("───"), 3, 1)

        self.total_cost_label = SimpleValueLabel("--")
        self.total_cost_label.setStyleSheet("""
            color: #4A90D9;
            font-weight: bold;
            font-size: 16px;
        """)
        cost_layout.addWidget(self.total_cost_label, 4, 1)

        layout.addWidget(cost_group)

        # Performance analysis
        perf_group = QGroupBox("PERFORMANCE")
        perf_group.setStyleSheet("""
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
        perf_layout = QGridLayout(perf_group)
        perf_layout.setContentsMargins(10, 15, 10, 10)
        perf_layout.setSpacing(8)

        # DPS
        perf_layout.addWidget(QLabel("DPS:"), 0, 0)
        self.dps_label = SimpleValueLabel("--")
        self.dps_label.setStyleSheet("color: #E74C3C; font-weight: bold;")
        perf_layout.addWidget(self.dps_label, 0, 1)

        # DPP (Damage per PEC)
        perf_layout.addWidget(QLabel("DPP:"), 1, 0)
        self.dpp_label = SimpleValueLabel("--")
        self.dpp_label.setStyleSheet("color: #2ECC71; font-weight: bold;")
        perf_layout.addWidget(self.dpp_label, 1, 1)

        # Efficiency
        perf_layout.addWidget(QLabel("EFFICIENCY:"), 2, 0)
        self.efficiency_label = SimpleValueLabel("--")
        self.efficiency_label.setStyleSheet("color: #3498DB; font-weight: bold;")
        perf_layout.addWidget(self.efficiency_label, 2, 1)

        # Ammo/shot
        perf_layout.addWidget(QLabel("AMMO/SHOT:"), 3, 0)
        self.ammo_per_shot_label = SimpleValueLabel("--")
        self.ammo_per_shot_label.setStyleSheet("color: #E0E1E3;")
        perf_layout.addWidget(self.ammo_per_shot_label, 3, 1)

        layout.addWidget(perf_group)

        # Cost breakdown bar
        breakdown_group = QGroupBox("COST BREAKDOWN")
        breakdown_group.setStyleSheet("""
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
        breakdown_layout = QVBoxLayout(breakdown_group)
        breakdown_layout.setContentsMargins(10, 15, 10, 10)

        self.cost_breakdown_bar = QProgressBar()
        self.cost_breakdown_bar.setStyleSheet("""
            QProgressBar {
                background: #1A1F2E;
                border: 1px solid #2D3D4F;
                border-radius: 4px;
                height: 24px;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 3px;
            }
        """)
        self.cost_breakdown_bar.setTextVisible(False)
        breakdown_layout.addWidget(self.cost_breakdown_bar)

        breakdown_legend = QHBoxLayout()
        breakdown_legend.setSpacing(15)

        decay_dot = QLabel("●")
        decay_dot.setStyleSheet("color: #E74C3C;")
        decay_dot_label = QLabel("Decay")
        decay_dot_label.setStyleSheet("color: #888; font-size: 11px;")
        breakdown_legend.addWidget(decay_dot)
        breakdown_legend.addWidget(decay_dot_label)

        ammo_dot = QLabel("●")
        ammo_dot.setStyleSheet("color: #3498DB;")
        ammo_dot_label = QLabel("Ammo")
        ammo_dot_label.setStyleSheet("color: #888; font-size: 11px;")
        breakdown_legend.addWidget(ammo_dot)
        breakdown_legend.addWidget(ammo_dot_label)

        breakdown_legend.addStretch()
        breakdown_layout.addLayout(breakdown_legend)

        layout.addWidget(breakdown_group)

        layout.addStretch()

        return widget

    def _create_session_bar(self) -> QWidget:
        """Create the session statistics bar"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background: #1E2A3A;
                border: 1px solid #2D3D4F;
                border-radius: 8px;
            }
        """)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(20)

        # Title
        session_title = QLabel("SESSION STATS")
        session_title.setStyleSheet(
            "color: #4A90D9; font-weight: bold; font-size: 12px;"
        )
        layout.addWidget(session_title)

        # Stats
        self.session_ammo_label = QLabel("Ammo: 0")
        self.session_ammo_label.setStyleSheet("color: #E0E1E3; font-size: 13px;")
        layout.addWidget(self.session_ammo_label)

        self.session_decay_label = QLabel("Decay: 0.00 PED")
        self.session_decay_label.setStyleSheet("color: #E0E1E3; font-size: 13px;")
        layout.addWidget(self.session_decay_label)

        self.session_shots_label = QLabel("Shots: 0")
        self.session_shots_label.setStyleSheet("color: #E0E1E3; font-size: 13px;")
        layout.addWidget(self.session_shots_label)

        self.session_cost_label = QLabel("Cost: 0.00 PED")
        self.session_cost_label.setStyleSheet(
            "color: #4A90D9; font-weight: bold; font-size: 13px;"
        )
        layout.addWidget(self.session_cost_label)

        layout.addStretch()

        # Reset button
        reset_btn = QPushButton("Reset Session")
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #2D3D4F;
                border: 1px solid #E74C3C;
                border-radius: 6px;
                padding: 6px 14px;
                color: #E74C3C;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #E74C3C;
                color: #1A1F2E;
            }
        """)
        reset_btn.clicked.connect(self._reset_session)
        layout.addWidget(reset_btn)

        return widget

    def connect_signals(self):
        """Connect signals and slots"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_session_stats)
        self.update_timer.start(1000)
        logger.debug("WeaponSelector signals connected")

    def _delayed_load(self):
        """Delayed data loading"""
        try:
            asyncio.run(self._load_data())
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            logger.info("Using empty data - database not initialized yet")

    async def _load_data(self):
        """Load weapon and attachment data from database"""
        logger.info("Loading weapon data from database...")

        if not self.db_manager:
            logger.warning("No db_manager available")
            return

        # Load weapons
        try:
            weapons = await self.db_manager.get_all_weapons()
            self.weapons = {w.name: w for w in weapons}
            logger.info(f"Loaded {len(self.weapons)} weapons")
        except Exception as e:
            logger.error(f"Error loading weapons: {e}")
            self.weapons = {}

        # Load attachments
        try:
            from src.services.game_data_service import GameDataService

            data_service = GameDataService()

            all_attachments = await data_service.get_all_attachments()

            # Create dict with name as key
            self.attachments = {}
            self.scopes = {}
            self.sights = {}

            for a in all_attachments:
                self.attachments[a.name] = {
                    "decay": float(a.decay),
                    "ammo": a.ammo,
                    "damage_bonus": float(a.damage_bonus),
                    "economy_bonus": float(a.economy_bonus),
                    "type": a.attachment_type,
                    "range_bonus": a.range_bonus,
                }
                if a.attachment_type == "Scope":
                    self.scopes[a.name] = self.attachments[a.name]
                elif a.attachment_type == "Sight":
                    self.sights[a.name] = self.attachments[a.name]

            logger.info(
                f"Loaded {len(self.attachments)} attachments ({len(self.scopes)} scopes, {len(self.sights)} sights)"
            )
        except Exception as e:
            logger.error(f"Error loading attachments: {e}")
            self.attachments = {}
            self.scopes = {}
            self.sights = {}

        # Populate UI
        self._populate_weapon_table()
        self._populate_attachment_combos()

        logger.info("Data loading complete")

    def _populate_weapon_table(self):
        """Populate the weapon table with all weapons"""
        self.weapon_table.setRowCount(0)

        for weapon in self.weapons.values():
            row = self.weapon_table.rowCount()
            self.weapon_table.insertRow(row)

            # Name
            name_item = QTableWidgetItem(weapon.name)
            name_item.setData(Qt.ItemDataRole.UserRole, weapon.name)
            self.weapon_table.setItem(row, 0, name_item)

            # Type
            type_item = QTableWidgetItem(weapon.weapon_type or "Unknown")
            self.weapon_table.setItem(row, 1, type_item)

            # Ammo
            ammo_item = QTableWidgetItem(str(weapon.ammo))
            self.weapon_table.setItem(row, 2, ammo_item)

            # Decay
            decay_val = float(weapon.decay) if weapon.decay else 0
            decay_item = QTableWidgetItem(f"{decay_val:.5f}")
            self.weapon_table.setItem(row, 3, decay_item)

            # DPS
            dps_val = float(weapon.dps) if weapon.dps else 0
            dps_item = QTableWidgetItem(f"{dps_val:.2f}")
            self.weapon_table.setItem(row, 4, dps_item)

    def _populate_attachment_combos(self):
        """Populate all attachment combo boxes"""
        # Amplifier - show all non-scope/sight attachments
        self.amplifier_combo.clear()
        self.amplifier_combo.addItem("None", None)
        amp_data = {}
        for name, att in self.attachments.items():
            if att.get("type") not in ["Scope", "Sight"]:
                self.amplifier_combo.addItem(name, name)
                amp_data[name] = att
        self.amplifier_combo.setStatsData(amp_data)

        # Scopes
        self.scope_combo.clear()
        self.scope_combo.addItem("None", None)
        scope_data = {}
        for name, att in self.scopes.items():
            self.scope_combo.addItem(name, name)
            scope_data[name] = att
        self.scope_combo.setStatsData(scope_data)

        # Sights
        self.sight1_combo.clear()
        self.sight1_combo.addItem("None", None)
        self.sight2_combo.clear()
        self.sight2_combo.addItem("None", None)
        sight_data = {}
        for name, att in self.sights.items():
            self.sight1_combo.addItem(name, name)
            self.sight2_combo.addItem(name, name)
            sight_data[name] = att
        self.sight1_combo.setStatsData(sight_data)
        self.sight2_combo.setStatsData(sight_data)

    def _on_weapon_selected(self):
        """Handle weapon selection from table"""
        selected = self.weapon_table.selectedItems()
        if not selected:
            return

        weapon_name = selected[0].data(Qt.ItemDataRole.UserRole)
        if weapon_name and weapon_name in self.weapons:
            self.current_weapon = self.weapons[weapon_name]
            self._update_weapon_info()
            self._calculate_costs()

            self.signals.weapon_selected.emit(
                {
                    "weapon": self.current_weapon.name,
                    "type": self.current_weapon.weapon_type,
                }
            )

    def _on_type_changed(self, text: str):
        """Handle weapon type filter change"""
        self._filter_weapons()

    def _on_search_changed(self, text: str):
        """Handle search filter change"""
        self._filter_weapons()

    def _filter_weapons(self):
        """Filter weapons by type and search"""
        type_filter = self.type_combo.currentData()
        search_text = self.search_edit.text().lower()

        for row in range(self.weapon_table.rowCount()):
            name_item = self.weapon_table.item(row, 0)
            type_item = self.weapon_table.item(row, 1)

            if not name_item or not type_item:
                continue

            name = name_item.text()
            weapon_type = type_item.text()

            # Type filter
            if type_filter and weapon_type != type_filter:
                self.weapon_table.setRowHidden(row, True)
                continue

            # Search filter
            if search_text and search_text not in name.lower():
                self.weapon_table.setRowHidden(row, True)
                continue

            self.weapon_table.setRowHidden(row, False)

    def _clear_search(self):
        """Clear search and filters"""
        self.search_edit.clear()
        self.type_combo.setCurrentIndex(0)

    def _on_attachment_changed(self, text: str):
        """Handle attachment selection change"""
        self._amplifier = self.amplifier_combo.currentData()
        self._scope = self.scope_combo.currentData()
        self._sight_1 = self.sight1_combo.currentData()
        self._sight_2 = self.sight2_combo.currentData()
        self._calculate_costs()

    def _on_enhancement_changed(self, value: int):
        """Handle enhancement level change"""
        self._damage_enh = self.damage_slider.value()
        self._accuracy_enh = self.accuracy_slider.value()
        self._economy_enh = self.economy_slider.value()
        self._calculate_costs()

    def _update_weapon_info(self):
        """Update weapon info display"""
        if not self.current_weapon:
            return

        self.weapon_name_label.setText(self.current_weapon.name)
        self.weapon_type_label.setText(
            f"Type: {self.current_weapon.weapon_type or 'Unknown'}"
        )
        # Use range_ instead of range_value (dataclass uses trailing underscore)
        range_val = getattr(self.current_weapon, "range_", None) or 50
        self.weapon_range_label.setText(f"Range: {range_val}m")

    def _calculate_costs(self):
        """Calculate and display costs with all modifiers"""
        if not self.current_weapon:
            return

        # Base values - convert Decimal to float
        base_decay = (
            float(self.current_weapon.decay) if self.current_weapon.decay else 0.0
        )
        base_ammo = self.current_weapon.ammo if self.current_weapon.ammo else 0

        # Enhancement multipliers (0-20 scale)
        damage_mult = 1.0 + (self._damage_enh * 0.1)  # +10% per level
        economy_mult = 1.0 - (self._economy_enh * 0.05)  # -5% per level
        accuracy_mult = 1.0 + (self._accuracy_enh * 0.02)  # +2% per level

        # Apply enhancements to base
        enhanced_decay = base_decay * damage_mult * economy_mult
        enhanced_ammo = base_ammo * damage_mult

        # Add attachment costs
        amp_decay = 0.0
        amp_ammo = 0
        if self._amplifier and self._amplifier in self.attachments:
            amp = self.attachments[self._amplifier]
            amp_decay += float(amp.get("decay", 0))
            amp_ammo += amp.get("ammo", 0)

        scope_decay = 0.0
        scope_ammo = 0
        if self._scope and self._scope in self.scopes:
            scope = self.scopes[self._scope]
            scope_decay += float(scope.get("decay", 0))
            scope_ammo += scope.get("ammo", 0)

        sight1_decay = 0.0
        sight1_ammo = 0
        if self._sight_1 and self._sight_1 in self.sights:
            sight = self.sights[self._sight_1]
            sight1_decay += float(sight.get("decay", 0))
            sight1_ammo += sight.get("ammo", 0)

        sight2_decay = 0.0
        sight2_ammo = 0
        if self._sight_2 and self._sight_2 in self.sights:
            sight = self.sights[self._sight_2]
            sight2_decay += float(sight.get("decay", 0))
            sight2_ammo += sight.get("ammo", 0)

        # Calculate totals
        total_decay = (
            enhanced_decay + amp_decay + scope_decay + sight1_decay + sight2_decay
        )
        total_ammo = enhanced_ammo + amp_ammo + scope_ammo + sight1_ammo + sight2_ammo
        ammo_cost = total_ammo / 10000.0  # Convert to PED
        total_cost = total_decay + ammo_cost

        # Calculate DPS
        base_dps = float(self.current_weapon.dps) if self.current_weapon.dps else 0.0
        enhanced_dps = base_dps * damage_mult

        # DPP (Damage per PEC) - 100 PEC = 1 PED
        # DPP = Total Damage / Total Cost in PEC
        # Total Cost in PEC = (decay * 100) + (ammo / 100)  [since 1 PED = 100 PEC]
        total_cost_pec = (total_cost * 100.0) if total_cost > 0 else 0.0
        damage_per_pec = (
            (enhanced_dps * 3.0) / total_cost_pec if total_cost_pec > 0 else 0.0
        )

        # Calculate efficiency percentage (vs base)
        base_cost = base_decay + (base_ammo / 10000.0)
        efficiency = (base_cost / total_cost * 100.0) if total_cost > 0 else 100.0

        # Update displays
        self.base_cost_label.setValue(base_cost)
        self.attachment_cost_label.setValue(total_cost - base_cost)
        self.enhancement_cost_label.setValue(
            total_cost * 0.1 if total_cost > 0 else 0.0
        )
        self.total_cost_label.setValue(total_cost)

        self.dps_label.setValue(enhanced_dps)
        self.dpp_label.setValue(damage_per_pec)
        self.efficiency_label.setValue(efficiency)
        self.ammo_per_shot_label.setValue(float(total_ammo))

        # Update cost breakdown bar
        if total_cost > 0:
            decay_percent = int((total_decay / total_cost) * 100)

            # Create gradient style
            self.cost_breakdown_bar.setStyleSheet(f"""
                QProgressBar {{
                    background: #1A1F2E;
                    border: 1px solid #2D3D4F;
                    border-radius: 4px;
                    height: 24px;
                    text-align: center;
                }}
                QProgressBar::chunk {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #E74C3C, stop:{decay_percent / 100} #E74C3C,
                        stop:{decay_percent / 100} #3498DB, stop:1 #3498DB);
                    border-radius: 3px;
                }}
            """)
            self.cost_breakdown_bar.setMaximum(100)
            self.cost_breakdown_bar.setValue(100)

        self.signals.cost_calculated.emit(
            {
                "total_cost": total_cost,
                "decay": total_decay,
                "ammo": ammo_cost,
                "dps": enhanced_dps,
                "efficiency": efficiency,
            }
        )

    def _update_session_stats(self):
        """Update session statistics (placeholder for real tracking)"""
        pass

    def _reset_session(self):
        """Reset session statistics"""
        self.session_ammo_used = Decimal("0")
        self.session_decay = Decimal("0")
        self.session_shots = 0
        self.session_ammo_label.setText("Ammo: 0")
        self.session_decay_label.setText("Decay: 0.00 PED")
        self.session_shots_label.setText("Shots: 0")
        self.session_cost_label.setText("Cost: 0.00 PED")

    def _save_loadout(self):
        """Save current loadout to database"""
        if not self.current_weapon:
            QMessageBox.warning(self, "No Weapon", "Please select a weapon first.")
            return

        # Get loadout name
        name, ok = self._get_loadout_name()
        if not ok or not name:
            return

        # Create loadout
        from src.services.loadout_service import LoadoutService, WeaponLoadout

        loadout = WeaponLoadout(
            name=name,
            weapon=self.current_weapon.name,
            amplifier=self._amplifier,
            scope=self._scope,
            sight_1=self._sight_1,
            sight_2=self._sight_2,
            damage_enh=self._damage_enh,
            accuracy_enh=self._accuracy_enh,
            economy_enh=self._economy_enh,
        )

        # Save to database
        async def save():
            service = LoadoutService()
            await service.create_loadout(loadout)
            return True

        try:
            asyncio.run(save())
            QMessageBox.information(
                self, "Saved", f"Loadout '{name}' saved successfully!"
            )
            logger.info(f"Loadout saved: {name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save loadout: {e}")
            logger.error(f"Error saving loadout: {e}")

    def _get_loadout_name(self) -> tuple:
        """Get loadout name from user"""
        from PyQt6.QtWidgets import QInputDialog, QLineEdit

        return QInputDialog.getText(
            self, "Save Loadout", "Enter loadout name:", QLineEdit.EchoMode.Normal
        )

    def _load_loadout(self):
        """Load saved loadouts"""

        async def load():
            from src.services.loadout_service import LoadoutService

            service = LoadoutService()
            loadouts = await service.get_all_loadouts()
            return [l.name for l in loadouts]

        try:
            loadout_names = asyncio.run(load())
            if not loadout_names:
                QMessageBox.information(self, "No Loadouts", "No saved loadouts found.")
                return

            # Show loadout selection dialog
            name, ok = QInputDialog.getItem(
                self, "Load Loadout", "Select a loadout:", loadout_names, 0, False
            )

            if ok and name:
                self._apply_loadout(name)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load loadouts: {e}")
            logger.error(f"Error loading loadouts: {e}")

    def _apply_loadout(self, name: str):
        """Apply a saved loadout"""

        async def apply():
            from src.services.loadout_service import LoadoutService

            service = LoadoutService()
            loadout = await service.get_loadout_by_name(name)
            return loadout

        try:
            loadout = asyncio.run(apply())
            if not loadout:
                return

            # Find and select weapon
            if loadout.weapon in self.weapons:
                self.current_weapon = self.weapons[loadout.weapon]
                # Select in table
                for row in range(self.weapon_table.rowCount()):
                    item = self.weapon_table.item(row, 0)
                    if item and item.text() == loadout.weapon:
                        self.weapon_table.selectRow(row)
                        break
                self._update_weapon_info()

            # Set attachments
            self._set_combo_by_data(self.amplifier_combo, loadout.amplifier)
            self._set_combo_by_data(self.scope_combo, loadout.scope)
            self._set_combo_by_data(self.sight1_combo, loadout.sight_1)
            self._set_combo_by_data(self.sight2_combo, loadout.sight_2)

            # Set enhancers
            self.damage_slider.setValue(loadout.damage_enh)
            self.accuracy_slider.setValue(loadout.accuracy_enh)
            self.economy_slider.setValue(loadout.economy_enh)

            self._calculate_costs()
            logger.info(f"Applied loadout: {name}")
        except Exception as e:
            logger.error(f"Error applying loadout: {e}")

    def _set_combo_by_data(self, combo, data):
        """Set combo box to item with matching data"""
        for i in range(combo.count()):
            if combo.itemData(i) == data:
                combo.setCurrentIndex(i)
                return
        # If not found, try by text
        if data:
            index = combo.findText(data)
            if index >= 0:
                combo.setCurrentIndex(index)

    def _reset_loadout(self):
        """Reset loadout to defaults"""
        self.amplifier_combo.setCurrentIndex(0)
        self.scope_combo.setCurrentIndex(0)
        self.sight1_combo.setCurrentIndex(0)
        self.sight2_combo.setCurrentIndex(0)
        self.damage_slider.setValue(0)
        self.accuracy_slider.setValue(0)
        self.economy_slider.setValue(0)

    def _apply_theme(self):
        """Apply the current theme to all UI elements"""
        if self._theme == "dark":
            # Dark theme colors
            bg_color = "#1A1F2E"
            fg_color = "#E0E1E3"
            border_color = "#2D3D4F"
            accent_color = "#4A90D9"
            group_bg = "#1E2A3A"
            input_bg = "#1E2A3A"
        else:
            # Light theme colors - fully visible
            bg_color = "#FFFFFF"
            fg_color = "#19232D"
            border_color = "#D1D5DB"
            accent_color = "#2563EB"
            group_bg = "#F3F4F6"
            input_bg = "#FFFFFF"

        # Apply to main widget
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
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QLineEdit {{
                background: {input_bg};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 6px 10px;
                color: {fg_color};
            }}
            QLineEdit:focus {{
                border-color: {accent_color};
            }}
            QComboBox {{
                background: {input_bg};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 6px 10px;
                color: {fg_color};
                min-width: 120px;
            }}
            QComboBox:hover {{
                border-color: {accent_color};
            }}
            QPushButton {{
                background: {group_bg};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 8px 16px;
                color: {fg_color};
            }}
            QPushButton:hover {{
                background: {accent_color}22;
                border-color: {accent_color};
            }}
            QTableWidget {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                gridline-color: {border_color};
            }}
            QTableWidget::item:selected {{
                background: {accent_color}44;
            }}
            QHeaderView::section {{
                background: {group_bg};
                color: {fg_color};
                padding: 8px;
                font-weight: bold;
            }}
            QLabel {{
                color: {fg_color};
            }}
            QProgressBar {{
                background: {group_bg};
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
            QFrame {{
                background: {group_bg};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)

        # Update sliders
        self.damage_slider.setTheme(self._theme)
        self.accuracy_slider.setTheme(self._theme)
        self.economy_slider.setTheme(self._theme)

    def setTheme(self, theme: str = "dark"):
        """Set theme and update UI"""
        self._theme = theme
        self._apply_theme()
