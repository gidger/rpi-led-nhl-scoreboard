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
                'home_team_scored': None, # Will get populated below.
                'away_team_scored': None
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
            if game['gameType'] in [2, 3]:
                games.append(game_dict)

    return games


def run_scoreboard_loop() -> None:
    """ Infite loop of getting scores and displaying them on the matrix. """

    # Determine reporting day.
    cur_datetime = dt.datetime.today()
    cur_time = cur_datetime.time()
    report_date = date_utils.determine_report_date(cur_datetime, cur_time, DATE_ROLLOVER_TIME)

    # Build and display the loading screen.
    nhl_scoreboard_image.build_loading()
    matrix_utils.transition(matrix, nhl_scoreboard_image, transition_type=TRANSITION_TYPE, transition_direction='in')

    # Load game data and wait one extra second on the loading screen before transitioning out. Users thoguht it was too quick.
    games = load_nhl_game_data(report_date)
    time.sleep(1)
    matrix_utils.transition(matrix, nhl_scoreboard_image, transition_type=TRANSITION_TYPE, transition_direction='out')

    # Process data, build images, and display on scoreboard.
    while True:
        display_scoreboard(games, report_date)

        # If time is later than the DISPLAY_CURRENT_DAY_START_TIME and the report date isn't today's date, also display the upcoming games for today.
        if cur_time > DISPLAY_CURRENT_DAY_START_TIME and cur_datetime != report_date:
            games_tod = load_nhl_game_data(cur_datetime)
            display_scoreboard(games_tod, cur_datetime, forward_looking=True)

        # Update dates and times. Load new game data, noting if there's a score changes from old game data.
        cur_datetime = dt.datetime.today()
        cur_time = cur_datetime.time()
        report_date = date_utils.determine_report_date(cur_datetime, cur_time, DATE_ROLLOVER_TIME)
        games = load_nhl_game_data(report_date, games_old=games)


def display_scoreboard(games, date, forward_looking=False) -> None:
    """ Determines what should be displayed on the matrix, builds the required image, and displays on the matrix.

    Args:
        games (list): List of dicts of game data.
        date (date): Date of games.
        forward_looking (bool, optional): If we're displaying games for today before the date rollover time. Defaults to False.
    """

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
            duration = DISPLAY_DURATION if len(games) > 1 else DISPLAY_DURATION_SINGLE_GAME

            # Display the generated image to the matrix. This will handle any goal fade animations required.
            matrix_utils.display_image(matrix, nhl_scoreboard_image, transition_type=TRANSITION_TYPE, display_duration=duration, goal_fade_animation=GOAL_FADE_ANIMATION, 
                                        away_score=game['away_score'], home_score=game['home_score'], away_team_scored=game['away_team_scored'], home_team_scored=game['home_team_scored'])

    # If there's no games, build the no games image.
    else:
        nhl_scoreboard_image.build_no_games(date)
        duration = DISPLAY_DURATION_NO_GAMES if not forward_looking else DISPLAY_DURATION_SINGLE_GAME # If you're currently displyaing the scores from yesterday, we don't want a super long pause on the no games screen for today.
        matrix_utils.display_image(matrix, nhl_scoreboard_image, transition_type=TRANSITION_TYPE, display_duration=duration)


if __name__ == '__main__':
    # Initial setup. This creates matrix and scoreboard image objects, as well as some constants that will be needed throughout the code.
    # Constatants created below are specifed in config.yaml.

    # Load config.yaml to CONFIG.
    CONFIG = data_utils.read_yaml('config.yaml')

    # Create constants based on values in CONFIG.
    BASE_URL = CONFIG['api']['nhl_base_url']
    DISPLAY_DURATION = CONFIG['scoreboard_behaviour']['display_duration']
    DISPLAY_DURATION_SINGLE_GAME = CONFIG['scoreboard_behaviour']['display_duration_single_game']
    DISPLAY_DURATION_NO_GAMES = CONFIG['scoreboard_behaviour']['display_duration_no_games']
    DISPLAY_CURRENT_DAY_START_TIME = dt.datetime.strptime(CONFIG['scoreboard_behaviour']['display_current_day_start_time'], '%H:%M').time() # Casted string to time.
    DATE_ROLLOVER_TIME = dt.datetime.strptime(CONFIG['scoreboard_behaviour']['date_rollover_time'], '%H:%M').time() # Casted string to time.
    TRANSITION_TYPE = CONFIG['scoreboard_behaviour']['transition_type']
    GOAL_FADE_ANIMATION = CONFIG['scoreboard_behaviour']['goal_fade_animation']

    # Create a session, and define a retry strategy. Used for API calls.
    session = requests.Session()
    retry_strategy = Retry(
        total=10, # Maximum number of retries.
        backoff_factor=1, 
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

    # Create an NHLScoreboardImageGenerator object that will be displayed on the matrix.
    nhl_scoreboard_image = NHLScoreboardImageGenerator(matrix_options.rows, matrix_options.cols)

    # Run main loop.
    run_scoreboard_loop()