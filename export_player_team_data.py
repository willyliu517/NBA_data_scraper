import selenium 
import os
import pandas as pd
import numpy as np
import yaml
import argparse
from pathlib import Path
from selenium import webdriver 
from datetime import date, timedelta, datetime
from data_scraper_scripts import data_scraper

#Defines set of directories needed
home_dir = Path('/Users/Liu')
repo_dir = home_dir / 'NBA_data_scraper'
#Link this to the directory the chromedriver is saved
driver_path = home_dir /'chromedriver'

#Loads in abbreviation team mappings
with open(repo_dir / 'configs/team_name_mappings_abbrv_full.yml', 'r') as stream:
    try:
        team_config = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_date", type = str, help = 'Start date of data scrape (i.e. 2021-02-01)', required = True)
    parser.add_argument("--end_date", type = str, help = 'End date of data scrape (i.e. 2021-02-28)', required = True)
    
    args = parser.parse_args() 
    start_date_str = args.start_date
    end_date_str = args.end_date
    
    #NBA season - creates the subfolder to output data 
    nba_season = '2020-2021_NBA_Season'
    
    #output directory of datasets
    output_dir = Path(f'/Users/Liu/nba_data/{nba_season}/')
    
    if not os.path.exists(output_dir): 
        os.makedirs(output_dir)
    
    #Converts start and end date from string to datetime
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    #Difference between start date and end date
    delta = end_date - start_date  
    
    #Appends list of date between start and end date to strings
    date_list = []
    for i in range(delta.days + 1):
        day  = start_date + timedelta(days=i)
        date_list.append(str(day))
    
    #Initalizes the chromedriver
    driver = data_scraper.init_driverpath(driver_path)
    
    player_df = pd.DataFrame()
    team_df = pd.DataFrame()
    
    for date in date_list:
        print(f'Now scraping data from NBA games on {date}')
        
        home_team_list = data_scraper.get_list_of_hometeams(driver, date)
        
        if len(home_team_list) > 0:
            
            counter = 1 

            for home_team in home_team_list:
                if counter == 1: 
                    player_df_full = data_scraper.get_player_data(home_team = team_config[home_team]['Full Name'], 
                                                                              date_played = date, 
                                                                              driver = driver)
                    team_df_full = data_scraper.get_team_data(home_team = team_config[home_team]['Full Name'], 
                                                              date_played = date, 
                                                              driver = driver)
                else:
                    player_df_full = player_df_full.append(data_scraper.get_player_data(home_team = team_config[home_team]['Full Name'], 
                                                                                        date_played = date, 
                                                                                        driver = driver), ignore_index=True)
                    team_df_full = team_df_full.append(data_scraper.get_team_data(home_team = team_config[home_team]['Full Name'], 
                                                                                  date_played = date, 
                                                                                  driver = driver), ignore_index=True)
                counter+=1
                
        player_df = player_df.append(player_df_full)
        team_df = team_df.append(team_df_full)
            
    player_df.to_csv(output_dir / f'NBA_player_data_{start_date_str}_to_{end_date_str}.csv', index = False)
    team_df.to_csv(output_dir / f'NBA_team_data_to_{start_date_str}_to_{end_date_str}.csv', index = False)
    
    driver.quit()
    
        
    