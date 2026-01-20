"""
Weapon selection UI components
Separated UI logic from business logic
"""

from typing import Optional, List
from decimal import Decimal

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QGroupBox, QLabel, QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont

from src.services.weapon_service import (
    WeaponStats, AttachmentStats, EnhancedWeaponStats,
    WeaponCalculator, WeaponDataManager
)


class WeaponSelectionSignals(QObject):
    """Signals for weapon selection component"""
    weapon_selected = pyqtSignal(WeaponStats)
    search_changed = pyqtSignal(str)


class WeaponTableWidget(QWidget):
    """Weapon table widget with search functionality"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = WeaponSelectionSignals()
        self.weapons: List[WeaponStats] = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Search box
        search_container = QHBoxLayout()
        search_container.addWidget(QLabel("Search:"))
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search weapons...")
        self.search_edit.textChanged.connect(self.on_search_changed)
        search_container.addWidget(self.search_edit)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_search)
        search_container.addWidget(clear_btn)
        
        layout.addLayout(search_container)
        
        # Weapon table
        self.weapon_table = QTableWidget()
        self.weapon_table.setColumnCount(5)
        self.weapon_table.setHorizontalHeaderLabels([
            "Name", "Type", "Damage", "Ammo/Shot", "Decay"
        ])
        self.weapon_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.weapon_table.setSortingEnabled(True)
        self.weapon_table.itemSelectionChanged.connect(self.on_weapon_selected)
        
        # Configure columns
        header = self.weapon_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.weapon_table)
    
    def set_weapons(self, weapons: List[WeaponStats]):
        """Set the weapons list"""
        self.weapons = weapons
        self.populate_table()
    
    def populate_table(self):
        """Populate the table with weapons"""
        self.weapon_table.setRowCount(len(self.weapons))
        
        for row, weapon in enumerate(self.weapons):
            self.weapon_table.setItem(row, 0, QTableWidgetItem(weapon.name))
            self.weapon_table.setItem(row, 1, QTableWidgetItem(weapon.weapon_type))
            self.weapon_table.setItem(row, 2, QTableWidgetItem(str(weapon.damage)))
            self.weapon_table.setItem(row, 3, QTableWidgetItem(str(weapon.ammo_burn)))
            self.weapon_table.setItem(row, 4, QTableWidgetItem(f"{weapon.decay:.4f}"))
    
    def on_search_changed(self, text: str):
        """Handle search text change"""
        self.signals.search_changed.emit(text)
        
        # Filter visible rows
        search_lower = text.lower()
        for row, weapon in enumerate(self.weapons):
            hide = text and search_lower not in weapon.name.lower()
            self.weapon_table.setRowHidden(row, hide)
    
    def clear_search(self):
        """Clear the search"""
        self.search_edit.clear()
    
    def on_weapon_selected(self):
        """Handle weapon selection"""
        selected_items = self.weapon_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        selected_weapon = self.weapons[row]
        self.signals.weapon_selected.emit(selected_weapon)
    
    def get_selected_weapon(self) -> Optional[WeaponStats]:
        """Get currently selected weapon"""
        selected_items = self.weapon_table.selectedItems()
        if not selected_items:
            return None
        
        row = selected_items[0].row()
        return self.weapons[row]


class AttachmentSelectorWidget(QWidget):
    """Widget for selecting attachments and enhancements"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = WeaponSelectionSignals()
        self.attachments: List[AttachmentStats] = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # Amplifier selection
        amp_layout = QHBoxLayout()
        amp_layout.addWidget(QLabel("Amplifier:"))
        
        self.amplifier_combo = QComboBox()
        self.amplifier_combo.addItem("None", None)
        self.amplifier_combo.currentTextChanged.connect(self.on_selection_changed)
        amp_layout.addWidget(self.amplifier_combo)
        
        layout.addLayout(amp_layout)
        
        # Scope selection
        scope_layout = QHBoxLayout()
        scope_layout.addWidget(QLabel("Scope:"))
        
        self.scope_combo = QComboBox()
        self.scope_combo.addItem("None", None)
        self.scope_combo.currentTextChanged.connect(self.on_selection_changed)
        scope_layout.addWidget(self.scope_combo)
        
        layout.addLayout(scope_layout)
        
        # Enhancement settings
        enh_group = QGroupBox("Enhancements")
        enh_layout = QGridLayout(enh_group)
        
        # Damage enhancement
        enh_layout.addWidget(QLabel("Damage Enh:"), 0, 0)
        self.damage_enh_spin = QSpinBox()
        self.damage_enh_spin.setRange(0, 10)
        self.damage_enh_spin.valueChanged.connect(self.on_selection_changed)
        enh_layout.addWidget(self.damage_enh_spin, 0, 1)
        
        # Economy enhancement
        enh_layout.addWidget(QLabel("Economy Enh:"), 1, 0)
        self.economy_enh_spin = QSpinBox()
        self.economy_enh_spin.setRange(0, 10)
        self.economy_enh_spin.valueChanged.connect(self.on_selection_changed)
        enh_layout.addWidget(self.economy_enh_spin, 1, 1)
        
        layout.addWidget(enh_group)
        layout.addStretch()
    
    def set_attachments(self, attachments: List[AttachmentStats]):
        """Set the attachments list"""
        self.attachments = attachments
        self.populate_combos()
    
    def populate_combos(self):
        """Populate attachment combo boxes"""
        # Clear existing items except "None"
        self.amplifier_combo.clear()
        self.amplifier_combo.addItem("None", None)
        self.scope_combo.clear()
        self.scope_combo.addItem("None", None)
        
        # Add amplifiers
        for attachment in self.attachments:
            if attachment.attachment_type == 'amplifier':
                self.amplifier_combo.addItem(attachment.name, attachment)
        
        # Add scopes
        for attachment in self.attachments:
            if attachment.attachment_type == 'scope':
                self.scope_combo.addItem(attachment.name, attachment)
    
    def on_selection_changed(self):
        """Handle selection change"""
        self.signals.search_changed.emit("")  # Signal that configuration changed
    
    def get_selected_amplifier(self) -> Optional[AttachmentStats]:
        """Get selected amplifier"""
        return self.amplifier_combo.currentData()
    
    def get_selected_scope(self) -> Optional[AttachmentStats]:
        """Get selected scope"""
        return self.scope_combo.currentData()
    
    def get_damage_enhancement(self) -> int:
        """Get damage enhancement level"""
        return self.damage_enh_spin.value()
    
    def get_economy_enhancement(self) -> int:
        """Get economy enhancement level"""
        return self.economy_enh_spin.value()
    
    def reset_selections(self):
        """Reset all selections"""
        self.amplifier_combo.setCurrentIndex(0)
        self.scope_combo.setCurrentIndex(0)
        self.damage_enh_spin.setValue(0)
        self.economy_enh_spin.setValue(0)


class CostAnalysisWidget(QWidget):
    """Widget for displaying cost analysis and performance metrics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # Cost breakdown
        cost_group = QGroupBox("Cost Analysis")
        cost_layout = QGridLayout(cost_group)
        
        self.base_cost_label = QLabel("Base Cost: -- PED/shot")
        self.enhanced_cost_label = QLabel("Enhanced Cost: -- PED/shot")
        self.total_cost_label = QLabel("Total Cost: -- PED/shot")
        self.ammo_cost_label = QLabel("Ammo Cost: -- PED/shot")
        self.decay_cost_label = QLabel("Decay Cost: -- PED/shot")
        
        # Apply monospace font to cost labels
        cost_font = QFont("Consolas, Monaco, monospace", 9)
        for label in [self.base_cost_label, self.enhanced_cost_label, 
                     self.total_cost_label, self.ammo_cost_label, self.decay_cost_label]:
            label.setFont(cost_font)
        
        cost_layout.addWidget(self.base_cost_label, 0, 0)
        cost_layout.addWidget(self.enhanced_cost_label, 1, 0)
        cost_layout.addWidget(self.total_cost_label, 2, 0)
        cost_layout.addWidget(QLabel("───"), 3, 0)
        cost_layout.addWidget(self.ammo_cost_label, 4, 0)
        cost_layout.addWidget(self.decay_cost_label, 5, 0)
        
        layout.addWidget(cost_group)
        
        # Performance metrics
        perf_group = QGroupBox("Performance Metrics")
        perf_layout = QGridLayout(perf_group)
        
        self.dps_label = QLabel("DPS: --")
        self.dpp_label = QLabel("Damage per PED: --")
        self.range_label = QLabel("Range: --")
        self.reload_label = QLabel("Reload: --s")
        
        # Apply monospace font to metric labels
        for label in [self.dps_label, self.dpp_label, self.range_label, self.reload_label]:
            label.setFont(cost_font)
        
        perf_layout.addWidget(QLabel("Damage per Second:"), 0, 0)
        perf_layout.addWidget(self.dps_label, 0, 1)
        perf_layout.addWidget(QLabel("Damage per PED:"), 1, 0)
        perf_layout.addWidget(self.dpp_label, 1, 1)
        perf_layout.addWidget(QLabel("Effective Range:"), 2, 0)
        perf_layout.addWidget(self.range_label, 2, 1)
        perf_layout.addWidget(QLabel("Reload Time:"), 3, 0)
        perf_layout.addWidget(self.reload_label, 3, 1)
        
        layout.addWidget(perf_group)
        layout.addStretch()
    
    def update_stats(self, enhanced_stats: EnhancedWeaponStats):
        """Update the statistics display"""
        # Update cost labels
        base_cost = enhanced_stats.base_weapon.calculate_base_cost_per_shot()
        self.base_cost_label.setText(f"Base Cost: {base_cost:.6f} PED/shot")
        self.enhanced_cost_label.setText(f"Enhanced Cost: {enhanced_stats.total_cost_per_shot:.6f} PED/shot")
        self.total_cost_label.setText(f"Total Cost: {enhanced_stats.total_cost_per_shot:.6f} PED/shot")
        
        # Calculate component costs
        ammo_cost = enhanced_stats.ammo_burn / Decimal('10000')
        decay_cost = enhanced_stats.decay
        
        self.ammo_cost_label.setText(f"Ammo Cost: {ammo_cost:.6f} PED/shot")
        self.decay_cost_label.setText(f"Decay Cost: {decay_cost:.6f} PED/shot")
        
        # Update performance labels
        self.dps_label.setText(f"{enhanced_stats.dps:.2f}")
        self.dpp_label.setText(f"{enhanced_stats.damage_per_ped:.2f}")
        self.range_label.setText(f"{enhanced_stats.effective_range}m")
        self.reload_label.setText(f"{enhanced_stats.base_weapon.reload_time}s")
    
    def clear_stats(self):
        """Clear all statistics"""
        self.base_cost_label.setText("Base Cost: -- PED/shot")
        self.enhanced_cost_label.setText("Enhanced Cost: -- PED/shot")
        self.total_cost_label.setText("Total Cost: -- PED/shot")
        self.ammo_cost_label.setText("Ammo Cost: -- PED/shot")
        self.decay_cost_label.setText("Decay Cost: -- PED/shot")
        self.dps_label.setText("DPS: --")
        self.dpp_label.setText("Damage per PED: --")
        self.range_label.setText("Range: --")
        self.reload_label.setText("Reload: --s")
    
    def update_weapon_info(self, weapon: WeaponStats):
        """Update only the base weapon info"""
        base_cost = weapon.calculate_base_cost_per_shot()
        dps = weapon.calculate_base_dps()
        
        self.base_cost_label.setText(f"Base Cost: {base_cost:.6f} PED/shot")
        self.dps_label.setText(f"{dps:.2f}")
        self.range_label.setText(f"{weapon.range}m")
        self.reload_label.setText(f"{weapon.reload_time}s")