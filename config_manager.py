#!/usr/bin/env python3
"""
Configuration manager for SF6 Analysis project
Handles loading configuration from files and environment variables
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple

class ConfigManager:
    """Manages configuration loading with fallbacks"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or self._find_config_file()
        self.config = self._load_config()
        
    def _find_config_file(self) -> str:
        """Find configuration file in order of preference"""
        search_paths = [
            os.environ.get('SF6_CONFIG_FILE'),
            './config.json',
            './personal_config.json',
            './config.example.json'
        ]
        
        for path in search_paths:
            if path and os.path.exists(path):
                return path
                
        # If no config found, create from example
        if os.path.exists('./config.example.json'):
            import shutil
            shutil.copy('./config.example.json', './config.json')
            return './config.json'
            
        raise FileNotFoundError("No configuration file found")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file with environment variable overrides"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logging.warning(f"Could not load config file {self.config_file}: {e}")
            config = self._get_default_config()
        
        # Override with environment variables if present
        self._apply_env_overrides(config)
        return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration fallback"""
        return {
            "spider_settings": {
                "base_delay": 1.0,
                "max_delay": 3.0,
                "concurrent_requests": 1,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"
            },
            "output": {
                "data_directory": "./output",
                "file_prefix": {
                    "fighting_stats": "fighting_stats",
                    "usage_stats": "master_usage_stats"
                }
            },
            "selenium": {
                "window_width": 1920,
                "window_height": 1080,
                "page_load_timeout": 20,
                "element_wait_timeout": 10
            },
            "urls": {
                "fighting_stats_base": "https://www.streetfighter.com/6/buckler/stats/dia_master",
                "usage_stats_base": "https://www.streetfighter.com/6/buckler/stats/usagerate_master"
            }
        }
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> None:
        """Apply environment variable overrides"""
        env_mappings = {
            'SF6_OUTPUT_DIR': ('output', 'data_directory'),
            'SF6_BASE_DELAY': ('spider_settings', 'base_delay'),
            'SF6_MAX_DELAY': ('spider_settings', 'max_delay'),
            'SF6_WINDOW_WIDTH': ('selenium', 'window_width'),
            'SF6_WINDOW_HEIGHT': ('selenium', 'window_height'),
            'SF6_USER_AGENT': ('spider_settings', 'user_agent')
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.environ.get(env_var)
            if value:
                if section not in config:
                    config[section] = {}
                # Try to convert to appropriate type
                try:
                    if key in ['base_delay', 'max_delay']:
                        config[section][key] = float(value)
                    elif key in ['window_width', 'window_height', 'concurrent_requests']:
                        config[section][key] = int(value)
                    else:
                        config[section][key] = value
                except ValueError:
                    config[section][key] = value
    
    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """Get configuration value"""
        if key is None:
            return self.config.get(section, default)
        return self.config.get(section, {}).get(key, default)
    
    def get_output_dir(self) -> str:
        """Get output directory, creating if needed"""
        output_dir = self.get('output', 'data_directory', './output')
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    def get_timestamped_output_dir(self) -> str:
        """Get timestamped output directory with format master_dataDDMonYYYY"""
        now = datetime.now()
        # Format: master_data19Jul2025
        folder_name = now.strftime("master_data%d%b%Y")
        
        base_output_dir = self.get('output', 'data_directory', './output')
        timestamped_dir = os.path.join(base_output_dir, folder_name)
        os.makedirs(timestamped_dir, exist_ok=True)
        return timestamped_dir
    
    def get_months_to_scrape(self) -> List[Tuple[str, str]]:
        """Get list of months to scrape"""
        months_config = self.get('scraping', 'months_to_scrape')
        if months_config:
            return [(m['code'], m['name']) for m in months_config]
        
        # Fallback to default months
        return [
            ("202502", "022025"),
            ("202503", "032025"), 
            ("202504", "042025"),
            ("202505", "052025"),
            ("202506", "062025")
        ]
    
    def get_leagues_to_scrape(self) -> List[Tuple[int, str]]:
        """Get list of leagues to scrape"""
        leagues_config = self.get('scraping', 'leagues')
        if leagues_config:
            return [(l['index'], l['name']) for l in leagues_config]
        
        # Fallback to default leagues
        return [
            (1, "Master"),
            (2, "High Master"),
            (3, "Grand Master"),
            (4, "Ultimate Master")
        ]

# Global config instance
_config_instance = None

def get_config() -> ConfigManager:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance