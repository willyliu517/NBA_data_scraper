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

#Extracts player data for both the Home and Away Team for the game specified
def get_team_data(home_team, date_played, driver, config = team_config):
    
    #Converts team name to abbreviations 
    home_team_abrv = config[home_team]
    modified_date = date_played.replace('-', '')
    
    game_dir = 'https://www.basketball-reference.com/boxscores/' + modified_date + '0' + home_team_abrv + '.html'
    driver.get(game_dir)
    
    #Grabs the Away Team from the Title
    away_team = driver.title.split(' at')[0]
    away_team_abrv = config[away_team]
    
    team_df = scrape_team_data(driver, 
                               date_played = date_played, 
                               modified_date = modified_date, 
                               home_team_name = home_team, 
                               away_team_name = away_team, 
                               home_team_abrv = home_team_abrv, 
                               away_team_abrv = away_team_abrv)
    return team_df
    
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
        #checks if the +/- field is empty (there are instances in Basketball Reference where the +/- field for a player who has played doesn't exist)
        if (len(df_cols) - len(player_stats)) == 1:
            player_stats = player_stats + ['']
        
        
        player_df.loc[i] = player_stats

    #Grabs the stats for the starters on the Away Team    
    #Data for Players that didn't play or not with team are not stored
    k = 11    
    while ((source.text.split('\n')[k].split(' ')[2] != 'Did') and 
           (source.text.split('\n')[k].split(' ')[2] != 'Not') and 
           (source.text.split('\n')[k].split(' ')[0] != 'Team')):
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
        #checks if the +/- field is empty (there are instances in Basketball Reference where the +/- field for a player who has played doesn't exist)
        if (len(df_cols) - len(player_stats)) == 1:
            player_stats = player_stats + ['']

        player_df.loc[k - 6] = player_stats

        k+=1
        
    return player_df 

def scrape_team_data(driver, date_played, modified_date, home_team_name,
                    away_team_name, home_team_abrv, away_team_abrv):
    
    #ID of the home team box score on the Basketball Reference
    home_team_element_id = 'all_box-' + home_team_abrv + '-game-basic'
    ht_source = driver.find_element_by_id(home_team_element_id)
    ht_team_stats = ht_source.text.split('\n')[-1].split(' ')
    del ht_team_stats[0]
    del ht_team_stats[0]
    
    #ID of the away team box score on the Basketball Reference
    away_team_element_id = 'all_box-' + away_team_abrv + '-game-basic'
    rt_source = driver.find_element_by_id(away_team_element_id)
    rt_team_stats = rt_source.text.split('\n')[-1].split(' ')
    del rt_team_stats[0]
    del rt_team_stats[0]
    
    #Creates the columns for the Dataframe
    #Grabs the line with columns
    df_cols = ht_source.text.split('\n')[4].split(' ')
    
    #Inserts additional columns
    df_cols[0] = 'F'
    df_cols.insert(0, 'OT5')
    df_cols.insert(0, 'OT4')
    df_cols.insert(0, 'OT3')
    df_cols.insert(0, 'OT2')
    df_cols.insert(0, 'OT1')
    df_cols.insert(0, '4Q')
    df_cols.insert(0, '3Q')
    df_cols.insert(0, '2Q')
    df_cols.insert(0, '1Q')
    df_cols.insert(0, 'Venue(R/H)')
    df_cols.insert(0, 'Team')
    df_cols.insert(0, 'Date')
    df_cols.insert(0, 'Game-ID')
    del df_cols[-1]
    
    #Creates team_df 
    team_df = pd.DataFrame(columns = df_cols)
    
    #Grabs the box score by source id 
    box_source = driver.find_element_by_id('line_score')
    
    #Grabs box score stats basketball ref
    away_score = box_source.text.split('\n')[-2].split(' ')
    home_score = box_source.text.split('\n')[-1].split(' ')
    del away_score[0]
    del home_score[0]
    #Converts data to integers
    away_score = list(map(int, away_score))
    home_score = list(map(int, home_score))
    
    #Transforms box scores to append to Team DF
    num_zeros = 9 - len(home_score[0: len(home_score) - 1])
    ht_box_score = home_score[0: len(home_score) - 1] + ['']*num_zeros + [home_score[-1]]
    rt_box_score = away_score[0: len(away_score) - 1] + ['']*num_zeros + [away_score[-1]]
    
    ht_team_stats = [modified_date + home_team_abrv, date_played, home_team_name, 'H'] + ht_box_score + ht_team_stats
    rt_team_stats = [modified_date + home_team_abrv, date_played, away_team_name, 'R'] + rt_box_score + rt_team_stats
    
    team_df.loc[0] = ht_team_stats
    team_df.loc[1] = rt_team_stats
    
    return team_df
    

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
    
    if len(source) == 1:
        print(f'On {games_date}, there are no games in the NBA.')
        return []
    
    else:    
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
