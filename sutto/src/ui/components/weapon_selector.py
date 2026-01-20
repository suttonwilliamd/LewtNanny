"""
Weapon Selector Component - PyQt6 Version
Modern weapon selection and cost calculation component
"""

from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal
from pathlib import Path
import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QGroupBox, QLabel, QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QDoubleSpinBox, QCheckBox, QTextEdit, QScrollArea,
    QSplitter, QFrame, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QPalette


class WeaponData:
    """Data model for weapon information"""
    
    def __init__(self, weapon_data: Dict[str, Any]):
        self.id = weapon_data.get('id', '')
        self.name = weapon_data.get('name', '')
        self.damage = Decimal(str(weapon_data.get('damage', 0)))
        self.ammo_burn = Decimal(str(weapon_data.get('ammo_burn', 0)))
        self.decay = Decimal(str(weapon_data.get('decay', 0)))
        self.hits = int(weapon_data.get('hits', 0))
        self.range = weapon_data.get('range', 0)
        self.reload_time = Decimal(str(weapon_data.get('reload_time', 0)))
        self.weapon_type = weapon_data.get('weapon_type', '')
        
    def calculate_base_cost_per_shot(self) -> Decimal:
        """Calculate base cost per shot without attachments"""
        return self.decay + (self.ammo_burn / Decimal('10000'))


class AttachmentData:
    """Data model for attachment information"""
    
    def __init__(self, attachment_data: Dict[str, Any]):
        self.id = attachment_data.get('id', '')
        self.name = attachment_data.get('name', '')
        self.damage_bonus = Decimal(str(attachment_data.get('damage_bonus', 0)))
        self.ammo_bonus = Decimal(str(attachment_data.get('ammo_bonus', 0)))
        self.decay_modifier = Decimal(str(attachment_data.get('decay_modifier', 0)))
        self.attachment_type = attachment_data.get('type', '')


class WeaponSelectorSignals(QObject):
    """Signals for weapon selector component"""
    weapon_selected = pyqtSignal(dict)  # Emitted when weapon is selected
    cost_calculated = pyqtSignal(dict)  # Emitted when cost is calculated
    loadout_changed = pyqtSignal(dict)  # Emitted when loadout changes


class WeaponSelector(QWidget):
    """Modern PyQt6 weapon selector component"""
    
    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.signals = WeaponSelectorSignals()
        
        # Data storage
        self.weapons: Dict[str, WeaponData] = {}
        self.attachments: Dict[str, AttachmentData] = {}
        self.sights_scopes: Dict[str, AttachmentData] = {}
        self.current_weapon: Optional[WeaponData] = None
        self.current_attachments: List[AttachmentData] = []
        
        # Session tracking
        self.session_ammo_used = Decimal('0')
        self.session_decay = Decimal('0')
        
        # Initialize UI
        self.setup_ui()
        self.load_data()
        self.connect_signals()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Weapon selection and configuration
        left_widget = self.create_selection_panel()
        splitter.addWidget(left_widget)
        
        # Right side - Cost analysis and stats
        right_widget = self.create_analysis_panel()
        splitter.addWidget(right_widget)
        
        # Set splitter proportions
        splitter.setSizes([500, 400])
        splitter.setChildrenCollapsible(False)
        
        layout.addWidget(splitter)
        
    def create_selection_panel(self) -> QWidget:
        """Create the weapon selection panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Weapon search and selection
        search_group = QGroupBox("Weapon Selection")
        search_layout = QVBoxLayout(search_group)
        search_layout.setContentsMargins(10, 20, 10, 10)
        
        # Search box
        search_container = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search weapons...")
        self.search_edit.textChanged.connect(self.filter_weapons)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_search)
        
        search_container.addWidget(QLabel("Search:"))
        search_container.addWidget(self.search_edit)
        search_container.addWidget(clear_btn)
        
        search_layout.addLayout(search_container)
        
        # Weapon list
        self.weapon_table = QTableWidget()
        self.weapon_table.setColumnCount(4)
        self.weapon_table.setHorizontalHeaderLabels(["Name", "Damage", "Ammo/Shot", "Decay"])
        self.weapon_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.weapon_table.setSortingEnabled(True)
        self.weapon_table.itemSelectionChanged.connect(self.on_weapon_selected)
        
        # Configure table columns
        header = self.weapon_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        search_layout.addWidget(self.weapon_table)
        layout.addWidget(search_group)
        
        # Attachment configuration
        attachment_group = QGroupBox("Attachments")
        attachment_layout = QVBoxLayout(attachment_group)
        attachment_layout.setContentsMargins(10, 20, 10, 10)
        
        # Amplifier
        amp_container = QHBoxLayout()
        amp_container.addWidget(QLabel("Amplifier:"))
        self.amplifier_combo = QComboBox()
        self.amplifier_combo.addItem("None", None)
        self.amplifier_combo.currentTextChanged.connect(self.update_cost_calculation)
        amp_container.addWidget(self.amplifier_combo)
        
        # Sight/Scope
        sight_container = QHBoxLayout()
        sight_container.addWidget(QLabel("Scope:"))
        self.scope_combo = QComboBox()
        self.scope_combo.addItem("None", None)
        self.scope_combo.currentTextChanged.connect(self.update_cost_calculation)
        sight_container.addWidget(self.scope_combo)
        
        attachment_layout.addLayout(amp_container)
        attachment_layout.addLayout(sight_container)
        
        # Enhancement sliders
        enh_group = QGroupBox("Enhancements")
        enh_layout = QGridLayout(enh_group)
        
        # Damage enhancement
        enh_layout.addWidget(QLabel("Damage Enh:"), 0, 0)
        self.damage_enh_spin = QSpinBox()
        self.damage_enh_spin.setRange(0, 10)
        self.damage_enh_spin.valueChanged.connect(self.update_cost_calculation)
        enh_layout.addWidget(self.damage_enh_spin, 0, 1)
        
        # Economy enhancement
        enh_layout.addWidget(QLabel("Economy Enh:"), 1, 0)
        self.economy_enh_spin = QSpinBox()
        self.economy_enh_spin.setRange(0, 10)
        self.economy_enh_spin.valueChanged.connect(self.update_cost_calculation)
        enh_layout.addWidget(self.economy_enh_spin, 1, 1)
        
        attachment_layout.addWidget(enh_group)
        layout.addWidget(attachment_group)
        
        # Session controls
        session_group = QGroupBox("Session Controls")
        session_layout = QHBoxLayout(session_group)
        session_layout.setContentsMargins(10, 20, 10, 10)
        
        self.reset_session_btn = QPushButton("Reset Session")
        self.reset_session_btn.clicked.connect(self.reset_session)
        
        session_layout.addWidget(self.reset_session_btn)
        session_layout.addStretch()
        
        layout.addWidget(session_group)
        layout.addStretch()
        
        return widget
    
    def create_analysis_panel(self) -> QWidget:
        """Create the cost analysis panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Cost breakdown
        cost_group = QGroupBox("Cost Analysis")
        cost_layout = QGridLayout(cost_group)
        cost_layout.setContentsMargins(10, 20, 10, 10)
        
        # Cost labels
        self.base_cost_label = QLabel("Base Cost: -- PED/shot")
        self.enhanced_cost_label = QLabel("Enhanced Cost: -- PED/shot")
        self.total_cost_label = QLabel("Total Cost: -- PED/shot")
        self.ammo_cost_label = QLabel("Ammo Cost: -- PED/shot")
        self.decay_cost_label = QLabel("Decay Cost: -- PED/shot")
        
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
        perf_layout.setContentsMargins(10, 20, 10, 10)
        
        self.dps_label = QLabel("DPS: --")
        self.dpp_label = QLabel("Damage per PED: --")
        self.range_label = QLabel("Range: --")
        self.reload_label = QLabel("Reload: --s")
        
        perf_layout.addWidget(QLabel("Damage per Second:"), 0, 0)
        perf_layout.addWidget(self.dps_label, 0, 1)
        perf_layout.addWidget(QLabel("Damage per PED:"), 1, 0)
        perf_layout.addWidget(self.dpp_label, 1, 1)
        perf_layout.addWidget(QLabel("Effective Range:"), 2, 0)
        perf_layout.addWidget(self.range_label, 2, 1)
        perf_layout.addWidget(QLabel("Reload Time:"), 3, 0)
        perf_layout.addWidget(self.reload_label, 3, 1)
        
        layout.addWidget(perf_group)
        
        # Session statistics
        session_group = QGroupBox("Session Statistics")
        session_layout = QGridLayout(session_group)
        session_layout.setContentsMargins(10, 20, 10, 10)
        
        self.session_ammo_label = QLabel("Ammo Used: 0")
        self.session_decay_label = QLabel("Total Decay: 0.00 PED")
        self.session_shots_label = QLabel("Shots Fired: 0")
        self.session_cost_label = QLabel("Session Cost: 0.00 PED")
        
        session_layout.addWidget(QLabel("Ammo Used:"), 0, 0)
        session_layout.addWidget(self.session_ammo_label, 0, 1)
        session_layout.addWidget(QLabel("Total Decay:"), 1, 0)
        session_layout.addWidget(self.session_decay_label, 1, 1)
        session_layout.addWidget(QLabel("Shots Fired:"), 2, 0)
        session_layout.addWidget(self.session_shots_label, 2, 1)
        session_layout.addWidget(QLabel("Session Cost:"), 3, 0)
        session_layout.addWidget(self.session_cost_label, 3, 1)
        
        layout.addWidget(session_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return widget
    
    def connect_signals(self):
        """Connect signals and slots"""
        # Timer for updating stats
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_session_stats)
        self.update_timer.start(1000)  # Update every second
    
    def load_data(self):
        """Load weapon and attachment data"""
        self.load_weapons()
        self.load_attachments()
        self.populate_weapon_table()
        self.populate_attachment_combos()
    
    def load_weapons(self):
        """Load weapons from database or JSON"""
        # For now, create some sample data
        # In a real implementation, this would load from the database
        sample_weapons = [
            {
                'id': '1', 'name': 'Korss H400 (L)', 'damage': 28, 'ammo_burn': 11,
                'decay': 0.10, 'hits': 36, 'range': 55, 'reload_time': 3.0, 'weapon_type': 'Pistol'
            },
            {
                'id': '2', 'name': 'HL11 (L)', 'damage': 32, 'ammo_burn': 16,
                'decay': 0.20, 'hits': 27, 'range': 58, 'reload_time': 3.2, 'weapon_type': 'Rifle'
            },
            {
                'id': '3', 'name': 'Opalo', 'damage': 12, 'ammo_burn': 6,
                'decay': 0.03, 'hits': 30, 'range': 45, 'reload_time': 2.8, 'weapon_type': 'Pistol'
            }
        ]
        
        self.weapons = {
            weapon['id']: WeaponData(weapon) 
            for weapon in sample_weapons
        }
    
    def load_attachments(self):
        """Load attachment data from JSON files"""
        try:
            # Load amplifiers
            amp_path = Path('attachments.json')
            if amp_path.exists():
                with open(amp_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data.get('data', []):
                        attachment = AttachmentData(item)
                        if attachment.attachment_type == 'amplifier':
                            self.attachments[attachment.id] = attachment
        except Exception as e:
            print(f"Error loading attachments: {e}")
        
        # Create sample attachments for demonstration
        sample_attachments = [
            {
                'id': 'a1', 'name': 'A106 Amplifier', 'type': 'amplifier',
                'damage_bonus': 0.5, 'ammo_bonus': 0, 'decay_modifier': 0.25
            },
            {
                'id': 'a2', 'name': 'A204 Amplifier', 'type': 'amplifier',
                'damage_bonus': 1.0, 'ammo_bonus': 0, 'decay_modifier': 0.50
            }
        ]
        
        self.attachments.update({
            item['id']: AttachmentData(item) 
            for item in sample_attachments
        })
    
    def populate_weapon_table(self):
        """Populate the weapon table with data"""
        self.weapon_table.setRowCount(len(self.weapons))
        
        for row, weapon in enumerate(self.weapons.values()):
            self.weapon_table.setItem(row, 0, QTableWidgetItem(weapon.name))
            self.weapon_table.setItem(row, 1, QTableWidgetItem(str(weapon.damage)))
            self.weapon_table.setItem(row, 2, QTableWidgetItem(str(weapon.ammo_burn)))
            self.weapon_table.setItem(row, 3, QTableWidgetItem(f"{weapon.decay:.4f} PED"))
    
    def populate_attachment_combos(self):
        """Populate attachment combo boxes"""
        # Clear existing items except "None"
        self.amplifier_combo.clear()
        self.amplifier_combo.addItem("None", None)
        self.scope_combo.clear()
        self.scope_combo.addItem("None", None)
        
        # Add amplifiers
        for attachment in self.attachments.values():
            if attachment.attachment_type == 'amplifier':
                self.amplifier_combo.addItem(attachment.name, attachment)
        
        # Add scopes (if any)
        for attachment in self.sights_scopes.values():
            if attachment.attachment_type == 'scope':
                self.scope_combo.addItem(attachment.name, attachment)
    
    def filter_weapons(self, search_text: str):
        """Filter weapons based on search text"""
        search_lower = search_text.lower()
        
        for row, weapon in enumerate(self.weapons.values()):
            hide = search_text and search_lower not in weapon.name.lower()
            self.weapon_table.setRowHidden(row, hide)
    
    def clear_search(self):
        """Clear the search filter"""
        self.search_edit.clear()
    
    def on_weapon_selected(self):
        """Handle weapon selection change"""
        selected_items = self.weapon_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        weapon_id = list(self.weapons.keys())[row]
        self.current_weapon = self.weapons[weapon_id]
        
        # Emit weapon selection signal
        self.signals.weapon_selected.emit({
            'weapon': self.current_weapon,
            'attachments': self.current_attachments
        })
        
        # Update cost calculation
        self.update_cost_calculation()
    
    def update_cost_calculation(self):
        """Update cost calculations based on current selections"""
        if not self.current_weapon:
            return
        
        # Get current attachments
        amplifier = self.amplifier_combo.currentData()
        scope = self.scope_combo.currentData()
        damage_enh = self.damage_enh_spin.value()
        economy_enh = self.economy_enh_spin.value()
        
        # Calculate enhanced stats
        base_damage = self.current_weapon.damage
        base_ammo = self.current_weapon.ammo_burn
        base_decay = self.current_weapon.decay
        
        # Apply enhancements
        damage_multiplier = 1.0 + (0.1 * damage_enh)
        economy_multiplier = 1.0 - (0.01 * economy_enh)
        
        enhanced_damage = base_damage * damage_multiplier
        enhanced_ammo = base_ammo * damage_multiplier
        enhanced_decay = base_decay * damage_multiplier * economy_multiplier
        
        # Apply amplifier
        if amplifier:
            enhanced_damage += amplifier.damage_bonus
            enhanced_ammo += amplifier.ammo_bonus
            enhanced_decay += amplifier.decay_modifier
        
        # Calculate costs
        ammo_cost_per_shot = enhanced_ammo / Decimal('10000')  # Convert to PED
        decay_cost_per_shot = enhanced_decay
        total_cost_per_shot = ammo_cost_per_shot + decay_cost_per_shot
        
        # Calculate metrics
        dpp = enhanced_damage / total_cost_per_shot if total_cost_per_shot > 0 else 0
        dps = enhanced_damage / self.current_weapon.reload_time if self.current_weapon.reload_time > 0 else 0
        
        # Update labels
        self.base_cost_label.setText(f"Base Cost: {self.current_weapon.calculate_base_cost_per_shot():.6f} PED/shot")
        self.enhanced_cost_label.setText(f"Enhanced Cost: {total_cost_per_shot:.6f} PED/shot")
        self.total_cost_label.setText(f"Total Cost: {total_cost_per_shot:.6f} PED/shot")
        self.ammo_cost_label.setText(f"Ammo Cost: {ammo_cost_per_shot:.6f} PED/shot")
        self.decay_cost_label.setText(f"Decay Cost: {decay_cost_per_shot:.6f} PED/shot")
        
        self.dps_label.setText(f"{dps:.2f}")
        self.dpp_label.setText(f"{dpp:.2f}")
        self.range_label.setText(f"{self.current_weapon.range}m")
        self.reload_label.setText(f"{self.current_weapon.reload_time}s")
        
        # Emit cost calculation signal
        self.signals.cost_calculated.emit({
            'total_cost': float(total_cost_per_shot),
            'dpp': float(dpp),
            'dps': float(dps),
            'ammo_cost': float(ammo_cost_per_shot),
            'decay_cost': float(decay_cost_per_shot)
        })
    
    def reset_session(self):
        """Reset session statistics"""
        self.session_ammo_used = Decimal('0')
        self.session_decay = Decimal('0')
        self.update_session_stats()
    
    def update_session_stats(self):
        """Update session statistics display"""
        self.session_ammo_label.setText(f"Ammo Used: {self.session_ammo_used}")
        self.session_decay_label.setText(f"Total Decay: {self.session_decay:.2f} PED")
        
        # Calculate estimated shots and cost (these would come from actual usage)
        estimated_shots = int(self.session_ammo_used / max(1, self.current_weapon.ammo_burn)) if self.current_weapon else 0
        estimated_cost = float(self.session_decay)
        
        self.session_shots_label.setText(f"Shots Fired: {estimated_shots}")
        self.session_cost_label.setText(f"Session Cost: {estimated_cost:.2f} PED")
    
    def add_shot_data(self, ammo_used: Decimal, decay: Decimal):
        """Add shot data to session statistics"""
        self.session_ammo_used += ammo_used
        self.session_decay += decay
        self.update_session_stats()