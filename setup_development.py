#!/usr/bin/env python3
"""
Setup script for Orchesity IDE OSS
Helps with initial project setup and configuration
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python {version.major}.{version.minor} is not supported. Please use Python 3.9+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def setup_virtual_environment():
    """Create and activate virtual environment"""
    if os.path.exists("venv"):
        print("ℹ️  Virtual environment already exists")
        return True

    return run_command("python -m venv venv", "Creating virtual environment") is not None

def install_dependencies():
    """Install project dependencies"""
    # Activate virtual environment
    if os.name == "nt":  # Windows
        activate_cmd = ".\\venv\\Scripts\\activate"
        pip_cmd = ".\\venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "./venv/bin/pip"

    # Install dependencies
    commands = [
        f"{pip_cmd} install --upgrade pip",
        f"{pip_cmd} install -r requirements.txt",
        f"{pip_cmd} install -e \".[dev]\"",
    ]

    for cmd in commands:
        if run_command(cmd, f"Installing dependencies") is None:
            return False

    return True

def setup_environment_file():
    """Create .env file from template"""
    if os.path.exists(".env"):
        print("ℹ️  .env file already exists")
        return True

    if os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your API keys")
        return True
    else:
        print("❌ .env.example template not found")
        return False

def run_initial_tests():
    """Run initial test suite"""
    return run_command("python -m pytest tests/ -v", "Running initial tests") is not None

def check_git_repository():
    """Check if this is a git repository"""
    if os.path.exists(".git"):
        print("✅ Git repository detected")
        return True
    else:
        print("ℹ️  Not a git repository. Run 'git init' if needed")
        return False

def main():
    """Main setup function"""
    print("🚀 Orchesity IDE OSS Setup")
    print("=" * 40)

    # Check Python version
    if not check_python_version():
        return 1

    # Check git repository
    check_git_repository()

    # Setup virtual environment
    if not setup_virtual_environment():
        return 1

    # Install dependencies
    if not install_dependencies():
        return 1

    # Setup environment file
    if not setup_environment_file():
        return 1

    # Run initial tests
    if not run_initial_tests():
        print("⚠️  Some tests failed. Check the output above")
    else:
        print("✅ All tests passed!")

    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your API keys")
    print("2. Run 'python -m src.main' to start the application")
    print("3. Visit http://localhost:8000 in your browser")
    print("\nFor development:")
    print("- Run 'make test' to run tests")
    print("- Run 'make lint' to check code quality")
    print("- Run 'make format' to format code")

    return 0

if __name__ == "__main__":
    sys.exit(main())