from .fav_team_next_game_scene import FavTeamNextGameScene
from setup.matrix_setup import matrix
import data.nhl_data
from utils import data_utils, date_utils

from datetime import datetime as dt
from time import sleep


class NHLFavTeamNextGameScene(FavTeamNextGameScene):
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
        self.settings = data_utils.read_yaml('config.yaml')['scene_settings'][self.LEAGUE.lower()]['fav_team_next_game']
        self.favourite_teams = data_utils.read_yaml('config.yaml')['favourite_teams'][self.LEAGUE.lower()]
        self.alt_logos = data_utils.read_yaml('config.yaml')['alt_logos'][self.LEAGUE.lower()] if data_utils.read_yaml('config.yaml')['alt_logos'][self.LEAGUE.lower()] else {} # Note the teams with an alternative logo per config.yaml.

        # TODO: Clean

        # Get current day game data. Save this for future reference.
        self.data = {
            'date_pulled': None, # dt.today().date(), # Note the previous date.
            'next_game': {}
        }

        # Determine next game for each team in fav teams.
        for team in self.favourite_teams:
            # self.data['next_game'][team] = data.nhl_data.get_next_game(team)
            # print(self.data['next_game'][team])
            next_game_details = data.nhl_data.get_next_game(team)
            self.build_next_game_image(team, next_game_details)
            self.transition_image(direction='in', image_already_combined=True)
            sleep(self.settings['image_display_duration'])
            self.transition_image(direction='out', image_already_combined=True)