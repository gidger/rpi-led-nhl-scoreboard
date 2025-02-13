from rgbmatrix import RGBMatrix, RGBMatrixOptions
from image_generator.nhl_image_generator import NHLScoreboardImageGenerator
from utils import data_utils, date_utils, matrix_utils
import requests
from requests.adapters import HTTPAdapter, Retry
import json
import datetime as dt
import time


def load_nhl_game_data(date, games_old=None) -> list:
    """ Loads NHL game data. If games_old is provided, will also check if either team has scored since last data pull.

    Args:
        date (date): Date that game data should be pulled for.
        games_old (list, optional): List of dicts of game data from a previous data pull. Will be a previous output of this function. Defaults to None.

    Returns:
        list: List of dicts of game data.
    """
    
    # Create an empty list to hold the game dicts.
    games = []

    # Call the NHL API for the date specified and store the JSON results.
    games_response = session.get(url=f"{BASE_URL}{date.strftime(format='%Y-%m-%d')}")
    games_json = games_response.json()['games']

    # For each game, build a dict recording current game details.
    if games_json: # If games today.
        for game in games_json:
            game_dict =  {
                'game_id': game['id'],
                'home_team': game['homeTeam']['abbrev'],
                'away_team': game['awayTeam']['abbrev'],
                'home_score': game['homeTeam'].get('score'),
                'away_score': game['awayTeam'].get('score'),
                'start_time': dt.datetime.strptime(game['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc).astimezone(tz=None), # This converts UTC to local time.
                'status': game['gameState'],
                'period_num': game.get('period'), # Doesn't exist for games not started yet.
                'period_type': game.get('periodDescriptor', {}).get('periodType'), # If periodDesciprtor doesn't exist, then return an empty dict so second .get can execute.
                'period_time_remaining': game.get('clock', {}).get('timeRemaining'),
                'is_intermission': game.get('clock', {}).get('inIntermission'),
                'home_team_scored': False, # Will get populated below.
                'away_team_scored': False
            }

            # Check if any team scored. Only do this if the games_old list was handed to the function.
            if games_old:
                # First get the specific game that we care about from games_old. This will return a list.
                matching_game = list(filter(lambda game_old: game_old['game_id'] == game_dict['game_id'], games_old))
                
                # If the game we care about was found in games_old, the list should have a single element. We should never see more than a single element in the list.
                if matching_game and game_dict['home_score'] is not None and game_dict['away_score'] is not None:
                    game_old_dict = matching_game[0]

                    # Check if new scores are bigger than old scores.
                    if game_old_dict['home_score'] is not None and game_old_dict['away_score'] is not None:
                        game_dict['home_team_scored'] = True if game_dict['home_score'] > game_old_dict['home_score'] else False                
                        game_dict['away_team_scored'] = True if game_dict['away_score'] > game_old_dict['away_score'] else False

            # Append the dict to the games list. We only want to get regular season (2) and playoff (3) games, so any other games are not added.
            if game['gameType'] in [2, 3, 19]: # Add additional special event codes as needed. 
                games.append(game_dict)

    return games


def run_scoreboard_loop() -> None:
    """ Infite loop of getting scores and displaying them on the matrix. """

    # Set games to False. This will ensure we don't check for score changes in the initial loop.
    games = False

    # Process data, build images, and display on scoreboard.
    while True:
        # Determine reporting day, etc.
        cur_datetime = dt.datetime.today()
        cur_time = cur_datetime.time()
        report_date = date_utils.determine_report_date(cur_datetime, cur_time, DATE_ROLLOVER_TIME)
        
        # Load game data, noting if there's a score changes from game data of previous loop.
        games = load_nhl_game_data(report_date, games_old=games)

        # If time is later than the DISPLAY_CURRENT_DAY_START_TIME and the report date isn't today's date, display yesterday's final scores, as well as the upcoming games for today.
        if cur_time > DISPLAY_CURRENT_DAY_START_TIME and cur_datetime != report_date:
            display_scoreboard(games, report_date, forward_looking=True)
            games_tod = load_nhl_game_data(cur_datetime)
            display_scoreboard(games_tod, cur_datetime, forward_looking=True)
        # Otherwise, just display today's scores.
        else:
            display_scoreboard(games, report_date)


def display_scoreboard(games, date, forward_looking=False) -> None:
    """ Determines what should be displayed on the matrix, builds the required image, and displays on the matrix.

    Args:
        games (list): List of dicts of game data.
        date (date): Date of games.
        forward_looking (bool, optional): If we're displaying games for today before the date rollover time. Defaults to False.
    """

    # Get configured display duration info from config.yaml.
    config = data_utils.read_yaml('config.yaml')
    display_duration = config['scoreboard_behaviour']['display_duration']
    display_duration_single_game = config['scoreboard_behaviour']['display_duration_single_game']
    display_duration_no_games = config['scoreboard_behaviour']['display_duration_no_games']

    # If there's games today, loop through the games list.
    if games:
        for game in games:
            # If the game has yet to begin, build the game not started image.
            if game['status'] in ['FUT', 'PRE']:
                nhl_scoreboard_image.build_game_not_started(game)

            # If the game is over, build the final score image.
            elif game['status'] in ['OFF', 'FINAL']:
                nhl_scoreboard_image.build_game_over(game)

            # Otherwise, the game is in progress. Build the game in progress screen.
            elif game['status'] in ['LIVE', 'CRIT']:
                nhl_scoreboard_image.build_game_in_progress(game)
            else:
                print(f"Unexpected gameState encountered from API: {game['status']}.")
            
            # If there's only one game, hold for longer.
            duration = display_duration if len(games) > 1 else display_duration_single_game

            # Display the generated image to the matrix.
            matrix_utils.display_image(
                matrix,
                nhl_scoreboard_image,
                display_duration=duration, 
                away_score=game['away_score'],
                home_score=game['home_score'],
                away_team_scored=game['away_team_scored'],
                home_team_scored=game['home_team_scored']
            )

    # If there's no games, build the no games image.
    else:
        nhl_scoreboard_image.build_no_games(date)
        duration = display_duration_no_games if not forward_looking else display_duration_single_game # If you're currently displyaing the scores from yesterday, we don't want a super long pause on the no games screen for today.
        matrix_utils.display_image(matrix, nhl_scoreboard_image, display_duration=duration)


if __name__ == '__main__':
    # Initial setup. This creates matrix and scoreboard image objects, as well as some constants that will be needed throughout the code. Constatants specifed in config.yaml.

    # Load config.yaml to CONFIG.
    CONFIG = data_utils.read_yaml('config.yaml')

    # Create constants based on values in CONFIG.
    BASE_URL = CONFIG['api']['nhl_base_url']
    DISPLAY_CURRENT_DAY_START_TIME = dt.datetime.strptime(CONFIG['scoreboard_behaviour']['display_current_day_start_time'], '%H:%M').time() # Casted string to time.
    DATE_ROLLOVER_TIME = dt.datetime.strptime(CONFIG['scoreboard_behaviour']['date_rollover_time'], '%H:%M').time() # Casted string to time.

    # Create a session, and define a retry strategy. Used for API calls.
    session = requests.Session()
    retry_strategy = Retry(
        total=100, # Maximum number of retries.
        backoff_factor=0.5, 
        status_forcelist=[429, 500, 502, 503, 504] # HTTP status codes to retry on.
    )
    session.mount('http://', HTTPAdapter(max_retries=retry_strategy))

    # Configure options for the matrix based on values in CONFIG and create a matrix object to control the LED matrix.
    matrix_options = RGBMatrixOptions()
    matrix_options.rows = CONFIG['matrix_options']['rows']
    matrix_options.cols = CONFIG['matrix_options']['cols']
    matrix_options.chain_length = CONFIG['matrix_options']['chain_length']
    matrix_options.parallel = CONFIG['matrix_options']['parallel']
    matrix_options.gpio_slowdown= CONFIG['matrix_options']['gpio_slowdown']
    matrix_options.hardware_mapping = CONFIG['matrix_options']['hardware_mapping']
    matrix_options.drop_privileges = False # Need to ensure fonts and images load correctly. Could also give deamon user access to those folders instead...
    matrix = RGBMatrix(options=matrix_options)

    # The ammout of extra pixels on the R/L of the image that aren't displayed outside of horizontal tranitions.
    h_buffer = 25

    # Create an NHLScoreboardImageGenerator object that will be displayed on the matrix.
    nhl_scoreboard_image = NHLScoreboardImageGenerator(matrix_options.rows, matrix_options.cols, h_buffer)

    # Run main loop.
    run_scoreboard_loop()
