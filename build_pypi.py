#!/usr/bin/env python3
"""
Build and test script for Orchesity IDE OSS PyPI package
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a shell command and return success status"""
    print(f"  {description}...")
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        print(f"  {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def main():
    """Main build and test function"""
    print("Orchesity IDE OSS - PyPI Build & Test")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: pyproject.toml not found. Run from project root.")
        return 1

    # Install build tools
    if not run_command("pip install build twine", "Installing build tools"):
        return 1

    # Clean previous builds
    if Path("dist").exists():
        import shutil

        shutil.rmtree("dist")
        print("Cleaned previous build files")

    # Build the package
    if not run_command("python -m build", "Building package"):
        return 1

    # Check what was built
    dist_files = list(Path("dist").glob("*"))
    if not dist_files:
        print("❌ No distribution files found")
        return 1

    print(f"Built files: {[f.name for f in dist_files]}")

    # Test installation in a virtual environment
    print("\nTesting package installation...")

    # Create temporary venv for testing
    test_venv = Path("test_venv")
    if test_venv.exists():
        import shutil

        shutil.rmtree(test_venv)

    if not run_command("python -m venv test_venv", "Creating test virtual environment"):
        return 1

    # Install package in test venv
    wheel_file = next((f for f in dist_files if f.suffix == ".whl"), None)
    if not wheel_file:
        print("❌ No wheel file found")
        return 1

    pip_cmd = (
        str(test_venv / "Scripts" / "pip")
        if os.name == "nt"
        else str(test_venv / "bin" / "pip")
    )

    if not run_command(
        f"{pip_cmd} install {wheel_file}", "Installing package in test environment"
    ):
        return 1

    # Test import
    python_cmd = (
        str(test_venv / "Scripts" / "python")
        if os.name == "nt"
        else str(test_venv / "bin" / "python")
    )

    test_script = """
try:
    import src
    print("✅ Package import successful")
    print(f"Package location: {src.__file__}")
except ImportError as e:
    print(f"Import failed: {e}")
    exit(1)
"""

    if not run_command(f'{python_cmd} -c "{test_script}"', "Testing package import"):
        return 1

    # Clean up test venv
    try:
        import shutil

        shutil.rmtree(test_venv)
        print("   Cleaned up test environment")
    except Exception as e:
        print(f"   Warning: Could not clean up test environment: {e}")
        print("   You can manually delete the 'test_venv' directory if needed")

    print("\nPackage build and test completed successfully!")
    print("\nReady for PyPI upload:")
    print(f"   twine upload dist/*")
    print("\nFiles ready for upload:")
    for f in dist_files:
        print(f"   - {f.name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
