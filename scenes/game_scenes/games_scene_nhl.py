from .games_scene import GamesScene
from setup.matrix_setup import matrix
import data.nhl_data
from utils import data_utils, date_utils

from datetime import datetime as dt
from time import sleep


class NHLGamesScene(GamesScene):
    """ Game scene for the NHL. Contains functionality to pull data from NHL API, parse, and build+display specific images based on the result.
    This class extends the general Scene and GameScene classes. An object of this class type is created when the scoreboard is started.
    """

    def __init__(self):
        """ Defines the league as NHL. Used to identify the correct files when adding logos to images.
        First runs init from the generic GameScene class.
        """
        
        super().__init__()
        self.LEAGUE = 'NHL'


    def display_scene(self):
        """ Displays the scene on the matrix.
        Includes logic on which image to build, when to display, etc.
        """

        # Refresh config and load to settings key.
        self.settings = data_utils.read_yaml('config.yaml')['scene_settings']['nhl']['games']

        # Determine which days should have data. Will generate a list with one or two elements. Two means we're in rollover time and yesterdays games should be displayed.
        dates_to_display = date_utils.determine_dates_to_display_games(self.settings['rollover']['rollover_start_time_local'], self.settings['rollover']['rollover_end_time_local'])

        # Pull data for yesterday's games if needed.
        yesterday_games = data.nhl_data.get_games(dates_to_display[0]) if len(dates_to_display) == 2 else []
            
        # Get current day game data. Save this for future reference.
        self.data = {
            'games_previous': self.data['games'] if hasattr(self, 'data') else None, # If this is the first time this is run, we'd expect self.data to not exist.
            'games': data.nhl_data.get_games(dates_to_display[-1]), # Get data for current day. Current day will always be the last element of dates_to_display.
        }

        # Note the number of games to display between yesterday and today.
        num_games_today = len(self.data['games'])
        num_games_yesterday = len(yesterday_games)

        # If there are games to display from yesterday, build and display splash image, then images for those games.
        if yesterday_games:
            self.display_splash_image(num_games_yesterday, date=dates_to_display[0])
            self.display_game_images(yesterday_games)

        # For the current day's games, note if any goals were scored since the last data pull.
        if self.data['games_previous']: # Only applicable if there's a previous copy to compare to.
            for game in self.data['games']:
                if game['status'] not in ['FUT', 'PRE']: # Not applicable if the game hasn't started yet.
                    # Match games between data pulls.
                    matched_game = next(filter(lambda x: x['game_id'] == game['game_id'], self.data['games_previous']))
                    
                    # Determine if either team scored and set keys accordingly.
                    game['away_team_scored'] = True if game['away_score'] > matched_game['away_score'] else False
                    game['home_team_scored'] = True if game['home_score'] > matched_game['home_score'] else False
                    
                    if game['away_team_scored'] and game['home_team_scored']:
                        game['scoring_team'] = 'both'
                    elif game['away_team_scored']:
                        game['scoring_team'] = 'away'
                    elif game['home_team_scored']:
                        game['scoring_team'] = 'home'
                    
        # Display splash and game image(s) on the matrix.
        self.display_splash_image(num_games_today, date=dates_to_display[-1])
        self.display_game_images(self.data['games'])


    def display_splash_image(self, num_games, date):
        """ Builds and displays splash screen for games on date.

        Args:
            num_games (int): Num of games happening on date.
            date (date): Date of games.
        """
        
        # Build splash image, transition in, pause, transition out. 
        self.build_splash_image(num_games, date)
        self.transition_image(direction='in', image_already_combined=True)
        sleep(self.settings['image_display_duration'])
        self.transition_image(direction='out', image_already_combined=True)
                                                                                               

    def display_game_images(self, games):
        """ Builds and displays images on the matrix for each game in games.

        Args:
            games (list): List of game dicts. Each element has all details for a single game.
        """
        
        # If there's any games to display, loop through them and build the appropriate images.
        if games:
            for game in games:
                
                # TESTING
                # game['status'] = 'LIVE'
                # # game['period_type'] = 'OT'
                # game['period_num'] = 3
                # game['period_time_remaining'] = '00:20'
                # game['scoring_team'] = 'home'

                # If the game has yet to begin, build the game not started image.
                if game['status'] in ['FUT', 'PRE']:
                    self.build_game_not_started_image(game)

                # If the game is over, build the final score image.
                elif game['status'] in ['OFF', 'FINAL']:
                    self.build_game_complete_image(game)

                # Otherwise, the game is in progress. Build the game in progress screen.
                elif game['status'] in ['LIVE', 'CRIT']:
                    self.build_game_in_progress_image(game)
                else:
                    print(f"Unexpected gameState encountered from API: {game['status']}.")

                # Transition the image in on the matrix.
                self.transition_image(direction='in')

                # If a goal was scored, do goal fade animation (if enabled).
                if self.settings['score_alerting']['score_coloured'] and self.settings['score_alerting']['score_fade_animation']:
                    if game['scoring_team']:
                        self.fade_score_change(game)
                
                # Hold image for calculated duration and transition out.
                sleep(self.settings['image_display_duration'])
                self.transition_image(direction='out')


    def add_playing_period_to_image(self, game):
        """ Adds current playing period to the centre image.
        This exists within the specific league class due to huge differences in playing periods between sports (periods, quarters, innings, etc.).

        Args:
            game (dict): Dictionary with all details of a specific game.
        """

        # If intermission, add "INT" to the image.
        if game['is_intermission']:
            self.draw['centre'].text((1, 7), 'INT', font=self.FONTS['med'], fill=self.COLOURS['white'])

        # If the first period, add "1st" to the image.
        if game['period_num'] == 1:
            self.draw['centre'].text((4, -1), '1', font=self.FONTS['med'], fill=self.COLOURS['white'])
            self.draw['centre'].text((8, -1), 's', font=self.FONTS['sm'], fill=self.COLOURS['white'])
            self.draw['centre'].text((12, -1), 't', font=self.FONTS['sm'], fill=self.COLOURS['white'])

        # If the second period, add "2nd" to the image.
        elif game['period_num'] == 2:
            self.draw['centre'].text((3, -1), '2', font=self.FONTS['med'], fill=self.COLOURS['white'])
            self.draw['centre'].text((9, -1), 'n', font=self.FONTS['sm'], fill=self.COLOURS['white'])
            self.draw['centre'].text((13, -1), 'd', font=self.FONTS['sm'], fill=self.COLOURS['white'])

        # If the third period, add "3rd" to the image.
        elif game['period_num'] == 3:
            self.draw['centre'].text((3, -1), '3', font=self.FONTS['med'], fill=self.COLOURS['white'])
            self.draw['centre'].text((9, -1), 'r', font=self.FONTS['sm'], fill=self.COLOURS['white'])
            self.draw['centre'].text((13, -1), 'd', font=self.FONTS['sm'], fill=self.COLOURS['white'])

        # If in shootout or first OT, add that to the image.
        elif game['period_type'] == 'SO' or (game['period_type'] == 'OT' and game['period_num'] == 4):
            self.draw['centre'].text((4, -1), game['period_type'], font=self.FONTS['med'], fill=self.COLOURS['white'])

        # Otherwise, we're in 2OT, or later. Calculate the number of OT periods and add that to the image.
        elif game['period_type'] == 'OT':
            per = f'{game['per_number'] - 3}{game['period_type']}'
            self.draw['centre'].text((1, -1), per, font=self.FONTS['med'], fill=self.COLOURS['white'])


    def add_final_playing_period_to_image(self, game):
        """ Adds final playing period to the centre image if game ended in OT, xOT, or a SO.

        Args:
            game (dict): Dictionary with all details of a specific game.
        """

        # If game ended in a SO or the first OT, add that to the centre image.
        if game['period_type'] == 'SO' or (game['period_type'] == 'OT' and game['period_num'] == 4): # If the game ended in single OT a SO.
            self.draw['centre'].text((4, 8), game['period_type'], font=self.FONTS['med'], fill=self.COLOURS['white'])

        # Or if in 2OT or later. Calculate the number of OT periods and add that to the centre image.
        elif game['period_type'] == 'OT':
            self.draw['centre'].text((1, 8), str(game['period_num'] - 3), font=self.FONTS['med'], fill=self.COLOURS['white'])
            self.draw['centre'].text((8, 8), game['period_type'], font=self.FONTS['med'], fill=self.COLOURS['white'])


    def should_display_time_remaining_in_playing_period(self, game):
        """ Determines if the time remaining in the playing period should be added to the centre image.

        Args:
            game (dict): Dictionary with all details of a specific game.

        Returns:
            Bool: f the time remaining in the playing period should be added to the centre image (True) or not (False).
        """

        if not game['is_intermission'] and game['period_type'] != 'SO':
            return True
        else:
            return False