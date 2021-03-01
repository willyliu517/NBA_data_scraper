import selenium 
import pandas as pd
import numpy as np
import yaml
import os
from pathlib import Path
from selenium import webdriver 

home_dir  = Path(os.path.expanduser('~'))
repo_dir = home_dir / 'NBA_data_scraper'


#Loads in abbreviation team mappings
with open(repo_dir / 'configs/team_name_abbreviation_mapings.yml', 'r') as stream:
    try:
        team_config = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

#Initializes the Selenium Driver
def init_driverpath(driver_path):
    driver = webdriver.Chrome(str(driver_path))
    return driver

#Extracts player data for both the Home and Away Team for the game specified
def get_player_data(home_team, date_played, driver, config = team_config):
    
    #Converts team name to abbreviations 
    home_team_abr = config[home_team]
    modified_date = date_played.replace('-', '')
    
    game_dir = 'https://www.basketball-reference.com/boxscores/' + modified_date + '0' + home_team_abr + '.html'
    driver.get(game_dir)
    
    #Grabs the Away Team from the Title
    away_team = driver.title.split(' at')[0]
    away_team_abr = config[away_team]
    
    home_team_df = scrape_player_data(driver, 
                                      date_played, 
                                      modified_date, 
                                      team_name = home_team, 
                                      home_team_abrv = home_team_abr,
                                      team_abrv = home_team_abr, 
                                      home_or_away = 'H')
    
    away_team_df = scrape_player_data(driver, 
                                      date_played, 
                                      modified_date, 
                                      team_name = away_team, 
                                      home_team_abrv = home_team_abr,
                                      team_abrv = away_team_abr, 
                                      home_or_away = 'R')
    
    player_df = pd.concat([home_team_df, away_team_df])
    
    return player_df
    
    
def scrape_player_data(driver, date_played, modified_date, team_name, 
                       home_team_abrv, team_abrv, home_or_away):
    
    #ID of the box score on the Basketball Reference
    element_id = 'all_box-' + team_abrv + '-game-basic'
    source = driver.find_element_by_id(element_id)
    
    #Creates the columns for the Dataframe
    #Grabs the line with columns
    df_cols = source.text.split('\n')[4].split(' ')
    df_cols[0] = 'Player Name'
    #Inserts additional columns
    df_cols.insert(0, 'Starter(Y/N)')
    df_cols.insert(0, 'Venue(R/H)')
    df_cols.insert(0, 'Team')
    df_cols.insert(0, 'Date')
    df_cols.insert(0, 'Game-ID')
    
    player_df = pd.DataFrame(columns = df_cols)
    
    #Grabs the stats for the starters on the Home Team
    for i in range(0, 5):
        player_stats = source.text.split('\n')[i + 5].split(' ')
        player_stats[0] = player_stats[0] +  ' ' + player_stats[1]
        del player_stats[1]
        player_stats.insert(0, 'Y')
        player_stats.insert(0, home_or_away)
        player_stats.insert(0, team_name)
        player_stats.insert(0, date_played)
        player_stats.insert(0, modified_date + home_team_abrv)
        #checks if FGA is empty
        if player_stats[8] == '0':
            player_stats.insert(9, '')
        #checks if 3PA is empty 
        if player_stats[11] == '0':
            player_stats.insert(12, '')
        #checks if FTA is empty 
        if player_stats[14] == '0':
            player_stats.insert(15, '')
        
        player_df.loc[i] = player_stats

    #Grabs the stats for the starters on the Away Team    
    #Data for Players that didn't play are not stored
    k = 11    
    while source.text.split('\n')[k].split(' ')[2] != 'Did':
        player_stats = source.text.split('\n')[k].split(' ')
        player_stats[0] = player_stats[0] +  ' ' + player_stats[1]
        del player_stats[1]
        player_stats.insert(0, 'N')
        player_stats.insert(0, home_or_away)
        player_stats.insert(0, team_name)
        player_stats.insert(0, date_played)
        player_stats.insert(0, modified_date + home_team_abrv)
        #checks if FGA is empty
        if player_stats[8] == '0':
            player_stats.insert(9, '')
        #checks if 3PA is empty 
        if player_stats[11] == '0':
            player_stats.insert(12, '')
        #checks if FTA is empty 
        if player_stats[14] == '0':
            player_stats.insert(15, '')

        player_df.loc[k - 6] = player_stats

        k+=1
        
    return player_df 

#Returns list of Home Teams that have played on a certain date
def get_list_of_hometeams(driver, games_date):
    modified_date = games_date.replace('-', '')
    year = modified_date[0:4]
    month = modified_date[4:6]
    days = modified_date[6:8]
    
    #Directory for all games on a specific date 
    scores_dir = f'https://www.basketball-reference.com/boxscores/?month={month}&day={days}&year={year}'
    driver.get(scores_dir)
    source = driver.find_elements_by_class_name('game_summaries')
    
    num_games = len(source[1].text.split('\n')) / 8
    
    print(f'On {games_date} there are {int(num_games)} games in the NBA.')
    
    home_team_list = []
    position = 4
    for i in range(0, int(num_games)):
        home_team_list.append(source[1].text.split('\n')[position].split('  ')[0])
        position += 8
    
    return home_team_list
    
#Quit Driver - use after scraping needed data
def quit_driver(driver):
    driver.quit()
