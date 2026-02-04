"""Modern Weapon Loadout Component - Evolution of LootNanny Design
Simplified, game-inspired weapon selection and attachment management
"""

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class EquipmentSlot(QWidget):
    """Individual equipment slot with icon-based design"""

    item_selected = pyqtSignal(str, str)

    def __init__(self, slot_name: str, icon_text: str, color: str = "#21262D", parent=None):
        super().__init__(parent)
        self.slot_name = slot_name
        self.current_item = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Slot header
        header = QLabel(slot_name)
        header.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        header.setStyleSheet("color: #8B949E; background-color: transparent;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Slot button with icon
        self.slot_btn = QPushButton()
        self.slot_btn.setFixedSize(60, 60)
        self.slot_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 2px solid #30363D;
                border-radius: 8px;
                color: #E6EDF3;
                font-size: 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #21262D;
                border: 2px solid #1565C0;
            }}
        """)
        self.slot_btn.setText(icon_text)
        self.slot_btn.clicked.connect(self._on_slot_click)
        layout.addWidget(self.slot_btn)

        # Item label
        self.item_label = QLabel("Empty")
        self.item_label.setFont(QFont("Arial", 8))
        self.item_label.setStyleSheet("color: #8B949E;")
        self.item_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.item_label.setWordWrap(True)
        layout.addWidget(self.item_label)

    def _on_slot_click(self):
        """Handle slot click"""
        # Show selection dialog
        dialog = QInputDialog(self)
        dialog.setWindowTitle(f"Select {self.slot_name}")
        dialog.setLabelText(f"Choose {self.slot_name} for your loadout:")
        dialog.setInputMode(QInputDialog.InputMode.TextInput)

        if dialog.exec() == QInputDialog.DialogCode.Accepted:
            selected = dialog.textValue()
            self.set_item(selected)
            self.item_selected.emit(self.slot_name, selected)

    def set_item(self, item_name: str):
        """Set the item in this slot"""
        self.current_item = item_name
        if item_name:
            self.item_label.setText(item_name[:12])  # Truncate long names
            self.slot_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1565C0;
                    border: 2px solid #0D47A1;
                    border-radius: 8px;
                    color: #FFFFFF;
                    font-size: 20px;
                    font-weight: bold;
                }
            """)
        else:
            self.item_label.setText("Empty")
            self.slot_btn.setStyleSheet("""
                QPushButton {
                    background-color: #21262D;
                    border: 2px solid #30363D;
                    border-radius: 8px;
                    color: #E6EDF3;
                    font-size: 24px;
                    font-weight: bold;
                }
            """)


class EnhancementPanel(QWidget):
    """Collapsible enhancement panel with modern sliders"""

    values_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_collapsed = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header with toggle button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Enhancements")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #0D47A1;")

        self.toggle_btn = QPushButton("▼")
        self.toggle_btn.setFixedSize(24, 24)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #0D47A1;
                font-weight: bold;
                font-size: 16px;
            }
        """)
        self.toggle_btn.clicked.connect(self._toggle_panel)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_btn)
        layout.addLayout(header_layout)

        # Content area
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border: 1px solid #21262D;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setSpacing(12)

        self.sliders = {}
        enhancements = [
            ("damage", "⚔", "#E53935"),
            ("accuracy", "🎯", "#1E88E5"),
            ("economy", "💰", "#43A047"),
        ]

        for name, icon, color in enhancements:
            slider_widget = self._create_enhancement_slider(name, icon, color)
            self.sliders[name] = slider_widget
            content_layout.addWidget(slider_widget)

        layout.addWidget(self.content_frame)

    def _create_enhancement_slider(self, name: str, icon: str, color: str):
        """Create individual enhancement slider"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Icon and label
        label_widget = QWidget()
        label_widget.setFixedWidth(80)
        label_layout = QHBoxLayout(label_widget)
        label_layout.setContentsMargins(0, 0, 0, 0)

        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 16))
        icon_label.setStyleSheet(f"color: {color};")

        name_label = QLabel(name.title())
        name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #8B949E;")

        label_layout.addWidget(icon_label)
        label_layout.addWidget(name_label)
        label_layout.addStretch()

        layout.addWidget(label_widget)

        # Slider
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(20)
        slider.setValue(0)
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: #21262D;
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {color};
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
                border: 2px solid #161B22;
            }}
            QSlider::sub-page:horizontal {{
                background: {color};
                border-radius: 4px;
            }}
        """)

        # Value label
        value_label = QLabel("0")
        value_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        value_label.setStyleSheet(
            "color: #E6EDF3; background-color: #21262D; padding: 2px 6px; border-radius: 4px;"
        )
        value_label.setFixedWidth(30)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        slider.valueChanged.connect(lambda v: value_label.setText(str(v)))

        layout.addWidget(slider)
        layout.addWidget(value_label)

        # Store reference
        widget.slider = slider
        widget.value_label = value_label

        return widget

    def _toggle_panel(self):
        """Toggle panel collapsed state"""
        self.is_collapsed = not self.is_collapsed
        self.content_frame.setVisible(not self.is_collapsed)
        self.toggle_btn.setText("▶" if self.is_collapsed else "▼")

    def get_values(self) -> dict:
        """Get current enhancement values"""
        return {name: widget.slider.value() for name, widget in self.sliders.items()}


class ModernWeaponSelector(QWidget):
    """Modern weapon selector inspired by LootNanny design patterns"""

    weapon_selected = pyqtSignal(dict)
    cost_calculated = pyqtSignal(dict)

    def __init__(self, parent=None, db_manager=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_weapon = None
        self.current_attachments = {}

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Setup the modern UI layout"""
        # Initialize attributes first
        self.equipment_slots = {}
        self.enhancement_panel = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Weapon selection area
        weapon_section = self._create_weapon_selection()
        layout.addWidget(weapon_section)

        # Equipment slots area
        equipment_section = self._create_equipment_slots()
        layout.addWidget(equipment_section)

        # Enhancement panel
        enhancement_section = EnhancementPanel()
        enhancement_section.values_changed.connect(self._on_enhancements_changed)
        layout.addWidget(enhancement_section)

        # Performance metrics
        metrics_section = self._create_performance_metrics()
        layout.addWidget(metrics_section)

        # Store references
        self.enhancement_panel = enhancement_section

    def _create_weapon_selection(self):
        """Create weapon selection dropdown"""
        group = QGroupBox("Weapon Selection")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                border: 1px solid #21262D;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 20px;
                color: #E6EDF3;
                background-color: #161B22;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 4px 8px;
                color: #0D47A1;
                background-color: #0D1117;
                border-radius: 4px;
                font-weight: 700;
            }
        """)

        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        search_label = QLabel("Search:")
        search_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))

        self.weapon_search = QLineEdit()
        self.weapon_search.setPlaceholderText("Type to filter weapons...")
        self.weapon_search.setStyleSheet("""
            QLineEdit {
                background-color: #0D1117;
                border: 1px solid #21262D;
                border-radius: 6px;
                padding: 8px 12px;
                color: #E6EDF3;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #1565C0;
            }
        """)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.weapon_search)
        layout.addLayout(search_layout)

        # Weapon dropdown
        self.weapon_combo = QComboBox()
        self.weapon_combo.setStyleSheet("""
            QComboBox {
                background-color: #0D1117;
                border: 1px solid #21262D;
                border-radius: 6px;
                padding: 8px 12px;
                color: #E6EDF3;
                font-size: 13px;
                min-height: 20px;
            }
            QComboBox::down-arrow {
                border: none;
                width: 24px;
                background-color: #21262D;
                border-radius: 0 6px 6px 0;
                margin-right: -12px;
            }
            QComboBox QAbstractItemView {
                background-color: #161B22;
                border: 1px solid #21262D;
                color: #E6EDF3;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        self.weapon_combo.currentTextChanged.connect(self._on_weapon_changed)
        layout.addWidget(self.weapon_combo)

        return group

    def _create_equipment_slots(self):
        """Create equipment slot grid"""
        group = QGroupBox("Equipment Slots")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                border: 1px solid #21262D;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 20px;
                color: #E6EDF3;
                background-color: #161B22;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 4px 8px;
                color: #0D47A1;
                background-color: #0D1117;
                border-radius: 4px;
                font-weight: 700;
            }
        """)

        layout = QGridLayout(group)
        layout.setSpacing(12)

        # Create slots
        slots_config = [
            ("Amplifier", "⚡", "#FF6F00"),
            ("Scope", "🔭", "#1E88E5"),
            ("Sight 1", "👁", "#43A047"),
            ("Sight 2", "👁", "#43A047"),
        ]

        for i, (name, icon, color) in enumerate(slots_config):
            slot = EquipmentSlot(name, icon, color)
            slot.item_selected.connect(self._on_slot_item_selected)
            self.equipment_slots[name] = slot
            layout.addWidget(slot, 0, i)

        return group

    def _create_performance_metrics(self):
        """Create performance metrics display"""
        group = QGroupBox("Performance Metrics")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                border: 1px solid #21262D;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 20px;
                color: #E6EDF3;
                background-color: #161B22;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 4px 8px;
                color: #0D47A1;
                background-color: #0D1117;
                border-radius: 4px;
                font-weight: 700;
            }
        """)

        layout = QGridLayout(group)
        layout.setSpacing(8)

        metrics = [
            ("DPS", "0.0", "#43A047"),
            ("Cost/Shot", "0.000 PED", "#FF6F00"),
            ("DPP", "0.00", "#1E88E5"),
            ("Efficiency", "0%", "#E53935"),
        ]

        for i, (label, value, color) in enumerate(metrics):
            row, col = divmod(i, 2)

            # Metric name
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            label_widget.setStyleSheet("color: #8B949E;")
            layout.addWidget(label_widget, row * 2, col * 2)

            # Metric value
            value_widget = QLabel(value)
            value_widget.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
            value_widget.setStyleSheet(f"""
                color: {color};
                background-color: #21262D;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: 700;
            """)
            value_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(value_widget, row * 2, col * 2 + 1)

        return group

    def _on_weapon_changed(self, weapon_name: str):
        """Handle weapon selection change"""
        if weapon_name:
            # Emit weapon selected signal
            data = {
                "weapon": weapon_name,
                "type": "selected",
                "attachments": self.current_attachments,
            }
            self.weapon_selected.emit(data)
            self._calculate_performance()

    def _on_slot_item_selected(self, slot_name: str, item_name: str):
        """Handle equipment slot selection"""
        self.current_attachments[slot_name] = item_name
        self._calculate_performance()

    def _on_enhancements_changed(self, values: dict):
        """Handle enhancement value changes"""
        # Recalculate performance with new enhancements
        self._calculate_performance()

    def _calculate_performance(self):
        """Calculate and emit performance metrics"""
        # Simplified calculation - in real implementation would use weapon stats
        enhancements = self.enhancement_panel.get_values()

        # Mock calculations for demonstration
        base_dps = 25.0
        base_cost = 0.05

        damage_enh = enhancements.get("damage", 0)
        enhancements.get("accuracy", 0)
        economy_enh = enhancements.get("economy", 0)

        # Apply enhancement bonuses
        dps = base_dps * (1 + damage_enh * 0.05)
        cost = base_cost * (1 + economy_enh * 0.02)

        dpp = dps / cost if cost > 0 else 0
        efficiency = min(100, dpp * 10)  # Mock efficiency

        # Emit performance data
        performance_data = {
            "dps": dps,
            "cost_per_shot": cost,
            "dpp": dpp,
            "efficiency": efficiency,
            "total_cost": cost,
        }

        self.cost_calculated.emit(performance_data)
        self._update_metrics_display(performance_data)

    def _update_metrics_display(self, data: dict):
        """Update the metrics display with new values"""
        # Update the performance labels
        # This would require storing references to the metric labels
        pass

    def setup_connections(self):
        """Setup signal connections"""
        pass

    async def load_weapons(self):
        """Load weapons from database"""
        try:
            if self.db_manager:
                weapons = await self.db_manager.get_all_weapons()
                self.weapon_combo.clear()
                self.weapon_combo.addItem("Select Weapon...", None)

                for weapon in weapons:
                    self.weapon_combo.addItem(weapon.name, weapon.id)

                logger.info(f"Loaded {len(weapons)} weapons")
        except Exception as e:
            logger.error(f"Error loading weapons: {e}")


# For backward compatibility, create alias
WeaponSelector = ModernWeaponSelector
