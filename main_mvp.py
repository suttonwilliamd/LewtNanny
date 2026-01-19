"""
Updated MVP with weapon selection and proper parsing
"""

import sys
import json
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal

# Import real chat reader and overlay
try:
    from src.services.chat_reader_real import ChatLogReader, ChatEvent, CombatEvent, LootEvent, SkillEvent, GlobalEvent
    from overlay import SessionOverlay
    from weapon_selector import WeaponSelector, WeaponConfig
    REAL_PARSING_AVAILABLE = True
except ImportError:
    print("Warning: Real components not available, using fallback")
    ChatLogReader = None
    ChatEvent = None
    SessionOverlay = None
    WeaponSelector = None
    WeaponConfig = None
    REAL_PARSING_AVAILABLE = False

# Basic in-memory database for MVP
class SimpleDB:
    def __init__(self):
        self.sessions = {}
        self.events = []
        self.weapons = {}
        self.blueprints = {}
        
    async def initialize(self):
        """Load data from JSON files"""
        # Load weapons
        weapons_path = Path("weapons.json")
        if weapons_path.exists():
            with open(weapons_path, 'r', encoding='utf-8') as f:
                weapons_data = json.load(f)
                for weapon_id, info in weapons_data.get('data', {}).items():
                    self.weapons[weapon_id] = info
        
        # Load crafting
        crafting_path = Path("crafting.json")
        if crafting_path.exists():
            with open(crafting_path, 'r', encoding='utf-8') as f:
                crafting_data = json.load(f)
                for blueprint_id, materials in crafting_data.get('data', {}).items():
                    self.blueprints[blueprint_id] = materials
    
    def search_weapons(self, query: str, limit: int = 10):
        """Search weapons by name"""
        results = []
        for weapon_id, info in self.weapons.items():
            if query.lower() in weapon_id.lower() or query.lower() in info.get('type', '').lower():
                results.append((weapon_id, info))
                if len(results) >= limit:
                    break
        return results
    
    def create_session(self, session_id: str, activity_type: str):
        """Create new session"""
        self.sessions[session_id] = {
            'id': session_id,
            'start_time': datetime.now(),
            'activity_type': activity_type,
            'events': []
        }
        
    def add_event(self, event_data: Dict[str, Any]):
        """Add event to current session"""
        session_id = event_data.get('session_id')
        if session_id and session_id in self.sessions:
            self.sessions[session_id]['events'].append(event_data)
        self.events.append(event_data)


class SimpleConfig:
    def __init__(self):
        self.data = {
            'chat_monitoring': {
                'log_file_path': '',
                'monitoring_enabled': True
            }
        }
    
    def get(self, key: str, default=None):
        """Get config value"""
        keys = key.split('.')
        value = self.data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


# Simple main window using tkinter (built-in)
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, scrolledtext
    
    class SimpleMainWindow:
        def __init__(self, db, config):
            self.db = db
            self.config = config
            self.current_session = None
            self.chat_reader = None
            self.overlay = None
            self.weapon_selector = None
            self.weapon_config = None
            
            # Create main window
            self.root = tk.Tk()
            self.root.title("LewtNanny - Entropia Universe Loot Tracker")
            self.root.geometry("1200x800")
            
            self.setup_ui()
            
            # Apply theme
            self.apply_theme("dark")
            
            # Initialize overlay if available
            if SessionOverlay and REAL_PARSING_AVAILABLE:
                self.overlay = SessionOverlay(db, config)
            if WeaponSelector and REAL_PARSING_AVAILABLE:
                self.weapon_selector = WeaponSelector(self.root, db, self.weapon_callback)
            if WeaponConfig and REAL_PARSING_AVAILABLE:
                self.weapon_config = WeaponConfig(self.root, db)
            
        def setup_ui(self):
            """Setup the UI"""
            # Main container
            main_frame = ttk.Frame(self.root)
            main_frame.pack(fill='both', expand=True, padx=5, pady=5)
            
            # Status bar
            status_frame = ttk.Frame(main_frame)
            status_frame.pack(fill='x', pady=(0, 5))
            
            self.session_label = ttk.Label(status_frame, text="No active session")
            self.session_label.pack(side='left', padx=(0, 10))
            
            self.start_btn = ttk.Button(status_frame, text="Start Session", command=self.start_session)
            self.start_btn.pack(side='left', padx=(0, 10))
            
            ttk.Label(status_frame, text="Activity:").pack(side='left', padx=(0, 5))
            self.activity_var = tk.StringVar(value="hunting")
            self.activity_combo = ttk.Combobox(status_frame, textvariable=self.activity_var, 
                                          values=["hunting", "crafting", "mining"], state="readonly")
            self.activity_combo.pack(side='left')
            
            # Overlay button
            if SessionOverlay and REAL_PARSING_AVAILABLE:
                self.overlay_btn = ttk.Button(status_frame, text="Show Overlay", command=self.toggle_overlay)
                self.overlay_btn.pack(side='right', padx=(10, 0))
            
            # Notebook for tabs
            self.notebook = ttk.Notebook(main_frame)
            self.notebook.pack(fill='both', expand=True)
            
            # Create tabs
            self.create_loot_tab()
            self.create_analysis_tab()
            self.create_weapon_tab()
            self.create_config_tab()
            
        def create_loot_tab(self):
            """Create loot tracking tab"""
            loot_frame = ttk.Frame(self.notebook)
            self.notebook.add(loot_frame, text="Loot")
            
            # Splitter using paned window
            paned = ttk.PanedWindow(loot_frame, orient='horizontal')
            paned.pack(fill='both', expand=True)
            
            # Loot feed
            loot_frame_inner = ttk.LabelFrame(paned, text="Recent Events")
            
            self.loot_text = scrolledtext.ScrolledText(loot_frame_inner, height=20, width=50)
            self.loot_text.pack(fill='both', expand=True, padx=5, pady=5)
            
            paned.add(loot_frame_inner, weight=2)
            
            # Stats
            stats_frame = ttk.LabelFrame(paned, text="Session Stats")
            
            self.cost_label = ttk.Label(stats_frame, text="Cost: 0.00 PED")
            self.cost_label.pack(anchor='w', padx=5, pady=2)
            
            self.return_label = ttk.Label(stats_frame, text="Return: 0.00 PED")
            self.return_label.pack(anchor='w', padx=5, pady=2)
            
            self.profit_label = ttk.Label(stats_frame, text="Profit: 0.00 PED")
            self.profit_label.pack(anchor='w', padx=5, pady=2)
            
            self.events_label = ttk.Label(stats_frame, text="Events: 0")
            self.events_label.pack(anchor='w', padx=5, pady=2)
            
            paned.add(stats_frame, weight=1)
            
        def create_analysis_tab(self):
            """Create analysis tab"""
            analysis_frame = ttk.Frame(self.notebook)
            self.notebook.add(analysis_frame, text="Analysis")
            
            # Event history
            history_frame = ttk.LabelFrame(analysis_frame, text="Event History")
            history_frame.pack(fill='both', expand=True, padx=5, pady=5)
            
            # Treeview for events
            columns = ("Time", "Type", "Activity", "Details")
            self.event_tree = ttk.Treeview(history_frame, columns=columns, show='headings')
            
            for col in columns:
                self.event_tree.heading(col, text=col)
                self.event_tree.column(col, width=150)
            
            # Scrollbars
            vsb = ttk.Scrollbar(history_frame, orient="vertical", command=self.event_tree.yview)
            hsb = ttk.Scrollbar(history_frame, orient="horizontal", command=self.event_tree.xview)
            self.event_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            
            self.event_tree.pack(side='left', fill='both', expand=True)
            vsb.pack(side='right', fill='y')
            hsb.pack(side='bottom', fill='x')
            
        def create_weapon_tab(self):
            """Create weapon selection tab"""
            if not WeaponSelector:
                return
                
            weapon_frame = ttk.Frame(self.notebook)
            self.notebook.add(weapon_frame, text="Weapons")
            
            if self.weapon_selector:
                self.weapon_selector.frame.pack(fill='both', expand=True, padx=5, pady=5)
                # Populate weapons from database
                self.weapon_selector.weapons = self.db.weapons
                self.weapon_selector.populate_weapons()
            
            # Weapon config section
            if self.weapon_config:
                self.weapon_config.frame.pack(fill='x', padx=5, pady=5)
            
        def create_config_tab(self):
            """Create config tab"""
            config_frame = ttk.Frame(self.notebook)
            self.notebook.add(config_frame, text="Config")
            
            # Chat settings
            chat_frame = ttk.LabelFrame(config_frame, text="Chat Monitoring")
            chat_frame.pack(fill='x', padx=5, pady=5)
            
            # Show default path
            default_log_path = os.path.join(os.path.expanduser("~"), "Documents", "Entropia Universe", "chat.log")
            ttk.Label(chat_frame, text="Default Log Location:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
            ttk.Label(chat_frame, text=default_log_path, wraplength=400).grid(row=0, column=1, padx=5, pady=5, sticky='w')
            
            # Override option
            ttk.Label(chat_frame, text="Override Log File:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
            self.log_file_var = tk.StringVar()
            self.log_file_entry = ttk.Entry(chat_frame, textvariable=self.log_file_var, width=50)
            self.log_file_entry.grid(row=1, column=1, padx=5, pady=5)
            
            ttk.Button(chat_frame, text="Browse...", command=self.browse_log_file).grid(row=1, column=2, padx=5, pady=5)
            
            self.monitoring_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(chat_frame, text="Enable monitoring", variable=self.monitoring_var).grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky='w')
            
            # Status
            status_frame = ttk.LabelFrame(config_frame, text="Status")
            status_frame.pack(fill='x', padx=5, pady=5)
            
            # Check if default log exists
            log_exists = os.path.exists(default_log_path)
            status_text = "Found" if log_exists else "Not Found"
            
            ttk.Label(status_frame, text=f"Default Chat Log: {status_text}").pack(anchor='w', padx=5, pady=2)
            
            # Data info
            data_frame = ttk.LabelFrame(config_frame, text="Database Status")
            data_frame.pack(fill='x', padx=5, pady=5)
            
            weapons_count = len(self.db.weapons)
            blueprints_count = len(self.db.blueprints)
            
            ttk.Label(data_frame, text=f"Weapons loaded: {weapons_count}").pack(anchor='w', padx=5, pady=2)
            ttk.Label(data_frame, text=f"Blueprints loaded: {blueprints_count}").pack(anchor='w', padx=5, pady=2)
            ttk.Label(data_frame, text=f"Chat Reader: {'Available' if ChatLogReader else 'Not Available'}").pack(anchor='w', padx=5, pady=2)
            ttk.Label(data_frame, text=f"Overlay: {'Available' if SessionOverlay else 'Not Available'}").pack(anchor='w', padx=5, pady=2)
            ttk.Label(data_frame, text=f"Weapon Selector: {'Available' if WeaponSelector else 'Not Available'}").pack(anchor='w', padx=5, pady=2)
            
        def apply_theme(self, theme_name: str):
            """Apply theme (simple color scheme for tkinter)"""
            themes = {
                'dark': {
                    'bg': '#2C3B49',
                    'fg': '#E0E1E3',
                    'select_bg': '#346792',
                    'button_bg': '#346792'
                },
                'light': {
                    'bg': '#FFFFFF',
                    'fg': '#19232D',
                    'select_bg': '#9FCBFF',
                    'button_bg': '#9FCBFF'
                }
            }
            
            theme = themes.get(theme_name, themes['dark'])
            
            # Apply basic theme (tkinter has limited theming)
            self.root.configure(bg=theme['bg'])
            
        def weapon_callback(self, event_type: str, data):
            """Handle weapon-related callbacks"""
            if event_type == 'weapon_selected':
                if self.overlay:
                    self.overlay.add_event({
                        'event_type': 'system',
                        'parsed_data': {'weapon_data': data},
                        'raw_message': f"Selected: {data.get('id', 'Unknown')}",
                        'session_id': self.current_session
                    })
                    
            elif event_type == 'ammo_used':
                if self.overlay:
                    self.overlay.add_event({
                        'event_type': 'cost',
                        'parsed_data': {'ammo_used': data},
                        'raw_message': f"Ammo used: {data}",
                        'session_id': self.current_session
                    })
            
        def add_event(self, event_type: str, details: str, color="white"):
            """Add event to display"""
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Add to loot feed with color
            self.loot_text.insert('end', f"[{timestamp}] {event_type}: {details}\n", color)
            self.loot_text.see('end')
            self.loot_text.tag_config(color, foreground=color)
            
            # Add to tree
            self.event_tree.insert('', 'end', values=(timestamp, event_type, self.activity_var.get(), details[:50]))
            
            # Update event count
            if self.current_session and self.current_session in self.db.sessions:
                event_count = len(self.db.sessions[self.current_session]['events'])
                self.events_label.config(text=f"Events: {event_count}")
                
        def handle_chat_event(self, event):
            """Handle real chat event from ChatLogReader"""
            if not event:
                return
                
            event_type = event.event_type.upper()
            details = event.raw_message
            
            # Choose color based on event type
            colors = {
                'COMBAT': '#7DB8F5',  # Blue
                'LOOT': '#5CAF50',     # Green
                'SKILL': '#FF9800',    # Orange
                'GLOBAL': '#F44336'     # Red
            }
            color = colors.get(event.event_type.upper(), 'white')
            
            # Add to display
            self.add_event(event_type, details, color)
            
            # Also add to database
            event_data = {
                'event_type': event.event_type,
                'activity_type': self.activity_var.get(),
                'raw_message': event.raw_message,
                'parsed_data': {
                    'timestamp': event.timestamp.isoformat(),
                    'event_data': event.__dict__ if hasattr(event, '__dict__') else {}
                },
                'session_id': self.current_session
            }
            self.db.add_event(event_data)
            
            # Update overlay if available
            if self.overlay:
                self.overlay.add_event(event_data)
            
            # Track ammo for weapon selector
            if self.weapon_selector and event_type == 'COMBAT':
                parsed_data = event_data.get('parsed_data', {}).get('event_data', {})
                if hasattr(parsed_data, 'damage'):
                    current_weapon = self.weapon_selector.get_current_weapon()
                    if current_weapon:
                        ammo_per_shot = current_weapon.get('ammo', 1)
                        self.weapon_selector.add_combat_event(float(parsed_data.damage), hasattr(parsed_data, 'critical'))
                        
            # Track loot
            if self.overlay and event_type == 'LOOT':
                parsed_data = event_data.get('parsed_data', {}).get('event_data', {})
                if hasattr(parsed_data, 'items'):
                    total_value = sum(float(item[2]) for item in parsed_data.items)
                    # Update loot value in overlay
                    
        def start_chat_monitoring(self):
            """Start real chat log monitoring"""
            if not ChatLogReader:
                print("Chat reader not available")
                return
                
            # Default Entropia Universe chat log location
            default_log_path = os.path.join(os.path.expanduser("~"), "Documents", "Entropia Universe", "chat.log")
            
            # Use configured path or default
            log_file = self.log_file_var.get() or default_log_path
            
            if self.chat_reader:
                self.chat_reader.stop_monitoring()
                
            try:
                self.chat_reader = ChatLogReader(log_file, self.handle_chat_event)
                if self.chat_reader.start_monitoring():
                    self.add_event("SYSTEM", f"Started monitoring: {log_file}", "#7DB8F5")
                else:
                    self.add_event("ERROR", f"Failed to start monitoring: {log_file}", "#F44336")
            except Exception as e:
                self.add_event("ERROR", f"Chat reader error: {e}", "#F44336")
                
        def toggle_overlay(self):
            """Toggle overlay window"""
            if not self.overlay:
                return
                
            # Always show overlay in separate thread to avoid blocking
            import threading
            def show_overlay():
                self.overlay.show()
            threading.Thread(target=show_overlay, daemon=True).start()
            self.overlay_btn.config(text="Overlay Running")
                
        def start_session(self):
            """Start tracking session"""
            if self.current_session:
                self.stop_session()
                return
                
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            activity = self.activity_var.get()
            
            self.db.create_session(session_id, activity)
            self.current_session = session_id
            
            self.start_btn.config(text="Stop Session")
            self.session_label.config(text=f"Active: {session_id[:8]}... - {activity}")
            
            # Start real chat monitoring
            self.start_chat_monitoring()
            
            # Start overlay session
            if self.overlay:
                self.overlay.start_session(session_id, activity)
                
            # Reset weapon selector session
            if self.weapon_selector:
                self.weapon_selector.reset_session()
                
        def stop_session(self):
            """Stop tracking session"""
            # Stop chat monitoring
            if self.chat_reader:
                self.chat_reader.stop_monitoring()
                self.chat_reader = None
                
            # Stop overlay session
            if self.overlay:
                self.overlay.stop_session()
                
            self.current_session = None
            self.start_btn.config(text="Start Session")
            self.session_label.config(text="No active session")
            
        def browse_log_file(self):
            """Browse for log file"""
            filename = filedialog.askopenfilename(
                title="Select Chat Log File",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if filename:
                self.log_file_var.set(filename)
                
        def run(self):
            """Start the GUI"""
            self.root.mainloop()

except ImportError:
    print("tkinter not available, using console mode")
    SimpleMainWindow = None


async def main():
    """Main function for MVP"""
    print("LewtNanny MVP - Initializing...")
    
    # Initialize database
    db = SimpleDB()
    await db.initialize()
    
    print(f"Loaded {len(db.weapons)} weapons and {len(db.blueprints)} blueprints")
    
    # Initialize config
    config = SimpleConfig()
    
    # Start GUI if available
    if SimpleMainWindow:
        app = SimpleMainWindow(db, config)
        app.run()
    else:
        # Console mode
        print("GUI not available, running in console mode")
        print("Weapons database sample:")
        for i, (weapon_id, info) in enumerate(list(db.weapons.items())[:5]):
            print(f"  {i+1}. {weapon_id}: Type={info.get('type')}, Ammo={info.get('ammo')}, Decay={info.get('decay')}")
        
        # Interactive mode
        while True:
            query = input("\nEnter weapon name to search (or 'quit' to exit): ").strip()
            if query.lower() == 'quit':
                break
                
            results = db.search_weapons(query)
            if results:
                print(f"Found {len(results)} weapons:")
                for weapon_id, info in results:
                    print(f"  - {weapon_id}: Type={info.get('type')}, Ammo={info.get('ammo')}, Decay={info.get('decay')}")
            else:
                print("No weapons found")


if __name__ == "__main__":
    asyncio.run(main())