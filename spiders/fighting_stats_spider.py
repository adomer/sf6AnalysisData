import scrapy
import json
import csv
import os
import re
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging

class FightingStatsSpider(scrapy.Spider):
    name = 'fighting_stats'
    allowed_domains = ['streetfighter.com']
    start_urls = ['https://www.streetfighter.com/6/buckler/stats/dia_master']
    
    def __init__(self):
        self.driver = None
        self.base_url = "https://www.streetfighter.com/6/buckler/stats/dia_master"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('fighting_stats_debug.log'),
                logging.StreamHandler()
            ]
        )
        self.custom_logger = logging.getLogger(__name__)
        
    def start_requests(self):
        yield scrapy.Request(
            url=self.start_urls[0],
            callback=self.setup_selenium,
            dont_filter=True
        )
    
    def setup_selenium(self, response):
        self.custom_logger.info("Setting up Selenium WebDriver")
        
        firefox_options = Options()
        firefox_options.add_argument("--width=1920")
        firefox_options.add_argument("--height=1080")
        
        try:
            self.driver = webdriver.Firefox(options=firefox_options)
            self.driver.get(self.start_urls[0])
            
            # Wait for page to load
            time.sleep(3.0)
            
            self.custom_logger.info("Page loaded, proceeding with scraping...")
            return self.scrape_all_months()
            
        except Exception as e:
            self.custom_logger.error(f"Error setting up Selenium: {str(e)}")
            if self.driver:
                self.driver.quit()
            return []
    
    def discover_available_months(self):
        """Discover available months from the page"""
        try:
            month_selector_xpath = "/html/body/div/div/article[2]/aside[1]/div/section"
            month_elements = self.driver.find_elements(By.XPATH, f"{month_selector_xpath}/*")
            
            months = []
            for i, element in enumerate(month_elements):
                try:
                    month_text = element.text.strip()
                    if month_text and '/' in month_text:
                        # Split by newlines in case multiple months are in one element
                        month_lines = [line.strip() for line in month_text.split('\n') if line.strip() and '/' in line]
                        
                        for month_line in month_lines:
                            self.custom_logger.info(f"Found month option: {month_line}")
                            months.append({
                                'index': len(months),
                                'text': month_line,
                                'url_format': month_line.replace('/', '')
                            })
                except Exception as e:
                    self.custom_logger.warning(f"Error processing month element {i}: {str(e)}")
                    continue
            
            self.custom_logger.info(f"Discovered {len(months)} month options: {[m['text'] for m in months]}")
            return months
            
        except Exception as e:
            self.custom_logger.error(f"Error discovering months: {str(e)}")
            return []
    
    def scrape_all_months(self):
        """Scrape data from multiple months using correct YYYYMM URL format"""
        self.custom_logger.info("Scraping from multiple months with correct URL format")
        
        all_data = []
        
        # Define months to scrape (YYYYMM format) - All available months
        months_to_scrape = [
            ("202502", "02/2025"),
            ("202503", "03/2025"),
            ("202504", "04/2025"),
            ("202505", "05/2025"),
            ("202506", "06/2025")
        ]
        
        # Define leagues to scrape (matching street_fighter_spider)
        leagues_to_scrape = [
            (1, "Master"),
            (2, "High Master"),
            (3, "Grand Master"),
            (4, "Ultimate Master")
        ]
        
        for month_code, month_name in months_to_scrape:
            try:
                self.custom_logger.info(f"Scraping {month_name}")
                
                # Construct URL with correct YYYYMM format
                month_url = f"{self.base_url}/{month_code}"
                self.custom_logger.info(f"Navigating to: {month_url}")
                
                # Navigate to the month-specific URL
                self.driver.get(month_url)
                time.sleep(5)  # Wait for page to load
                
                # Skip cookie dialog handling as it's not working properly
                
                # Check that we're on the right page
                current_url = self.driver.current_url
                self.custom_logger.info(f"Current URL after navigation: {current_url}")
                
                # Scrape all leagues for this month
                for league_index, league_name in leagues_to_scrape:
                    try:
                        self.custom_logger.info(f"Scraping {league_name} for {month_name}")
                        
                        # Click on the league selection
                        self.select_league(league_index, league_name)
                        
                        # Parse data from this month and league
                        month_league_data = self.parse_fighting_stats_data(month_name, league_name)
                        all_data.extend(month_league_data)
                        
                        self.custom_logger.info(f"Extracted {len(month_league_data)} entries from {month_name} {league_name}")
                        
                    except Exception as e:
                        self.custom_logger.error(f"Error scraping {league_name} for {month_name}: {str(e)}")
                        continue
                
            except Exception as e:
                self.custom_logger.error(f"Error scraping {month_name}: {str(e)}")
                continue
        
        # Write CSV files
        self.write_csv_files(all_data)
        
        if self.driver:
            self.driver.quit()
        
        return all_data
    
    def dismiss_cookie_dialog(self):
        """Dismiss cookie dialog if present"""
        try:
            # Look for cookie dialog and dismiss it
            cookie_selectors = [
                "//button[contains(@class, 'CybotCookiebot')]",
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'OK')]",
                "//div[@id='CybotCookiebotDialog']//button",
                "//*[contains(@class, 'cookie')]//button"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = self.driver.find_element(By.XPATH, selector)
                    if cookie_button.is_displayed():
                        cookie_button.click()
                        self.custom_logger.info(f"Dismissed cookie dialog using selector: {selector}")
                        time.sleep(2)
                        return True
                except:
                    continue
            
            self.custom_logger.info("No cookie dialog found or already dismissed")
            return True
            
        except Exception as e:
            self.custom_logger.warning(f"Error handling cookie dialog: {str(e)}")
            return False

    def select_league(self, league_index, league_name):
        """Select a specific league from the aside navigation"""
        try:
            # Wait for the league selection area to be present
            aside_xpath = "/html/body/div/div/article[2]/aside[2]"
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, aside_xpath))
            )
            
            # Click on the specific league li element
            league_li_xpath = f"/html/body/div/div/article[2]/aside[2]/ul/li[{league_index}]"
            self.custom_logger.info(f"Clicking on league: {league_name} (li[{league_index}])")
            
            # Scroll to element to ensure it's visible
            league_element = self.driver.find_element(By.XPATH, league_li_xpath)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", league_element)
            time.sleep(1)
            
            # Try to click the element, use JavaScript if normal click fails
            try:
                league_element.click()
            except Exception as click_error:
                self.custom_logger.warning(f"Normal click failed, trying JavaScript click: {click_error}")
                self.driver.execute_script("arguments[0].click();", league_element)
            
            # Wait for the table to update after league selection
            time.sleep(3)
            
            self.custom_logger.info(f"Successfully selected {league_name}")
            
        except Exception as e:
            self.custom_logger.error(f"Error selecting league {league_name}: {str(e)}")
            raise
    
    def scroll_to_load_full_table(self):
        """Scroll both horizontally and vertically through the table to ensure all content is loaded"""
        try:
            self.custom_logger.info("Scrolling to load full table content (both horizontal and vertical)...")
            
            # Get the table element
            table_xpath = "//*[@id='tableArea']/div[1]/table[1]"
            table = self.driver.find_element(By.XPATH, table_xpath)
            
            # Get table dimensions
            table_width = self.driver.execute_script("return arguments[0].scrollWidth;", table)
            table_height = self.driver.execute_script("return arguments[0].scrollHeight;", table)
            viewport_width = self.driver.execute_script("return window.innerWidth;")
            viewport_height = self.driver.execute_script("return window.innerHeight;")
            
            self.custom_logger.info(f"Table dimensions: {table_width}x{table_height}, Viewport: {viewport_width}x{viewport_height}")
            
            # First, scroll vertically to ensure we're positioned at the table
            self.custom_logger.info("Scrolling vertically to position table properly...")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", table)
            time.sleep(0.5)
            
            # Vertical scrolling through the table to load all rows
            self.driver.execute_script("arguments[0].scrollIntoView(false);", table)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", table)
            time.sleep(0.5)
            
            # Now drag the table horizontally to load all content
            self.custom_logger.info("Dragging table horizontally to load all character columns...")
            
            # Import ActionChains for drag operations
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            
            # Calculate how much we need to reveal (hidden content)
            hidden_content = table_width - viewport_width
            self.custom_logger.info(f"Hidden content width: {hidden_content}px")
            
            # Use single larger drag to cover the full table width with headroom
            drag_distance = 850  # Cover full 751px width plus extra headroom
            
            self.custom_logger.info(f"Performing single drag of {drag_distance}px to cover full table")
            
            # Single drag left to reveal all content
            try:
                actions.move_to_element(table).click_and_hold().move_by_offset(-drag_distance, 0).release().perform()
                time.sleep(0.5)
                self.custom_logger.info("Completed single drag (leftward to show all characters)")
            except Exception as drag_error:
                self.custom_logger.warning(f"Single drag failed: {drag_error}")
            
            # Give time for content to fully load
            time.sleep(1)
            
            # Now position back to the very beginning to see early characters
            self.custom_logger.info("Positioning back to beginning to show early characters...")
            try:
                # Drag far right to show the early characters (reduced offset to stay within viewport)
                actions.move_to_element(table).click_and_hold().move_by_offset(750, 0).release().perform()
                time.sleep(0.5)
                self.custom_logger.info("Positioned at beginning - early characters should now be visible")
            except Exception as position_error:
                self.custom_logger.warning(f"Positioning to beginning failed: {position_error}")
            
            # Try JavaScript scrollLeft as backup to ensure proper positioning
            self.custom_logger.info("Using JavaScript scroll to ensure proper positioning...")
            try:
                self.driver.execute_script("arguments[0].scrollLeft = 0;", table)
                time.sleep(0.5)
            except Exception as js_error:
                self.custom_logger.warning(f"JavaScript scroll backup failed: {js_error}")
            
            self.custom_logger.info("Completed table dragging and positioning for extraction")
            
            self.custom_logger.info("Completed full table scrolling (horizontal and vertical)")
            
        except Exception as e:
            self.custom_logger.warning(f"Error during table scrolling: {str(e)}")
            # Continue with extraction even if scrolling fails
    
    def parse_fighting_stats_data(self, month, league="Master"):
        """Parse the tabular fighting stats data using two-pass approach"""
        try:
            # Wait for table to load with longer timeout - using correct table ID
            table_xpath = "//*[@id='tableArea']/div[1]/table[1]"
            self.custom_logger.info(f"Waiting for table to load: {table_xpath}")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, table_xpath))
            )
            self.custom_logger.info("Table found, proceeding with two-pass data extraction")
            
            # Initial setup - ensure we're positioned at the beginning
            table = self.driver.find_element(By.XPATH, table_xpath)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", table)
            self.driver.execute_script("arguments[0].scrollLeft = 0;", table)
            time.sleep(1)
            
            # Extract character names from header images
            character_names = self.extract_character_names()
            self.custom_logger.info(f"Found {len(character_names)} characters: {character_names}")
            
            # FIRST PASS: Extract from initial position (early characters)
            self.custom_logger.info("FIRST PASS: Extracting early characters from initial position")
            first_pass_data = self.extract_table_data(table_xpath, character_names, month, league, "first_pass")
            
            # Drag right to reveal late characters
            self.custom_logger.info("Dragging right to reveal late characters...")
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            try:
                actions.move_to_element(table).click_and_hold().move_by_offset(-850, 0).release().perform()
                time.sleep(1)
                self.custom_logger.info("Successfully dragged to show late characters")
            except Exception as drag_error:
                self.custom_logger.warning(f"Drag failed: {drag_error}")
            
            # SECOND PASS: Extract from shifted position (late characters)
            self.custom_logger.info("SECOND PASS: Extracting late characters from shifted position")
            second_pass_data = self.extract_table_data(table_xpath, character_names, month, league, "second_pass")
            
            # Combine and deduplicate data
            combined_data = self.deduplicate_table_data(first_pass_data + second_pass_data)
            
            self.custom_logger.info(f"Successfully extracted {len(combined_data)} data points for {month} (after deduplication)")
            return combined_data
            
        except Exception as e:
            self.custom_logger.error(f"Error parsing fighting stats data for {month}: {str(e)}")
            # Try alternative approach if main table xpath fails
            try:
                self.custom_logger.info("Attempting alternative table detection...")
                all_tables = self.driver.find_elements(By.TAG_NAME, "table")
                self.custom_logger.info(f"Found {len(all_tables)} tables on page")
                return []
            except:
                pass
            return []
    
    def extract_table_data(self, table_xpath, character_names, month, league, pass_name):
        """Extract data from table at current position"""
        try:
            data = []
            table = self.driver.find_element(By.XPATH, table_xpath)
            tbody = table.find_element(By.TAG_NAME, "tbody")
            rows = tbody.find_elements(By.TAG_NAME, "tr")
            
            self.custom_logger.info(f"{pass_name}: Found {len(rows)} rows in table body")
            
            for row_index, row in enumerate(rows):
                try:
                    # Get the row character name from the character order
                    if row_index < len(character_names):
                        row_character = character_names[row_index].upper()
                    else:
                        row_character = f"ROW_{row_index + 1}"
                    
                    # Get all td elements for this row
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    # Extract data for each character
                    for cell_index, cell in enumerate(cells):
                        cell_value = cell.text.strip()
                        
                        if cell_index == 0:
                            # First column is the character's total stats
                            data.append({
                                'character_name': 'TOTAL',
                                'month': month,
                                'league': league,
                                'row_type': row_character,
                                'value': cell_value,
                                'row_index': row_index + 1,
                                'column_index': cell_index + 1,
                                'source': f'tabular_extraction_{pass_name}'
                            })
                        else:
                            # Matchup columns start at index 1
                            matchup_index = cell_index - 1
                            if matchup_index < len(character_names):
                                column_character = character_names[matchup_index]
                                
                                data.append({
                                    'character_name': column_character.upper(),
                                    'month': month,
                                    'league': league,
                                    'row_type': row_character,
                                    'value': cell_value,
                                    'row_index': row_index + 1,
                                    'column_index': cell_index + 1,
                                    'source': f'tabular_extraction_{pass_name}'
                                })
                    
                    # Log sample for first row
                    if row_index == 0 and len(cells) > 0:
                        self.custom_logger.info(f"{pass_name} - First row sample - {row_character}: {cells[0].text[:50]}...")
                
                except Exception as e:
                    self.custom_logger.warning(f"{pass_name}: Error processing row {row_index}: {str(e)}")
                    continue
            
            self.custom_logger.info(f"{pass_name}: Extracted {len(data)} data points")
            return data
            
        except Exception as e:
            self.custom_logger.error(f"{pass_name}: Error extracting table data: {str(e)}")
            return []
    
    def deduplicate_table_data(self, combined_data):
        """Remove duplicate entries and keep the one with non-empty value"""
        try:
            # Create a dictionary to track unique entries
            unique_data = {}
            
            for entry in combined_data:
                # Create unique key based on character_name, row_type, column_index
                key = (entry['character_name'], entry['row_type'], entry['column_index'])
                
                # If this is the first occurrence or current entry has value while stored doesn't
                if key not in unique_data:
                    unique_data[key] = entry
                elif entry['value'] and (not unique_data[key]['value'] or unique_data[key]['value'] in ['', '-']):
                    # Prefer entries with actual values
                    unique_data[key] = entry
            
            # Convert back to list and update source to indicate deduplication
            deduplicated_data = []
            for entry in unique_data.values():
                entry['source'] = 'tabular_extraction_deduplicated'
                deduplicated_data.append(entry)
            
            self.custom_logger.info(f"Deduplication: {len(combined_data)} -> {len(deduplicated_data)} entries")
            return deduplicated_data
            
        except Exception as e:
            self.custom_logger.error(f"Error deduplicating data: {str(e)}")
            return combined_data  # Return original data if deduplication fails
    
    def extract_character_names(self):
        """Extract character names from row header span elements"""
        character_names = []
        
        try:
            # Use the correct table path
            table_xpath = "//*[@id='tableArea']/div[1]/table[1]"
            table = self.driver.find_element(By.XPATH, table_xpath)
            
            # Ensure we scroll through table to load all rows before extraction
            self.custom_logger.info("Ensuring table is fully loaded before character extraction...")
            self.scroll_to_load_full_table()
            
            # Look for character names in row headers - specifically in th/div/span[1] elements
            tbody = table.find_element(By.TAG_NAME, "tbody")
            rows = tbody.find_elements(By.TAG_NAME, "tr")
            self.custom_logger.info(f"Found {len(rows)} rows for character extraction")
            
            for i, row in enumerate(rows):
                try:
                    # Look for th/div/span[1] in each row without individual scrolling
                    span_xpath = ".//th/div/span[1]"
                    span_element = row.find_element(By.XPATH, span_xpath)
                    character_name = span_element.text.strip().lower()
                    
                    if character_name:
                        character_names.append(character_name)
                        if i < 5 or i % 5 == 0:  # Only log every 5th character to reduce output
                            self.custom_logger.info(f"Row {i+1}: Found character '{character_name}'")
                
                except Exception as e:
                    self.custom_logger.warning(f"Error extracting character from row {i+1}: {str(e)}")
                    continue
            
            # If we found characters but not all expected ones, log the difference
            expected_count = 26  # Total expected SF6 characters
            if character_names and len(character_names) < expected_count:
                self.custom_logger.warning(f"Only found {len(character_names)} characters, expected {expected_count}")
                self.custom_logger.info(f"Found characters: {character_names}")
            
            # If no characters found from span elements, use the verified character order as fallback
            if not character_names:
                self.custom_logger.warning("No characters found from span elements, using verified character order")
                # This is the actual character order from the fighting stats website span elements
                # Both rows and columns follow this same order
                character_names = [
                    "elena", "e. honda", "dhalsim", "kimberly", "jp", "dee jay", "terry", "luke", 
                    "marisa", "blanka", "lily", "a.k.i.", "chun-li", "m. bison", "rashid", "jamie", 
                    "guile", "juri", "ken", "ryu", "cammy", "mai", "manon", "ed", "akuma", "zangief"
                ]
                self.custom_logger.info(f"Using verified character order with {len(character_names)} characters")
        
        except Exception as e:
            self.custom_logger.error(f"Error extracting character names: {str(e)}")
            # Return fallback character list
            character_names = [
                "elena", "e. honda", "dhalsim", "kimberly", "jp", "dee jay", "terry", "luke", 
                "marisa", "blanka", "lily", "a.k.i.", "chun-li", "m. bison", "rashid", "jamie", 
                "guile", "juri", "ken", "ryu", "cammy", "mai", "manon", "ed", "akuma", "zangief"
            ]
            self.custom_logger.info(f"Using fallback character order with {len(character_names)} characters")
        
        return character_names
    
    def write_csv_files(self, all_data):
        """Write data to CSV files"""
        if not all_data:
            self.custom_logger.warning("No data to write")
            return
        
        # Group data by month only (all leagues combined per month)
        months_data = {}
        for item in all_data:
            month = item['month']
            if month not in months_data:
                months_data[month] = []
            months_data[month].append(item)
        
        # Write individual month files (containing all leagues)
        for month, month_data in months_data.items():
            month_clean = month.replace('/', '')
            
            # Use config manager for timestamped output directory
            from config_manager import get_config
            config = get_config()
            output_dir = config.get_timestamped_output_dir()
            filename = os.path.join(output_dir, f"fighting_stats_{month_clean}.csv")
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                if month_data:
                    fieldnames = month_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(month_data)
            
            # Count entries per league for logging
            league_counts = {}
            for item in month_data:
                league = item['league']
                league_counts[league] = league_counts.get(league, 0) + 1
            
            league_summary = ", ".join([f"{league}: {count}" for league, count in league_counts.items()])
            self.custom_logger.info(f"Written {len(month_data)} total entries to {filename} ({league_summary})")
        
        # Write combined file
        from config_manager import get_config
        config = get_config()
        output_dir = config.get_timestamped_output_dir()
        combined_filename = os.path.join(output_dir, "fighting_stats_all_months.csv")
        with open(combined_filename, 'w', newline='', encoding='utf-8') as csvfile:
            if all_data:
                fieldnames = all_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_data)
        
        self.custom_logger.info(f"Written {len(all_data)} total entries to {combined_filename}")
    
    def closed(self, reason):
        if self.driver:
            self.driver.quit()
        self.custom_logger.info(f"Spider closed: {reason}")