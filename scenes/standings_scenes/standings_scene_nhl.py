from .standings_scene import StandingsScene
from setup.matrix_setup import matrix
import data.nhl_data
from utils import data_utils

from datetime import datetime as dt
from time import sleep


class NHLStandingsScene(StandingsScene):
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
        self.settings = data_utils.read_yaml('config.yaml')['scene_settings'][self.LEAGUE.lower()]['standings']
        self.favourite_teams = data_utils.read_yaml('config.yaml')['favourite_teams'][self.LEAGUE.lower()]

        if self.settings['display_splash']:
            self.display_splash_image()
        self.display_standing_image()

    def display_standing_image(self):
        self.build_standings_image(None, None)
        self.transition_image(direction='in', image_already_combined=True)
        # sleep(3)
        self.slide_standings()
        # sleep(3)
        self.transition_image(direction='out', image_already_combined=True)

    def display_splash_image(self):
        # Build splash image, transition in, pause, transition out. 
        self.build_splash_image(dt.today().date(), None, None)
        self.transition_image(direction='in', image_already_combined=True)
        sleep(self.settings['image_display_duration'])
        self.transition_image(direction='out', image_already_combined=True)