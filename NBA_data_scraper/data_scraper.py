""" Core module for NBA Data Scraper """

import selenium 
import pandas as pd
import numpy as np
import yaml
import os
import sys
from pathlib import Path
from selenium import webdriver 
from datetime import date, timedelta, datetime
from .util_helpers import get_list_of_hometeams, get_player_data, get_team_data

#Dictionary used to map NBA cities to full team names and abbreviations 
team_full_abrv_config = { 
  'Atlanta': {'Full Name': 'Atlanta Hawks', 
              'Abbreviation': 'ATL'},
  'Boston': {'Full Name': 'Boston Celtics', 
             'Abbreviation': 'BOS'},   
  'Brooklyn': {'Full Name': 'Brooklyn Nets',
               'Abbreviation': 'BRK'},
  'Chicago': {'Full Name': 'Chicago Bulls',
              'Abbreviation': 'CHI'},
  'Charlotte': {'Full Name': 'Charlotte Hornets',
                'Abbreviation': 'CHO'},
  'Cleveland': {'Full Name': 'Cleveland Cavaliers',
                'Abbreviation': 'CLE'},  
  'Dallas': {'Full Name': 'Dallas Mavericks',
             'Abbreviation': 'DAL'},  
  'Denver': {'Full Name': 'Denver Nuggets',
             'Abbreviation': 'DEN'},  
  'Detroit': {'Full Name': 'Detroit Pistons',
              'Abbreviation': 'DET'},  
  'Golden State':  {'Full Name': 'Golden State Warriors',
                    'Abbreviation': 'GSW'},  
  'Houston': {'Full Name': 'Houston Rockets',
              'Abbreviation': 'HOU'},
  'Indiana': {'Full Name': 'Indiana Pacers',
              'Abbreviation': 'IND'},
  'LA Clippers': {'Full Name': 'Los Angeles Clippers',
                  'Abbreviation': 'LAC'},
  'LA Lakers': {'Full Name': 'Los Angeles Lakers',
                'Abbreviation': 'LAL'},
  'Miami': {'Full Name': 'Miami Heat',
            'Abbreviation': 'MIA'},
  'Milwaukee': {'Full Name': 'Milwaukee Bucks',
                'Abbreviation': 'MIL'},
  'Minnesota': {'Full Name': 'Minnesota Timberwolves',
                'Abbreviation': 'MIN'},
  'Memphis': {'Full Name': 'Memphis Grizzlies',
              'Abbreviation': 'MEM'},
  'New Orleans': {'Full Name': 'New Orleans Pelicans',
                  'Abbreviation': 'NOP'},
  'New York': {'Full Name': 'New York Knicks',
               'Abbreviation': 'NYK'},
  'Oklahoma City': {'Full Name': 'Oklahoma City Thunder',
                    'Abbreviation': 'OKC'},
  'Orlando': {'Full Name': 'Orlando Magic',
              'Abbreviation': 'ORL'},
  'Philadelphia': {'Full Name': 'Philadelphia 76ers',
                   'Abbreviation': 'PHI'},
  'Phoenix': {'Full Name': 'Phoenix Suns',
              'Abbreviation': 'PHO'},
  'Portland': {'Full Name': 'Portland Trail Blazers',
               'Abbreviation': 'POR'},
  'Sacramento': {'Full Name': 'Sacramento Kings',
                 'Abbreviation': 'SAC'},
  'San Antonio': {'Full Name': 'San Antonio Spurs', 
                  'Abbreviation': 'SAS'},
  'Toronto': {'Full Name': 'Toronto Raptors',
              'Abbreviation': 'TOR'},
  'Utah': {'Full Name': 'Utah Jazz',
           'Abbreviation': 'UTA'},
  'Washington': {'Full Name': 'Washington Wizards',
                 'Abbreviation': 'WAS'}
 }

class NBA_scraper:
    
    """NBA_scraper class
    
    This class holds methods of initializing chromedriver, checking how many games there are in a 
    particular date and extracting player / team data to new or existing datasets. In order to use this 
    class, chromedriver will need to downloaded. 
    
    Please download the appropriate chromedriver here:
    https://sites.google.com/a/chromium.org/chromedriver/downloads 
    
    Parameters
    ----------
    
    driverpath: str, 
        Directory to the Chromedriver
    
    team_full_abrv_config: dict,
        yaml file containing mappings of both Full Names and Abbreviations for NBA cities (i.e. Boston, full name is Boston Celtics and abbreviated is BOS)
        
    
    """
    
    def __init__(self, 
                 driverpath, 
                 team_full_abrv_config = team_full_abrv_config):
    
        self.driverpath = driverpath
        self.team_full_abrv_config = team_full_abrv_config
        self.init_driverpath()
        
    def init_driverpath(self):
        """Initializes the Selenium Webdriver
        
        Parameters
        ----------
        driver_path: str
            driver_path to chromedriver
        
        Returns
        -------
        selenium.webdriver.chrome.webdriver.WebDriver
        
        """
        try:
            self.driver = webdriver.Chrome(str(self.driverpath))
        except:
            raise Exception('The chromedriver path is not valid, please ensure you have the correct path')
    
    def get_player_team_data(self, start_date, end_date = None, 
                             get_player_data_ind = True, get_team_data_ind = True, 
                             pre_player_data_dir = None, pre_team_data_dir = None):
        """Function used to get player and data for games between the start and end date range 
        
        start_date: str
            start date of player data scrape
        end_date: str
            optional, end date of player data scrape only data for the start_date will be scraped
        get_player_data_ind: bool
            Indicate whether to scrape player data    
        get_team_data_ind: bool
            Indicate whether to scrape team data
        pre_player_data_dir: str
            optional, directory of the existing player dataset
            newly scraped data will be appended to this if inserted    
        pre_team_data_dir: str
            optional, directory of the existing team dataset
            newly scraped data will be appended to this if inserted 
            
        Returns
        -------
            pandas.DataFrame, pandas.DataFrame
            can be up to two datasets (player and team DF)
            
        """
        #Converts start and end date from string to datetime
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else: 
            end_date = start_date
        
        delta = end_date - start_date  
        
        if pre_player_data_dir:
            try: 
                #Reads in the existing player dataset to append the scraped data to 
                exist_player_data = pd.read_csv(pre_player_data_dir)
            except:
                raise Exception('Cannot read in existing player dataset please ensure the directory is correct')
                
        if pre_team_data_dir:
            try: 
                #Reads in the existing player dataset to append the scraped data to 
                exist_team_data = pd.read_csv(pre_team_data_dir)
            except:
                raise Exception('Cannot read in existing team dataset please ensure the directory is correct')
            
        #Appends list of date between start and end date to strings
        date_list = []
        for i in range(delta.days + 1):
            day  = start_date + timedelta(days=i)
            date_list.append(str(day))
        
        for date in date_list:
            
            print(f'Now scraping data from NBA games on {date}')
            home_team_list = get_list_of_hometeams(self.driver, date)

            if len(home_team_list) > 0:

                counter = 1 

                for home_team in home_team_list:
                    
                    if counter == 1:       
                        if get_player_data_ind: 
                            player_df_full = get_player_data(home_team = team_full_abrv_config[home_team]['Full Name'], 
                                                             date_played = date, 
                                                             driver = self.driver)
                        if get_team_data_ind:
                            team_df_full = get_team_data(home_team = team_full_abrv_config[home_team]['Full Name'], 
                                                         date_played = date, 
                                                         driver = self.driver)
                    else:
                        if get_player_data_ind: 
                            player_df_full = player_df_full.append(get_player_data(home_team = team_full_abrv_config[home_team]['Full Name'], 
                                                                                   date_played = date, 
                                                                                   driver = self.driver), ignore_index=True)
                        if get_team_data_ind:
                            team_df_full = team_df_full.append(get_team_data(home_team = team_full_abrv_config[home_team]['Full Name'], 
                                                                             date_played = date, 
                                                                             driver = self.driver), ignore_index=True)
                    counter+=1
            
            if pre_player_data_dir:
                exist_player_data = exist_player_data.append(player_df_full)
                exist_player_data.to_csv(pre_player_data_dir, index = False)
                print(f'Updated player dataset will be overwritten in {pre_player_data_dir}')
                
            if pre_team_data_dir:
                exist_team_data = exist_team_data.append(team_df_full)
                exist_team_data.to_csv(pre_team_data_dir, index = False)
                print(f'Updated team dataset will be overwritten in {pre_team_data_dir}')
                
            if pre_player_data_dir and pre_team_data_dir:
                return exist_player_data, exist_team_data
            elif pre_player_data_dir:
                return exist_player_data
            elif pre_team_data_dir:
                return exist_team_data
            elif get_player_data_ind and get_team_data_ind:
                return player_df_full, team_df_full 
            elif get_player_data_ind:
                return player_df_full
            elif get_team_data_ind:
                return team_df_full 
            
    def quit(self):
        """
        Quit chromedriver, use after scraping needed data (note: you will need to initialize once you quit)
        """
        self.driver.quit()