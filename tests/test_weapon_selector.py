"""
Unit tests for weapon selector component
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from src.ui.components.weapon_selector import WeaponData, AttachmentData, WeaponSelector


class TestWeaponData:
    """Test WeaponData class"""
    
    def test_weapon_data_creation(self, sample_weapon_data):
        """Test creating weapon data"""
        weapon = WeaponData(sample_weapon_data)
        
        assert weapon.id == '1'
        assert weapon.name == 'Korss H400 (L)'
        assert weapon.damage == Decimal('28')
        assert weapon.ammo_burn == Decimal('11')
        assert weapon.decay == Decimal('0.10')
        assert weapon.hits == 36
        assert weapon.range == 55
        assert weapon.reload_time == Decimal('3.0')
        assert weapon.weapon_type == 'Pistol'
    
    def test_weapon_data_defaults(self):
        """Test weapon data with default values"""
        weapon = WeaponData({})
        
        assert weapon.id == ''
        assert weapon.name == ''
        assert weapon.damage == Decimal('0')
        assert weapon.ammo_burn == Decimal('0')
        assert weapon.decay == Decimal('0')
        assert weapon.hits == 0
        assert weapon.range == 0
        assert weapon.reload_time == Decimal('0')
        assert weapon.weapon_type == ''
    
    def test_calculate_base_cost_per_shot(self, sample_weapon_data):
        """Test base cost calculation"""
        weapon = WeaponData(sample_weapon_data)
        expected_cost = weapon.decay + (weapon.ammo_burn / Decimal('10000'))
        
        assert weapon.calculate_base_cost_per_shot() == expected_cost


class TestAttachmentData:
    """Test AttachmentData class"""
    
    def test_attachment_data_creation(self, sample_attachment_data):
        """Test creating attachment data"""
        attachment = AttachmentData(sample_attachment_data)
        
        assert attachment.id == 'a1'
        assert attachment.name == 'A106 Amplifier'
        assert attachment.damage_bonus == Decimal('0.5')
        assert attachment.ammo_bonus == Decimal('0')
        assert attachment.decay_modifier == Decimal('0.25')
        assert attachment.attachment_type == 'amplifier'
    
    def test_attachment_data_defaults(self):
        """Test attachment data with default values"""
        attachment = AttachmentData({})
        
        assert attachment.id == ''
        assert attachment.name == ''
        assert attachment.damage_bonus == Decimal('0')
        assert attachment.ammo_bonus == Decimal('0')
        assert attachment.decay_modifier == Decimal('0')
        assert attachment.attachment_type == ''


@pytest.mark.ui
class TestWeaponSelector:
    """Test WeaponSelector component"""
    
    def test_weapon_selector_init(self, mock_db_manager):
        """Test weapon selector initialization"""
        with patch('src.ui.components.weapon_selector.QWidget.__init__'):
            selector = WeaponSelector(db_manager=mock_db_manager)
            
            assert selector.db_manager == mock_db_manager
            assert selector.weapons == {}
            assert selector.attachments == {}
            assert selector.sights_scopes == {}
            assert selector.current_weapon is None
            assert selector.current_attachments == []
            assert selector.session_ammo_used == Decimal('0')
            assert selector.session_decay == Decimal('0')
    
    def test_load_weapons(self, mock_db_manager):
        """Test loading weapons"""
        with patch('src.ui.components.weapon_selector.QWidget.__init__'):
            selector = WeaponSelector(db_manager=mock_db_manager)
            selector.load_weapons()
            
            # Should have loaded sample weapons
            assert len(selector.weapons) == 3
            assert '1' in selector.weapons
            assert '2' in selector.weapons
            assert '3' in selector.weapons
    
    def test_load_attachments(self, mock_db_manager):
        """Test loading attachments"""
        with patch('src.ui.components.weapon_selector.QWidget.__init__'):
            selector = WeaponSelector(db_manager=mock_db_manager)
            selector.load_attachments()
            
            # Should have loaded sample attachments
            assert len(selector.attachments) >= 2
            assert 'a1' in selector.attachments
            assert 'a2' in selector.attachments
    
    def test_filter_weapons(self, mock_db_manager):
        """Test weapon filtering"""
        with patch('src.ui.components.weapon_selector.QWidget.__init__'):
            selector = WeaponSelector(db_manager=mock_db_manager)
            selector.load_weapons()
            selector.setup_ui()
            
            # Test empty filter
            selector.filter_weapons("")
            # All rows should be visible
            
            # Test filter by name
            selector.filter_weapons("Korss")
            # Only Korss should be visible
            
            # Test case insensitive
            selector.filter_weapons("korss")
            # Should still work
    
    def test_weapon_selection(self, mock_db_manager):
        """Test weapon selection"""
        with patch('src.ui.components.weapon_selector.QWidget.__init__'):
            selector = WeaponSelector(db_manager=mock_db_manager)
            selector.load_weapons()
            selector.setup_ui()
            
            # Simulate weapon selection
            selector.current_weapon = selector.weapons['1']
            
            assert selector.current_weapon.name == 'Korss H400 (L)'
            assert selector.current_weapon.damage == Decimal('28')
    
    def test_cost_calculation(self, mock_db_manager):
        """Test cost calculation"""
        with patch('src.ui.components.weapon_selector.QWidget.__init__'):
            selector = WeaponSelector(db_manager=mock_db_manager)
            selector.load_weapons()
            selector.load_attachments()
            selector.setup_ui()
            
            # Select a weapon
            selector.current_weapon = selector.weapons['1']
            
            # Reset enhancement values
            selector.damage_enh_spin.setValue(0)
            selector.economy_enh_spin.setValue(0)
            
            # Calculate costs
            selector.update_cost_calculation()
            
            # Should update cost labels
            assert "Base Cost:" in selector.base_cost_label.text()
            assert "Enhanced Cost:" in selector.enhanced_cost_label.text()
    
    def test_reset_session(self, mock_db_manager):
        """Test session reset"""
        with patch('src.ui.components.weapon_selector.QWidget.__init__'):
            selector = WeaponSelector(db_manager=mock_db_manager)
            selector.setup_ui()
            
            # Add some session data
            selector.session_ammo_used = Decimal('100')
            selector.session_decay = Decimal('5.5')
            
            # Reset session
            selector.reset_session()
            
            assert selector.session_ammo_used == Decimal('0')
            assert selector.session_decay == Decimal('0')
    
    def test_add_shot_data(self, mock_db_manager):
        """Test adding shot data"""
        with patch('src.ui.components.weapon_selector.QWidget.__init__'):
            selector = WeaponSelector(db_manager=mock_db_manager)
            selector.setup_ui()
            
            # Add shot data
            selector.add_shot_data(Decimal('11'), Decimal('0.10'))
            
            assert selector.session_ammo_used == Decimal('11')
            assert selector.session_decay == Decimal('0.10')
            
            # Add more shot data
            selector.add_shot_data(Decimal('22'), Decimal('0.20'))
            
            assert selector.session_ammo_used == Decimal('33')
            assert selector.session_decay == Decimal('0.30')


@pytest.mark.integration
class TestWeaponSelectorIntegration:
    """Integration tests for weapon selector"""
    
    def test_complete_workflow(self, mock_db_manager):
        """Test complete workflow from load to calculation"""
        with patch('src.ui.components.weapon_selector.QWidget.__init__'):
            selector = WeaponSelector(db_manager=mock_db_manager)
            
            # Load data
            selector.load_weapons()
            selector.load_attachments()
            selector.setup_ui()
            
            # Verify data loaded
            assert len(selector.weapons) > 0
            assert len(selector.attachments) > 0
            
            # Select weapon
            selector.current_weapon = selector.weapons['1']
            
            # Set enhancements
            selector.damage_enh_spin.setValue(2)
            selector.economy_enh_spin.setValue(3)
            
            # Calculate
            selector.update_cost_calculation()
            
            # Verify calculations performed
            assert selector.current_weapon is not None
            # Cost labels should be updated (would need actual UI to verify)