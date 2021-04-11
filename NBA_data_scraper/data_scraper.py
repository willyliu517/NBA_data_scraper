""" Core module for NBA Data Scraper """

import selenium 
import pandas as pd
import numpy as np
import yaml
import os
from pathlib import Path
from selenium import webdriver 
from datetime import date, timedelta, datetime
import utils

home_dir  = Path(os.path.expanduser('~'))
repo_dir = 'NBA_data_scraper'

#Loads in abbreviation team mappings
with open('./configs/team_name_mappings_abbrv_full.yml', 'r') as stream:
    try:
        team_full_abrv_config = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

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
    
    def __init__(self, driverpath, 
                 team_full_abrv_config = team_full_abrv_config):
    
        self.driverpath = driverpath
        self.team_full_abrv_config = team_full_abrv_config
        self.driver = init_driverpath(driverpath)
        
    def init_driverpath(driver_path):
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
            driver = webdriver.Chrome(str(driver_path))
            return driver
        except:
            raise Exception('The chromedriver path is not valid, please ensure you have the correct path')
    
    def get_player_team_data(self, start_date, end_date = None, 
                             get_player_data = True, get_team_data = True, 
                             pre_player_data_dir = None, pre_team_data_dir = None):
        """Function used to get player and data for games between the start and end date range 
        
        start_date: str
            start date of player data scrape
        end_date: str
            optional, end date of player data scrape only data for the start_date will be scraped
        get_player_data: bool
            Indicate whether to scrape player data    
        get_team_data: bool
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
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        if end_date:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else: 
            end_date = start_date
            
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
            home_team_list = data_scraper.get_list_of_hometeams(driver, date)

            if len(home_team_list) > 0:

                counter = 1 

                for home_team in home_team_list:
                    
                    if counter == 1:       
                        if get_player_data: 
                            player_df_full = data_scraper.get_player_data(home_team = team_config[home_team]['Full Name'], 
                                                                                      date_played = date, 
                                                                                      driver = driver)
                        if get_team_data:
                            team_df_full = data_scraper.get_team_data(home_team = team_config[home_team]['Full Name'], 
                                                                      date_played = date, 
                                                                      driver = driver)
                    else:
                        if get_player_data: 
                            player_df_full = player_df_full.append(data_scraper.get_player_data(home_team = team_config[home_team]['Full Name'], 
                                                                                                date_played = date, 
                                                                                                driver = driver), ignore_index=True)
                        if get_team_data:
                            team_df_full = team_df_full.append(data_scraper.get_team_data(home_team = team_config[home_team]['Full Name'], 
                                                                                          date_played = date, 
                                                                                          driver = driver), ignore_index=True)
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
            elif get_player_data and get_team_data:
                return player_df_full, team_df_full 
            elif get_player_data
                return player_df_full
            elif get_team_data:
                return team_df_full 
            
    def quit_(self):
        """
        Quit chromedriver, use after scraping needed data (note: you will need to initialize once you quit)
        """
        self.driver.quit()