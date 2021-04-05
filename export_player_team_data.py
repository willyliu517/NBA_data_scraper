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
    parser.add_argument("--existing_player_dataset", type=str, help='Directory to existing player dataset', required=False)
    parser.add_argument("--existing_team_dataset", type=str, help='Directory to existing team dataset',  required=False)

    args = parser.parse_args() 
    start_date_str = args.start_date
    end_date_str = args.end_date
    
    #Checks if existing player dataset is passed in
    if args.existing_player_dataset:
        player_dir = Path(args.existing_player_dataset)
        #Reads in the existing player dataset to append the scraped data to 
        exist_player_data = pd.read_csv(player_dir)
    #Checks if existing team dataset is passed in 
    if args.existing_team_dataset:
        team_dir = Path(args.existing_team_dataset)
        #Reads in the existing team dataset to append the scraped data to 
        exist_team_data = pd.read_csv(team_dir)
    
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
    
    if args.existing_player_dataset:
        exist_player_data = exist_player_data.append(player_df)
        #Overwrites existing dataset with new player data appended
        exist_player_data.to_csv(player_dir, index = False)
    else:
        player_df.to_csv(output_dir / f'NBA_player_data_{start_date_str}_to_{end_date_str}.csv', index = False)
        
    if args.existing_team_dataset:
        exist_team_data = exist_team_data.append(team_df)
        #Overwrites existing dataset with new player data appended
        exist_team_data.to_csv(team_dir, index = False)
    else:
        team_df.to_csv(output_dir / f'NBA_team_data_to_{start_date_str}_to_{end_date_str}.csv', index = False)
    
    driver.quit()
    
        
    