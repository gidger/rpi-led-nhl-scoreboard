from .fav_team_next_game_scene import FavTeamNextGameScene
from setup.matrix_setup import matrix
import data.nhl_data
from utils import data_utils

from datetime import datetime as dt
from time import sleep


class NHLFavTeamNextGameScene(FavTeamNextGameScene):
    """ Favourite team next game scene for the NHL. Contains functionality to pull schedule data from NHL API, parse, and build+display images based on the result.
    This class extends the general Scene and FavTeamNextGameScene classes. An object of this class type is created when the scoreboard is started.
    """

    def __init__(self):
        """ Defines the league as NHL. Used to identify the correct files when adding logos to images.
        First runs init from the generic GameScene class.
        """
        
        super().__init__()
        self.LEAGUE = 'NHL'


    def display_scene(self):
        """ Displays the scene on the matrix.
        """

        # Refresh config and load to settings key.
        self.settings = data_utils.read_yaml('config.yaml')['scene_settings'][self.LEAGUE.lower()]['fav_team_next_game']
        self.favourite_teams = data_utils.read_yaml('config.yaml')['favourite_teams'][self.LEAGUE.lower()]
        self.alt_logos = data_utils.read_yaml('config.yaml')['alt_logos'][self.LEAGUE.lower()] if data_utils.read_yaml('config.yaml')['alt_logos'][self.LEAGUE.lower()] else {} # Note the teams with an alternative logo per config.yaml.

        # Determine next game for each fav team per config.yaml. Build images and display.
        for team in self.favourite_teams:
            next_game_details = data.nhl_data.get_next_game(team)
            self.build_next_game_image(team, next_game_details)
            
            self.transition_image(direction='in')
            sleep(self.settings['image_display_duration'])
            self.transition_image(direction='out')