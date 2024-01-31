""" Core module for NBA Data Scraper """

from bs4 import BeautifulSoup
from bs4 import element
import pandas as pd
import numpy as np
import time
from typing import Dict, List, Tuple
import yaml
import os
import sys
from pathlib import Path
from datetime import date, timedelta, datetime
from .helpers import load_yaml_file, ensure_dir_exists, get_soup, get_game_urls, get_game_table, get_player_stats, create_player_boxscore, get_team_stats, create_team_boxscore

bball_ref_url = 'https://www.basketball-reference.com'
default_source = 'basketball_references'
alternative_sources = ['espn', 'nba']

class NBA_scraper:
    
    """NBA_scraper class
    
    This class holds methods of scraping both player and team level data from select sources (Basketball 
    References will be used by default)
        
    Parameters
    ----------
    data_source: str
    source in which the scraper will be attaining data from - by defaul this will be basketball references
    other options (not yet available) will be ESPN / NBA.com

    Side Effects
    ----------
    Initializes the scrape_source, start_date, end_date
    """
    
    def __init__(self, data_source = 'basketball_references'):
        self.scrape_source = data_source
        self.start_date = None
        self.end_date = None
        
    def get_game_summary(self, 
                         start_date: date, 
                         end_date=None,
                        ) -> Tuple[int, List[str]]:

        '''
        Attains the number of games that have occured between the defined time periods. 

        Parameters
        ----------
        start_date: date
            Start date of the observed time range 
        end_date: date
            End date of the observed time range

        Side Effects
        ----------
        Stores the list boxscore urls within scraper class 

        Returns
        ------- 
        Tuple[int, List[str]]
            int: nunber of games that have transpired between the specificed period (inclusive)
            List[str]: list of urls to the specific boxscores
            
        '''
        date_list = []
        
        if end_date is not None:
            displayed_verbiage =  f'between {start_date} and {end_date}'    
            if start_date > end_date:
                raise Exception("End date must come after start date!")
                
            delta = end_date - start_date 
            for i in range(delta.days + 1):
                day = start_date + timedelta(days=i)
                date_list.append(day)
        else:
            displayed_verbiage =  f'on {start_date}'    
            date_list.append(start_date)
        
        num_games = 0
        url_list = []
        
        if self.scrape_source == default_source:
            # used to keep track of volume of requests since last timeout
            multiplier = 0
            for index, game_date in enumerate(date_list):
                # prevent errors associated with Too Many Requests (Error 429)
                if index - multiplier > 20:
                    print(f'Request limit reached within 1 min threshold at {game_date} pausing for 70 seconds')
                    time.sleep(70)
                    multiplier += 20
                high_level_info = get_game_urls(game_date)
                num_games += high_level_info[0]
                url_list += high_level_info[1]
    
            self.game_url_list = url_list
            self.start_date = start_date
            self.end_date = end_date,
            self.num_games = num_games
            print(f'{num_games} games have occured {displayed_verbiage}')
        
        return (num_games, url_list)

    def generate_player_data(self,
                             start_date = None,
                             end_date = None,
                             game_urls = None,
                             stats_type = 'basic'
                            ) -> pd.DataFrame:
        '''
        Attains the number of games that have occured between the defined time periods. 

        Parameters
        ----------
        start_date: date
            Start date of the observed time range 
            Can be None if get_game_summary is ran perviously
        end_date: date
            End date of the observed time range
            Can be None if get_game_summary is ran perviously
        game_urls: List[str]
            list of strings indicating the game urls to scrape from
        stats_type: str 
            one of advanced or basic indicating basic / advanced stats to scrape 
            
        Returns
        ------- 
        pandas.DataFrame
          DataFrame indicating the stats for each individiual player over the course of the all games played during the 
          select time period
            
        '''
        
        if start_date is not None:
            num_games, game_url_list = self.get_game_summary(start_date, end_date)
            
        master_player_df = pd.DataFrame()
        
        if self.scrape_source == default_source:
            # used to keep track of volume of requests since last timeout
            multiplier = 0
            for index, game in enumerate(self.game_url_list):
                if index - multiplier > 20:
                    print(f'Request limit reached within 1 min threshold at {game} pausing for 70 seconds')
                    time.sleep(70)
                    multiplier += 20
                year_str = game.split('/')[2][0:4]
                month_str = game.split('/')[2][4:6]
                day_str = game.split('/')[2][6:8]
                game_date = f"{year_str}-{month_str}-{day_str}"

                soup = get_soup(bball_ref_url + game)
            
                home_player_df = create_player_boxscore(
                                    soup = soup,
                                    home_ind = True,
                                    stats_type = stats_type,
                                    source = self.scrape_source)
                road_player_df = create_player_boxscore(
                                    soup = soup,
                                    home_ind = False,
                                    stats_type = stats_type,
                                    source = self.scrape_source)
                
                agg_game_df = pd.concat([home_player_df, road_player_df], ignore_index = True)
                agg_game_df['game_date'] = game_date
                master_player_df = pd.concat([master_player_df, agg_game_df], ignore_index = True)
                
        return master_player_df

    def generate_team_stats(self,
                            start_date = None,
                            end_date = None,
                            game_urls = None,
                            stats_type = 'basic'
                           ) -> pd.DataFrame:
        '''
        Attains the number of games that have occured between the defined time periods. 

        Parameters
        ----------
        start_date: date
            Start date of the observed time range 
            Can be None if get_game_summary is ran perviously
        end_date: date
            End date of the observed time range
            Can be None if get_game_summary is ran perviously
        game_urls: List[str]
            list of strings indicating the game urls to scrape from
        stats_type: str 
            one of advanced or basic indicating basic / advanced stats to scrape 
            
        Returns
        ------- 
        pandas.DataFrame
          DataFrame indicating the stats at a team level for all games that have occured between the start / end time ranges
            
        '''
        
        if start_date is not None:
            num_games, game_url_list = self.get_game_summary(start_date, end_date)    
        
        team_dataset = pd.DataFrame()
        
        if self.scrape_source == default_source:
            # used to keep track of volume of requests since last timeout
            multiplier = 0
            for index, game in enumerate(self.game_url_list):
                if index - multiplier > 20:
                    print(f'Request limit reached within 1 min threshold at {game} pausing for 70 seconds')
                    time.sleep(70)
                    multiplier += 20
                    
                year_str = game.split('/')[2][0:4]
                month_str = game.split('/')[2][4:6]
                day_str = game.split('/')[2][6:8]
                game_date = f"{year_str}-{month_str}-{day_str}"
                
                soup = get_soup(bball_ref_url + game)

                specific_game_df = create_team_boxscore(soup = soup,
                                                        stats_type = 'basic',
                                                        source = default_source)
                
                specific_game_df['game_date'] = game_date

                team_dataset = pd.concat([team_dataset, specific_game_df], ignore_index = True)

        return team_dataset
                    
            
    
                
            
                