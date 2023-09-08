# Exploratory Analysis

All data was pulled from https://www.streetfighter.com/6/buckler/ranking/league. The live dashboard with the visualizations can be found here: https://public.tableau.com/app/profile/austin.domer5220/viz/SF6MasterAnalysis/SF6_Analysis. 
Details around the spider can be found below.

The initial randomly selected sample size for this analysis was 29890 profiles. At the time of data extraction (9.8.23 6:30 AM PST), the total number of master rank players was 57476. In the August patch, Master Rating (MR) as a system was introduced to provide elo rankings for characters within the Master league. Anyone who was in Master that hasn't played a game since that patch would flag with a MR of 0. From this random pull, there were a total of 2200 selected profiles that hadn't played a ranked game since the August patch. These profiles will be treated as null as they may not reflect the current state of the meta, and their prior character's data isn't available with this method of scraping. Removing these from the dataset, grants a final sample size of 27691. Using a confidence level of 95%, we get an expected margin of error of 0.42% for the results. At the time of writing this analysis, the Master rank is comprised of the top 1.9% of players across SF6's playerbase. Given all players in this sample are master rank, it's safe to assume they've played enough games to have a solid understanding of the game and their character.

For the pulled profiles, I only scraped the character data for their character with the highest MR value. This was done to prevent duplicate profiles from populating for people who had gotten >1 character to Master rank.

There were 3 primary visualizations that were constructed to provide additional insight into the breakout among masters players: an overall character distribution, a character distribution by MR range, and a character count by aggregate MR. The goal of this analysis will be to provide a high level overview for each of the visualizations and potential contributing factors to these outcomes.

## Overall Character Distribution

For this visualization the character cast was plotted on a square pie chart, with the character's name, total % of population, and actual # of population listed. Ken was the most picked character by a wide margin, coming in at 11.26% of the total population with JP following at 8.11% of the total population. Following JP the spread gets a bit tighter with the next 5 characters coming within +/- 1% of each other. With Random included, there are 20 selectable characters on the cast, so with even representation each character should in theory represent 5% of the total.

Ken's disproportionately large representation is likely attributed to a few factors. Ken's redesign of his kit/moveset resulted in a playstyle that is generally viewed as fun to play. He's a rush-down archetype with a lot of corner carry and side-switching which are viewed as very powerful tools in SF6 given how dangerous the corner is. The winner of Evo, the largest SF6 tourney that has taken place since the game's release, played Ken so it makes sense that this would be a strong character others would want to practice if they're a competitor. JP following suit as the 2nd most picked character also aligns with the general consensus that he is a strong character. JP is a new addition to the SF series with a very unique design. Being viewed as a strong character with a 'cool' design is a formula for success in the upper echelons of the ranks.

Random, Lily, and Dhalsim were the 3 lowest picked characters, all coming in at under 3% of the population. Random had only 0.03% of the population, which makes sense as this setting will randomly select a character for the player every battle. To consistently win and eventually hit Master rank, you would need to be able to consistently win with the majority of the cast. Lily is widely regarded as the weakest character in the cast, so her coming in at the 2nd least picked aligns with the general public's consensus of character status. Dhalsim being the 3rd least picked character is likely a result of his playstyle being so jarringly different from the rest of the cast. Dhalsim is far more 'floaty' to play and would require a greater amount of effort to master than an easier character like Ken.

## Character Distribution by Master Rating (MR) Range

For this visualization, the MR for each player were bucketed into one of the following ranges: 0-1000, 1001-1250, 1251-1500, 1501-1750, 1751-2000, 2000+. MR functions as an elo system within the Master rank to track where a player's overall skill may fall in relation to their peers. All players start at 1500 MR upon entering master rank and this rating is gained/lost as you win/lose and the awarded amounts are scaled in relation to the opponent. For example, if a 1500 MR player beats a 1670 MR player, they would gain far more MR than they would if the same player had beaten a 1370 MR player. 93.32% of the Master population fall within the 1251-1750 range. Anyone at 1750+ is generally considered a 'very strong' player and are likely your tournament contenders/winners.

The distributions here fall in line with the overall character distributions, with Ken and JP dominating the top 2 spots for each of the buckets. There's an interesting swap in the 2000+ bucket with Dee Jay falling out of top 5, and Chun Li claiming the #3 spot. The influence here may be similar to Ken's, with a Chun-Li placing in Top 8 at Evo, with 0 Dee Jay representation in the Top 8. Chun Li may have a higher skill ceiling leading to greater reward for mastery which explains this higher than normal representation in the top bracket.

## Character Count by Aggregate Master Rating (MR)

This visualization maps aggregate master rating by character against the total count of said character. The goal here was to identify if there were any trends and to possibly identify any characters that may have a higher than usual ratio of master rating to pick rate. The correlation here was actually extremely strong with most character counts falling directly on the peak of the aggregate master rating give or take a couple thousand rating points. The largest discrepancies appear to be between Zangief, Ryu, JP, and Chun-Li. JP and Chun-Li's intersection is below the aggregate rating, indicating that their players on average have more master rating than their counterparts, whereas Zangief and Ryu are the opposite. Both JP and Chun-Li are regarded as strong characters whereas Zangief and Ryu are regarded as weaker characters, so this falls in line with expectations.

Taking this a step further to build out a fraud index per character to indicate whether some characters have a higher likelihood of 'carrying' their player through the ranks would be an interesting next step.

# Street Fighter Spider

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

`main.py` is the main script that configures and starts a Scrapy process with the `StreetFighterSpider` spider.

`config.py` contains the logging configuration and the common settings for the spiders.

`spiders/street_fighter_spider.py` contains the `StreetFighterSpider` spider class.

`spiders/middlewares.py` contains two middleware classes: `RandomUserAgentMiddleware` and `RetryChangeProxyMiddleware`.

- `RandomUserAgentMiddleware` sets a random User-Agent for each request to help avoid getting blocked by the site.
- `RetryChangeProxyMiddleware` handles failed requests and retries them after adjusting the delay.

## How the Spider Works

This spider fetches player data and writes it into CSV files. It uses Selenium to handle pages that contain JavaScript and also implements retry logic and request delay adjustment based on consecutive failed requests.

Before the scraper can start, it will open Firefox and navigate to the Street Fighter site. You will need to log in manually, and then press Enter in your terminal to continue.

Please note that the scraper needs to be run from a command-line interface, like Terminal on MacOS or Command Prompt / PowerShell on Windows.

The spider works by first logging into the Street Fighter site and then navigating to different pages to collect player data.

For each rank in the game, it randomly samples pages and fetches player data. It continues sampling pages until it has collected at least 2500 valid samples (i.e., players with a certain number of ranked battles) for each rank.

Once it has collected enough samples for a rank, it writes the data to a CSV file and moves on to the next rank.

If the spider encounters an error while fetching a page, it retries the request with an exponential backoff delay. This helps to handle temporary issues like network errors or server overloads.

## Output

The spider writes the scraped data to CSV files. There is a separate file for each rank. The files are named like `output_{rank}.csv`, where `{rank}` is the rank of the players in the file.

Each row in the CSV files contains the following fields:

    Username: The player's username
    Rank: The player's rank
    Character: The character used by the player
    Ranked Battle Count: The total number of ranked battles played by the player
    Scaled Win Count: The win count of the player, scaled according to their win ratio and ranked battle count

## Limitations and Considerations

- The scraper is dependent on the structure of the web pages. If the site changes its layout or the way it delivers data, the scraper may stop working.
- The scraper uses a single-threaded model for fetching pages. Although it can handle a high number of requests, it may not be the most efficient method for large-scale scraping.
- The scraper does not use proxies to rotate IP addresses. If the site blocks your IP due to too many requests, you may need to wait a while before running the scraper again.

## How to Run

Before running, update the players_per_rank in the spider to reflect current numbers, check and/or change the user agents, and check/change the output file.

You can run the scraper from your terminal using the following command:

```shell
python main.py
```

## Disclaimer and Liability

Please be advised that this repository is provided for instructional and educational purposes only.

The data scraping practices demonstrated in this repository must be used responsibly and ethically. Always respect the terms of service of any website or online service you interact with. Be aware that improper use of data scraping techniques can violate the terms of service of some websites or even local laws and regulations.

Under no circumstances should the code be used for any illegal or unethical activities. The authors of this repository disclaim all liability for any damage, loss, or consequence caused directly or indirectly by the use or inability to use the information or code contained within this repository.

Please use this code responsibly and consider the potential impact on servers, respect privacy, and adhere to all relevant terms of service and laws. If you choose to use the code provided in this repository, you do so at your own risk.

## License

This project is licensed under the MIT License. This license does not include the right to use this code, or any derivative work thereof, for any illegal or unethical activities. By using or adapting this code, you agree to assume all liability and responsibility for your actions.
