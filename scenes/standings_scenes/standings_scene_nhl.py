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

        self.data = {
            'standings': None
        }

        # Get data... # TODO: for real...
        self.data['standings'] =  {
            'division': {
                'playoff_cutoff_hard': 3,
                'divisions': {
                    'Atl': [
                        {
                            'team_abrv': 'BOS',
                            'rank': 1,
                            'points': 114,
                            'has_clinched': True
                        },
                        {
                            'team_abrv': 'MTL',
                            'rank': 2,
                            'points': 18,
                            'has_clinched': True
                        },
                        {
                            'team_abrv': 'OTT',
                            'rank': 3,
                            'points': 16,
                            'has_clinched': False
                        },
                        {
                            'team_abrv': 'DET',
                            'rank': 4,
                            'points': 14,
                            'has_clinched': False
                        },
                        {
                            'team_abrv': 'TOR',
                            'rank': 5,
                            'points': 12,
                            'has_clinched': False
                        },
                        {
                            'team_abrv': 'TOR',
                            'rank': 10,
                            'points': 12,
                            'has_clinched': False
                        },
                        {
                            'team_abrv': 'TOR',
                            'rank': 11,
                            'points': 12,
                            'has_clinched': False
                        },
                        {
                            'team_abrv': 'TOR',
                            'rank': 12,
                            'points': 3,
                            'has_clinched': False
                        }
                    ],

                    'Met': [
                        {
                            'team_abrv': 'BOS',
                            'rank': 1,
                            'points': 114,
                            'has_clinched': True
                        },
                        {
                            'team_abrv': 'BOS',
                            'rank': 1,
                            'points': 114,
                            'has_clinched': False
                        },
                        {
                            'team_abrv': 'BOS',
                            'rank': 1,
                            'points': 114,
                            'has_clinched': True
                        },
                        {
                            'team_abrv': 'BOS',
                            'rank': 1,
                            'points': 114,
                            'has_clinched': False
                        }
                    ]
                }
            },

            'wildcard': {
                'conferences': {
                    'EWC': [

                    ],
                    'WWC': [

                    ]
                }
            },

            'conference': {
                'conferences': {
                    'E': [

                    ],
                    'W': [

                    ]
                }
            },

            'overall': {
                'OVR': [

                ]
            }
        }

        

        # Get data.

        if self.settings['display_splash']:
            self.display_splash_image()

        for type in self.settings['display_for']:
            if type == 'division':
                for div_name, standings in self.data['standings']['division']['divisions'].items():
                    print(div_name, standings)
                    self.build_standings_image('division', div_name, standings, self.data['standings']['division']['playoff_cutoff_hard'])
                    self.display_standing_images()
            
                

    def display_standing_images(self):
        self.transition_image(direction='in', image_already_combined=True)
        sleep(self.settings['image_display_duration'])
        self.slide_standings()
        sleep(self.settings['image_display_duration'])
        self.transition_image(direction='out', image_already_combined=True)

    def display_splash_image(self):
        # Build splash image, transition in, pause, transition out. 
        self.build_splash_image(dt.today().date(), None, None)
        self.transition_image(direction='in', image_already_combined=True)
        sleep(self.settings['image_display_duration'])
        self.transition_image(direction='out', image_already_combined=True)