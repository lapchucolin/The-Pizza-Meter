"""
Pentagon Pizza Index - Launcher
================================
This script launches the Pentagon Pizza Index dashboard.
Can be compiled to an executable with PyInstaller.

To create the EXE:
    python -m PyInstaller --onefile --windowed --icon=pizza.ico --name="PizzaIndex" launcher.py
"""

import subprocess
import sys
import os


def get_script_dir():
    """Get the directory where this script is located."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))


def main():
    script_dir = get_script_dir()
    dashboard_path = os.path.join(script_dir, 'dashboard.py')
    
    # Check if dashboard exists
    if not os.path.exists(dashboard_path):
        # Try parent directory's src folder
        dashboard_path = os.path.join(os.path.dirname(script_dir), 'src', 'dashboard.py')
    
    if not os.path.exists(dashboard_path):
        print("Error: dashboard.py not found!")
        print(f"Looked in: {dashboard_path}")
        input("Press Enter to exit...")
        return 1
    
    print("=" * 50)
    print("  🍕 Pentagon Pizza Index Launcher")
    print("=" * 50)
    print()
    print("  Starting dashboard server...")
    print("  Your browser will open automatically.")
    print()
    
    # Run the dashboard
    try:
        subprocess.run([sys.executable, dashboard_path], check=True)
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
