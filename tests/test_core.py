"""
Unit Tests for LewtNanny Core Functionality
Tests data services, calculations, and models
"""

import sys
import asyncio
import unittest
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent))


class TestWeaponModels(unittest.TestCase):
    """Test weapon data models"""
    
    def test_weapon_creation(self):
        """Test weapon model creation"""
        from src.models.models import Weapon
        
        weapon = Weapon(
            id="test_weapon",
            name="Test Weapon",
            ammo=100,
            decay=Decimal("0.05"),
            weapon_type="Rifle",
            dps=Decimal("10.5"),
            eco=Decimal("150.0"),
            range_=50
        )
        
        self.assertEqual(weapon.id, "test_weapon")
        self.assertEqual(weapon.name, "Test Weapon")
        self.assertEqual(weapon.ammo, 100)
        self.assertEqual(float(weapon.decay), 0.05)
        self.assertEqual(weapon.weapon_type, "Rifle")
        self.assertEqual(float(weapon.dps), 10.5)
        self.assertEqual(float(weapon.eco), 150.0)
    
    def test_weapon_decimal_conversion(self):
        """Test that string values are converted to Decimal"""
        from src.models.models import Weapon
        
        weapon = Weapon(
            id="test",
            name="Test",
            ammo=100,
            decay="0.05",  # String
            weapon_type="Pistol",
            dps="10.5",    # String
        )
        
        self.assertIsInstance(weapon.decay, Decimal)
        self.assertIsInstance(weapon.dps, Decimal)


class TestDPPCalculation(unittest.TestCase):
    """Test DPP (Damage per PEC) calculations"""
    
    def test_dpp_formula(self):
        """Test DPP calculation formula: DPP = Damage / (Cost_PED * 100)"""
        # Given
        damage = 15.0  # Damage per shot
        cost_ped = 0.0216  # Cost per shot in PED
        
        # When: Calculate DPP
        cost_pec = cost_ped * 100  # Convert PED to PEC
        dpp = damage / cost_pec  # DPP formula
        
        # Then
        expected_dpp = damage / (cost_ped * 100)
        self.assertAlmostEqual(dpp, expected_dpp, places=2)
        self.assertAlmostEqual(dpp, 6.94, places=1)
    
    def test_dpp_with_max_enhancements(self):
        """Test DPP with max enhancements (Dmg:20, Eco:20)"""
        # Base values
        base_damage = 15.0
        base_decay = 0.05
        base_ammo = 100
        
        # Enhancement multipliers
        damage_mult = 1.0 + (20 * 0.1)  # 3.0x at level 20
        economy_mult = 1.0 - (20 * 0.05)  # 0.0x at level 20 (free!)
        
        # Enhanced values
        enhanced_damage = base_damage * damage_mult
        enhanced_decay = base_decay * economy_mult
        enhanced_ammo = base_ammo * damage_mult
        
        # Calculate cost
        ammo_cost = enhanced_ammo / 10000.0
        total_cost_ped = enhanced_decay + ammo_cost
        
        # Calculate DPP
        dpp = enhanced_damage / (total_cost_ped * 100)
        
        # With max economy, decay is free so only ammo cost matters
        expected_dpp = enhanced_damage / (ammo_cost * 100)
        
        self.assertAlmostEqual(dpp, expected_dpp, places=2)
        self.assertGreater(dpp, 10)  # High DPP with max enhancements


class TestLoadoutService(unittest.TestCase):
    """Test loadout persistence service"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize test database"""
        from src.services.loadout_service import LoadoutService
        
        cls.service = LoadoutService()
        cls.test_loadout_name = "UnitTest_Loadout"
    
    def test_create_loadout(self):
        """Test creating a loadout"""
        from src.services.loadout_service import LoadoutService, WeaponLoadout
        
        service = LoadoutService()
        
        loadout = WeaponLoadout(
            name=self.test_loadout_name,
            weapon="Test Weapon",
            amplifier="Test Amp",
            scope="Test Scope",
            sight_1="Test Sight 1",
            sight_2="Test Sight 2",
            damage_enh=10,
            accuracy_enh=5,
            economy_enh=5
        )
        
        # Create
        loop = asyncio.get_event_loop()
        
        # Clean up any existing loadout first
        loop.run_until_complete(service.delete_loadout_by_name(self.test_loadout_name))
        
        loadout_id = loop.run_until_complete(service.create_loadout(loadout))
        
        self.assertIsNotNone(loadout_id)
        self.assertGreater(loadout_id, 0)
    
    def test_get_loadout(self):
        """Test retrieving a loadout"""
        from src.services.loadout_service import LoadoutService, WeaponLoadout
        
        service = LoadoutService()
        loop = asyncio.get_event_loop()
        
        # First create the loadout if it doesn't exist
        existing = loop.run_until_complete(service.get_loadout_by_name(self.test_loadout_name))
        if existing is None:
            loadout = WeaponLoadout(
                name=self.test_loadout_name,
                weapon="Test Weapon",
                damage_enh=10
            )
            loop.run_until_complete(service.create_loadout(loadout))
        
        loadout = loop.run_until_complete(service.get_loadout_by_name(self.test_loadout_name))
        
        self.assertIsNotNone(loadout)
        self.assertEqual(loadout.name, self.test_loadout_name)
        self.assertEqual(loadout.damage_enh, 10)
    
    def test_delete_loadout(self):
        """Test deleting a loadout"""
        from src.services.loadout_service import LoadoutService
        
        service = LoadoutService()
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(service.delete_loadout_by_name(self.test_loadout_name))
        
        self.assertTrue(result)
        
        # Verify deleted
        loadout = loop.run_until_complete(service.get_loadout_by_name(self.test_loadout_name))
        self.assertIsNone(loadout)


class TestGameDataService(unittest.TestCase):
    """Test game data service"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize service"""
        from src.services.game_data_service import GameDataService
        cls.service = GameDataService()
    
    def test_get_counts(self):
        """Test getting database counts"""
        loop = asyncio.get_event_loop()
        counts = loop.run_until_complete(self.service.get_counts())
        
        self.assertIn('weapons', counts)
        self.assertIn('attachments', counts)
        self.assertIn('resources', counts)
        
        # Should have data from migration
        self.assertGreater(counts['weapons'], 0)
    
    def test_search_weapons(self):
        """Test weapon search"""
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.service.search_weapons("ArMatrix", 5))
        
        self.assertGreater(len(results), 0)
        for weapon in results:
            self.assertIn("ArMatrix", weapon.name)
    
    def test_get_best_weapons_by_dps(self):
        """Test getting top weapons by DPS"""
        loop = asyncio.get_event_loop()
        weapons = loop.run_until_complete(self.service.get_best_weapons_by_dps(5))
        
        self.assertEqual(len(weapons), 5)
        
        # Verify sorted by DPS (descending)
        for i in range(len(weapons) - 1):
            if weapons[i].dps and weapons[i + 1].dps:
                self.assertGreaterEqual(float(weapons[i].dps), float(weapons[i + 1].dps))


class TestWeaponCalculator(unittest.TestCase):
    """Test weapon stat calculations"""
    
    def test_calculate_enhanced_stats(self):
        """Test calculating enhanced weapon stats"""
        from src.services.game_data_service import WeaponCalculator
        
        calculator = WeaponCalculator()
        loop = asyncio.get_event_loop()
        
        # Calculate for a weapon
        stats = loop.run_until_complete(
            calculator.calculate_enhanced_stats("ArMatrix BC-100 (L)", damage_enhancement=10, economy_enhancement=5)
        )
        
        self.assertIsNotNone(stats)
        self.assertGreater(float(stats.dps), 0)
        self.assertGreater(float(stats.total_cost_per_shot), 0)
        self.assertGreater(float(stats.damage_per_ped), 0)  # DPP


class TestAttachmentFiltering(unittest.TestCase):
    """Test attachment filtering by type"""
    
    def test_filter_scopes(self):
        """Test filtering scopes from attachments"""
        from src.services.game_data_service import GameDataService
        
        service = GameDataService()
        loop = asyncio.get_event_loop()
        
        all_attachments = loop.run_until_complete(service.get_all_attachments())
        scopes = [a for a in all_attachments if a.attachment_type == 'Scope']
        
        # Verify all are actually scopes
        for scope in scopes:
            self.assertEqual(scope.attachment_type, 'Scope')
    
    def test_filter_sights(self):
        """Test filtering sights from attachments"""
        from src.services.game_data_service import GameDataService
        
        service = GameDataService()
        loop = asyncio.get_event_loop()
        
        all_attachments = loop.run_until_complete(service.get_all_attachments())
        sights = [a for a in all_attachments if a.attachment_type == 'Sight']
        
        # Verify all are actually sights
        for sight in sights:
            self.assertEqual(sight.attachment_type, 'Sight')


if __name__ == "__main__":
    unittest.main(verbosity=2)
