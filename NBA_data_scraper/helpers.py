from bs4 import BeautifulSoup
from bs4 import element
import requests
import pandas as pd
import numpy as np
import re
import time
from typing import Dict, List, Tuple
import datetime
from pathlib import Path

headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'}
default_source = 'basketball_references'
alternative_sources = ['espn', 'nba']
bball_ref_url = 'https://www.basketball-reference.com/'

def load_yaml_file(path):
    "loads in the yaml file specified in the path"
    with open(path, 'r') as stream:
        try:
            config = yaml.load(stream)
            return config
        except yaml.YAMLError as exc:
            print(exc)


def ensure_dir_exists(dir_path):
    "checks if the directory exists and creates it if not"
    try:
        os.makedirs(dir_path)
        return dir_path
    except FileExistsError:
        return dir_path

def get_soup(url: str,
             headers = headers) -> BeautifulSoup: 
    '''
    Gets BeautifulSoup based on input url

    Parameters
    ----------
    url: str
        target url to scrape from
    dict: 
    

    Returns
    ------- 
    BeautifulSoup
        leveraged for scraping 
    '''
    url_request = requests.get(url, headers = headers, timeout = 5)
    if url_request.status_code == 200:
        soup = BeautifulSoup(url_request.text, features='html.parser')    
        return soup 
        
    # instance of too many requests 
    elif url_request.status_code == 429:
        raise Exception(f"Too many requests generated. Please try again later!")
    else: 
        raise Exception(f"The request generated status code: {url_request.status_code}")


def get_game_urls(game_date: datetime.date, 
                  source = 'basketball_references') -> Tuple[List[str], int]:
    '''
    takes in a date and outputs the number of NBA games that have occured on that date
    
    Parameters
    ----------
    game_date: datetime.date
        date in the following format (%YYYY, %MM, %DD)
    source: str
        source in which the data will be scraped from; by default this will be basketball_references
    
    Returns
    ------- 
    Tuple[int, List[str]]:
        int: indicating the number of games that occured on that particular date
        List[str]: indicating the list of urls associated with the underlying games; only components 
        after https://www.basketball-reference.com/ are outputted  
        
    '''
    if source == default_source:
        game_year = str(game_date.year)
        game_month = str(game_date.month)
        game_day = str(game_date.day)
        
        date_centric_url = f'boxscores/?month={game_month}&day={game_day}&year={game_year}'
    
        soup_text = get_soup(bball_ref_url + date_centric_url)
        gamelinks = soup_text.find_all('td', class_ = 'right gamelink')
    
        num_games = len(gamelinks)
    
        game_urls = [gamelink.find('a').get('href') for gamelink in gamelinks]
        
    return (num_games,game_urls)

def get_column_names(game_url: str, source = 'basketball_references') -> Tuple[List[str], List[str]]:
    '''
    Gets the column names of the format table from the underlying source

    Parameters
    ----------
    game_url: str
        target url to attain column names from
    source: str
        source in which the data will be scraped from; by defualt this will be basketball_references

    Returns
    ------- 
    Tuple[List[str], List[str]]
        List[str]: where each string represents the full column name 
        List[str]: where each string represents the abbreviated column name 
    '''

    soup_text = get_soup(game_url)

    if source == default_source:
        game_tables = soup_text.find_all('table')[0]
        column_names = game_tables.find_all('tr')[1].find_all('th', class_ = 'poptip')
        full_column_names = [column_name.get('aria-label').lower() for column_name in column_names]
        abbreviated_column_names = [column_name.text.lower() for column_name in column_names]
        
    return (full_column_names, abbreviated_column_names)

def get_game_table(soup: BeautifulSoup,
                   stats_type: str,
                   home_ind: bool,
                   source = 'basketball_references') -> element.Tag:
    '''
    Outputs the element.Tag representing the game table in which we will be scraping player stats from

    Parameters
    ----------
    soup: BeautifulSoup
        BeautifulSoup class to scrape from
    stats_type: str
        indicating what type of stats to pull in for the underlying player; one of 'advanced' or 'basic' 
    home_ind: bool
        boolean indicating whether the player was on the home team
    Returns
    ------- 
    element.Tag representing the player stats table containing player level information 
    
    '''
    if source == default_source:
        if stats_type == 'basic':
            string_format = 'game-basic'
        elif stats_type == 'advanced':
            string_format = 'game-advanced'
            
        game_basic_scores = soup.find_all('table', id = re.compile(f"{string_format}$"))

        if home_ind:
            game_table = game_basic_scores[1]
        else: 
            game_table = game_basic_scores[0]

    return game_table

def get_player_stats(soup: BeautifulSoup, 
                     player_index: int, 
                     starter_ind: bool,
                     home_ind: bool,
                     stats_type = 'basic' ,
                     source = 'basketball_references') -> Dict:
    '''
    Gets the underlying basic stats for a particular player from a given game (based on the BeautifulSoup class)

    Parameters
    ----------
    soup: BeautifulSoup
        BeautifulSoup class to scrape from
    player_index: int
        int indicating the index of the player (i.e. first, second, third row from the text table)
    starter_ind: bool
        boolean indicating whether the player was a starter
    home_ind: bool
        boolean indicating whether the player was on the home team
    stats_type: str
        indicating what type of stats to pull in for the underlying player; one of advanced or basic 
    source: str
        data source in which the data will be scraped from; by default this will be basketball_references

    Returns
    ------- 
    Dict 
        JSON where the keys represent the stat fields and values resentings the actual stats pertaining to the fields
    '''

    game_table = get_game_table(soup = soup, 
                                stats_type = stats_type, 
                                home_ind = home_ind, 
                                source = source)
    if source == default_source:

        team = game_table.get('id')[4:7]
        
        if starter_ind: 
            player_index +=1 
            if player_index > 6:
                raise Exception("There can only be 5 starters in a game")
        else:
            player_index+=7
        
        try: 
            player_info = game_table.find_all('tr')[player_index]
            
        except IndexError:
            return None
    
        if player_info.find('th').text == 'Team Totals':
            return None
        
        stats_dict = {}
        
        # indicates whether the underlying player has played 
        if player_info.find('td').text == 'Did Not Play':
            played_ind = False
        else: 
            played_ind = True
        
        stats_dict['team'] = team
        stats_dict['player_name'] = player_info.find('th').text
        stats_dict['home_team_ind'] = home_ind
        stats_dict['starter_ind'] = starter_ind
        stats_dict['played_ind'] = played_ind
        if played_ind: 
            for stat in player_info.find_all('td'):
                stats_dict[stat.get('data-stat')] = stat.text

    return stats_dict

def create_player_boxscore(soup: BeautifulSoup,
                           home_ind: bool,
                           stats_type: str,
                           source = 'basketball_references') -> pd.DataFrame:
    '''
    Outputs players performance in a Pandas DataFrame for either the home / away team.

    Parameters
    ----------
    soup: BeautifulSoup
        BeautifulSoup class to scrape from
    home_ind: bool
        boolean indicating whether the player was on the home team
    stats_type: str
        indicating what type of stats to pull in for the underlying player; one of advanced or basic 
    source: str
        data source in which the data will be scraped from; by default this will be basketball_references

    Returns
    -------
    pd.DataFrame
        DataFrame containing stats for each individual player associated with the team (either home or away)
    '''

    player_df = pd.DataFrame()
    if source == default_source:
        for starter_player in range(1,6):
            starter_dict = get_player_stats(
                            soup = soup,
                            player_index = starter_player, 
                            starter_ind =  True,
                            home_ind = home_ind,
                            stats_type = stats_type ,
                            source = source)
            
            if starter_player == 1: 
                player_df = pd.DataFrame(data = starter_dict, index = [starter_player])
            else: 
                player_df.loc[starter_player] = list(starter_dict.values())
    
        bench_player = 1
        
        while True:
            bench_dict = get_player_stats(
                            soup = soup,
                            player_index = bench_player, 
                            starter_ind =  False,
                            home_ind = home_ind,
                            stats_type = stats_type ,
                            source = source)
            
            if bench_dict is None: 
                break
                
            dict_length = len(bench_dict)
            df_length = len(starter_dict)

            if dict_length < df_length:
                player_df.loc[bench_player+5] = list(bench_dict.values()) + list(np.repeat(np.nan, df_length - dict_length))
            else:
                player_df.loc[bench_player+5] = list(bench_dict.values())
            bench_player += 1
            
    return player_df

def get_team_stats(soup: BeautifulSoup, 
                   home_ind: bool,
                   stats_type = 'basic',
                   source = 'basketball_references') -> Dict:
    '''
    Outputs aggregate team stats in a Dictionary for either the home / away team.

    Parameters
    ----------
    soup: BeautifulSoup
        BeautifulSoup class to scrape from
    home_ind: bool
        boolean indicating whether the player was on the home team
    stats_type: str
        indicating what type of stats to pull in for the underlying player; one of advanced or basic 
    source: str
        data source in which the data will be scraped from; by default this will be basketball_references

    Returns
    -------
    Dict
        Representing the basic / advanced team total stats scraped from the Soup class
    '''
    if source == default_source:
        game_table = get_game_table(soup = soup, 
                                    stats_type = stats_type, 
                                    home_ind = home_ind, 
                                    source = source)
    
        team_totals = game_table.find_all('tr')[-1]
    
        team_stats_dict = {}
        team_name = game_table.get('id')[4:7]
        
        team_stats_dict['team_name'] = team_name
        team_stats_dict['home_team_ind'] = home_ind
    
        for stat in team_totals.find_all('td'):
            team_stats_dict[stat.get('data-stat')] = stat.text

    return team_stats_dict

def create_team_boxscore(soup: BeautifulSoup, 
                         stats_type = 'basic',
                         source = 'basketball_references') -> pd.DataFrame:
    '''
    Outputs team performance in a Pandas DataFrame.

    Parameters
    ----------
    soup: BeautifulSoup
        BeautifulSoup class to scrape from
    stats_type: str
        indicating what type of stats to pull in for the underlying player; one of advanced or basic 
    source: str
        data source in which the data will be scraped from; by default this will be basketball_references

    Returns
    -------
    pd.DataFrame
        Output will be a dataframe of two rows representing the aggregate stats for the home and away team 
    '''
    team_stats_df = pd.DataFrame()
    
    if source == default_source:
        home_team_stats = get_team_stats(soup=soup, 
                                         home_ind = True,
                                         stats_type = stats_type)
        road_team_stats = get_team_stats(soup=soup, 
                                         home_ind = False,
                                         stats_type = stats_type)
        
        home_team_df = pd.DataFrame(data = home_team_stats, index = [0])
        road_team_df = pd.DataFrame(data = road_team_stats, index = [1])

        return pd.concat([home_team_df, road_team_df], ignore_index = True)

    
    

    