"""
Quick refresh test to force weapon selector
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

def main():
    print("Testing refresh mechanism...")
    
    # Test creating a refresh function
    try:
        import tkinter as tk
        root = tk.Tk()
        root.title("Refresh Test")
        
        def refresh_weapons():
            print("Weapons refreshed!")
        
        def force_init():
            try:
                import main_mvp
                if hasattr(main_mvp, 'WeaponSelector'):
                    print("Creating WeaponSelector...")
                    selector = main_mvp.WeaponSelector(root, None, None)
                    print("Weapons passed to selector:", hasattr(selector, 'weapons'))
                else:
                    print("WeaponSelector class not available")
            except Exception as e:
                print(f"Error: {e}")
        
        # Add refresh button
        btn = tk.Button(root, text="Initialize Weapons", command=force_init)
        btn.pack(pady=20)
        
        btn = tk.Button(root, text="Refresh Weapons", command=refresh_weapons)
        btn.pack(pady=10)
        
        root.mainloop()
        
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    main()