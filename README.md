# Street Fighter 6 Data Analysis

An automated data collection system for Street Fighter 6 battle statistics and character usage data from the official Buckler's Boot Camp website.

## Features

- **Fighting Stats**: Scrapes character matchup data across all Master rank divisions
- **Usage Statistics**: Collects character usage rates and popularity trends
- **Historical Data**: Supports multiple months of data collection
- **Export Formats**: Clean CSV files for analysis

## Quick Start

### 1. Run Data Collection
```bash
# Run fighting stats scraper
python -c "from spiders.fighting_stats_spider import FightingStatsSpider; spider = FightingStatsSpider(); spider.setup_selenium(None)"

# Run usage statistics scraper  
python main.py
```

## Output Structure

Each scrape run creates a timestamped folder:

```
output/
├── master_data19Jul2025/                 # July 19, 2025 scrape
│   ├── fighting_stats_022025.csv        # Fighting stats (Feb 2025)
│   ├── fighting_stats_032025.csv        # Fighting stats (Mar 2025)
│   ├── master_usage_stats_022025.csv    # Usage stats (Feb 2025)
│   ├── master_usage_stats_032025.csv    # Usage stats (Mar 2025)
│   └── *_all_months.csv                 # Combined data files
├── master_data14Aug2025/                 # August 14, 2025 scrape
│   ├── fighting_stats_022025.csv        # (Updated data)
│   └── ...
└── master_data11Sep2025/                 # September 11, 2025 scrape
    └── ...
```

### Data Format
**Fighting Stats CSV:**
```csv
character_name,month,league,row_type,value,row_index,column_index,source
E. HONDA,022025,Master,E. HONDA,-,2,3,tabular_extraction
KIMBERLY,022025,Master,E. HONDA,5.288,2,4,tabular_extraction
```

**Usage Statistics CSV:**
```csv
rank,character_name,usage_percentage,change_rate,month,league
1,KEN,5.855%,-2.0%,02/2025,Master
```

## Street Fighter Spider

Street Fighter Spider is a Python web scraper based on Scrapy that scrapes the Street Fighter gaming site for player data. It uses Selenium for dealing with JavaScript and to control the flow of the application.

### Requirements

This project requires Python 3.7+ and the following Python libraries installed:

- Scrapy
- Selenium
- json
- csv
- collections
- logging

You will also need to have Firefox installed on your machine, as the project uses the Firefox webdriver for Selenium.

## Project Structure

The project consists of several Python files organized into the following structure:

- `main.py`
- `config.py`
- `spiders/street_fighter_spider.py`
- `spiders/middlewares.py`
-`spiders/fighting_stats_spider.py`

`main.py` is the main script that configures and starts a Scrapy process with both the `StreetFighterSpider` and the `FightingStatsSpider` spiders.

`config.py` contains the logging configuration and the common settings for the spiders.

`spiders/street_fighter_spider.py` contains the `StreetFighterSpider` spider class.

`spiders/fighting_stats_spider.py` contains the `FightingStatsSpider` spider class.

`spiders/middlewares.py` contains two middleware classes: `RandomUserAgentMiddleware` and `RetryChangeProxyMiddleware`.

- `RandomUserAgentMiddleware` sets a random User-Agent for each request to help avoid getting blocked by the site.
- `RetryChangeProxyMiddleware` handles failed requests and retries them after adjusting the delay.

## How the Spider Works

This spider fetches player data and writes it into CSV files. It uses Selenium to handle pages that contain JavaScript and also implements retry logic and request delay adjustment based on consecutive failed requests.

Before the scraper can start, it will open Firefox and navigate to the Street Fighter site.

Please note that the scraper needs to be run from a command-line interface, like Terminal on MacOS or Command Prompt / PowerShell on Windows.

The spider works by navigating to different pages to collect player data.

## Limitations and Considerations

- The scraper is dependent on the structure of the web pages. If the site changes its layout or the way it delivers data, the scraper may stop working.
- The scraper uses a single-threaded model for fetching pages. Although it can handle a high number of requests, it may not be the most efficient method for large-scale scraping.
- The scraper does not use proxies to rotate IP addresses. If the site blocks your IP due to too many requests, you may need to wait a while before running the scraper again.

## Disclaimer and Liability

Please be advised that this repository is provided for instructional and educational purposes only.

The data scraping practices demonstrated in this repository must be used responsibly and ethically. Always respect the terms of service of any website or online service you interact with. Be aware that improper use of data scraping techniques can violate the terms of service of some websites or even local laws and regulations.

Under no circumstances should the code be used for any illegal or unethical activities. The authors of this repository disclaim all liability for any damage, loss, or consequence caused directly or indirectly by the use or inability to use the information or code contained within this repository.

Please use this code responsibly and consider the potential impact on servers, respect privacy, and adhere to all relevant terms of service and laws. If you choose to use the code provided in this repository, you do so at your own risk.

## License

This project is licensed under the MIT License. This license does not include the right to use this code, or any derivative work thereof, for any illegal or unethical activities. By using or adapting this code, you agree to assume all liability and responsibility for your actions.
