from ..scene import Scene
from setup.matrix_setup import matrix, matrix_options
from utils import image_utils

from PIL import Image, ImageDraw
from time import sleep
import math


class StandingsScene(Scene):
    """ Generic scene for favourite teams next games, regardless of league/sport. Contains functionality to build images and display them on the matrix.
    This class extends the general Scene class and is extended by those of specific leagues. An object of this class type is never created directly.
    """
    
    def __init__(self):
        """ Creates Image object to be displayed on the matrix and ImageDraw object allowing us to add logos, text, etc. to the image.
        First runs init from generic Scene class.
        """

        super().__init__()

        self.images = {
            # 'top':      Image.new('RGB', (matrix_options.cols, 8)),
            # 'bottom':   Image.new('RGB', (matrix_options.cols, 24)),
            'side':     Image.new('RGB', (8, matrix_options.rows)),
            # '8_team':   Image.new('RGB', (56, 64)),
            # '10_team':  Image.new('RGB', (56, 80)),
            'main':     Image.new('RGB', (56, 80)),
            'full':     Image.new('RGB', (matrix_options.cols, matrix_options.rows))
        }

        # ImageDraw object associated with each of the above Image objects.
        self.draw = {
            # 'top':      ImageDraw.Draw(self.images['top']),
            # 'bottom':   ImageDraw.Draw(self.images['bottom']),
            'side':     ImageDraw.Draw(self.images['side']),
            # '8_team':   ImageDraw.Draw(self.images['8_team']),
            # '10_team':  ImageDraw.Draw(self.images['10_team']),
            'main':     ImageDraw.Draw(self.images['main']),
            'full':     ImageDraw.Draw(self.images['full'])
        }


    def build_standings_image(self, type, name):
        """ Builds next game image for the specified team and game.

        Args:
            team (str): Team abv to build next game image for.
            game (dit): Dict of next game details.
        """

        # Should be able to build the image by looping over the standings object.
        # Then add the nums, team abvs, and pts.
        # Will need dynamic spacing for points, should be right aligned against the right edge of the matrix.
        test_standings = {
            'type': 'division',
            'name': 'Atl',
            'playoff_cutoff': 3,
            'standings': 
                [
                    {
                        'team_abv': 'BOS',
                        'rank': 1,
                        'points': 114,
                        'in_playoff_position': True
                    },
                    {
                        'team_abv': 'MTL',
                        'rank': 2,
                        'points': 18,
                        'in_playoff_position': True
                    },
                    {
                        'team_abv': 'OTT',
                        'rank': 3,
                        'points': 16,
                        'in_playoff_position': True
                    },
                    {
                        'team_abv': 'DET',
                        'rank': 4,
                        'points': 14,
                        'in_playoff_position': False
                    },
                    {
                        'team_abv': 'TOR',
                        'rank': 5,
                        'points': 12,
                        'in_playoff_position': False
                    },
                    {
                        'team_abv': 'TOR',
                        'rank': 6,
                        'points': 12,
                        'in_playoff_position': False
                    },
                    {
                        'team_abv': 'TOR',
                        'rank': 7,
                        'points': 12,
                        'in_playoff_position': False
                    },
                    {
                        'team_abv': 'TOR',
                        'rank': 8,
                        'points': 12,
                        'in_playoff_position': False
                    }
                ]
        }

        # For sidways text.
        tmp_img = Image.new('RGB', (32, 8))
        tmp_draw = ImageDraw.Draw(tmp_img)
        tmp_draw.rectangle([(0, 0), (32, 8)], fill=self.COLOURS['white'])
        # tmp_draw.text((1, 0), 'Atl', font=self.FONTS['sm'], fill=self.COLOURS['black'])
        # tmp_draw.text((17, 0), 'Div', font=self.FONTS['sm'], fill=self.COLOURS['black'])
        tmp_draw.text((1, 0), self.LEAGUE, font=self.FONTS['sm'], fill=self.COLOURS['black'])
        tmp_draw.text((17, 0), test_standings['name'], font=self.FONTS['sm'], fill=self.COLOURS['black']) # TODO: Make dynamic.
        tmp_img = tmp_img.rotate(90, expand=True)
        self.images['side'].paste(tmp_img, (0,0))

        # Building 'main' image.
        offset = -1
        itt = 0
        for team in test_standings['standings']: # Will need to do a zip that uses a range to calculate the offset.
            line_colour = self.COLOURS['red'] if itt == 3 else self.COLOURS['grey_dark']
            team_colour = self.COLOURS['yellow'] if team['team_abv'] in self.favourite_teams else self.COLOURS['white']
            self.draw['main'].line([(1, offset), (54, offset)], fill=line_colour)
            self.draw['main'].text((1, offset), str(team['rank']), font=self.FONTS['sm'], fill=team_colour)
            self.draw['main'].text((13, offset), team['team_abv'], font=self.FONTS['sm'], fill=team_colour) # TODO: Make more centered?
            self.draw['main'].text((46, offset), str(team['points']), font=self.FONTS['sm'], fill=team_colour) # TODO: make placement dynamic based on num points to keep right aligned.
            offset += 8
            itt += 1

        self.images['full'].paste(self.images['side'], (0, 0))
        self.images['full'].paste(self.images['main'], (8 , 0))
        matrix.SetImage(self.images['full'])


    def slide_standings(self, num_teams=8):

        delta = matrix_options.rows - self.images['main'].size[1] 
        for offset in range(0, delta - 1, -1):
            image_utils.clear_image(self.images['full'], self.draw['full'])
            self.images['full'].paste(self.images['side'], (0, 0))
            self.images['full'].paste(self.images['main'], (8 , offset))
            matrix.SetImage(self.images['full'])
            sleep(0.1)
            if offset % 8 == 0:
                sleep(1.5)
            if offset == -4 * num_teams:
                break

    def build_splash_image(self, date, type, name):
        """ Builds splash screen image.
        Includes league logo, date, and number of games on that date.

        Args:
            num_games (int): Number of games on the provided date.
            date (date): Date to display.
        """

         # First, add the league logo image.
        self.add_league_logo_to_image()

        # Add 'Games' and a horizontal line.
        self.draw['full'].text((33, 0), 'Stand', font=self.FONTS['med_bold'], fill=self.COLOURS['white'])
        self.draw['full'].line([(32, 10), (62, 10)], fill=self.COLOURS['white'])

        # # Determine horizontal location, and add the number of games.
        # num_games_col = 45 if len(str(num_games)) == 1 else 42
        # self.draw['full'].text((num_games_col, 12), str(num_games), font=self.FONTS['med'], fill=self.COLOURS['white'])

        # # Add type... # TODO: make this dynamically centre.
        # self.draw['full'].text((36, 12), 'East', font=self.FONTS['med'], fill=self.COLOURS['white']) # TODO: actually make this taken as an input.
        self.draw['full'].text((38, 12), 'ATL', font=self.FONTS['med'], fill=self.COLOURS['white']) # TODO: actually make this taken as an input.
        # self.draw['full'].text((50, 12), 'Div', font=self.FONTS['sm'], fill=self.COLOURS['white'])

        # self.draw['full'].text((33, 11), 'Atl', font=self.FONTS['med'], fill=self.COLOURS['white']) # TODO: actually make this taken as an input.
        # self.draw['full'].text((33, 21), 'Div', font=self.FONTS['med'], fill=self.COLOURS['white'])

        # Note the month (3 char) and day number.
        month = date.strftime('%b')
        day = date.strftime('%-d')

        # Determine horizontal location, and add the date.
        month_col = 37 if len(day) == 1 else 35
        self.draw['full'].text((month_col, 22), month, font=self.FONTS['sm'], fill=self.COLOURS['white'])
        day_col = 53 if len(day) == 1 else 51
        self.draw['full'].text((day_col, 22), day, font=self.FONTS['sm'], fill=self.COLOURS['white'])


    def add_league_logo_to_image(self):
        """ Adds logo for a specific league to the full image.
        League is determined in the extended class specific to each league.
        """

        # Load, crop, and resize the league logo.
        league_logo = Image.open(f'assets/images/{self.LEAGUE}/league/{self.LEAGUE}.png')
        league_logo = image_utils.crop_image(league_logo)
        league_logo.thumbnail((30, 30))

        # Determine placement, centre within the left half of the matrix.
        row_location = math.floor(1 + (30 - league_logo.size[0]) / 2)
        col_location = math.ceil(1 + (30 - league_logo.size[1]) / 2)

        # Add it to the centre image.
        self.images['full'].paste(league_logo, (row_location, col_location))



    def transition_image(self, direction, image_already_combined=False):
        """ Transitions between image and blank screen or vise versa.
        Practically, this means the transition between games (one direction). Transition is set in config.yaml.

        Args:
            direction (str): Direction of the transition. 'in' or 'out'.
            image_already_combined (bool, optional): If the image was build directly to the full image. If true, skip building it here. Defaults to False.
        """

        # 'Cut' transition.
        if self.settings['transition'] == 'cut':
            if direction == 'in':
                # Build combined image if needed.
                if not image_already_combined:
                    self.images['full'].paste(self.images['side'], (0, 0))
                    self.images['full'].paste(self.images['main'], (8, 0))
                
                # Since there's no animation of any sort, an out transition is not needed. Simply display the image on the matrix.
                matrix.SetImage(self.images['full'])
        
        # 'Fade' transition.
        elif self.settings['transition'] == 'fade':
            # Define the 'fade rule', that is the steps between 0 (transparent) and 255 (opaque).
            fade = (255, -1, -15) if direction == 'in' else (0, 256, 15)

            # Build combined image if needed.
            if not image_already_combined:
                self.images['full'].paste(self.images['side'], (0, 0))
                self.images['full'].paste(self.images['main'], (8, 0))

            # Loop over opacities to apply to image.
            for overlay_opacity in range(*fade):
                # Create faded image to display on matrix.
                faded_for_display_image = self.create_faded_image(self.images['full'], overlay_opacity)

                # Display and sleep for a short time to pace the animation.
                matrix.SetImage(faded_for_display_image)
                sleep(0.025)

            # Hold a moment with nothing displayed after fading out.
            if direction == 'out':
                sleep(0.2)

        # 'Modern' transition.
        elif self.settings['transition'] == 'modern':
            # Define the 'fade rule', that is the steps between 0 (transparent) and 255 (opaque).
            fade = (255, -1, -15) if direction == 'in' else (0, 256, 15)

            # If the final image already exists, make a copy for later use.
            if image_already_combined:
                combined_image = self.images['full'].copy()

            if direction == 'in':
                # Loop over opacities to apply to image and horizontal movement via col_offset.
                for overlay_opacity, col_offset in zip(range(*fade), range(-len(range(*fade))+1, 1, 1)):
                    # Rebuild full image with offsets. Will first need to clear the image. This will also ensure there's no artifacts between loops of animation.    
                    image_utils.clear_image(self.images['full'], self.draw['full'])
                    
                    # If the image has not already been combined, add each sub-image to the full with a col_offset applied.
                    if not image_already_combined: 
                        self.images['full'].paste(self.images['side'], (0 + col_offset, 0))
                        self.images['full'].paste(self.images['main'], (8 + col_offset, 0))   
                    # Otherwise, copy the combined_image copied above to full with a col_offset applied.
                    else:
                        self.images['full'].paste(combined_image, (col_offset, 0))

                    # Create faded image to display on matrix.
                    faded_for_display_image = self.create_faded_image(self.images['full'], overlay_opacity)

                    # Display and sleep for a short time to pace the animation.
                    matrix.SetImage(faded_for_display_image)
                    sleep(0.025)
            
            elif direction == 'out':
                # Loop over opacities to apply to image and horizontal movement via col_offset.
                for overlay_opacity, col_offset in zip(range(*fade), range(0, len(range(*fade)), 1)):
                    # Rebuild full image with offsets. Will first need to clear the image. This will also ensure there's no artifacts between loops of animation.    
                    image_utils.clear_image(self.images['full'], self.draw['full'])
                    
                    # If the image has not already been combined, add each sub-image to the full with a col_offset applied.
                    if not image_already_combined:                        
                        self.images['full'].paste(self.images['side'], (0 + col_offset, 0))
                        self.images['full'].paste(self.images['main'], (8 + col_offset, 0))      
                    # Otherwise, copy the combined_image copied above to full with a col_offset applied.
                    else:
                        self.images['full'].paste(combined_image, (col_offset, 0))

                    # Create faded image to display on matrix.
                    faded_for_display_image = self.create_faded_image(self.images['full'], overlay_opacity)

                    # Display and sleep for a short time to pace the animation.
                    matrix.SetImage(faded_for_display_image)
                    sleep(0.025)

                # Hold a moment with nothing displayed.
                sleep(0.2)

        # On way out of 'out' transitions, reset all images to black for next image build.
        if direction == 'out':
            for image, image_draw in zip(self.images.values(), self.draw.values()):
                image_utils.clear_image(image, image_draw)