"""
Crafting tab implementation for LewtNanny
Tracks crafting statistics and provides blueprint cost calculator
"""

import json
import logging
import asyncio
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QComboBox, QLineEdit,
    QScrollArea, QFrame, QCheckBox, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor

logger = logging.getLogger(__name__)


class CraftingTabWidget(QWidget):
    """Crafting statistics and tracking widget with blueprint calculator"""

    # Signal to add crafting cost as negative loot
    add_crafting_cost = pyqtSignal(float)

    def __init__(self, db_manager=None, config_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.crafting_data = []
        self.blueprints_data = {}
        self.resources_data = {}
        self.current_blueprint = None
        self.total_crafts = 0
        self.total_successes = 0
        self.total_cost = Decimal('0')
        self.total_return = Decimal('0')

        # Initialize UI elements to prevent AttributeError
        self.blueprint_combo = None
        self.blueprint_search = None
        self.materials_table = None
        self.craft_history_table = None
        self.blueprint_name_label = None
        self.materials_cost_label = None
        self.markup_label = None
        self.crafting_stats_labels = {}
        self.form_fields = {}
        self.calculated_labels = {}
        self.add_to_session_btn = None
        self.residue_checkbox = None
        self.override_checkbox = None

        self.load_game_data()
        self.setup_ui()
        logger.info("CraftingTabWidget initialized")

    def load_game_data(self):
        """Load blueprints and resources data from database and JSON files"""
        try:
            # Try to load from database first
            if self.db_manager:
                self.load_blueprints_from_db()
            else:
                # Fallback to JSON if no database manager
                self.load_blueprints_from_json()

            # Load resources from JSON (these are reference data)
            resources_path = Path(__file__).parent.parent.parent.parent / "data" / "resources.json"
            if resources_path.exists():
                with open(resources_path, 'r') as f:
                    data = json.load(f)
                    self.resources_data = data.get('data', {})

            logger.debug(f"Loaded {len(self.blueprints_data)} blueprints and {len(self.resources_data)} resources")
        except Exception as e:
            logger.error(f"Error loading game data: {e}")

    def load_blueprints_from_db(self):
        """Load blueprints from database"""
        try:
            import aiosqlite

            async def load_and_populate():
                async with aiosqlite.connect(self.db_manager.db_path) as db:
                    # First try to load existing blueprints
                    cursor = await db.execute("""
                        SELECT id, name, materials FROM crafting_blueprints
                        WHERE materials IS NOT NULL AND materials != '[]' AND materials != ''
                    """)
                    rows = await cursor.fetchall()
                    logger.info(f"Database query returned {len(rows)} blueprint rows")

                    blueprints = {}
                    for row in rows:
                        try:
                            materials = json.loads(row[2]) if isinstance(row[2], str) else row[2]
                            if materials and isinstance(materials, list) and len(materials) > 0:
                                blueprints[row[1]] = materials  # Use name as key
                            else:
                                logger.debug(f"Blueprint {row[1]} has no valid materials: {materials}")
                        except (json.JSONDecodeError, TypeError, IndexError) as e:
                            logger.warning(f"Failed to parse materials for blueprint {row[1]}: {e}")
                            continue

                    logger.info(f"Parsed {len(blueprints)} valid blueprints from database")

                    # If no blueprints, populate from JSON
                    if not blueprints:
                        logger.info("No blueprints found in database, populating from JSON")
                        await self.populate_blueprints_from_json(db)

                        # Reload after population
                        cursor = await db.execute("""
                            SELECT id, name, materials FROM crafting_blueprints
                            WHERE materials IS NOT NULL AND materials != '[]' AND materials != ''
                        """)
                        rows = await cursor.fetchall()
                        logger.info(f"After population, database query returned {len(rows)} blueprint rows")

                        for row in rows:
                            try:
                                materials = json.loads(row[2]) if isinstance(row[2], str) else row[2]
                                if materials and isinstance(materials, list) and len(materials) > 0:
                                    blueprints[row[1]] = materials
                            except (json.JSONDecodeError, TypeError, IndexError) as e:
                                logger.warning(f"Failed to parse materials for blueprint {row[1]}: {e}")
                                continue

                        logger.info(f"After population, parsed {len(blueprints)} valid blueprints")

                    return blueprints

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                self.blueprints_data = loop.run_until_complete(load_and_populate())
            finally:
                loop.close()

            logger.info(f"Database loading complete. Blueprints loaded: {len(self.blueprints_data) if self.blueprints_data else 0}")

            if self.blueprints_data:
                logger.info(f"Loaded {len(self.blueprints_data)} blueprints from database")
            else:
                logger.warning("No blueprints loaded from database, falling back to JSON")
                self.load_blueprints_from_json()

        except Exception as e:
            logger.error(f"Error loading blueprints from database: {e}")
            self.load_blueprints_from_json()

        except Exception as e:
            logger.error(f"Error loading blueprints from database: {e}")
            self.load_blueprints_from_json()

    def load_blueprints_from_json(self):
        """Fallback: Load blueprints from JSON file"""
        try:
            blueprints_path = Path(__file__).parent.parent.parent.parent / "data" / "crafting.json"
            if blueprints_path.exists():
                with open(blueprints_path, 'r') as f:
                    data = json.load(f)
                    self.blueprints_data = data.get('data', {})
        except Exception as e:
            logger.error(f"Error loading blueprints from JSON: {e}")
            self.blueprints_data = {}

    async def populate_blueprints_from_json(self, db):
        """Populate crafting_blueprints table from JSON data"""
        try:
            blueprints_path = Path(__file__).parent.parent.parent.parent / "data" / "crafting.json"
            if not blueprints_path.exists():
                logger.warning("crafting.json not found, cannot populate database")
                return

            with open(blueprints_path, 'r', encoding='utf-8') as f:
                crafting_data = json.load(f)

            blueprints_migrated = 0
            for blueprint_id, materials in crafting_data.get('data', {}).items():
                try:
                    result_item = blueprint_id.replace(' Blueprint (L)', '').replace(' Blueprint', '')
                    # Store materials as JSON in crafting_blueprints table
                    materials_json = json.dumps(materials) if isinstance(materials, list) else '[]'

                    await db.execute("""
                        INSERT OR IGNORE INTO crafting_blueprints (id, name, materials, result_item, result_quantity)
                        VALUES (?, ?, ?, ?, ?)
                    """, (blueprint_id, blueprint_id, materials_json, result_item, 1))

                    blueprints_migrated += 1
                except Exception as e:
                    logger.error(f"Error migrating blueprint {blueprint_id}: {e}")

            await db.commit()
            logger.info(f"Populated {blueprints_migrated} blueprints into database")

        except Exception as e:
            logger.error(f"Error populating blueprints from JSON: {e}")

    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Blueprint selection dropdown at top
        blueprint_selector = self.create_blueprint_dropdown()
        layout.addWidget(blueprint_selector)

        # Materials table below
        materials_section = self.create_materials_table_section()
        layout.addWidget(materials_section)

        # Comprehensive vertical form layout
        form_section = self.create_crafting_form_section()
        layout.addWidget(form_section)

        # Wide button to add crafting data to session
        add_button_section = self.create_add_to_session_button()
        layout.addWidget(add_button_section)

        # Additional calculated fields below
        calculated_fields_section = self.create_calculated_fields_section()
        layout.addWidget(calculated_fields_section)

        layout.addStretch()

    def showEvent(self, event):
        """Called when the widget becomes visible"""
        super().showEvent(event)
        # Update blueprint dropdown when widget becomes visible
        if hasattr(self, 'blueprint_combo') and self.blueprint_combo:
            self.update_blueprint_dropdown()

    def create_blueprint_dropdown(self):
        """Create blueprint selection dropdown at top"""
        section = QWidget()
        layout = QHBoxLayout(section)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        label = QLabel("Blueprint:")
        label.setFont(QFont("Arial", 10))
        label.setStyleSheet("color: #8B949E;")
        layout.addWidget(label)

        self.blueprint_combo = QComboBox()
        self.blueprint_combo.setStyleSheet("""
            QComboBox {
                background-color: #0D1117;
                border: 1px solid #30363D;
                border-radius: 4px;
                padding: 6px;
                color: #E6EDF3;
                min-width: 300px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #8B949E;
            }
        """)
        layout.addWidget(self.blueprint_combo)

        self.blueprint_combo.currentIndexChanged.connect(self.on_blueprint_selected)

        layout.addStretch()
        return section

    def create_materials_table_section(self):
        """Create materials table with multiple columns"""
        section = QGroupBox("Materials Required")
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #8B949E;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 28, 4, 4)
        layout.setSpacing(4)

        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(6)
        self.materials_table.setHorizontalHeaderLabels([
            "Resource", "Per Click", "Total", "TT Cost", "Markup", "Total Cost"
        ])
        self.materials_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.materials_table.setAlternatingRowColors(True)

        header = self.materials_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.materials_table)
        section.setLayout(layout)
        return section

    def create_crafting_form_section(self):
        """Create comprehensive vertical form with various field types"""
        section = QGroupBox("")
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Initialize form fields
        self.form_fields = {}

        # Form fields in exact order specified
        form_field_specs = [
            ("Total Clicks:", "0", "text"),
            ("Use Residue:", "", "checkbox"),
            ("OVERRIDE: 1 Item Per Success:", "", "checkbox"),
            ("Item Max TT:", "0.00", "currency"),
            ("Residue Markup:", "0", "percentage"),
            ("Blueprint Markup:", "0", "percentage"),
            ("Residue Required:", "0", "text"),
            ("TT Cost:", "0.00", "currency"),
            ("Total Cost:", "0.00", "currency")
        ]

        for label_text, default, field_type in form_field_specs:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)

            label = QLabel(label_text)
            label.setFont(QFont("Arial", 9))
            label.setStyleSheet("color: #FFFFFF;")
            label.setFixedWidth(180)
            row_layout.addWidget(label)

            if field_type == "checkbox":
                checkbox = QCheckBox()
                if label_text == "Use Residue:":
                    self.residue_checkbox = checkbox
                elif label_text == "OVERRIDE: 1 Item Per Success:":
                    self.override_checkbox = checkbox
                checkbox.setStyleSheet("color: #FFFFFF;")
                row_layout.addWidget(checkbox)
                row_layout.addStretch()
                self.form_fields[label_text] = checkbox

            elif field_type == "percentage":
                container = QWidget()
                container_layout = QHBoxLayout(container)
                container_layout.setContentsMargins(0, 0, 0, 0)
                container_layout.setSpacing(2)

                line_edit = QLineEdit(default)
                line_edit.setStyleSheet("""
                    QLineEdit {
                        background-color: #0D1117;
                        border: 1px solid #30363D;
                        border-radius: 4px;
                        padding: 4px;
                        color: #E6EDF3;
                    }
                """)
                line_edit.setFixedWidth(80)
                container_layout.addWidget(line_edit)

                percent_label = QLabel("%")
                percent_label.setStyleSheet("color: #8B949E;")
                container_layout.addWidget(percent_label)

                row_layout.addWidget(container)
                row_layout.addStretch()
                self.form_fields[label_text] = line_edit

            elif field_type == "currency":
                container = QWidget()
                container_layout = QHBoxLayout(container)
                container_layout.setContentsMargins(0, 0, 0, 0)
                container_layout.setSpacing(2)

                line_edit = QLineEdit(default)
                line_edit.setStyleSheet("""
                    QLineEdit {
                        background-color: #0D1117;
                        border: 1px solid #30363D;
                        border-radius: 4px;
                        padding: 4px;
                        color: #E6EDF3;
                    }
                """)
                line_edit.setFixedWidth(80)
                container_layout.addWidget(line_edit)

                ped_label = QLabel("PED")
                ped_label.setStyleSheet("color: #8B949E; font-size: 10px;")
                container_layout.addWidget(ped_label)

                row_layout.addWidget(container)
                row_layout.addStretch()
                self.form_fields[label_text] = line_edit

            else:  # text field
                line_edit = QLineEdit(default)
                line_edit.setStyleSheet("""
                    QLineEdit {
                        background-color: #0D1117;
                        border: 1px solid #30363D;
                        border-radius: 4px;
                        padding: 4px;
                        color: #E6EDF3;
                    }
                """)
                line_edit.setFixedWidth(100)
                row_layout.addWidget(line_edit)
                row_layout.addStretch()
                self.form_fields[label_text] = line_edit

                # Connect Total Clicks field to update materials when changed
                if label_text == "Total Clicks:":
                    line_edit.textChanged.connect(self.update_materials_display)

            layout.addLayout(row_layout)

        section.setLayout(layout)
        return section

    def create_add_to_session_button(self):
        """Create wide button to add crafting data to session"""
        section = QWidget()
        layout = QHBoxLayout(section)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.add_to_session_btn = QPushButton("Add Run To Active Run")
        self.add_to_session_btn.setFixedHeight(40)
        self.add_to_session_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2EA043;
            }
            QPushButton:pressed {
                background-color: #1F6FEB;
            }
            QPushButton:disabled {
                background-color: #3D444D;
                color: #6A737D;
            }
        """)
        self.add_to_session_btn.clicked.connect(self._on_add_to_session_clicked)
        layout.addWidget(self.add_to_session_btn)

        return section

    def create_calculated_fields_section(self):
        """Create additional calculated fields section"""
        section = QGroupBox("")
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
            }
        """)

        layout = QGridLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Additional calculated fields in exact order
        calculated_items = [
            ("Quantity Success %:", "0.0%"),
            ("Item Markup:", "0.0%"),
            ("Expected Successes:", "0"),
            ("Success TT Value:", "0.00 PED"),
            ("Partials TT Value:", "0.00 PED"),
            ("Expected Returns:", "0.00 PED"),
            ("Breakeven Markup:", "0.0%")
        ]

        self.calculated_labels = {}

        for i, (label_text, default) in enumerate(calculated_items):
            row = i // 2
            col = (i % 2) * 2

            # Label
            label = QLabel(label_text)
            label.setFont(QFont("Arial", 9))
            label.setStyleSheet("color: #8B949E;")
            layout.addWidget(label, row, col)

            # Value
            value_label = QLabel(default)
            value_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
            value_label.setStyleSheet("""
                color: #58A6FF;
                background-color: #0D1117;
                border: 1px solid #30363D;
                border-radius: 4px;
                padding: 4px 8px;
            """)
            layout.addWidget(value_label, row, col + 1)

            self.calculated_labels[label_text] = value_label

        section.setLayout(layout)
        return section

    def create_materials_section(self):
        """Create materials display section"""
        section = QGroupBox("Materials Required")
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #8B949E;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 28, 4, 4)
        layout.setSpacing(4)

        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(4)
        self.materials_table.setHorizontalHeaderLabels([
            "Material", "Quantity", "TT Value", "Total Cost"
        ])
        self.materials_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.materials_table.setAlternatingRowColors(True)
        self.materials_table.setSortingEnabled(True)

        header = self.materials_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.materials_table)

        section.setLayout(layout)
        return section

    def create_cost_summary_section(self):
        """Create cost summary section"""
        section = QGroupBox("Cost Summary")
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #8B949E;
                font-size: 11px;
            }
        """)

        layout = QGridLayout()
        layout.setContentsMargins(4, 28, 4, 4)
        layout.setSpacing(4)

        self.blueprint_name_label = QLabel("No Blueprint Selected")
        self.blueprint_name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.blueprint_name_label.setStyleSheet("color: #E6EDF3;")
        layout.addWidget(self.blueprint_name_label, 0, 0, 1, 2)

        materials_cost_label = QLabel("Materials Cost:")
        materials_cost_label.setFont(QFont("Arial", 9))
        materials_cost_label.setStyleSheet("color: #8B949E;")
        layout.addWidget(materials_cost_label, 1, 0)

        self.materials_cost_label = QLabel("0.00 PED")
        self.materials_cost_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.materials_cost_label.setStyleSheet("""
            color: #E6EDF3;
            background-color: #0D1117;
            border: 1px solid #30363D;
            border-radius: 4px;
            padding: 4px;
        """)
        layout.addWidget(self.materials_cost_label, 1, 1)

        markup_label = QLabel("Est. Markup:")
        markup_label.setFont(QFont("Arial", 9))
        markup_label.setStyleSheet("color: #8B949E;")
        layout.addWidget(markup_label, 2, 0)

        self.markup_label = QLabel("0%")
        self.markup_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.markup_label.setStyleSheet("""
            color: #58A6FF;
            background-color: #0D1117;
            border: 1px solid #30363D;
            border-radius: 4px;
            padding: 4px;
        """)
        layout.addWidget(self.markup_label, 2, 1)

        section.setLayout(layout)
        return section

    def create_stats_section(self):
        """Create session stats section"""
        section = QGroupBox("Session Stats")
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #8B949E;
                font-size: 11px;
            }
        """)

        layout = QGridLayout()
        layout.setContentsMargins(4, 28, 4, 4)
        layout.setSpacing(4)

        stats_items = [
            ("Total Crafts", "0"),
            ("Successes", "0"),
            ("Success Rate", "0.0%"),
            ("Total Cost", "0.00 PED"),
            ("Total Return", "0.00 PED"),
            ("Profit/Loss", "0.00 PED")
        ]

        self.crafting_stats_labels = {}

        for i, (label, default) in enumerate(stats_items):
            row = i // 3
            col = i % 3

            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(2)

            lbl = QLabel(label)
            lbl.setFont(QFont("Arial", 9))
            lbl.setStyleSheet("color: #8B949E;")
            container_layout.addWidget(lbl)

            value_lbl = QLabel(default)
            value_lbl.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
            value_lbl.setStyleSheet("""
                color: #E6EDF3;
                background-color: #0D1117;
                border: 1px solid #30363D;
                border-radius: 4px;
                padding: 4px;
            """)
            container_layout.addWidget(value_lbl)

            self.crafting_stats_labels[label] = value_lbl
            layout.addWidget(container, row, col)

        section.setLayout(layout)
        return section

    def create_craft_history_section(self):
        """Create craft history section"""
        section = QGroupBox("Crafting Log")
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #8B949E;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 28, 4, 4)
        layout.setSpacing(4)

        self.craft_history_table = QTableWidget()
        self.craft_history_table.setColumnCount(5)
        self.craft_history_table.setHorizontalHeaderLabels([
            "Time", "Blueprint", "Result", "Cost", "Return"
        ])
        self.craft_history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.craft_history_table.setAlternatingRowColors(True)
        self.craft_history_table.setSortingEnabled(True)

        header = self.craft_history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.craft_history_table)

        section.setLayout(layout)
        return section

    def update_blueprint_dropdown(self):
        """Update blueprint dropdown with blueprints that have materials defined"""
        logger.info(f"update_blueprint_dropdown called with {len(self.blueprints_data)} blueprints")
        if self.blueprint_combo is None:
            logger.warning("blueprint_combo is None, skipping")
            return

        self.blueprint_combo.clear()
        self.blueprint_combo.addItem("Select Blueprint...", None)

        count_added = 0
        for bp_name in sorted(self.blueprints_data.keys()):
            bp_data = self.blueprints_data[bp_name]
            # Only include blueprints that have materials defined
            if bp_data and isinstance(bp_data, list) and len(bp_data) > 0:
                self.blueprint_combo.addItem(bp_name, bp_name)
                count_added += 1

        logger.info(f"Added {count_added} blueprints to dropdown. Total items: {self.blueprint_combo.count()}")

        self.blueprint_combo.clear()
        self.blueprint_combo.addItem("Select Blueprint...", None)

        count_added = 0
        for bp_name in sorted(self.blueprints_data.keys()):
            bp_data = self.blueprints_data[bp_name]
            # Only include blueprints that have materials defined
            if bp_data and isinstance(bp_data, list) and len(bp_data) > 0:
                self.blueprint_combo.addItem(bp_name, bp_name)
                count_added += 1
                if count_added <= 5:  # Log first 5 for debugging
                    logger.debug(f"Added blueprint: {bp_name}")

        logger.info(f"Added {count_added} blueprints to dropdown. Total items: {self.blueprint_combo.count()}")

        logger.info(f"Blueprint dropdown populated with {self.blueprint_combo.count()} items (including placeholder)")

    def filter_blueprints(self, text):
        """Filter blueprint list based on search text"""
        if not self.blueprint_combo:
            return
            
        self.blueprint_combo.blockSignals(True)
        current_data = self.blueprint_combo.currentData()

        self.blueprint_combo.clear()
        self.blueprint_combo.addItem("Select Blueprint...", None)

        for bp_name in sorted(self.blueprints_data.keys()):
            if text.lower() in bp_name.lower():
                self.blueprint_combo.addItem(bp_name, bp_name)

        if current_data:
            index = self.blueprint_combo.findData(current_data)
            if index >= 0:
                self.blueprint_combo.setCurrentIndex(index)

        self.blueprint_combo.blockSignals(False)

    def on_blueprint_selected(self, index):
        """Handle blueprint selection"""
        if not self.blueprint_combo:
            return

        bp_name = self.blueprint_combo.currentData()
        self.current_blueprint = bp_name
        self.update_materials_display()

    def update_materials_display(self):
        """Update materials table with current blueprint, multiplied by total clicks"""
        if not self.materials_table:
            return

        self.materials_table.setRowCount(0)

        if not self.current_blueprint or self.current_blueprint not in self.blueprints_data:
            if self.blueprint_name_label:
                self.blueprint_name_label.setText("No Blueprint Selected")
            if self.materials_cost_label:
                self.materials_cost_label.setText("0.00 PED")
            if self.markup_label:
                self.markup_label.setText("0%")
            return

        bp_data = self.blueprints_data[self.current_blueprint]
        materials = bp_data if bp_data else []

        if self.blueprint_name_label:
            self.blueprint_name_label.setText(self.current_blueprint)

        # Get total clicks multiplier
        total_clicks = 1  # Default to 1
        if "Total Clicks:" in self.form_fields:
            clicks_text = self.form_fields["Total Clicks:"].text().strip()
            try:
                total_clicks = int(clicks_text) if clicks_text else 1
                total_clicks = max(1, total_clicks)  # Ensure minimum of 1
            except ValueError:
                total_clicks = 1

        total_cost = Decimal('0')
        row = 0

        # Handle both formats: nested arrays and flat arrays
        for material_info in materials:
            if isinstance(material_info, list) and len(material_info) >= 2:
                # Format: [material_name, quantity]
                material_name = material_info[0]
                base_quantity = material_info[1]
            elif isinstance(material_info, list) and len(material_info) == 1:
                # Format: [material_name] - some blueprints have single materials
                continue
            else:
                continue

            tt_value = Decimal('0')
            if material_name in self.resources_data:
                tt_value = Decimal(str(self.resources_data[material_name]))

            # Multiply quantity by total clicks
            total_quantity = base_quantity * total_clicks
            material_total = tt_value * Decimal(str(total_quantity))
            total_cost += material_total

            if self.materials_table:
                self.materials_table.insertRow(row)
                self.materials_table.setItem(row, 0, QTableWidgetItem(material_name))
                self.materials_table.setItem(row, 1, QTableWidgetItem(f"{tt_value:.4f}"))  # Per Click
                self.materials_table.setItem(row, 2, QTableWidgetItem(str(total_quantity)))  # Total (multiplied)
                self.materials_table.setItem(row, 3, QTableWidgetItem(f"{tt_value:.4f}"))  # TT Cost
                self.materials_table.setItem(row, 4, QTableWidgetItem("0%"))  # Markup (placeholder)
                self.materials_table.setItem(row, 5, QTableWidgetItem(f"{material_total:.4f}"))  # Total Cost
            row += 1

        if self.materials_cost_label:
            self.materials_cost_label.setText(f"{total_cost:.2f} PED")
        if self.markup_label:
            self.markup_label.setText("0%")

    def calculate_craft_cost(self) -> Decimal:
        """Calculate total cost for current blueprint"""
        if not self.current_blueprint or self.current_blueprint not in self.blueprints_data:
            return Decimal('0')

        bp_data = self.blueprints_data[self.current_blueprint]
        materials = bp_data if bp_data else []

        total_cost = Decimal('0')
        for material_info in materials:
            if isinstance(material_info, list) and len(material_info) >= 2:
                # Format: [material_name, quantity]
                material_name = material_info[0]
                quantity = material_info[1]
            elif isinstance(material_info, list) and len(material_info) == 1:
                # Format: [material_name] - some blueprints have single materials
                continue
            else:
                continue

            tt_value = Decimal('0')
            if material_name in self.resources_data:
                tt_value = Decimal(str(self.resources_data[material_name]))

            total_cost += tt_value * Decimal(str(quantity))

        return total_cost

    def set_db_manager(self, db_manager):
        """Set database manager"""
        self.db_manager = db_manager
        self.load_crafting_data()

    def load_crafting_data(self):
        """Load crafting data from database"""
        logger.debug("Loading crafting data")
        self.update_crafting_display()

    def update_crafting_display(self):
        """Update crafting statistics display"""
        success_rate = (self.total_successes / self.total_crafts * 100) if self.total_crafts > 0 else Decimal('0')
        profit_loss = self.total_return - self.total_cost

        if "Total Crafts" in self.crafting_stats_labels:
            self.crafting_stats_labels["Total Crafts"].setText(str(self.total_crafts))
        if "Successes" in self.crafting_stats_labels:
            self.crafting_stats_labels["Successes"].setText(str(self.total_successes))
        if "Success Rate" in self.crafting_stats_labels:
            self.crafting_stats_labels["Success Rate"].setText(f"{success_rate:.1f}%")
        if "Total Cost" in self.crafting_stats_labels:
            self.crafting_stats_labels["Total Cost"].setText(f"{self.total_cost:.2f} PED")
        if "Total Return" in self.crafting_stats_labels:
            self.crafting_stats_labels["Total Return"].setText(f"{self.total_return:.2f} PED")

        profit_color = "#3FB950" if profit_loss >= 0 else "#F85149"
        if "Profit/Loss" in self.crafting_stats_labels:
            self.crafting_stats_labels["Profit/Loss"].setText(f"{profit_loss:.2f} PED")
            self.crafting_stats_labels["Profit/Loss"].setStyleSheet(f"""
                color: {profit_color};
                background-color: #0D1117;
                border: 1px solid #30363D;
                border-radius: 4px;
                padding: 4px;
            """)

        logger.debug("Crafting display updated")

    def add_crafting_event(self, event_data: Dict[str, Any]):
        """Add a crafting event"""
        event_type = event_data.get('event_type', '')

        if event_type == 'crafting':
            parsed_data = event_data.get('parsed_data', {})

            self.total_crafts += 1

            cost = parsed_data.get('cost', Decimal('0'))
            return_val = parsed_data.get('return', Decimal('0'))
            success = parsed_data.get('success', False)

            if success:
                self.total_successes += 1

            self.total_cost += Decimal(str(cost)) if cost else Decimal('0')
            self.total_return += Decimal(str(return_val)) if return_val else Decimal('0')

            if self.craft_history_table:
                row = self.craft_history_table.rowCount()
                self.craft_history_table.insertRow(row)

                timestamp = event_data.get('timestamp', '')
                if hasattr(timestamp, 'strftime'):
                    timestamp_str = timestamp.strftime('%H:%M:%S')
                else:
                    timestamp_str = str(timestamp)

                self.craft_history_table.setItem(row, 0, QTableWidgetItem(timestamp_str))
                self.craft_history_table.setItem(row, 1, QTableWidgetItem(
                    parsed_data.get('blueprint', 'Unknown')))
                result_text = "Success" if success else "Failure"
                result_item = QTableWidgetItem(result_text)
                result_item.setForeground(QColor("#3FB950") if success else QColor("#F85149"))
                self.craft_history_table.setItem(row, 2, result_item)
                self.craft_history_table.setItem(row, 3, QTableWidgetItem(f"{cost:.2f} PED"))
                self.craft_history_table.setItem(row, 4, QTableWidgetItem(f"{return_val:.2f} PED"))

            self.update_crafting_display()
            logger.debug(f"Crafting event added: {event_data}")

    def _on_add_to_session_clicked(self):
        """Handle add to session button click - add crafting cost as negative loot"""
        try:
            total_cost = self._get_current_total_material_cost()
            if total_cost > 0:
                # Emit signal with negative cost to subtract from loot
                self.add_crafting_cost.emit(-float(total_cost))
                logger.info(f"Added crafting cost {total_cost:.2f} PED to active run")
            else:
                logger.warning("No crafting cost to add - either no blueprint selected or cost is 0")
        except Exception as e:
            logger.error(f"Error adding crafting cost to session: {e}")

    def set_session_active(self, is_active: bool):
        """Enable or disable the 'Add to Session' button based on session status"""
        if hasattr(self, 'add_to_session_btn') and self.add_to_session_btn:
            self.add_to_session_btn.setEnabled(is_active)
            self.add_to_session_btn.setText("Add Run To Active Run")
            logger.debug(f"Crafting 'Add to Session' button {'enabled' if is_active else 'disabled'}")

    def _get_current_total_material_cost(self) -> Decimal:
        """Get the current total material cost for the selected blueprint * total clicks"""
        if not self.current_blueprint or self.current_blueprint not in self.blueprints_data:
            return Decimal('0')

        bp_data = self.blueprints_data[self.current_blueprint]
        materials = bp_data if bp_data else []

        # Get total clicks multiplier
        total_clicks = 1  # Default to 1
        if "Total Clicks:" in self.form_fields:
            clicks_text = self.form_fields["Total Clicks:"].text().strip()
            try:
                total_clicks = int(clicks_text) if clicks_text else 1
                total_clicks = max(1, total_clicks)  # Ensure minimum of 1
            except ValueError:
                total_clicks = 1

        total_cost = Decimal('0')
        for material_info in materials:
            if isinstance(material_info, list) and len(material_info) >= 2:
                material_name = material_info[0]
                base_quantity = material_info[1]
            else:
                continue

            tt_value = Decimal('0')
            if material_name in self.resources_data:
                tt_value = Decimal(str(self.resources_data[material_name]))

            # Multiply quantity by total clicks
            total_quantity = base_quantity * total_clicks
            material_total = tt_value * Decimal(str(total_quantity))
            total_cost += material_total

        return total_cost

    def clear_data(self):
        """Clear all crafting data"""
        self.crafting_data = []
        self.total_crafts = 0
        self.total_successes = 0
        self.total_cost = Decimal('0')
        self.total_return = Decimal('0')
        if self.craft_history_table:
            self.craft_history_table.setRowCount(0)
        self.update_crafting_display()
        logger.info("Crafting data cleared")
