"""
Weapon selector for damage calculation and cost tracking
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal


class WeaponSelector:
    """Weapon selection and ammunition tracking"""
    
    def __init__(self, parent, db_manager, callback):
        self.parent = parent
        self.db = db_manager
        self.callback = callback
        self.current_weapon = None
        self.session_ammo_used = Decimal('0')
        self.session_decay = Decimal('0')
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup weapon selector UI"""
        # Main frame
        self.frame = ttk.LabelFrame(self.parent, text="Weapon Selection", relief='ridge')
        
        # Weapon search
        search_frame = ttk.Frame(self.frame)
        search_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(search_frame, text="Weapon:").pack(side='left', padx=(0, 5))
        
        self.weapon_var = tk.StringVar()
        self.weapon_combo = ttk.Combobox(search_frame, textvariable=self.weapon_var, width=25)
        self.weapon_combo.pack(side='left', padx=5)
        self.weapon_combo.bind('<<ComboboxSelected>>', self.on_weapon_selected)
        
        ttk.Button(search_frame, text="Load", command=self.load_selected_weapon).pack(side='left', padx=5)
        
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
        
        # Session tracking
        self.session_frame = ttk.Frame(self.frame)
        self.session_frame.pack(fill='x', padx=5, pady=5)
        
        self.ammo_label = ttk.Label(self.session_frame, text="Ammo Used: 0.00")
        self.ammo_label.pack(anchor='w')
        
        self.decay_label = ttk.Label(self.session_frame, text="Weapon Decay: 0.00 PED")
        self.decay_label.pack(anchor='w')
        
        self.cost_label = ttk.Label(self.session_frame, text="Total Cost: 0.00 PED", 
                                font=('Arial', 10, 'bold'))
        self.cost_label.pack(anchor='w', pady=(5, 0))
        
        # Populate with some popular weapons
        self.populate_weapons()
        
    def populate_weapons(self):
        """Populate weapon combo with database weapons"""
        weapon_list = []
        
        # Get some popular/common weapons
        for weapon_id, info in list(self.db.weapons.items())[:50]:  # First 50 for performance
            weapon_list.append(f"{weapon_id} ({info.get('type', 'Unknown')})")
        
        self.weapon_combo['values'] = sorted(weapon_list)
        
        # Set some defaults
        if "Pulsar" in weapon_list:
            self.weapon_combo.set("Pulsar (Pistol)")
        elif weapon_list:
            self.weapon_combo.set(weapon_list[0])
    
    def on_weapon_selected(self, event):
        """Handle weapon selection"""
        selection = self.weapon_var.get()
        if not selection:
            return
            
        # Extract weapon ID from display string
        weapon_id = selection.split(' (')[0] if ' (' in selection else selection
        
        # Find weapon in database
        for db_id, info in self.db.weapons.items():
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
            'decay': str(self.current_weapon.get('decay', '0')),
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
        self.weapon_cost_label = ttk.Label(ammo_frame, text="Weapon: Not Selected")
        self.weapon_cost_label.pack(side='left', padx=(20, 0))
        
        # Instructions
        info_frame = ttk.Frame(self.frame)
        info_frame.pack(fill='x', padx=5, pady=10)
        
        info_text = """Instructions:
1. Select your weapon from the dropdown
2. Load weapon to see stats
3. Ammo usage is tracked per shot
4. Weapon decay is calculated automatically
5. Ammo cost can be adjusted here"""
        
        ttk.Label(info_frame, text=info_text, wraplength=300, justify='left').pack()
    
    def load_markup_config(self):
        """Load markup configuration"""
        # This would load from a config file in real version
        try:
            import json
            if Path("weapon_markups.json").exists():
                with open("weapon_markups.json", 'r') as f:
                    self.markup_values.update(json.load(f))
        except Exception:
            pass  # Use defaults
    
    def set_ammo_cost(self):
        """Set ammo cost"""
        try:
            cost = Decimal(self.ammo_cost_var.get())
            if cost > 0:
                self.markup_values['ammo'] = cost
                self.save_markup_config()
        except Exception:
            pass
    
    def save_markup_config(self):
        """Save markup configuration"""
        try:
            import json
            with open("weapon_markups.json", 'w') as f:
                # Convert Decimal to float for JSON
                serializable = {k: float(v) if isinstance(v, Decimal) else v 
                              for k, v in self.markup_values.items()}
                json.dump(serializable, f, indent=2)
        except Exception:
            pass
    
    def update_weapon_cost_display(self, weapon_info: Dict[str, Any]):
        """Update weapon cost display"""
        if not weapon_info:
            self.weapon_cost_label.config(text="Weapon: Not Selected")
            return
            
        ammo_per_shot = weapon_info.get('ammo', 1)
        decay_per_shot = weapon_info.get('decay', 0)
        ammo_cost = self.markup_values.get('ammo', Decimal('0.01'))
        
        total_cost_per_shot = (ammo_per_shot * ammo_cost) + Decimal(str(decay_per_shot))
        
        self.weapon_cost_label.config(
            text=f"Weapon: {total_cost_per_shot:.4f} PED/shot"
        )
    
    def get_ammo_cost(self) -> Decimal:
        """Get current ammo cost"""
        return self.markup_values.get('ammo', Decimal('0.01'))


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
    selector.frame.pack(padx=10, pady=10)
    
    root.mainloop()