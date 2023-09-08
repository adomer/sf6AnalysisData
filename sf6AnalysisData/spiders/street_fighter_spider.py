import logging
import random
import json
import csv
from collections import defaultdict
import scrapy
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from spiders.middlewares import RetryChangeProxyMiddleware, RandomUserAgentMiddleware
from config import COMMON_SPIDER_SETTINGS
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())

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

    # Data as of 7.15.23 (from stellaskyler)
    # {'m': 13978, 'd': 56252, 'p': 266185, 'g': 229197, 's': 282945, 'b': 205462, 'i': 209900}
    
    # Data as of 8.30.23 8 PM PST 
    # {'m': 51004, 'd': 124914, 'p': 448636, 'g': 327783, 's': 375164, 'b': 257380, 'i': 254701}

    # Data as of 9.5.23 12 PM PST
    # players_per_rank = {'m': 55779, 'd': 131548, 'p': 461286, 'g': 334709, 's': 382729, 'b': 260837, 'i': 258157}
   

    # Data as of 9.7.23 5:30 PM PST
    players_per_rank = {'m': 57476 }
    pages_per_rank = {}
    current_page = 0

    for rank in players_per_rank:
        start_page = current_page + 1
        end_page = current_page + players_per_rank[rank] // 20
        pages_per_rank[rank] = (start_page, end_page)
        current_page = end_page

    sampled_pages_per_rank = {rank: set() for rank in players_per_rank}
    valid_samples_per_rank = defaultdict(list)
    rank_flags = {rank: False for rank in players_per_rank}  # Flag to track if 2500 valid samples are reached for each rank

    def __init__(self):
        options = Options()
        self.driver = webdriver.Firefox(options=options)
        self.consecutive_errors = 0  # Keep track of consecutive errors

    def adjust_delay(self):
        # Calculate exponential backoff
        delay = min(0.5 * (2 ** self.consecutive_errors), 60)
        # Add jitter: random value between 0 and delay
        jitter = random.uniform(0, delay)
        self.custom_settings['DOWNLOAD_DELAY'] = delay + jitter

    def start_requests(self):
        self.driver.get("https://www.streetfighter.com/6/buckler")
        input("Press Enter after you've logged in manually...")
        cookies = self.driver.get_cookies()
        cookies_dict = {c['name']: c['value'] for c in cookies}  # Convert cookies into dict
        for rank in self.players_per_rank:
            yield from self.request_rank_pages(rank, cookies_dict)  # Pass cookies dict


    # min sample size based on a 57.5K pop size @ 95% confidence with a 2% margin of error is 2305. Will be rounding up to 2500.
    def request_rank_pages(self, rank, cookies):
        start_page, end_page = self.pages_per_rank[rank]
        while len(self.valid_samples_per_rank[rank]) < 2500 and len(self.sampled_pages_per_rank[rank]) < (
                end_page - start_page + 1):
            if self.rank_flags[rank]:
                # If the flag is True, indicating the threshold is reached, stop processing for the current rank
                logging.info(f"Threshold reached for rank {rank}. Skipping remaining pages.")
                return

            page = random.randint(start_page, end_page)
            if page not in self.sampled_pages_per_rank[rank]:
                self.sampled_pages_per_rank[rank].add(page)
                url = f"https://www.streetfighter.com/6/buckler/ranking/league?character_filter=1&character_id=luke&platform=1&user_status=1&home_filter=1&home_category_id=0&home_id=1&league_rank=36&page={page}"
                yield scrapy.Request(url, cookies=cookies, callback=self.parse_page,
                                     headers={'Referer': None},
                                     cb_kwargs={'rank': rank, 'page': page, 'cookies': cookies})

    def parse_page(self, response, rank, page, cookies):
        try:
            json_data = json.loads(response.css('script#__NEXT_DATA__::text').get())
            if 'league_point_ranking' not in json_data['props']['pageProps']:
                self.consecutive_errors += 1  # Increment the error count
                self.adjust_delay()  # Adjust the delay based on the error count
                print(f"No 'league_point_ranking' data found on page {page} for rank {rank}. Skipping to the next page.")
                return
            self.consecutive_errors = 0  # Reset the error count if the page is successfully parsed
            ranking_fighter_list = json_data['props']['pageProps']['league_point_ranking']['ranking_fighter_list']
            for fighter in ranking_fighter_list:
                username = fighter['fighter_banner_info']['personal_info']['short_id']
                character = fighter['character_name']
                url = f"https://www.streetfighter.com/6/buckler/profile/{username}/play"
                yield scrapy.Request(url, cookies=cookies, callback=self.parse,
                                     headers={'Referer': None},
                                     cb_kwargs={"username": username, "rank": rank, "character": character})
            logging.info(f"Parsed page {page} for rank {rank}.")
        except Exception as e:
            logging.error(f"Failed to parse page data for page {page} in rank {rank}: {e}")
            yield scrapy.Request(response.url, dont_filter=True,
                                 cb_kwargs={'rank': rank, 'page': page, 'cookies': cookies})

    def parse(self, response, username, rank, character):
        try:
            script_tag = response.css('script#__NEXT_DATA__::text').get()
            if script_tag is not None:
                json_data = json.loads(script_tag)
                # commenting out - not relevant for this analysis
                # characters_data = json_data['props']['pageProps']['play']['character_win_rates']
                # added to query for master rating
                character_league_infos = json_data['props']['pageProps']['play']['character_league_infos']
                # commenting out - not relevant for this analysis
                # total_battle_stats = json_data['props']['pageProps']['play']['battle_stats']

                # commenting out - not relevant for this analysis
                # ranked_battle_count = total_battle_stats['rank_match_play_count']
                
                # commenting out - not relevant for this analysis
                # character_data = next(
                #     (data for data in characters_data if data['character_name'].lower() == character.lower()), None)

                # initialize variable looking at max rating value across characters
                masters_data = max(character_league_infos, key=lambda x:x['league_info']['master_rating'])

                # commenting out - not relevant for this analysis
                # if character_data is not None and ranked_battle_count >= 90:
                #     if character_data['battle_count'] != 0:
                #         win_ratio = character_data['win_count'] / character_data['battle_count']
                #         scaled_win_count = win_ratio * ranked_battle_count
                #     else:
                #         win_ratio = 0
                #         scaled_win_count = 0

                    # added desired json outputs, removed mention of win #'s and rank
                self.valid_samples_per_rank[rank].append(
                    [username, masters_data['league_info']['master_rating'], masters_data['character_name']])
                logging.info(f"{rank}: {len(self.valid_samples_per_rank[rank])}/{2500}")
                if len(self.valid_samples_per_rank[rank]) >= 2500:
                        self.write_to_csv(rank)
                        self.valid_samples_per_rank[rank] = []  # Reset the samples for the rank
                        self.rank_flags[rank] = True  # Set the flag to True for the rank

                if all(self.rank_flags.values()):
                        # If all rank flags are True, indicating all ranks have reached the threshold, close the spider
                        self.crawler.engine.close_spider(self, "All ranks have reached the threshold")

            logging.info(f"Parsed profile data for user {username}.")
        except Exception as e:
            logging.error(f"Failed to parse profile data for user {username}: {e}")
            yield scrapy.Request(response.url, dont_filter=True,
                                 cb_kwargs={"username": username, "rank": rank, "character": character})

    def write_to_csv(self, rank):
        filename = f"output_{rank}.csv"
        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            samples = self.valid_samples_per_rank[rank]
            for sample in samples:
                writer.writerow(sample)

    def close_spider(self, spider):
        for rank in self.valid_samples_per_rank:
            if len(self.valid_samples_per_rank[rank]) > 0:
                self.write_to_csv(rank) 
