"""
Real-time session overlay for LewtNanny
Transparent window that displays live session statistics while gaming
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
        
        # Create overlay window
        self.overlay = tk.Tk()
        self.setup_overlay_window()
        
        # Session stats
        self.stats = {
            'events': 0,
            'total_damage': Decimal('0'),
            'total_loot_value': Decimal('0'),
            'critical_hits': 0,
            'misses': 0,
            'skills_gained': 0
        }
        
        self.create_widgets()
        
    def setup_overlay_window(self):
        """Setup transparent, always-on-top overlay"""
        self.overlay.title("LewtNanny Overlay")
        self.overlay.overrideredirect(True)  # Remove window decorations
        self.overlay.attributes('-topmost', True)  # Keep on top
        
        # Make window transparent (Windows)
        try:
            self.overlay.attributes('-transparentcolor', 'black')
            self.overlay.configure(bg='black')
        except tk.TclError:
            # Fallback for other systems
            self.overlay.attributes('-alpha', 0.9)
            
        # Set initial position and size
        self.overlay.geometry("300x400+50+50")
        self.overlay.configure(bg='#1a1a1a')
        
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
                
        def bind_all(widget):
            widget.bind('<Button-1>', on_start_drag)
            widget.bind('<B1-Motion>', on_drag)
            for child in widget.winfo_children():
                bind_all(child)
                
        bind_all(self.overlay)
        
    def create_widgets(self):
        """Create overlay widgets"""
        # Title
        title_frame = tk.Frame(self.overlay, bg='#1a1a1a')
        title_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        title_label = tk.Label(title_frame, text="🎯 LEWTNANNY", 
                           font=('Arial', 12, 'bold'), 
                           fg='#00ff00', bg='#1a1a1a')
        title_label.pack()
        
        # Session info
        self.session_label = tk.Label(title_frame, 
                                  text="No Active Session",
                                  font=('Arial', 10),
                                  fg='#ffcc00', bg='#1a1a1a')
        self.session_label.pack()
        
        # Stats container
        stats_frame = tk.Frame(self.overlay, bg='#2a2a2a', relief='ridge', bd=2)
        stats_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Stats display
        self.stats_labels = {}
        
        stats_to_show = [
            ('events', 'Events:', '#00ff00'),
            ('total_damage', 'Total Damage:', '#ff9900'),
            ('critical_hits', 'Critical Hits:', '#ff00ff'),
            ('misses', 'Misses:', '#ff6666'),
            ('total_loot_value', 'Loot Value:', '#00ccff'),
            ('skills_gained', 'Skills Gained:', '#ffff00'),
            ('dpp', 'DPP:', '#ffffff'),
            ('session_time', 'Session Time:', '#cccccc')
        ]
        
        for i, (key, label, color) in enumerate(stats_to_show):
            row_frame = tk.Frame(stats_frame, bg='#2a2a2a')
            row_frame.pack(fill='x', padx=5, pady=2)
            
            tk.Label(row_frame, text=label, font=('Arial', 9),
                    fg='#cccccc', bg='#2a2a2a', width=15, anchor='w').pack(side='left')
            
            value_label = tk.Label(row_frame, text="0", font=('Arial', 9, 'bold'),
                               fg=color, bg='#2a2a2a', anchor='e')
            value_label.pack(side='right')
            
            self.stats_labels[key] = value_label
        
        # Control buttons
        control_frame = tk.Frame(self.overlay, bg='#1a1a1a')
        control_frame.pack(fill='x', padx=10, pady=(5, 10))
        
        # Minimize/Close buttons
        button_frame = tk.Frame(control_frame, bg='#1a1a1a')
        button_frame.pack(side='right')
        
        minimize_btn = tk.Button(button_frame, text="—", font=('Arial', 8, 'bold'),
                             command=self.minimize, bg='#3a3a3a', fg='white',
                             bd=0, width=3)
        minimize_btn.pack(side='left', padx=2)
        
        close_btn = tk.Button(button_frame, text="×", font=('Arial', 8, 'bold'),
                           command=self.close, bg='#ff3333', fg='white',
                           bd=0, width=3)
        close_btn.pack(side='left', padx=2)
        
        # Visibility toggle
        self.visible = True
        self.minimized = False
        
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
        self.session_label.config(text=f"Session Active\n{activity_type.title()}")
        self.update_display()
        
    def stop_session(self):
        """Stop current session"""
        self.session_id = None
        self.session_start = None
        self.session_label.config(text="No Active Session")
        
    def add_event(self, event_data: Dict[str, Any]):
        """Update stats with new event"""
        if not self.session_id:
            return
            
        self.stats['events'] += 1
        
        event_type = event_data.get('event_type', '').lower()
        
        if event_type == 'combat':
            parsed_data = event_data.get('parsed_data', {}).get('event_data', {})
            if hasattr(parsed_data, 'damage'):
                self.stats['total_damage'] += Decimal(str(parsed_data.damage))
                if hasattr(parsed_data, 'critical') and parsed_data.critical:
                    self.stats['critical_hits'] += 1
                elif hasattr(parsed_data, 'miss') and parsed_data.miss:
                    self.stats['misses'] += 1
                    
        elif event_type == 'loot':
            parsed_data = event_data.get('parsed_data', {}).get('event_data', {})
            if hasattr(parsed_data, 'total_value'):
                self.stats['total_loot_value'] += Decimal(str(parsed_data.total_value))
                
        elif event_type == 'skill':
            self.stats['skills_gained'] += 1
            
        self.update_display()
        
    def update_display(self):
        """Update overlay display with current stats"""
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
            
    def minimize(self):
        """Minimize overlay"""
        if self.minimized:
            # Restore
            self.overlay.geometry("300x400")
            self.minimized = False
        else:
            # Minimize
            self.overlay.geometry("300x60")
            self.minimized = True
            
    def close(self):
        """Close overlay"""
        self.overlay.quit()
        
    def show(self):
        """Show the overlay"""
        self.overlay.mainloop()
        
    def hide(self):
        """Hide the overlay"""
        self.overlay.withdraw()
        
    def unhide(self):
        """Show the overlay"""
        self.overlay.deiconify()


def main():
    """Test the overlay standalone"""
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
        # Create mock objects
        class MockCombatEvent:
            def __init__(self, damage, critical=False, miss=False):
                self.damage = damage
                self.critical = critical
                self.miss = miss
                
        class MockLootEvent:
            def __init__(self, total_value):
                self.total_value = total_value
        
        overlay.add_event({'event_type': 'combat', 'parsed_data': {'event_data': MockCombatEvent(25.5, False)}})
        overlay.update_display()
        
        time.sleep(1)
        overlay.add_event({'event_type': 'combat', 'parsed_data': {'event_data': MockCombatEvent(45.0, True)}})
        overlay.update_display()
        
        time.sleep(1)
        overlay.add_event({'event_type': 'loot', 'parsed_data': {'event_data': MockLootEvent(5.25)}})
        overlay.update_display()
        
    threading.Thread(target=simulate_events, daemon=True).start()
    
    overlay.show()


if __name__ == "__main__":
    main()