"""
Weapon selector for damage calculation and cost tracking - Enhanced with loadout system
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from pathlib import Path
import json


class WeaponSelector:
    """Weapon selection and ammunition tracking"""

    def __init__(self, parent, db_manager, callback):
        self.parent = parent
        self.db = db_manager
        self.callback = callback
        self.current_weapon = None
        self.session_ammo_used = Decimal('0')
        self.session_decay = Decimal('0')
        self.weapons = {}  # Will be set from outside
        self.attachments = {}
        self.sights_and_scopes = {}
        self.frame = None  # Will be created when parent is set

        # Load attachment data
        self._load_attachment_data()

        # Only setup UI if parent is provided
        if self.parent:
            self.setup_ui()
    def _load_attachment_data(self):
        """Load attachments and scopes data from JSON files"""
        try:
            # Load attachments (amplifiers)
            with open('attachments.json', 'r', encoding='utf-8') as f:
                attachments_data = json.load(f)
                self.attachments = attachments_data.get('data', {})
        except FileNotFoundError:
            print("attachments.json not found")
            self.attachments = {}
        except Exception as e:
            print(f"Error loading attachments.json: {e}")
            self.attachments = {}
            
        try:
            # Load sights and scopes
            with open('sights_and_scopes.json', 'r', encoding='utf-8') as f:
                scopes_data = json.load(f)
                self.sights_and_scopes = scopes_data.get('data', {})
        except FileNotFoundError:
            print("sights_and_scopes.json not found")
            self.sights_and_scopes = {}
        except Exception as e:
            print(f"Error loading sights_and_scopes.json: {e}")
            self.sights_and_scopes = {}

    def _on_search_change(self, *args):
        """Handle search input change"""
        search_term = self.search_var.get().lower()
        
        if not search_term:
            # Show all weapons if search is empty
            self.populate_weapons()
            return
            
        # Filter weapons based on search term
        weapons_source = self.weapons or self.db.weapons
        filtered_weapons = []
        
        for weapon_id, info in weapons_source.items():
            weapon_type = info.get('type', 'Unknown')
            weapon_display = f"{weapon_id} ({weapon_type})"
            
            if (search_term in weapon_id.lower() or 
                search_term in weapon_type.lower()):
                filtered_weapons.append(weapon_display)
        
        # Update dropdown with filtered results
        if hasattr(self, 'weapon_combo'):
            self.weapon_combo['values'] = sorted(filtered_weapons)
        
            # Clear selection if current selection doesn't match filter
            current = self.weapon_var.get()
            if current and current not in filtered_weapons:
                self.weapon_var.set('')
                if filtered_weapons:
                    self.weapon_combo.set(filtered_weapons[0])

    def _on_weapon_selected(self, event):
        """Handle weapon selection"""
        selection = self.weapon_var.get()
        if not selection:
            return

        # Extract weapon ID from display string
        weapon_id = selection.split(' (')[0] if ' (' in selection else selection

        # Find weapon in database
        for db_id, info in (self.weapons or self.db.weapons).items():
            if db_id == weapon_id:
                self.current_weapon = info
                self.current_weapon['id'] = db_id
                self._update_weapon_display()

                # Notify callback
                if self.callback:
                    self.callback('weapon_selected', self.current_weapon)
                break
        
        # Recalculate cost after weapon selection
        if hasattr(self, '_calculate_cost'):
            self._calculate_cost()

    def _on_loadout_change(self, *args):
        """Handle any loadout configuration change"""
        self._calculate_cost()

    def _calculate_cost(self):
        """Calculate total cost per shot based on LootNanny formula"""
        try:
            # Get current selections
            weapon_name = self.weapon_var.get()
            amp_name = self.amp_var.get()
            scope_name = self.scope_var.get()
            sight_name = self.sight_var.get()
            damage_enh = self.damage_enh_var.get()
            economy_enh = self.economy_enh_var.get()
            
            # Get base weapon data
            weapons_source = self.weapons or self.db.weapons
            weapon = None
            for weapon_id, info in weapons_source.items():
                if weapon_id == weapon_name or f"{weapon_id} ({info.get('type', 'Unknown')})" == weapon_name:
                    weapon = info
                    break
            
            if not weapon:
                self._update_cost_display(0, 0, 0)
                return
            
            # Base weapon cost with enhancer modifiers
            base_ammo = weapon.get('ammo', 0)
            base_decay = Decimal(str(weapon.get('decay', 0)))
            
            # Apply enhancer multipliers (LootNanny formula)
            ammo = base_ammo * (1 + (0.1 * damage_enh)) * (1 - (0.01 * economy_enh))
            decay = base_decay * Decimal(1 + (0.1 * damage_enh)) * Decimal(1 - (0.01 * economy_enh))
            
            # Add amplifier cost
            if amp_name and amp_name in self.attachments:
                amp = self.attachments[amp_name]
                ammo += amp.get('ammo', 0)
                decay += Decimal(str(amp.get('decay', 0)))
            
            # Add scope cost
            if scope_name and scope_name in self.sights_and_scopes:
                scope = self.sights_and_scopes[scope_name]
                ammo += scope.get('ammo', 0)
                decay += Decimal(str(scope.get('decay', 0)))
            
            # Add sight cost
            if sight_name and sight_name in self.sights_and_scopes:
                sight = self.sights_and_scopes[sight_name]
                ammo += sight.get('ammo', 0)
                decay += Decimal(str(sight.get('decay', 0)))
            
            # Final cost per shot (LootNanny formula: ammo/10000 + decay)
            cost_per_shot = (ammo / 10000) + decay
            
            self._update_cost_display(ammo, decay, cost_per_shot)
            
        except Exception as e:
            print(f"Error calculating cost: {e}")
            self._update_cost_display(0, 0, 0)

    def _update_cost_display(self, ammo, decay, cost_per_shot):
        """Update the cost display labels"""
        if hasattr(self, 'ammo_label'):
            self.ammo_label.config(text=f"Ammo Burn: {ammo}")
        if hasattr(self, 'decay_label'):
            self.decay_label.config(text=f"Weapon Decay: {decay:.6f} PED")
        if hasattr(self, 'cost_label'):
            self.cost_label.config(text=f"Cost per Shot: {cost_per_shot:.6f} PED")

    def setup_ui(self):
        """Setup weapon selector UI"""
        if not self.parent:
            raise ValueError("Parent must be set before setting up UI")
        
        # Main frame
        self.frame = ttk.LabelFrame(self.parent, text="Weapon Selection", relief='ridge')

        # Weapon search
        search_frame = ttk.Frame(self.frame)
        search_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(search_frame, text="Search:").pack(side='left', padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_change)
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side='left', padx=5)

        ttk.Label(search_frame, text="Weapon:").pack(side='left', padx=(10, 5))

        self.weapon_var = tk.StringVar()
        self.weapon_combo = ttk.Combobox(search_frame, textvariable=self.weapon_var, width=25)
        self.weapon_combo.pack(side='left', padx=5)
        self.weapon_combo.bind('<<ComboboxSelected>>', self._on_weapon_selected)

        ttk.Button(search_frame, text="Load", command=self.load_selected_weapon).pack(side='left', padx=5)
        
        # Loadout configuration frame
        loadout_frame = ttk.LabelFrame(self.frame, text="Loadout Configuration")
        loadout_frame.pack(fill='x', padx=5, pady=5)
        
        # First row: Amplifier
        amp_row = ttk.Frame(loadout_frame)
        amp_row.pack(fill='x', padx=5, pady=2)
        ttk.Label(amp_row, text="Amplifier:").pack(side='left', padx=(0, 5))
        self.amp_var = tk.StringVar()
        self.amp_combo = ttk.Combobox(amp_row, textvariable=self.amp_var, width=25)
        self.amp_combo.pack(side='left', padx=5)
        self.amp_combo.bind('<<ComboboxSelected>>', self._on_loadout_change)
        
        # Second row: Scope
        scope_row = ttk.Frame(loadout_frame)
        scope_row.pack(fill='x', padx=5, pady=2)
        ttk.Label(scope_row, text="Scope:").pack(side='left', padx=(0, 5))
        self.scope_var = tk.StringVar()
        self.scope_combo = ttk.Combobox(scope_row, textvariable=self.scope_var, width=25)
        self.scope_combo.pack(side='left', padx=5)
        self.scope_combo.bind('<<ComboboxSelected>>', self._on_loadout_change)
        
        # Third row: Sight
        sight_row = ttk.Frame(loadout_frame)
        sight_row.pack(fill='x', padx=5, pady=2)
        ttk.Label(sight_row, text="Sight:").pack(side='left', padx=(0, 5))
        self.sight_var = tk.StringVar()
        self.sight_combo = ttk.Combobox(sight_row, textvariable=self.sight_var, width=25)
        self.sight_combo.pack(side='left', padx=5)
        self.sight_combo.bind('<<ComboboxSelected>>', self._on_loadout_change)
        
        # Fourth row: Enhancers
        enhancer_row = ttk.Frame(loadout_frame)
        enhancer_row.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(enhancer_row, text="Damage Enh:").pack(side='left', padx=(0, 5))
        self.damage_enh_var = tk.IntVar(value=0)
        damage_spin = ttk.Spinbox(enhancer_row, from_=0, to=10, textvariable=self.damage_enh_var, width=8)
        damage_spin.pack(side='left', padx=5)
        damage_spin.bind('<<SpinboxChanged>>', self._on_loadout_change)
        
        ttk.Label(enhancer_row, text="Economy Enh:").pack(side='left', padx=(10, 5))
        self.economy_enh_var = tk.IntVar(value=0)
        economy_spin = ttk.Spinbox(enhancer_row, from_=0, to=10, textvariable=self.economy_enh_var, width=8)
        economy_spin.pack(side='left', padx=5)
        economy_spin.bind('<<SpinboxChanged>>', self._on_loadout_change)
        
        # Populate attachment dropdowns
        self._populate_attachments()
    
    def _populate_attachments(self):
        """Populate attachment and scope dropdowns with data"""
        # Populate amplifier dropdown
        if self.attachments:
            amp_list = list(self.attachments.keys())
            self.amp_combo['values'] = sorted(amp_list)
            if amp_list:
                self.amp_combo.set(amp_list[0])
        
        # Populate scope dropdown (filter only scopes)
        if self.sights_and_scopes:
            scope_list = [name for name, info in self.sights_and_scopes.items() 
                        if info.get('type') == 'Scope']
            self.scope_combo['values'] = sorted(scope_list)
            if scope_list:
                self.scope_combo.set(scope_list[0])
        
        # Populate sight dropdown (filter only sights)
        sight_list = [name for name, info in self.sights_and_scopes.items() 
                     if info.get('type') == 'Sight']
        self.sight_combo['values'] = sorted(sight_list)
        if sight_list:
            self.sight_combo.set(sight_list[0])

        # Weapon stats display
        self.stats_frame = ttk.Frame(self.frame)
        self.stats_frame.pack(fill='x', padx=5, pady=5)

        # Create stat labels
        self.stat_labels = {}
        stats = ['ammo', 'decay', 'dps', 'eco', 'type']
        for stat in stats:
            stat_frame = ttk.Frame(self.stats_frame)
            stat_frame.pack(fill='x', pady=2)

            ttk.Label(stat_frame, text=f"{stat.title()}:", width=10).pack(side='left')
            value_label = ttk.Label(stat_frame, text="--", width=15)
            value_label.pack(side='left')

            self.stat_labels[stat] = value_label

        # Cost calculation display
        cost_frame = ttk.LabelFrame(self.frame, text="Cost Calculation")
        cost_frame.pack(fill='x', padx=5, pady=5)
        
        self.ammo_label = ttk.Label(cost_frame, text="Ammo Burn: --", font=('Arial', 10, 'bold'))
        self.ammo_label.pack(anchor='w', padx=5, pady=2)
        
        self.decay_label = ttk.Label(cost_frame, text="Weapon Decay: -- PED", font=('Arial', 10, 'bold'))
        self.decay_label.pack(anchor='w', padx=5, pady=2)
        
        self.cost_label = ttk.Label(cost_frame, text="Cost per Shot: -- PED", font=('Arial', 11, 'bold'))
        self.cost_label.pack(anchor='w', padx=5, pady=2)
        
        # Session tracking (original functionality)
        self.session_frame = ttk.Frame(self.frame)
        self.session_frame.pack(fill='x', padx=5, pady=5)

        self.session_ammo_label = ttk.Label(self.session_frame, text="Session Ammo Used: 0.00")
        self.session_ammo_label.pack(anchor='w')

        self.session_decay_label = ttk.Label(self.session_frame, text="Session Weapon Decay: 0.00 PED")
        self.session_decay_label.pack(anchor='w')

        self.session_cost_label = ttk.Label(self.session_frame, text="Session Total Cost: 0.00 PED",
                                      font=('Arial', 10, 'bold'))
        self.session_cost_label.pack(anchor='w', pady=(5, 0))

        # Populate with some popular weapons if available
        if self.weapons:
            self.populate_weapons()
        else:
            # Add placeholder weapons
            placeholder_weapons = ["Pulsar (Pistol)", "Korss H400 (Carbine)", "Karma Killer (L)"]
            self.weapon_combo['values'] = placeholder_weapons
            if placeholder_weapons:
                self.weapon_combo.set(placeholder_weapons[0])

    def populate_weapons(self):
        """Populate weapon combo with database weapons"""
        weapon_list = []

        # Use self.weapons if set, otherwise use db
        weapons_source = self.weapons or self.db.weapons

        # Include all weapons, but implement search functionality
        for weapon_id, info in weapons_source.items():
            weapon_type = info.get('type', 'Unknown')
            weapon_list.append(f"{weapon_id} ({weapon_type})")

        # Sort and populate dropdown
        sorted_weapons = sorted(weapon_list)
        self.weapon_combo['values'] = sorted_weapons

        # Find first weapon starting with 'F' as default
        for weapon in sorted_weapons:
            if weapon.startswith('F'):
                self.weapon_combo.set(weapon)
                break
        else:
            # Fallback to first pistol
            for weapon in sorted_weapons:
                if 'Pistol' in weapon and 'Pulsar' in weapon:
                    self.weapon_combo.set(weapon)
                    break
            else:
                if sorted_weapons:
                    self.weapon_combo.set(sorted_weapons[0])
        
        # Trigger cost calculation for default selection
        if hasattr(self, '_calculate_cost') and self.parent:
            self.parent.after(100, self._calculate_cost)
            
        # Trigger attachment population 
        if hasattr(self, '_populate_attachments'):
            self.parent.after(50, self._populate_attachments)

    def on_search_change(self, *args):
        """Handle search input change"""
        search_term = self.search_var.get().lower()
        
        if not search_term:
            # Show all weapons if search is empty
            self.populate_weapons()
            return
            
        # Filter weapons based on search term
        weapons_source = self.weapons or self.db.weapons
        filtered_weapons = []
        
        for weapon_id, info in weapons_source.items():
            weapon_type = info.get('type', 'Unknown')
            weapon_display = f"{weapon_id} ({weapon_type})"
            
            if (search_term in weapon_id.lower() or 
                search_term in weapon_type.lower()):
                filtered_weapons.append(weapon_display)
        
        # Update dropdown with filtered results
        self.weapon_combo['values'] = sorted(filtered_weapons)
        
        # Clear selection if current selection doesn't match filter
        current = self.weapon_var.get()
        if current and current not in filtered_weapons:
            self.weapon_var.set('')
            if filtered_weapons:
                self.weapon_combo.set(filtered_weapons[0])

    def on_weapon_selected(self, event):
        """Handle weapon selection"""
        selection = self.weapon_var.get()
        if not selection:
            return

        # Extract weapon ID from display string
        weapon_id = selection.split(' (')[0] if ' (' in selection else selection

        # Find weapon in database
        for db_id, info in (self.weapons or self.db.weapons).items():
            if db_id == weapon_id:
                self.current_weapon = info
                self.current_weapon['id'] = db_id
                self.update_weapon_display()

                # Notify callback
                if self.callback:
                    self.callback('weapon_selected', self.current_weapon)
                break

    def update_weapon_display(self):
        """Update weapon stats display"""
        if not self.current_weapon:
            for label in self.stat_labels.values():
                label.config(text="--")
            return

        # Update stat labels
        stats = {
            'ammo': str(self.current_weapon.get('ammo', 0)),
            'decay': str(self.current_weapon.get('decay', 0)),
            'dps': str(self.current_weapon.get('dps', '--')),
            'eco': str(self.current_weapon.get('eco', '--')),
            'type': self.current_weapon.get('type', 'Unknown')
        }

        for stat, value in stats.items():
            if stat in self.stat_labels:
                self.stat_labels[stat].config(text=value)

    def load_selected_weapon(self):
        """Load the selected weapon"""
        selection = self.weapon_var.get()
        if selection:
            self.on_weapon_selected(None)

    def add_combat_event(self, damage: float, critical: bool = False):
        """Track ammo usage from combat"""
        if not self.current_weapon:
            return

        ammo_per_shot = self.current_weapon.get('ammo', 1)
        if ammo_per_shot > 0:
            self.session_ammo_used += Decimal(str(ammo_per_shot))

        # Update display
        self.ammo_label.config(text=f"Ammo Used: {self.session_ammo_used}")

        # Notify callback
        if self.callback:
            self.callback('ammo_used', ammo_per_shot)

    def get_current_weapon(self) -> Optional[Dict[str, Any]]:
        """Get currently selected weapon"""
        return self.current_weapon

    def get_session_costs(self) -> Tuple[Decimal, Decimal]:
        """Get total ammo and decay costs for session"""
        return self.session_ammo_used, self.session_decay

    def reset_session(self):
        """Reset session tracking"""
        self.session_ammo_used = Decimal('0')
        self.session_decay = Decimal('0')

        # Update display
        self.ammo_label.config(text="Ammo Used: 0.00")
        self.decay_label.config(text="Weapon Decay: 0.00 PED")
        self.cost_label.config(text="Total Cost: 0.00 PED")


class WeaponConfig:
    """Weapon configuration and markup management"""

    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db = db_manager
        self.markup_values = {
            'ammo': Decimal('0.01'),  # Default 0.01 PED per ammo
            'Custom Values': {}
        }

        self.setup_ui()
        self.load_markup_config()
    
    def pack(self, **kwargs):
        """Pack the frame - compatibility method"""
        if hasattr(self, 'frame'):
            self.frame.pack(**kwargs)
    
    def load_markup_config(self):
        """Load markup configuration - no-op for WeaponConfig"""
        # WeaponConfig doesn't have the same UI structure as WeaponSelector
        # This method exists for compatibility but doesn't load markup config
        pass

    def setup_ui(self):
        """Setup weapon configuration UI"""
        # Markup config frame
        self.frame = ttk.LabelFrame(self.parent, text="Cost Configuration", relief='ridge')

        # Ammo cost
        ammo_frame = ttk.Frame(self.frame)
        ammo_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(ammo_frame, text="Ammo Cost (PED):").pack(side='left')
        self.ammo_cost_var = tk.StringVar(value="0.01")
        ammo_entry = ttk.Entry(ammo_frame, textvariable=self.ammo_cost_var, width=10)
        ammo_entry.pack(side='left', padx=5)

        ttk.Button(ammo_frame, text="Set", command=self.set_ammo_cost).pack(side='left')

        # Current weapon cost display
        cost_frame = ttk.Frame(self.frame)
        cost_frame.pack(fill='x', padx=5, pady=5)

        self.ammo_label = ttk.Label(cost_frame, text="Ammo Burn: 0.00")
        self.ammo_label.pack(side='left', padx=10)

        self.decay_label = ttk.Label(cost_frame, text="Weapon Decay: 0.00 PED")
        self.decay_label.pack(side='left', padx=10)

        self.cost_label = ttk.Label(cost_frame, text="Total Cost: 0.00 PED")
        self.cost_label.pack(side='left', padx=10)

        # Weapon search
        search_frame = ttk.Frame(self.frame)
        search_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(search_frame, text="Search Weapons:").pack(side='left')
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side='left', padx=5)

        ttk.Button(search_frame, text="Search", command=self.search_weapons).pack(side='left')

        # Weapon list
        list_frame = ttk.Frame(self.frame)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.weapon_combo = ttk.Combobox(list_frame, state='readonly')
        self.weapon_combo.pack(fill='x', pady=2)
        self.weapon_var = tk.StringVar()
        self.weapon_combo.config(textvariable=self.weapon_var)

        # Bind events
        self.search_var.trace('w', self._on_search_change)
        self.weapon_combo.bind('<<ComboboxSelected>>', self._on_weapon_selected)

        self.frame.pack(**kwargs)
            
    def _on_loadout_change(self, *args):
        """Handle any loadout configuration change - no-op for WeaponConfig"""
        # WeaponConfig doesn't have the same UI structure as WeaponSelector
        # This method exists for compatibility but doesn't do calculations
        pass
    
    def _calculate_cost(self):
        """Calculate total cost per shot based on LootNanny formula - no-op for WeaponConfig"""
        # WeaponConfig doesn't have the same UI structure as WeaponSelector
        # This method exists for compatibility but doesn't do calculations
        pass
    
    def _update_cost_display(self, ammo, decay, cost_per_shot):
        """Update the cost display labels - no-op for WeaponConfig"""
        # WeaponConfig doesn't have the same UI structure as WeaponSelector
        # This method exists for compatibility but doesn't update displays
        pass
    
    def set_ammo_cost(self):
        """Set ammo cost from entry field - no-op for WeaponConfig"""
        # WeaponConfig doesn't have the same UI structure as WeaponSelector
        # This method exists for compatibility but doesn't set ammo cost
        pass
    
    def search_weapons(self):
        """Search weapons - no-op for WeaponConfig"""
        # WeaponConfig doesn't have the same UI structure as WeaponSelector
        # This method exists for compatibility but doesn't search weapons
        pass
    
    def populate_weapons(self):
        """Populate weapons list - no-op for WeaponConfig"""
        # WeaponConfig doesn't have the same UI structure as WeaponSelector
        # This method exists for compatibility but doesn't populate weapons
        pass
    
    def _on_search_change(self, *args):
        """Handle search input change"""
        search_term = self.search_var.get().lower()
        
        if not search_term:
            # Show all weapons if search is empty
            self.populate_weapons()
            return
            
        # Filter weapons based on search term
        weapons_source = self.weapons or self.db.weapons
        filtered_weapons = []
        
        for weapon_id, info in weapons_source.items():
            weapon_type = info.get('type', 'Unknown')
            weapon_display = f"{weapon_id} ({weapon_type})"
            
            if (search_term in weapon_id.lower() or 
                search_term in weapon_type.lower()):
                filtered_weapons.append(weapon_display)
        
        # Update dropdown with filtered results
        self.weapon_combo['values'] = sorted(filtered_weapons)
        
        # Clear selection if current selection doesn't match filter
        current = self.weapon_var.get()
        if current and current not in filtered_weapons:
            self.weapon_var.set('')
            if filtered_weapons:
                self.weapon_combo.set(filtered_weapons[0])

    def _on_weapon_selected(self, event):
        """Handle weapon selection"""
        selection = self.weapon_var.get()
        if not selection:
            return

        # Extract weapon ID from display string
        weapon_id = selection.split(' (')[0] if ' (' in selection else selection

        # Find weapon in database
        for db_id, info in (self.weapons or self.db.weapons).items():
            if db_id == weapon_id:
                self.current_weapon = info
                self.current_weapon['id'] = db_id
                self._update_weapon_display()

                # Notify callback
                if self.callback:
                    self.callback('weapon_selected', self.current_weapon)
                break
        
        # Recalculate cost after weapon selection
        self._calculate_cost()


if __name__ == "__main__":
    # Test weapon selector
    root = tk.Tk()
    root.title("Weapon Selector Test")

    # Mock DB
    class MockDB:
        weapons = {
            "Pulsar (L)": {"ammo": 20, "decay": "0.084", "type": "Pistol"},
            "Korss H400 (L)": {"ammo": 28, "decay": "0.104", "type": "Carbine"},
        }

    def test_callback(event_type, data):
        print(f"Callback: {event_type} - {data}")

    selector = WeaponSelector(root, MockDB(), test_callback)
    selector.weapons = MockDB().weapons  # Set weapons for testing
    selector.populate_weapons()
    if selector.frame:
        selector.frame.pack(padx=10, pady=10)

    root.mainloop()