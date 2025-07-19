#!/usr/bin/env python3
"""
Setup script for SF6 Data Analysis project
"""

import os
import json
import sys
import subprocess

def create_directories():
    """Create necessary directories"""
    directories = ['output', 'logs', 'backups']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

def check_config():
    """Check if config.py exists"""
    if os.path.exists('config.py'):
        print("Configuration file (config.py) found")
        return True
    else:
        print("Warning: config.py not found")
        return False

def install_dependencies():
    """Install Python dependencies"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False
    except FileNotFoundError:
        print("requirements.txt not found")
        return False
    return True

def check_firefox():
    """Check if Firefox is installed"""
    try:
        subprocess.run(['firefox', '--version'], capture_output=True, check=True)
        print("Firefox found")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: Firefox not found. Please install Firefox for Selenium automation.")
        return False

def main():
    print("Setting up SF6 Data Analysis project...")
    
    # Create directories
    create_directories()
    
    # Check config
    check_config()
    
    # Install dependencies
    if not install_dependencies():
        print("Setup incomplete due to dependency installation failure")
        return
    
    # Check Firefox
    check_firefox()
    
    print("\nSetup complete!")
    print("\nNext steps:")
    print("1. Test the scrapers:")
    print("   run_monthly_export.bat")
    print("2. Or run individually:")
    print("   python -c \"from spiders.fighting_stats_spider import FightingStatsSpider; spider = FightingStatsSpider(); spider.setup_selenium(None)\"")
    print("   python main.py")
    print("3. Set up automated scheduling if desired (see setup_task_scheduler.md)")

if __name__ == '__main__':
    main()