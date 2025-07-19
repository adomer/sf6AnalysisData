import logging
import random
import csv
from collections import defaultdict
import scrapy
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from config import COMMON_SPIDER_SETTINGS
import geckodriver_autoinstaller

# Install geckodriver if not present
geckodriver_autoinstaller.install()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)


class StreetFighterSpider(scrapy.Spider):
    name = "street_fighter_spider"
    custom_settings = {**COMMON_SPIDER_SETTINGS}

    # Updated to target new stats endpoint
    stats_url = "https://www.streetfighter.com/6/buckler/stats/usagerate_master"
    scraped_data = []

    def __init__(self):
        self.driver = None  # Initialize as None, create when needed
        self.consecutive_errors = 0  # Keep track of consecutive errors
        
    def _init_driver(self):
        """Initialize the Firefox driver only when needed"""
        if self.driver is None:
            # Install geckodriver automatically
            geckodriver_path = geckodriver_autoinstaller.install()
            
            # Setup Firefox options
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Create service with geckodriver path
            service = Service(geckodriver_path)
            
            # Initialize Firefox webdriver
            self.driver = webdriver.Firefox(service=service, options=options)
            logging.info("Firefox driver initialized successfully")

    def adjust_delay(self):
        # Calculate exponential backoff
        delay = min(0.5 * (2 ** self.consecutive_errors), 60)
        # Add jitter: random value between 0 and delay
        jitter = random.uniform(0, delay)
        self.custom_settings['DOWNLOAD_DELAY'] = delay + jitter

    def start_requests(self):
        try:
            # Initialize the driver
            self._init_driver()
            
            logging.info("Navigating directly to Street Fighter stats page...")
            self.driver.get(self.stats_url)
            
            # Wait for initial page load
            import time
            time.sleep(5)
            
            # Check if page loaded successfully
            current_url = self.driver.current_url
            logging.info(f"Current URL: {current_url}")
            
            if "usagerate_master" not in current_url:
                logging.warning("Stats page may not have loaded correctly. Trying again...")
                self.driver.get(self.stats_url)
                time.sleep(5)
                current_url = self.driver.current_url
                logging.info(f"Retry URL: {current_url}")
            
            # Wait for dynamic content to load - this page uses JavaScript to load stats
            logging.info("Waiting for dynamic content to load...")
            time.sleep(10)  # Give JavaScript time to load the actual character data
            
            # Try to wait for specific elements that indicate data has loaded
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            try:
                # Wait for character usage data to appear
                wait = WebDriverWait(self.driver, 20)
                # Look for elements that might contain character data
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="character"], [class*="usage"], [class*="rate"], table, .chart')))
                logging.info("Dynamic content appears to have loaded")
            except Exception as wait_e:
                logging.warning(f"Timeout waiting for dynamic content: {wait_e}")
                logging.info("Proceeding anyway...")
            
            # First, identify all available month options
            self.scrape_all_months()
            
            # Write CSV data after parsing all months
            self.write_to_csv()
            
            # Important: yield an empty list to satisfy Scrapy's iterator requirement
            return iter([])
            
        except Exception as e:
            logging.error(f"Error in start_requests: {e}")
            if self.driver:
                self.driver.quit()
            return iter([])

    def scrape_all_months(self):
        """Hybrid approach: Dynamically discover available months, then navigate via URL"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            import time
            import re
            
            logging.info("Starting hybrid month scraping: dynamic discovery + URL navigation...")
            
            # Step 1: Dynamically discover available months from the selector
            month_section_xpath = '/html/body/div/div/article[2]/aside[1]/div/section'
            discovered_months = []
            
            try:
                wait = WebDriverWait(self.driver, 10)
                month_section = wait.until(EC.presence_of_element_located((By.XPATH, month_section_xpath)))
                logging.info("Found month selection section")
                
                # Try different selectors to find month options and extract their URLs/values
                selectors_to_try = [
                    (By.XPATH, f'{month_section_xpath}//a'),
                    (By.XPATH, f'{month_section_xpath}//li'),
                    (By.XPATH, f'{month_section_xpath}//option'),
                    (By.CSS_SELECTOR, '#usagerate aside section a'),
                    (By.CSS_SELECTOR, '#usagerate aside section li'),
                    (By.CSS_SELECTOR, '#usagerate aside section option')
                ]
                
                for selector_type, selector in selectors_to_try:
                    try:
                        month_elements = self.driver.find_elements(selector_type, selector)
                        if month_elements:
                            logging.info(f"Found {len(month_elements)} month elements using {selector}")
                            
                            for element in month_elements:
                                # Extract month information
                                month_text = element.text.strip()
                                month_url = None
                                month_value = None
                                
                                # Try to get URL from href attribute
                                try:
                                    month_url = element.get_attribute('href')
                                except:
                                    pass
                                
                                # Try to get value from value attribute  
                                try:
                                    month_value = element.get_attribute('value')
                                except:
                                    pass
                                
                                # Try to get URL from onclick or data attributes
                                try:
                                    onclick = element.get_attribute('onclick')
                                    if onclick:
                                        # Look for YYYYMM pattern in onclick
                                        url_match = re.search(r'202\d{3}', onclick)
                                        if url_match:
                                            month_value = url_match.group()
                                except:
                                    pass
                                
                                logging.info(f"Month element - Text: '{month_text}', URL: '{month_url}', Value: '{month_value}'")
                                
                                if month_text or month_url or month_value:
                                    # Extract YYYYMM format from URL or value
                                    month_id = None
                                    if month_url and 'usagerate_master' in month_url:
                                        # Extract YYYYMM from URL like /usagerate_master/202506
                                        url_match = re.search(r'/usagerate_master/(\d{6})', month_url)
                                        if url_match:
                                            month_id = url_match.group(1)
                                    elif month_value and re.match(r'^\d{6}$', month_value):
                                        month_id = month_value
                                    elif month_text:
                                        # Try to parse month text like "06/2025" to "202506"
                                        text_match = re.search(r'(\d{2})/(\d{4})', month_text)
                                        if text_match:
                                            month, year = text_match.groups()
                                            month_id = f"{year}{month}"
                                    
                                    if month_id:
                                        # Convert to display format MM/YYYY
                                        if len(month_id) == 6:
                                            year = month_id[:4]
                                            month = month_id[4:6]
                                            display_format = f"{month}/{year}"
                                            discovered_months.append((month_id, display_format))
                                            logging.info(f"Discovered month: {display_format} (ID: {month_id})")
                            
                            if discovered_months:
                                break  # Found months, no need to try other selectors
                                
                    except Exception as e:
                        logging.debug(f"Failed selector {selector}: {e}")
                
            except Exception as e:
                logging.warning(f"Could not find month selection section: {e}")
            
            # Remove duplicates and sort
            discovered_months = list(set(discovered_months))
            discovered_months.sort(key=lambda x: x[0], reverse=True)  # Sort by YYYYMM descending
            
            logging.info(f"Discovered {len(discovered_months)} unique months: {[m[1] for m in discovered_months]}")
            
            # Step 2: Navigate via URL to each discovered month
            if not discovered_months:
                logging.warning("No months discovered, falling back to current page")
                self.scrape_current_month_data("current")
                return
            
            base_url = "https://www.streetfighter.com/6/buckler/stats/usagerate_master"
            
            for month_id, month_display in discovered_months:
                try:
                    # Navigate to the specific month URL
                    month_url = f"{base_url}/{month_id}"
                    logging.info(f"Navigating to {month_display} data: {month_url}")
                    
                    self.driver.get(month_url)
                    
                    # Wait for page to load
                    time.sleep(5)
                    
                    # Verify we're on the correct page
                    current_url = self.driver.current_url
                    logging.info(f"Current URL: {current_url}")
                    
                    # Wait for dynamic content to load
                    logging.info(f"Waiting for {month_display} character data to load...")
                    time.sleep(10)
                    
                    # Wait for character data to be present
                    try:
                        wait = WebDriverWait(self.driver, 20)
                        # Wait for all 4 divs to be present
                        wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/article[2]/section/div/div[1]/ul/li[1]')))
                        wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/article[2]/section/div/div[4]/ul/li[1]')))
                        logging.info(f"Character data loaded for {month_display}")
                        
                        # Get first character for verification
                        first_char_element = self.driver.find_element(By.XPATH, '/html/body/div[2]/div/article[2]/section/div/div[1]/ul/li[1]')
                        first_char_data = first_char_element.text
                        logging.info(f"VERIFICATION - {month_display} first character data: {first_char_data}")
                        
                    except Exception as wait_e:
                        logging.warning(f"Timeout waiting for {month_display} data: {wait_e}")
                    
                    # Scrape data for this month
                    self.scrape_current_month_data(month_display)
                    
                    logging.info(f"Completed scraping for {month_display}")
                    
                except Exception as e:
                    logging.error(f"Error processing month {month_display}: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error in scrape_all_months: {e}")
            # Fallback: scrape current month
            self.scrape_current_month_data("fallback")

    def scrape_current_month_data(self, month_identifier):
        """Scrape data for the currently displayed month across all 4 divs"""
        try:
            logging.info(f"Scraping data for month: {month_identifier}")
            
            # Get the current page source
            page_source = self.driver.page_source
            
            # Create a scrapy Response object from the rendered page
            from scrapy.http import HtmlResponse
            rendered_response = HtmlResponse(
                url=self.stats_url,
                body=page_source.encode('utf-8'),
                encoding='utf-8'
            )
            
            # Parse all 4 divs for this month
            total_characters_found = 0
            
            for div_num in range(1, 5):  # div[1] through div[4]
                xpath = f'/html/body/div[2]/div/article[2]/section/div/div[{div_num}]/ul/li'
                character_lis = rendered_response.xpath(xpath)
                
                if character_lis:
                    logging.info(f"Found {len(character_lis)} character list items in div[{div_num}] for month {month_identifier}")
                    self.parse_character_ranking_data(character_lis, div_index=div_num, month=month_identifier)
                    total_characters_found += len(character_lis)
                else:
                    logging.info(f"No character data found in div[{div_num}] for month {month_identifier}")
            
            if total_characters_found == 0:
                logging.warning(f"No character data found for month {month_identifier}")
            else:
                logging.info(f"Total characters found for month {month_identifier}: {total_characters_found}")
                
        except Exception as e:
            logging.error(f"Error scraping month data for {month_identifier}: {e}")

            
    def parse_character_ranking_data(self, character_lis, div_index=None, month="unknown"):
        """Parse character ranking data from li elements containing dd values"""
        try:
            # Map div indices to Master rank divisions
            div_to_rank_mapping = {
                1: 'Master',
                2: 'High Master', 
                3: 'Grand Master',
                4: 'Ultimate Master'
            }
            
            for li in character_lis:
                # Extract all text content from this li element
                all_text = li.xpath('.//text()').getall()
                # Clean up the data - remove empty strings and strip whitespace
                cleaned_text = [text.strip() for text in all_text if text.strip()]
                
                if cleaned_text:
                    logging.debug(f"Raw text from li: {cleaned_text}")
                    
                    # Parse the character data based on the expected structure
                    # Expected pattern: [rank, character_name, usage_rate, %, change_rate]
                    # Example: ['3', 'KEN', '5.855', '%', '-2.0%']
                    
                    rank = None
                    character_name = None
                    usage_percentage = None
                    change_rate = None
                    
                    # Find rank (should be a digit)
                    for text in cleaned_text:
                        if text.isdigit():
                            rank = text
                            break
                    
                    # Find character name (usually all caps, appears after rank)
                    for i, text in enumerate(cleaned_text):
                        if text.isdigit() and i + 1 < len(cleaned_text):
                            # Next text after rank should be character name
                            potential_name = cleaned_text[i + 1]
                            # Character names are typically all caps and may contain dots, dashes, or spaces
                            if potential_name.isupper() and (potential_name.isalpha() or 
                                                            '.' in potential_name or 
                                                            '-' in potential_name or 
                                                            ' ' in potential_name):
                                character_name = potential_name
                                break
                    
                    # Find usage percentage (decimal number before %)
                    for i, text in enumerate(cleaned_text):
                        if '.' in text and text.replace('.', '').isdigit():
                            # This should be the usage rate
                            usage_percentage = text + '%'  # Add % for clarity
                            break
                    
                    # Find change rate (text with % that's not the main usage rate)
                    # Note: First month (02/2025) may not have change rates
                    for text in cleaned_text:
                        if '%' in text and text != '%' and text != usage_percentage:
                            change_rate = text
                            break
                    
                    # If no change rate found, it might be the first month
                    if not change_rate:
                        change_rate = "N/A"  # Mark as N/A for first month
                    
                    # Create character data entry if we have minimum required data
                    if rank and character_name and usage_percentage:
                        # Map div_index to rank name
                        rank_name = div_to_rank_mapping.get(div_index, f'Div {div_index}')
                        
                        character_data = {
                            'rank': rank,
                            'character_name': character_name,
                            'usage_percentage': usage_percentage,
                            'change_rate': change_rate,
                            'month': month,  # Use the passed month parameter
                            'div_index': div_index,  # Keep original div index
                            'rank_name': rank_name,  # Add mapped rank name
                            'source': 'xpath_extraction'
                        }
                        
                        self.scraped_data.append(character_data)
                        logging.info(f"Extracted from {rank_name} (div[{div_index}]) for {month}: Rank {rank}, {character_name}, {usage_percentage}, Change: {change_rate}")
                        
                        # Special logging for first few entries to verify data accuracy
                        if int(rank) <= 3:
                            logging.info(f"VERIFICATION - Month {month}, {rank_name}, Rank {rank}: {character_name} = {usage_percentage}, Change: {change_rate}")
                    else:
                        logging.debug(f"Could not parse character data from: {cleaned_text}")
                        logging.debug(f"  Found - Rank: {rank}, Name: {character_name}, Usage: {usage_percentage}")
                        
            logging.info(f"Total character data extracted: {len(self.scraped_data)}")
            
        except Exception as e:
            logging.error(f"Failed to parse character ranking data: {e}")
            
            
    def write_to_csv(self):
        """Write scraped usage rate data to CSV, organized by month"""
        if not self.scraped_data:
            logging.warning("No data to write to CSV")
            return
            
        # Group data by month
        from collections import defaultdict
        month_data = defaultdict(list)
        
        for entry in self.scraped_data:
            month = entry.get('month', 'unknown')
            month_data[month].append(entry)
        
        # Get timestamped output directory
        from config_manager import get_config
        import os
        config = get_config()
        output_dir = config.get_timestamped_output_dir()
        
        # Write separate CSV files for each month
        for month, data in month_data.items():
            # Clean month name for filename
            clean_month = ''.join(c for c in month if c.isalnum() or c in (' ', '-', '_')).strip()
            clean_month = clean_month.replace(' ', '_')
            
            filename = os.path.join(output_dir, f"master_usage_stats_{clean_month}.csv")
            
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                if data:
                    # Ensure all entries have the same keys
                    all_keys = set()
                    for entry in data:
                        all_keys.update(entry.keys())
                    
                    fieldnames = sorted(list(all_keys))
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
                    logging.info(f"Written {len(data)} character stats for {month} to {filename}")
        
        # Also write a combined CSV with all months
        combined_filename = os.path.join(output_dir, "master_usage_stats_all_months.csv")
        with open(combined_filename, 'w', newline='', encoding='utf-8') as file:
            if self.scraped_data:
                # Get all unique fieldnames
                all_keys = set()
                for entry in self.scraped_data:
                    all_keys.update(entry.keys())
                
                fieldnames = sorted(list(all_keys))
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.scraped_data)
                logging.info(f"Written {len(self.scraped_data)} total character stats to {combined_filename}")
        
        logging.info(f"Data organized by {len(month_data)} different months/periods")

    def close_spider(self, spider):
        """Called when spider is closing - cleanup and final reporting"""
        if self.driver:
            self.driver.quit()
            logging.info("Firefox driver closed")
        logging.info(f"Spider closed. Total characters processed: {len(self.scraped_data)}") 
