"""
Pentagon Pizza Index - Build Script
=====================================
Creates a standalone executable for the dashboard.
"""

import subprocess
import sys
import os
import shutil

def main():
    print("=" * 60)
    print("  🍕 Pentagon Pizza Index - Build Script")
    print("=" * 60)
    print()
    
    # Get the src directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    
    print(f"Project directory: {project_dir}")
    print(f"Source directory: {script_dir}")
    print()
    
    # Build command
    dashboard_path = os.path.join(script_dir, 'dashboard.py')
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Single executable
        "--name=PentagonPizzaIndex",  # Output name
        "--add-data", f"{dashboard_path};.",  # Include dashboard as data
        "--hidden-import=flask",
        "--hidden-import=plotly",
        "--hidden-import=pandas",
        "--hidden-import=yfinance",
        "--hidden-import=livepopulartimes",
        "--hidden-import=werkzeug",
        "--hidden-import=jinja2",
        "--collect-submodules=yfinance",
        "--collect-submodules=plotly",
        dashboard_path
    ]
    
    print("Building executable...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, cwd=project_dir, check=True)
        
        print()
        print("=" * 60)
        print("  ✅ BUILD SUCCESSFUL!")
        print("=" * 60)
        print()
        print(f"  Executable location:")
        print(f"  {os.path.join(project_dir, 'dist', 'PentagonPizzaIndex.exe')}")
        print()
        print("  To run, simply double-click the .exe file!")
        print("=" * 60)
        
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 60)
        print("  ❌ BUILD FAILED!")
        print("=" * 60)
        print(f"  Error: {e}")
        print()
        print("  Try running manually:")
        print("  python -m PyInstaller --onefile src/dashboard.py")
        print("=" * 60)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
