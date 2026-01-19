"""
Real-time session overlay for LewtNanny - Simplified version
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from decimal import Decimal

try:
    import tkinter as tk
    from tkinter import ttk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("tkinter not available, overlay disabled")


class SessionOverlay:
    """Transparent overlay window for live session stats"""
    
    def __init__(self, db_manager, config_manager):
        if not TKINTER_AVAILABLE:
            raise ImportError("tkinter not available")
            
        self.db = db_manager
        self.config = config_manager
        self.session_id = None
        self.session_start = None
        self.minimized = False
        
        # Session stats
        self.stats = {
            'events': 0,
            'total_damage': Decimal('0'),
            'total_loot_value': Decimal('0'),
            'critical_hits': 0,
            'misses': 0,
            'skills_gained': 0
        }
        
        self.overlay = None
        self.minimized = False
        
    def setup_overlay(self):
        """Setup transparent, always-on-top overlay"""
        if not TKINTER_AVAILABLE:
            return
            
        self.overlay = tk.Tk()
        self.overlay.title("LewtNanny Overlay")
        self.overlay.overrideredirect(True)  # Remove window decorations
        self.overlay.attributes('-topmost', True)  # Keep on top
        
        # Make window semi-transparent
        self.overlay.attributes('-alpha', 0.9)
        self.overlay.configure(bg='#1a1a1a')
        
        # Set initial position and size
        self.overlay.geometry("320x450+100+100")
        
        # Make window draggable
        self.bind_mouse_events()
        
    def bind_mouse_events(self):
        """Allow window to be dragged"""
        self.start_x = None
        self.start_y = None
        
        def on_start_drag(event):
            self.start_x = event.x
            self.start_y = event.y
            
        def on_drag(event):
            if self.start_x and self.start_y:
                x = self.overlay.winfo_x() + event.x - self.start_x
                y = self.overlay.winfo_y() + event.y - self.start_y
                self.overlay.geometry(f"+{x}+{y}")
                
        self.overlay.bind('<Button-1>', on_start_drag)
        self.overlay.bind('<B1-Motion>', on_drag)
        
    def create_widgets(self):
        """Create overlay widgets"""
        # Title bar
        self.title_frame = tk.Frame(self.overlay, bg='#0a0a0a', height=40)
        self.title_frame.pack(fill='x')
        self.title_frame.pack_propagate(False)
        
        title_label = tk.Label(self.title_frame, text="🎯 LEWTNANNY", 
                           font=('Arial', 14, 'bold'), 
                           fg='#00ff00', bg='#0a0a0a')
        title_label.pack(pady=8)
        
        # Session label
        self.session_label = tk.Label(self.title_frame, 
                                  text="No Active Session",
                                  font=('Arial', 11),
                                  fg='#ffcc00', bg='#0a0a0a')
        self.session_label.pack()
        
        # Main content area
        self.content_frame = tk.Frame(self.overlay, bg='#1a1a1a')
        self.content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Stats display
        self.create_stats_display()
        
        # Control bar
        self.control_frame = tk.Frame(self.overlay, bg='#0a0a0a', height=40)
        self.control_frame.pack(fill='x', side='bottom')
        self.control_frame.pack_propagate(False)
        
        self.create_controls()
        
    def create_stats_display(self):
        """Create stats display widgets"""
        stats_container = tk.Frame(self.content_frame, bg='#2a2a2a', relief='ridge', bd=2)
        stats_container.pack(fill='both', expand=True)
        
        self.stats_labels = {}
        
        stats_to_show = [
            ('events', 'Events', '#00ff00'),
            ('total_damage', 'Total Damage', '#ff9900'),
            ('critical_hits', 'Critical Hits', '#ff00ff'),
            ('misses', 'Misses', '#ff6666'),
            ('total_loot_value', 'Loot Value', '#00ccff'),
            ('skills_gained', 'Skills Gained', '#ffff00'),
            ('dpp', 'DPP', '#ffffff'),
            ('session_time', 'Session Time', '#cccccc')
        ]
        
        for i, (key, label, color) in enumerate(stats_to_show):
            row_frame = tk.Frame(stats_container, bg='#2a2a2a')
            row_frame.pack(fill='x', padx=10, pady=4)
            
            tk.Label(row_frame, text=label + ":", font=('Arial', 10),
                    fg='#aaaaaa', bg='#2a2a2a', width=12, anchor='w').pack(side='left')
            
            value_label = tk.Label(row_frame, text="0", font=('Arial', 10, 'bold'),
                               fg=color, bg='#2a2a2a', anchor='e')
            value_label.pack(side='right')
            
            self.stats_labels[key] = value_label
            
    def create_controls(self):
        """Create control buttons"""
        button_frame = tk.Frame(self.control_frame, bg='#0a0a0a')
        button_frame.pack(pady=5)
        
        # Minimize/Restore button
        self.minimize_btn = tk.Button(button_frame, text="—", font=('Arial', 10, 'bold'),
                                   command=self.toggle_minimize, bg='#3a3a3a', fg='white',
                                   bd=1, width=4)
        self.minimize_btn.pack(side='left', padx=5)
        
        # Close button
        close_btn = tk.Button(button_frame, text="×", font=('Arial', 10, 'bold'),
                           command=self.close, bg='#ff3333', fg='white',
                           bd=1, width=4)
        close_btn.pack(side='left', padx=5)
        
    def toggle_minimize(self):
        """Toggle between minimized and restored states"""
        if self.minimized:
            # Restore
            self.overlay.geometry("320x450+100+100")
            self.content_frame.pack(fill='both', expand=True, padx=10, pady=10)
            self.minimized = False
            self.minimize_btn.config(text="—")
        else:
            # Minimize
            self.overlay.geometry("320x100+100+100")
            self.content_frame.pack_forget()
            self.minimized = True
            self.minimize_btn.config(text="□")
            
        # Update session label when minimized
        if self.minimized:
            # Show useful info when minimized
            elapsed = ""
            if self.session_start:
                elapsed_time = datetime.now() - self.session_start
                hours, remainder = divmod(elapsed_time.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                elapsed = f"\n⏱ {hours:02d}:{minutes:02d}:{seconds:02d}"
            
            profit = ""
            if hasattr(self, 'stats') and self.stats.get('total_loot_value'):
                profit = f"\n💰 {self.stats.get('total_loot_value', 0):.2f} PED"
            
            events = ""
            if hasattr(self, 'stats') and self.stats.get('events'):
                events = f"\n📊 {self.stats.get('events', 0)} events"
                
            self.session_label.config(text=f"MINIMIZED{elapsed}{profit}{events}")
        else:
            self.update_session_label()
        
    def start_session(self, session_id: str, activity_type: str):
        """Start tracking a new session"""
        self.session_id = session_id
        self.session_start = datetime.now()
        
        # Reset stats
        self.stats = {
            'events': 0,
            'total_damage': Decimal('0'),
            'total_loot_value': Decimal('0'),
            'critical_hits': 0,
            'misses': 0,
            'skills_gained': 0
        }
        
        # Update display
        self.update_session_label()
        self.update_display()
        
    def update_session_label(self):
        """Update session label based on current state"""
        if self.overlay and hasattr(self, 'session_label'):
            if self.session_id:
                self.session_label.config(text="Session Active")
            else:
                self.session_label.config(text="No Active Session")
        
    def stop_session(self):
        """Stop current session"""
        self.session_id = None
        self.session_start = None
        self.update_session_label()
        
    def add_event(self, event_data: Dict[str, Any]):
        """Update stats with new event"""
        if not self.session_id:
            return
            
        self.stats['events'] += 1
        
        event_type = event_data.get('event_type', '').lower()
        parsed_data = event_data.get('parsed_data', {})
        
        if event_type == 'combat':
            combat_data = parsed_data.get('event_data', {})
            if hasattr(combat_data, 'damage'):
                self.stats['total_damage'] += Decimal(str(combat_data.damage))
                if hasattr(combat_data, 'critical') and combat_data.critical:
                    self.stats['critical_hits'] += 1
                elif hasattr(combat_data, 'miss') and combat_data.miss:
                    self.stats['misses'] += 1
                    
        elif event_type == 'loot':
            loot_data = parsed_data.get('event_data', {})
            if hasattr(loot_data, 'items'):
                total_value = sum(float(item[2]) for item in loot_data.items)
                self.stats['total_loot_value'] += Decimal(str(total_value))
                
        elif event_type == 'skill':
            self.stats['skills_gained'] += 1
            
        self.update_display()
        
    def update_display(self):
        """Update overlay display with current stats"""
        if self.minimized:
            return
            
        # Update basic stats
        self.stats_labels['events'].config(text=str(self.stats['events']))
        self.stats_labels['total_damage'].config(text=f"{self.stats['total_damage']:.1f}")
        self.stats_labels['critical_hits'].config(text=str(self.stats['critical_hits']))
        self.stats_labels['misses'].config(text=str(self.stats['misses']))
        self.stats_labels['total_loot_value'].config(text=f"{self.stats['total_loot_value']:.2f} PED")
        self.stats_labels['skills_gained'].config(text=str(self.stats['skills_gained']))
        
        # Calculate DPP (Damage Per PED)
        if self.stats['total_loot_value'] > 0:
            dpp = float(self.stats['total_damage']) / float(self.stats['total_loot_value'])
            self.stats_labels['dpp'].config(text=f"{dpp:.2f}")
        else:
            self.stats_labels['dpp'].config(text="N/A")
            
        # Update session time
        if self.session_start:
            elapsed = datetime.now() - self.session_start
            hours, remainder = divmod(elapsed.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.stats_labels['session_time'].config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            self.stats_labels['session_time'].config(text="00:00:00")
            
    def close(self):
        """Close overlay (hide, not quit to avoid closing main program)"""
        if self.overlay:
            self.overlay.withdraw()
            # Mark overlay as closed
            self.overlay = None
        
    def show(self):
        """Show the overlay"""
        if not self.overlay:
            self.setup_overlay()
            self.create_widgets()
        
        if self.overlay:
            # Configure overlay properties
            self.overlay.attributes('-topmost', True)
            self.overlay.attributes('-alpha', 0.9)
            
            # Start overlay in separate thread to avoid blocking
            import threading
            def run_overlay():
                if self.overlay:
                    self.overlay.mainloop()
            
            # Don't block main thread
            overlay_thread = threading.Thread(target=run_overlay, daemon=True)
            overlay_thread.start()


def main():
    """Test overlay standalone"""
    if not TKINTER_AVAILABLE:
        print("tkinter not available")
        return
        
    print("LewtNanny Overlay - Test Mode")
    print("Close window to exit")
    
    # Mock database and config for testing
    class MockDB:
        pass
    
    class MockConfig:
        pass
        
    overlay = SessionOverlay(MockDB(), MockConfig())
    
    # Simulate a session
    overlay.start_session("test_123", "hunting")
    
    # Simulate some events
    import threading
    
    def simulate_events():
        import time
        time.sleep(2)
        event_data = {
            'event_type': 'combat',
            'parsed_data': {
                'event_data': type('Mock', (), {'damage': 25.5, 'critical': False})()
            }
        }
        overlay.add_event(event_data)
        
        time.sleep(1)
        event_data = {
            'event_type': 'combat', 
            'parsed_data': {
                'event_data': type('Mock', (), {'damage': 45.0, 'critical': True})()
            }
        }
        overlay.add_event(event_data)
        
        time.sleep(1)
        event_data = {
            'event_type': 'loot',
            'parsed_data': {
                'event_data': type('Mock', (), {'items': [('Animal Oil', 5, 1.25)]})()
            }
        }
        overlay.add_event(event_data)
        
    threading.Thread(target=simulate_events, daemon=True).start()
    
    overlay.show()


if __name__ == "__main__":
    main()