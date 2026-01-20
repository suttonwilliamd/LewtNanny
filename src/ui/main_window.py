"""
Main window for LewtNanny PyQt6 GUI
"""

import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import json

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QTextEdit, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QGroupBox, QGridLayout, QLineEdit,
    QComboBox, QSpinBox, QCheckBox, QFileDialog,
    QStatusBar, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QTextCursor

from src.models.models import ActivityType, EventType


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, db_manager, config_manager):
        super().__init__()
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.chat_reader = None
        
        self.setWindowTitle("LewtNanny - Entropia Universe Loot Tracker")
        self.setGeometry(100, 100, 1200, 800)
        
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with proper margins
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Setup toolbar area
        self.setup_toolbar()
        
        # Setup weapon configuration panel
        self.setup_weapon_config()
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_loot_tab()
        self.create_analysis_tab()
        self.create_config_tab()
        
        # Setup proper status bar
        self.setup_status_bar()
        
    def setup_toolbar(self):
        """Setup toolbar area"""
        toolbar_widget = QFrame()
        toolbar_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        toolbar_layout.setSpacing(10)
        
        # Initialize theme state
        self.current_theme = 'dark'
        
        # Session controls
        self.session_label = QLabel("No active session")
        self.session_label.setProperty("class", "session-label")
        
        self.start_session_btn = QPushButton("Start Session")
        self.start_session_btn.clicked.connect(self.start_session)
        self.start_session_btn.setMinimumWidth(120)
        
        # Activity selector
        activity_label = QLabel("Activity:")
        self.activity_combo = QComboBox()
        self.activity_combo.addItems([t.value for t in ActivityType])
        self.activity_combo.currentTextChanged.connect(self.change_activity)
        self.activity_combo.setMinimumWidth(150)
        
        # Weapon config toggle button
        self.weapon_config_btn = QPushButton("⚙️ Weapon Config")
        self.weapon_config_btn.clicked.connect(self.toggle_weapon_config)
        self.weapon_config_btn.setMinimumWidth(120)
        
        # Current weapon display
        self.current_weapon_label = QLabel("No Weapon Selected")
        self.current_weapon_label.setProperty("class", "weapon-label")
        
        toolbar_layout.addWidget(self.session_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(activity_label)
        toolbar_layout.addWidget(self.current_weapon_label)
        toolbar_layout.addWidget(self.weapon_config_btn)
        toolbar_layout.addWidget(self.start_session_btn)
        
        # Session controls
        self.start_session_btn = QPushButton("Start Session")
        self.start_session_btn.clicked.connect(self.start_session)
        self.start_session_btn.setMinimumWidth(120)
        
        def start_session(self):
            """Start a new tracking session"""
            print(f"Session started at {datetime.now()}")
            self.session_active = True
            
            # Generate session ID
            import uuid
            session_id = str(uuid.uuid())[:8]
            
            # Update UI
            activity = self.activity_combo.currentText()
            weapon = self.get_selected_weapon()
            
            self.session_label.setText(f"Session Active - {activity}")
            self.current_weapon_label.setText(f"Weapon: {weapon}" if weapon else "No Weapon Selected")
            self.current_weapon_label.setProperty("class", "weapon-label-active" if weapon else "weapon-label")
            
            # Update overlay if visible
            if hasattr(self, 'overlay_window') and self.overlay_window:
                self.overlay_window.update_session_info(session_id, activity, None, weapon)
        
        # Theme toggle
        self.theme_toggle_btn = QPushButton("🌓 Theme")
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        self.theme_toggle_btn.setMinimumWidth(80)
        toolbar_layout.addWidget(self.theme_toggle_btn)
        
        # Overlay toggle
        self.overlay_btn = QPushButton("Toggle Overlay")
        self.overlay_btn.clicked.connect(self.toggle_overlay)
        self.overlay_btn.setMinimumWidth(120)
        toolbar_layout.addWidget(self.overlay_btn)
        
        self.main_layout.addWidget(toolbar_widget)
        
    def setup_weapon_config(self):
        """Setup comprehensive weapon configuration panel"""
        # Create collapsible weapon config widget
        self.weapon_config_widget = QFrame()
        self.weapon_config_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        self.weapon_config_widget.setVisible(False)  # Initially hidden
        
        config_layout = QVBoxLayout(self.weapon_config_widget)
        config_layout.setContentsMargins(15, 10, 15, 10)
        config_layout.setSpacing(10)
        
        # Title
        title_label = QLabel("⚙️ Weapon Configuration")
        title_label.setProperty("class", "config-title")
        config_layout.addWidget(title_label)
        
        # Create form layout for weapon components
        from PyQt6.QtWidgets import QFormLayout, QDoubleSpinBox, QSpinBox
        
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        
        # Weapon selector
        self.weapon_combo = QComboBox()
        self.weapon_combo.setEditable(True)
        self.weapon_combo.setMinimumWidth(200)
        self.weapon_combo.setPlaceholderText("Select or type weapon...")
        self.load_weapons()
        self.weapon_combo.currentTextChanged.connect(self.update_weapon_display)
        form_layout.addRow("Weapon:", self.weapon_combo)
        
        # Attachments
        self.attachment_combo = QComboBox()
        self.attachment_combo.setEditable(True)
        self.attachment_combo.addItems(["None", "A206 Amplifier", "A204 Amplifier", "A203 Amplifier", "Beast Amplifier", "Wolf Amplifier"])
        form_layout.addRow("Attachment:", self.attachment_combo)
        
        # Scope
        self.scope_combo = QComboBox()
        self.scope_combo.setEditable(True)
        self.scope_combo.addItems(["None", "Laser Sight", "Illumination", "Holographic Sight", "AIO Sight", "Force Sight"])
        form_layout.addRow("Scope:", self.scope_combo)
        
        # Enhancers section
        enhancer_group = QGroupBox("Enhancers")
        enhancer_layout = QGridLayout(enhancer_group)
        
        # Different enhancer types with numerical inputs
        enhancer_types = [
            ("Damage", "dmg_enh"),
            ("Range", "range_enh"), 
            ("Accuracy", "acc_enh"),
            ("Economy", "eco_enh")
        ]
        
        self.enhancer_inputs = {}
        for i, (label, key) in enumerate(enhancer_types):
            enh_label = QLabel(f"{label}:")
            enh_spinbox = QSpinBox()
            enh_spinbox.setMinimum(0)
            enh_spinbox.setMaximum(10)
            enh_spinbox.setValue(0)
            enh_spinbox.setSuffix(" units")
            self.enhancer_inputs[key] = enh_spinbox
            enhancer_layout.addWidget(enh_label, i, 0)
            enhancer_layout.addWidget(enh_spinbox, i, 1)
        
        form_layout.addRow(enhancer_group)
        
        # Additional stats
        self.dmg_spinbox = QDoubleSpinBox()
        self.dmg_spinbox.setRange(0.0, 999.9)
        self.dmg_spinbox.setSingleStep(0.1)
        self.dmg_spinbox.setDecimals(1)
        self.dmg_spinbox.setSuffix(" dmg")
        form_layout.addRow("Damage:", self.dmg_spinbox)
        
        self.ammo_spinbox = QDoubleSpinBox()
        self.ammo_spinbox.setRange(0.0, 99.9)
        self.ammo_spinbox.setSingleStep(0.01)
        self.ammo_spinbox.setDecimals(2)
        self.ammo_spinbox.setSuffix(" ammo")
        form_layout.addRow("Ammo/shot:", self.ammo_spinbox)
        
        config_layout.addLayout(form_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self.save_weapon_config)
        save_btn.setProperty("class", "save-btn")
        
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_weapon_config)
        reset_btn.setProperty("class", "reset-btn")
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        
        config_layout.addLayout(button_layout)
        
        # Add to main layout
        self.main_layout.addWidget(self.weapon_config_widget)
        
    def toggle_weapon_config(self):
        """Toggle weapon configuration panel visibility"""
        self.weapon_config_widget.setVisible(not self.weapon_config_widget.isVisible())
        if self.weapon_config_widget.isVisible():
            self.weapon_config_btn.setText("⚙️ Hide Config")
        else:
            self.weapon_config_btn.setText("⚙️ Weapon Config")
    
    def update_weapon_display(self):
        """Update the current weapon display in toolbar"""
        weapon = self.get_selected_weapon()
        if weapon:
            self.current_weapon_label.setText(f"Weapon: {weapon}")
            self.current_weapon_label.setProperty("class", "weapon-label-active")
        else:
            self.current_weapon_label.setText("No Weapon Selected")
            self.current_weapon_label.setProperty("class", "weapon-label")
        # Trigger style update - let theme handle styling
        
    # def filter_weapons(self, search_text):
    #     """Filter weapons based on search text and active filters"""
    #     # TODO: Implement advanced filtering with search and type filters
    #     pass
    
    # def apply_filter(self, filter_type):
    #     """Apply weapon type filter"""
    #     # TODO: Implement filter logic with visual feedback
    #     pass
    
    def save_weapon_config(self):
        """Save weapon configuration"""
        config = {
            'weapon': self.get_selected_weapon(),
            'attachment': self.attachment_combo.currentText(),
            'scope': self.scope_combo.currentText(),
            'dmg_enh': self.enhancer_inputs['dmg_enh'].value(),
            'range_enh': self.enhancer_inputs['range_enh'].value(),
            'acc_enh': self.enhancer_inputs['acc_enh'].value(),
            'eco_enh': self.enhancer_inputs['eco_enh'].value(),
            'damage': self.dmg_spinbox.value(),
            'ammo': self.ammo_spinbox.value()
        }
        print(f"Saved weapon config: {config}")
        self.update_weapon_display()
    
    def reset_weapon_config(self):
        """Reset weapon configuration"""
        self.weapon_combo.setCurrentIndex(0)
        self.attachment_combo.setCurrentIndex(0)
        self.scope_combo.setCurrentIndex(0)
        for spinbox in self.enhancer_inputs.values():
            spinbox.setValue(0)
        self.dmg_spinbox.setValue(0.0)
        self.ammo_spinbox.setValue(0.0)
        self.update_weapon_display()
    
    def toggle_theme(self):
        """Toggle between dark and light themes"""
        from pathlib import Path
        
        # Switch theme
        if self.current_theme == 'dark':
            self.current_theme = 'light'
            self.theme_toggle_btn.setText("☀️ Theme")
        else:
            self.current_theme = 'dark'
            self.theme_toggle_btn.setText("🌙 Theme")
        
        # Load new theme
        # Load weapons from database
        weapons_data = {}
        try:
            weapons_path = Path(__file__).parent / "weapons.json"
            if weapons_path.exists():
                with open(weapons_path, 'r') as f:
                    weapons_data = json.load(f)
                    print(f"Loaded weapons database with {len(weapons_data.get('data', {}))} weapons")
        except Exception as e:
            print(f"Error loading weapons database: {e}")
            weapons_data = {'data': {}}
        
        # Add search functionality
        self.weapon_search = QLineEdit()
        self.weapon_search.setPlaceholderText("Search weapons...")
        self.weapon_search.textChanged.connect(self.filter_weapons)
        
        # Add filter buttons
        filter_layout = QHBoxLayout()
        
        # Weapon type filters
        self.rifle_filter_btn = QPushButton("Rifle")
        self.pistol_filter_btn = QPushButton("Pistol")
        self.shortblade_filter_btn = QPushButton("Shortblade")
        self.amplifier_filter_btn = QPushButton("Amplifier")
        
        filter_layout.addWidget(QLabel("Filter:"))
        filter_layout.addWidget(self.rifle_filter_btn)
        filter_layout.addWidget(self.pistol_filter_btn)
        filter_layout.addWidget(self.shortblade_filter_btn)
        filter_layout.addWidget(self.amplifier_filter_btn)
        
        # Add search and filter to weapon selection
        weapon_layout = QHBoxLayout()
        weapon_layout.addWidget(self.weapon_search)
        weapon_layout.addLayout(filter_layout)
        weapon_layout.addWidget(self.weapon_combo)
        
        form_layout.addRow("Weapon:", weapon_layout)
        
        # Load weapons from weapons.json database
        weapons_data: Dict[str, Any] = {}
        try:
            weapons_path = Path(__file__).parent.parent / "weapons.json"
            if weapons_path.exists():
                with open(weapons_path, 'r') as f:
                    weapons_data = json.load(f)
                    print(f"Loaded weapons database with {len(weapons_data.get('data', {}))} weapons")
                
        except Exception as e:
            print(f"Error loading weapons database: {e}")
            weapons_data = {'data': {}}
        
        # Add weapons to combo box with real stats
        added_weapons = []
        for weapon_name, stats in weapons_data.get('data', {}).items():
            self.weapon_combo.addItem(weapon_name, weapon_name)
            added_weapons.append(weapon_name)
            
        # Add fallback weapons if database is empty
        if not added_weapons:
            fallback_weapons = [
                "Korss H400 (L)",
                "P5a (L)", 
                "H400 (L)",
                "ME(L)",
                "Karwapak (L)",
                "Adj. M107a",
                "ML-35"
            ]
            
            for weapon in fallback_weapons:
                self.weapon_combo.addItem(weapon, weapon)
                
        self.weapon_combo.addItem("Custom...", None)
        self.weapon_combo.currentTextChanged.connect(self.update_weapon_display)
            
        self.weapon_combo.addItem("Custom...", None)
        self.weapon_combo.currentTextChanged.connect(self.update_weapon_display)
        
        # Update overlay if it exists and session is active
        if hasattr(self, 'overlay_window') and self.overlay_window:
            # Get current session info
            session_active = "Session Active" in self.session_label.text()
            if session_active:
                activity = self.activity_combo.currentText()
                self.overlay_window.update_session_info("active", activity, weapon=weapon)
    
    def get_selected_weapon(self):
        """Get the currently selected weapon"""
        if not hasattr(self, 'weapon_combo'):
            return None
            
        current_data = self.weapon_combo.currentData()
        current_text = self.weapon_combo.currentText()
        
        if current_data is None:
            if current_text == "Select Weapon...":
                return None
            elif current_text == "Custom...":
                return None  # Could open dialog for custom weapon
            else:
                return current_text  # Custom typed weapon
        else:
            return current_data
    
    def get_weapon_stats(self, weapon_name):
        """Get detailed stats for selected weapon"""
        if not weapon_name:
            weapon_name = self.get_selected_weapon()
            if not weapon_name:
                return {}
        
        from pathlib import Path
        import json
        
        try:
            weapons_path = Path(__file__).parent.parent / "weapons.json"
            if weapons_path.exists():
                with open(weapons_path, 'r') as f:
                    weapons_data = json.load(f)
                    return weapons_data.get('data', {}).get(weapon_name, {})
        except Exception:
            return {}
        
    def get_full_weapon_config(self):
        """Get complete weapon configuration for calculations"""
        weapon_name = self.get_selected_weapon()
        base_stats = self.get_weapon_stats(weapon_name)
        
        # Add configuration panel values
        config_stats = {
            'attachment': getattr(self, 'attachment_combo', type('', (), {'currentText': lambda: 'None'})).currentText(),
            'scope': getattr(self, 'scope_combo', type('', (), {'currentText': lambda: 'None'})).currentText(),
            'enhancers': {
                'damage': getattr(self, 'enhancer_inputs', {}).get('dmg_enh', type('', (), {'value': lambda: 0})).value(),
                'range': getattr(self, 'enhancer_inputs', {}).get('range_enh', type('', (), {'value': lambda: 0})).value(),
                'accuracy': getattr(self, 'enhancer_inputs', {}).get('acc_enh', type('', (), {'value': lambda: 0})).value(),
                'economy': getattr(self, 'enhancer_inputs', {}).get('eco_enh', type('', (), {'value': lambda: 0})).value()
            },
            'damage_input': getattr(self, 'dmg_spinbox', type('', (), {'value': lambda: 0.0})).value(),
            'ammo_input': getattr(self, 'ammo_spinbox', type('', (), {'value': lambda: 0.0})).value()
        }
        
        return {**base_stats, **config_stats}
    
    def get_full_weapon_config(self):
        """Get complete weapon configuration for calculations"""
        config = {
            'weapon': self.get_selected_weapon(),
            'attachment': 'None',
            'scope': 'None',
            'enhancers': {'damage': 0, 'range': 0, 'accuracy': 0, 'economy': 0},
            'stats': {'damage': 0.0, 'ammo': 0.0}
        }
        
        if hasattr(self, 'attachment_combo') and hasattr(self.attachment_combo, 'currentText'):
            config['attachment'] = self.attachment_combo.currentText()
        if hasattr(self, 'scope_combo') and hasattr(self.scope_combo, 'currentText'):
            config['scope'] = self.scope_combo.currentText()
        if hasattr(self, 'enhancer_inputs'):
            def get_enhancer_value(key):
                enhancer = self.enhancer_inputs.get(key)
                return enhancer.value() if enhancer and hasattr(enhancer, 'value') else 0
            
            config['enhancers'] = {
                'damage': get_enhancer_value('dmg_enh'),
                'range': get_enhancer_value('range_enh'),
                'accuracy': get_enhancer_value('acc_enh'),
                'economy': get_enhancer_value('eco_enh')
            }
        if hasattr(self, 'dmg_spinbox') and hasattr(self.dmg_spinbox, 'value'):
            config['stats']['damage'] = self.dmg_spinbox.value()
        if hasattr(self, 'ammo_spinbox') and hasattr(self.ammo_spinbox, 'value'):
            config['stats']['ammo'] = self.ammo_spinbox.value()
            
        return config