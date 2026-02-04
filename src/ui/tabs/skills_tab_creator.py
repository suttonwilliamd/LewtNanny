"""Skills tab UI creation methods"""

import logging
from typing import Any

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class SkillsTabCreator:
    """Handles creation of the Skills tab UI components"""

    def __init__(self, parent_window):
        self.parent = parent_window

    def create_skills_tab(self):
        """Create the Skills tab with skill gain tracking"""
        skills_widget = QWidget()
        skills_layout = QVBoxLayout(skills_widget)
        skills_layout.setContentsMargins(8, 8, 8, 8)
        skills_layout.setSpacing(8)

        summary_field = self.create_skills_summary_field()
        skills_layout.addWidget(summary_field)

        skills_table = self.create_skills_table()
        skills_layout.addWidget(skills_table, 1)  # Give skills table stretch priority

        logger.info("Skills tab created")
        return skills_widget

    def create_skills_summary_field(self):
        """Create the skills summary field"""
        section = QGroupBox("")
        section.setStyleSheet("""
            QGroupBox {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        label = QLabel("Total Skill Gain:")
        label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        label.setStyleSheet("color: #8B949E;")
        layout.addWidget(label)

        self.parent.total_skill_gain_value = QLabel("0.00")
        self.parent.total_skill_gain_value.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self.parent.total_skill_gain_value.setStyleSheet("""
            color: #E6EDF3;
            background-color: #0D1117;
            border: 1px solid #30363D;
            border-radius: 4px;
            padding: 4px 12px;
        """)
        layout.addWidget(self.parent.total_skill_gain_value)

        layout.addStretch()

        section.setLayout(layout)
        return section

    def create_skills_table(self):
        """Create the skills table"""
        section = QGroupBox("Skills")
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

        self.parent.skills_table = QTableWidget()
        self.parent.skills_table.setColumnCount(5)
        self.parent.skills_table.setHorizontalHeaderLabels(
            ["#", "Skill Name", "Value", "Procs", "Proc %"]
        )
        self.parent.skills_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.parent.skills_table.setAlternatingRowColors(True)
        self.parent.skills_table.setSortingEnabled(True)

        header = self.parent.skills_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in range(2, 5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.parent.skills_table)

        section.setLayout(layout)
        return section

    def add_skill_event(self, event_data: dict[str, Any]):
        """Add a skill event to the skills tab"""
        event_type = event_data.get("event_type", "")
        parsed_data = event_data.get("parsed_data", {})

        if event_type in ["skill_gain", "skill"]:
            skill_name = parsed_data.get("skill", "")
            experience = parsed_data.get("experience", 0)
            improvement = parsed_data.get("improvement", 0)
            gain_value = experience or improvement

            logger.info(f"[UI] Adding skill event: {skill_name} +{gain_value} exp")

            # Update total skill gain
            current_total = float(self.parent.total_skill_gain_value.text())
            new_total = current_total + gain_value
            self.parent.total_skill_gain_value.setText(f"{new_total:.2f}")

            # Check if skill already exists in table
            existing_row = -1
            for row in range(self.parent.skills_table.rowCount()):
                name_item = self.parent.skills_table.item(row, 1)
                if name_item and name_item.text() == skill_name:
                    existing_row = row
                    break

            if existing_row >= 0:
                # Update existing skill row
                value_item = self.parent.skills_table.item(existing_row, 2)
                procs_item = self.parent.skills_table.item(existing_row, 3)

                current_value = float(value_item.text()) if value_item else 0
                current_procs = int(procs_item.text()) if procs_item else 0

                new_value = current_value + gain_value
                new_procs = current_procs + 1

                self.parent.skills_table.setItem(
                    existing_row, 2, QTableWidgetItem(f"{new_value:.2f}")
                )
                self.parent.skills_table.setItem(existing_row, 3, QTableWidgetItem(str(new_procs)))
            else:
                # Add new skill row
                row = self.parent.skills_table.rowCount()
                self.parent.skills_table.insertRow(row)

                self.parent.skills_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
                self.parent.skills_table.setItem(row, 1, QTableWidgetItem(skill_name))
                self.parent.skills_table.setItem(row, 2, QTableWidgetItem(f"{gain_value:.2f}"))
                self.parent.skills_table.setItem(row, 3, QTableWidgetItem("1"))

            # Recalculate proc % for all rows
            total_procs = sum(
                int(self.parent.skills_table.item(r, 3).text())
                for r in range(self.parent.skills_table.rowCount())
            )
            for r in range(self.parent.skills_table.rowCount()):
                procs = int(self.parent.skills_table.item(r, 3).text())
                proc_percent = (procs / total_procs) * 100 if total_procs > 0 else 100
                self.parent.skills_table.setItem(r, 4, QTableWidgetItem(f"{proc_percent:.0f}%"))

            logger.info("[UI] Skill event added to table")

    def load_session_skills(self, skill_events: list[dict[str, Any]]):
        """Load skills for a specific session"""
        self.parent.skills_table.setRowCount(0)

        for event_data in skill_events:
            skill_name = event_data.get("skill_name", "")
            gain_value = float(event_data.get("gain_value", 0))

            if not skill_name:
                continue

            # Check if skill already exists
            existing_row = None
            for row in range(self.parent.skills_table.rowCount()):
                name_item = self.parent.skills_table.item(row, 1)
                if name_item and name_item.text() == skill_name:
                    existing_row = row
                    break

            if existing_row is not None:
                # Update existing skill
                current_value = float(self.parent.skills_table.item(existing_row, 2).text())
                new_value = current_value + gain_value

                current_procs = int(self.parent.skills_table.item(existing_row, 3).text())
                new_procs = current_procs + 1

                self.parent.skills_table.setItem(
                    existing_row, 2, QTableWidgetItem(f"{new_value:.2f}")
                )
                self.parent.skills_table.setItem(existing_row, 3, QTableWidgetItem(str(new_procs)))
            else:
                # Add new skill
                row = self.parent.skills_table.rowCount()
                self.parent.skills_table.insertRow(row)
                self.parent.skills_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
                self.parent.skills_table.setItem(row, 1, QTableWidgetItem(skill_name))
                self.parent.skills_table.setItem(row, 2, QTableWidgetItem(f"{gain_value:.2f}"))
                self.parent.skills_table.setItem(row, 3, QTableWidgetItem("1"))

            # Update percentages
            total_procs = sum(
                int(self.parent.skills_table.item(r, 3).text())
                for r in range(self.parent.skills_table.rowCount())
            )

            for r in range(self.parent.skills_table.rowCount()):
                procs = int(self.parent.skills_table.item(r, 3).text())
                proc_percent = (procs / total_procs * 100) if total_procs > 0 else 0
                self.parent.skills_table.setItem(r, 4, QTableWidgetItem(f"{proc_percent:.0f}%"))
