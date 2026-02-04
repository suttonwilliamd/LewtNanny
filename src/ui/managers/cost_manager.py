"""Cost calculation and management logic for the main window
"""

import asyncio
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class CostManager:
    """Handles cost calculation and management for the main window"""

    def __init__(self, parent_window):
        self.parent = parent_window

    def check_and_update_cost(self):
        """Check if cost per attack needs to be recalculated"""
        if self.parent.cost_per_attack <= 0:
            new_cost = self.calculate_cost_per_attack()
            if new_cost > 0:
                self.parent.cost_per_attack = new_cost
                logger.info(
                    f"Cost per attack calculated: {self.parent.cost_per_attack:.6f} PED"
                )
                if self.parent.overlay:
                    self.parent.overlay.set_cost_per_attack(self.parent.cost_per_attack)
                self.update_total_cost_display()

    def calculate_cost_per_attack(self) -> float:
        """Calculate cost per attack from the active loadout"""
        try:
            if (
                not hasattr(self.parent, "config_widget")
                or not self.parent.config_widget
            ):
                return 0.0

            active_loadout = (
                self.parent.config_widget.active_loadout_combo.currentData()
            )
            if not active_loadout:
                return 0.0

            # Try to get cost from config_tab's calculated stats
            if hasattr(self.parent.config_widget, "ammo_burn_text") and hasattr(
                self.parent.config_widget, "weapon_decay_text"
            ):
                try:
                    ammo_burn = float(self.parent.config_widget.ammo_burn_text.text())
                    decay = float(self.parent.config_widget.weapon_decay_text.text())
                    ammo_cost = ammo_burn / 10000.0
                    return decay + ammo_cost
                except (ValueError, AttributeError) as e:
                    logger.debug(f"Could not get cost from config_tab: {e}")

            # Fallback: use centralized cost calculation service
            selected_loadout = None
            for loadout in self.parent.config_widget._loadouts:
                if loadout.id == active_loadout:
                    selected_loadout = loadout
                    break

            if not selected_loadout:
                return 0.0

            # Use the centralized cost calculation service
            from src.services.cost_calculation_service import CostCalculationService

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                cost = loop.run_until_complete(
                    CostCalculationService.calculate_cost_per_attack(selected_loadout)
                )
                return cost
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"Error calculating cost per attack: {e}")
            return 0.0

    def update_total_cost_display(self):
        """Update the total cost display based on shots taken and cost per attack"""
        try:
            if self.parent.cost_per_attack <= 0:
                calculated_cost = self.calculate_cost_per_attack()
                # Only use fallback if it gives us a valid cost
                if calculated_cost > 0:
                    self.parent.cost_per_attack = calculated_cost
                    logger.warning(
                        f"FALLBACK: Calculated cost_per_attack: {self.parent.cost_per_attack:.6f} PED"
                    )
                    if self.parent.overlay:
                        self.parent.overlay.set_cost_per_attack(
                            self.parent.cost_per_attack
                        )
                else:
                    logger.warning(
                        f"FALLBACK: Could not calculate valid cost_per_attack (got {calculated_cost:.6f})"
                    )

            if self.parent.cost_per_attack <= 0:
                logger.debug("Cannot update total cost: cost_per_attack is still 0")
                return

            # Calculate shot costs (not including crafting)
            shot_cost = self.parent.total_shots_taken * self.parent.cost_per_attack
            logger.debug(
                f"Updating total cost: shot_cost={shot_cost:.2f} PED (shots={self.parent.total_shots_taken}, cpa={self.parent.cost_per_attack})"
            )

            # Store the shot cost for later use in crafting cost preservation
            if not hasattr(self.parent, "_last_shot_cost"):
                self.parent._last_shot_cost = 0

            # Calculate delta from previous shot cost to avoid double counting
            shot_cost_delta = shot_cost - self.parent._last_shot_cost

            # Get current total cost and add only the incremental shot cost
            current_total = float(
                self.parent.loot_summary_labels["Total Cost"]
                .text()
                .replace(",", "")
                .split()[0]
            )
            new_total = current_total + shot_cost_delta
            self.parent.loot_summary_labels["Total Cost"].setText(
                f"{new_total:.2f} PED"
            )

            # Store current shot cost for next calculation
            self.parent._last_shot_cost = shot_cost

            if self.parent.overlay and self.parent.overlay.overlay_widget:
                self.parent._shots_taken = self.parent.total_shots_taken
                self.parent.overlay._stats["total_cost"] = Decimal(str(new_total))
                self.parent.overlay.overlay_widget._update_stats_display()

            total_return_str = (
                self.parent.loot_summary_labels["Total Return"]
                .text()
                .replace(",", "")
                .split()[0]
            )
            total_return = float(total_return_str)

            if new_total > 0:
                return_pct = (total_return / new_total) * 100
                self.parent.loot_summary_labels["% Return"].setText(
                    f"{return_pct:.1f}%"
                )
            elif total_return > 0:
                self.parent.loot_summary_labels["% Return"].setText("100.0%")

            self.parent._update_analysis_realtime()

        except Exception as e:
            logger.error(f"Error updating total cost display: {e}")

    def on_crafting_cost_added(self, cost: float):
        """Handle crafting cost added as spent cost (like ammo/decay)"""
        try:
            if not self.parent.current_session_id:
                logger.warning("No active session to add crafting cost to")
                return

            # Add crafting cost directly to overlay as spent cost
            if (
                self.parent.overlay
                and self.parent.overlay.overlay_widget
                and hasattr(self.parent.overlay.overlay_widget, "_stats")
            ):
                current_cost = float(
                    self.parent.overlay.overlay_widget._stats.get(
                        "total_cost", Decimal("0")
                    )
                )
                new_cost = current_cost + abs(cost)  # Cost is positive for spending
                self.parent.overlay.overlay_widget._stats["total_cost"] = Decimal(
                    str(new_cost)
                )

                # Update overlay display
                self.parent.overlay.overlay_widget._update_stats_display()

            # Add crafting materials to item breakdown for tracking (as negative for display)
            self.parent._process_loot_event(
                {
                    "item_name": "Crafting Materials",
                    "quantity": 1,
                    "value": cost,  # Keep as negative for item tracking
                }
            )

            # Update main UI totals to include crafting costs
            current_ui_cost = float(
                self.parent.loot_summary_labels["Total Cost"]
                .text()
                .replace(",", "")
                .split()[0]
            )
            new_ui_cost = current_ui_cost + abs(cost)
            self.parent.loot_summary_labels["Total Cost"].setText(
                f"{new_ui_cost:.2f} PED"
            )

            logger.info(f"Added crafting cost: {abs(cost):.2f} PED to spent total")

        except Exception as e:
            logger.error(f"Error handling crafting cost addition: {e}")

    def on_stats_calculated(self, total_cost: float):
        """Handle stats calculation completion - update cost per attack with synchronized value"""
        try:
            self.parent.cost_per_attack = total_cost
            logger.info(
                f"STATS CALCULATED: Updated cost per attack to {self.parent.cost_per_attack:.6f} PED"
            )

            # Update overlay with the synchronized cost
            if self.parent.overlay:
                logger.info(
                    f"STATS CALCULATED: Updating overlay with synchronized cost: {self.parent.cost_per_attack:.6f} PED"
                )
                self.parent.overlay.set_cost_per_attack(self.parent.cost_per_attack)

            # Update total cost display
            self.update_total_cost_display()

        except Exception as e:
            logger.error(f"Error handling stats calculation: {e}")
