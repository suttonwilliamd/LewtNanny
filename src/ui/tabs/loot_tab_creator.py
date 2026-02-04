"""Loot tab UI creation methods"""

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class LootTabCreator:
    """Handles creation of the Loot tab UI components"""

    def __init__(self, parent_window):
        self.parent = parent_window

    def create_loot_tab(self):
        """Create the Loot tab with summary, run log, and item breakdown"""
        loot_widget = QWidget()
        loot_layout = QVBoxLayout(loot_widget)
        loot_layout.setContentsMargins(8, 8, 8, 8)
        loot_layout.setSpacing(8)

        summary_section = self.create_loot_summary_section()
        loot_layout.addWidget(summary_section)

        run_log_section = self.create_run_log_table_section()
        loot_layout.addWidget(run_log_section, 1)  # Give run log stretch priority

        item_breakdown_section = self.create_item_breakdown_section()
        loot_layout.addWidget(item_breakdown_section, 1)  # Give item breakdown stretch priority

        logger.info("Loot tab created")
        return loot_widget

    def create_loot_summary_section(self):
        """Create the summary information section for Loot tab"""
        section = QGroupBox("Summary")
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
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        summary_items = [
            ("Creatures Looted", "0"),
            ("Total Cost", "0.00 PED"),
            ("Total Return", "0.00 PED"),
            ("% Return", "0.0%"),
            ("Globals", "0"),
            ("HOFs", "0"),
        ]

        self.parent.loot_summary_labels = {}

        for i, (label, default) in enumerate(summary_items):
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

            self.parent.loot_summary_labels[label] = value_lbl
            layout.addWidget(container, row, col)

        section.setLayout(layout)
        return section

    def create_run_log_table_section(self):
        """Create the run log table section for Loot tab"""
        section = QGroupBox("Run Log")
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
        layout.setContentsMargins(4, 28, 4, 4)  # Top margin accounts for title bar
        layout.setSpacing(4)

        self.parent.run_log_table = QTableWidget()
        self.parent.run_log_table.setColumnCount(7)
        self.parent.run_log_table.setHorizontalHeaderLabels(
            ["Status", "Start Time", "Duration", "Cost", "Return", "ROI", "Items"]
        )
        self.parent.run_log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.parent.run_log_table.setAlternatingRowColors(True)
        self.parent.run_log_table.setSortingEnabled(True)
        self.parent.run_log_table.setShowGrid(True)
        self.parent.run_log_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.parent.run_log_table.customContextMenuRequested.connect(
            self.parent._show_run_log_context_menu
        )
        self.parent.run_log_table.itemSelectionChanged.connect(
            self.parent._on_run_log_selection_changed
        )

        header = self.parent.run_log_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.parent.run_log_table)

        section.setLayout(layout)
        return section

    def create_item_breakdown_section(self):
        """Create the item breakdown table section for Loot tab"""
        section = QGroupBox("Item Breakdown")
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
        layout.setContentsMargins(4, 28, 4, 4)  # Top margin accounts for title bar
        layout.setSpacing(4)

        self.parent.item_breakdown_table = QTableWidget()
        self.parent.item_breakdown_table.setColumnCount(5)
        self.parent.item_breakdown_table.setHorizontalHeaderLabels(
            ["Item Name", "Count", "Value", "Markup", "Total Value"]
        )
        self.parent.item_breakdown_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.parent.item_breakdown_table.setAlternatingRowColors(True)

        header = self.parent.item_breakdown_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        # Enable sorting on header click
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self.parent.on_item_breakdown_header_clicked)

        # Track sort state for count column
        self.parent.item_breakdown_sort_order = Qt.SortOrder.AscendingOrder

        layout.addWidget(self.parent.item_breakdown_table)

        section.setLayout(layout)
        return section
