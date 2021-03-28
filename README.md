# NBA_data_scraper
This repo leverages [Selenium](https://www.selenium.dev/) to scrape both players and team data
from [Basketball Reference](https://www.basketball-reference.com/).

### Getting Started:

Ensure you have [chromedriver](https://sites.google.com/a/chromium.org/chromedriver/downloads) installed corresponding
to and placed in your home directory.

Create your conda environment with the following:

 ```bash
cd ~/NBA_data_scraper/
chmod 777 setup.sh
./setup.sh
 ```

To scrape both team and player data for NBA games within a set date range, run the following:

```bash
cd ~/NBA_data_scraper/
python export_player_team_data.py --start_date '2021-03-01' --end_date '2021-03-31'
```

The `start_date` and `end_date` parameters defines the range to scrape NBA games from.