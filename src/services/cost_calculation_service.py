"""Cost calculation service for weapon loadouts - consolidates calculation logic"""

import logging
from typing import Optional
from src.services.loadout_service import WeaponLoadout
from src.services.game_data_service import GameDataService


logger = logging.getLogger(__name__)


class CostCalculationService:
    """Centralized service for calculating weapon loadout costs"""
    
    @staticmethod
    async def calculate_cost_per_attack(loadout: WeaponLoadout) -> float:
        """
        Calculate cost per attack for a weapon loadout
        
        Args:
            loadout: Weapon loadout with all components and enhancers
            
        Returns:
            Total cost per attack in PED (weapon decay + ammo cost)
        """
        try:
            logger.debug(f"Calculating cost for loadout: {loadout.name} - Weapon: {loadout.weapon}")
            
            data_service = GameDataService()
            weapon = await data_service.get_weapon_by_name(loadout.weapon)
            if not weapon:
                logger.error(f"Weapon not found in database: {loadout.weapon}")
                return 0.0

            # Base weapon stats
            base_decay = float(weapon.decay) if weapon.decay else 0.0
            base_ammo = weapon.ammo if weapon.ammo else 0
            
            logger.debug(f"Base weapon stats: decay={base_decay:.6f} PED, ammo={base_ammo} PEC")

            # Apply enhancer multipliers
            damage_mult = 1.0 + (loadout.damage_enh * 0.1)  # 10% per damage enhancer
            economy_mult = 1.0 - (loadout.economy_enh * 0.05)  # 5% reduction per economy enhancer
            
            logger.debug(f"Multipliers: damage_mult={damage_mult:.3f}, economy_mult={economy_mult:.3f}")

            # Enhanced values after applying enhancers
            enhanced_decay = base_decay * damage_mult * economy_mult
            enhanced_ammo = base_ammo * damage_mult
            
            logger.debug(f"After weapon enhancers: decay={enhanced_decay:.6f} PED, ammo={enhanced_ammo:.1f} PEC")

            # Add amplifier contribution
            if loadout.amplifier:
                logger.debug(f"Looking up amplifier: {loadout.amplifier}")
                amp = await data_service.get_attachment_by_name(loadout.amplifier)
                if amp:
                    amp_decay = float(amp.decay) if amp.decay else 0
                    amp_ammo = amp.ammo if amp.ammo else 0
                    enhanced_decay += amp_decay
                    enhanced_ammo += amp_ammo
                    logger.debug(f"Amplifier added: decay={amp_decay:.6f} PED, ammo={amp_ammo} PEC")
                else:
                    logger.warning(f"Amplifier not found: {loadout.amplifier}")

            # Add scope contribution
            if loadout.scope:
                logger.debug(f"Looking up scope: {loadout.scope}")
                scope = await data_service.get_attachment_by_name(loadout.scope)
                if scope:
                    scope_decay = float(scope.decay) if scope.decay else 0
                    scope_ammo = scope.ammo if scope.ammo else 0
                    enhanced_decay += scope_decay
                    enhanced_ammo += scope_ammo
                    logger.debug(f"Scope added: decay={scope_decay:.6f} PED, ammo={scope_ammo} PEC")
                else:
                    logger.warning(f"Scope not found: {loadout.scope}")

            # Add sight 1 contribution
            if loadout.sight_1:
                logger.debug(f"Looking up sight 1: {loadout.sight_1}")
                sight = await data_service.get_attachment_by_name(loadout.sight_1)
                if sight:
                    sight_decay = float(sight.decay) if sight.decay else 0
                    sight_ammo = sight.ammo if sight.ammo else 0
                    enhanced_decay += sight_decay
                    enhanced_ammo += sight_ammo
                    logger.debug(f"Sight 1 added: decay={sight_decay:.6f} PED, ammo={sight_ammo} PEC")
                else:
                    logger.warning(f"Sight 1 not found: {loadout.sight_1}")

            # Add sight 2 contribution
            if loadout.sight_2:
                logger.debug(f"Looking up sight 2: {loadout.sight_2}")
                sight = await data_service.get_attachment_by_name(loadout.sight_2)
                if sight:
                    sight_decay = float(sight.decay) if sight.decay else 0
                    sight_ammo = sight.ammo if sight.ammo else 0
                    enhanced_decay += sight_decay
                    enhanced_ammo += sight_ammo
                    logger.debug(f"Sight 2 added: decay={sight_decay:.6f} PED, ammo={sight_ammo} PEC")
                else:
                    logger.warning(f"Sight 2 not found: {loadout.sight_2}")

            # Convert ammo cost from PEC to PED
            ammo_cost_ped = enhanced_ammo / 10000.0
            total_cost_ped = enhanced_decay + ammo_cost_ped
            
            logger.debug(f"FINAL RESULTS: decay={enhanced_decay:.6f} PED, ammo={enhanced_ammo:.1f} PEC ({ammo_cost_ped:.6f} PED)")
            logger.debug(f"TOTAL COST PER ATTACK: {total_cost_ped:.6f} PED")
            
            return total_cost_ped

        except Exception as e:
            logger.error(f"Error calculating cost for loadout {loadout.weapon}: {e}", exc_info=True)
            return 0.0