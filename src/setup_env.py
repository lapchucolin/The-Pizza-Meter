"""
Pentagon Pizza Index - Environment Setup
=========================================
Checks and installs required dependencies for the OSINT analysis pipeline.

Dependencies:
- livepopulartimes: For scraping Google Maps live busyness data
- yfinance: For fetching real-time financial data (VIX, Gold)
"""

import subprocess
import sys
import importlib


def check_package(package_name: str, import_name: str = None) -> bool:
    """Check if a package is installed and importable."""
    import_name = import_name or package_name
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False


def install_package(package_name: str) -> bool:
    """Install a package using pip."""
    print(f"  [INSTALLING] {package_name}...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"  [SUCCESS] {package_name} installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] Failed to install {package_name}")
        print(f"  STDERR: {e.stderr}")
        return False


def main():
    print("=" * 60)
    print("PENTAGON PIZZA INDEX - ENVIRONMENT SETUP")
    print("=" * 60)
    print()
    
    # Define required packages: (pip_name, import_name)
    required_packages = [
        ("livepopulartimes", "livepopulartimes"),
        ("yfinance", "yfinance"),
        ("requests", "requests"),  # Often needed for HTTP operations
    ]
    
    all_success = True
    
    for pip_name, import_name in required_packages:
        print(f"[CHECKING] {pip_name}...")
        
        if check_package(pip_name, import_name):
            print(f"  [OK] {pip_name} is already installed.")
        else:
            print(f"  [MISSING] {pip_name} not found. Installing...")
            if not install_package(pip_name):
                all_success = False
                continue
            
            # Verify installation
            if check_package(pip_name, import_name):
                print(f"  [VERIFIED] {pip_name} import successful.")
            else:
                print(f"  [WARNING] {pip_name} installed but import failed!")
                all_success = False
        
        print()
    
    print("=" * 60)
    if all_success:
        print("[SETUP COMPLETE] All dependencies are ready!")
        print()
        print("Next steps:")
        print("  1. Run: python src/find_places.py")
        print("  2. Run: python src/test_scraper.py")
    else:
        print("[SETUP INCOMPLETE] Some packages failed to install.")
        print("Please check the errors above and try manual installation.")
    print("=" * 60)
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
