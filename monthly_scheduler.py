#!/usr/bin/env python3
"""
SF6 Data Export Scheduler
Runs data exports on the 2nd Friday of every month
"""

import schedule
import time
import logging
import os
import sys
from datetime import datetime, timedelta
from spiders.fighting_stats_spider import FightingStatsSpider
import subprocess

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monthly_export_scheduler.log'),
        logging.StreamHandler()
    ]
)

def is_second_friday():
    """Check if today is the second Friday of the month"""
    today = datetime.now()
    
    # Get the first day of the month
    first_day = today.replace(day=1)
    
    # Find the first Friday
    days_until_friday = (4 - first_day.weekday()) % 7  # Friday is weekday 4
    first_friday = first_day + timedelta(days=days_until_friday)
    
    # Second Friday is 7 days later
    second_friday = first_friday + timedelta(days=7)
    
    return today.date() == second_friday.date()

def run_sf6_export():
    """Run the SF6 data export"""
    try:
        logging.info("Starting SF6 monthly data export")
        
        # Check if it's actually the second Friday
        if not is_second_friday():
            logging.info("Not the second Friday of the month, skipping export")
            return
        
        # Change to project directory
        project_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_dir)
        
        # Ensure timestamped output directory exists for this scrape run
        from config_manager import get_config
        config = get_config()
        output_dir = config.get_timestamped_output_dir()
        logging.info(f"Using output directory: {output_dir}")
        
        # Run fighting_stats spider
        logging.info("Running fighting_stats spider...")
        from spiders.fighting_stats_spider import FightingStatsSpider
        spider = FightingStatsSpider()
        spider.setup_selenium(None)
        logging.info("fighting_stats spider completed")
        
        # Run street_fighter spider
        logging.info("Running street_fighter spider...")
        result = subprocess.run([
            sys.executable, 
            'main.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("street_fighter spider completed successfully")
        else:
            logging.error(f"street_fighter spider failed: {result.stderr}")
        
        logging.info("SF6 monthly data export completed")
        
    except Exception as e:
        logging.error(f"Error during SF6 export: {str(e)}")

def main():
    """Main scheduler loop"""
    logging.info("SF6 Monthly Export Scheduler started")
    
    # Schedule the job to run every Friday at 2:00 AM
    # The function will check if it's the second Friday
    schedule.every().friday.at("02:00").do(run_sf6_export)
    
    # Alternative: Check daily at 2:00 AM
    # schedule.every().day.at("02:00").do(run_sf6_export)
    
    logging.info("Scheduler configured - checking every Friday at 2:00 AM")
    logging.info("Will export data on 2nd Friday of each month")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(3600)  # Check every hour
        except KeyboardInterrupt:
            logging.info("Scheduler stopped by user")
            break
        except Exception as e:
            logging.error(f"Scheduler error: {str(e)}")
            time.sleep(3600)  # Wait an hour before retrying

if __name__ == "__main__":
    # First, install the schedule package if not already installed
    try:
        import schedule
    except ImportError:
        print("Installing schedule package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "schedule"])
        import schedule
    
    main()