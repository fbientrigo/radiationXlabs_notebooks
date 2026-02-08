import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the directory structure for RadAnalysis: TMR Simulation Framework.
    """
    base_dir = Path("RadAnalysis")
    
    # Define structure
    directories = [
        base_dir / "src" / "core",
        base_dir / "src" / "physics",
        base_dir / "src" / "stats",
        base_dir / "src" / "utils",
        base_dir / "tests",
    ]
    
    # Create directories
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"[OK] Created directory: {directory}")
            # Create __init__.py in src subdirectories to make them packages
            if "src" in str(directory):
                init_file = directory / "__init__.py"
                init_file.touch(exist_ok=True)
                print(f"    [OK] Created __init__.py in {directory}")
        except Exception as e:
            print(f"[ERROR] Failed to create {directory}: {e}")

    # Create empty Init for src root as well
    (base_dir / "src" / "__init__.py").touch(exist_ok=True)
    
    print("\nStructure generation complete.")

if __name__ == "__main__":
    create_structure()
