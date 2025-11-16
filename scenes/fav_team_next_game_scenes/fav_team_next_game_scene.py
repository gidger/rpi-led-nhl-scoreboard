from ..scene import Scene
from setup.matrix_setup import matrix, matrix_options
from utils import image_utils

from PIL import Image, ImageDraw
from time import sleep
import math


class FavTeamNextGameScene(Scene):
    """ Generic game scene, regardless of league/sport. Contains functionality to build score, no game today, etc. images and display them on the matrix.
    This class extends the general Scene class and is extended by those of specific leagues. An object of this class type is never created directly.
    """
    
    def __init__(self):
        """ Creates Image objects to be displayed on the matrix and ImageDraw objects allowing us to add logos, text, etc. to each image.
        First runs init from generic Scene class.
        """

        super().__init__()

        # Image objects.
        self.images = {
            'full':     Image.new('RGB', (matrix_options.cols, matrix_options.rows))
        }

        # ImageDraw objects associated with each of the above Image objects.
        self.draw = {
            'full':     ImageDraw.Draw(self.images['full'])
        }


    def build_next_game_image(self, team, game):
        """ Builds splash screen image.
        Includes league logo, date, and number of games on that date.

        Args:
            num_games (int): Number of games on the provided date.
            date (date): Date to display.
        """

        # TODO: Clean.

        # First, add the league logo image.
        self.add_team_logo_to_image(team)

        # Add 'Games' and a horizontal line.
        self.draw['full'].text((36, 0), 'Next', font=self.FONTS['med_bold'], fill=self.COLOURS['white'])
        self.draw['full'].line([(34, 10), (60, 10)], fill=self.COLOURS['white'])

        if game['is_today']:
            if game['has_started']:
                self.draw['full'].text((38, 11), 'IPR', font=self.FONTS['med'], fill=self.COLOURS['white'])
            else:
                time_str = game['start_datetime_local'].time().strftime('%I:%M')
                if time_str[0] == "1": # If the first digit of the time is 1. When 10:00-19:59 left in per/qtr, or game start on or after 10pm.
                    # Hour/minutes.
                    self.draw['full'].text((35, 11), time_str[0], font=self.FONTS['med'], fill=self.COLOURS['white']) # Need to acount for horizonal padding.
                    self.draw['full'].text((41, 11), time_str[1], font=self.FONTS['med'], fill=self.COLOURS['white'])
                    # Colon.
                    self.draw['full'].point((47, 15), fill=self.COLOURS['white'])
                    self.draw['full'].point((47, 17), fill=self.COLOURS['white'])
                    # Minutes/seconds.
                    self.draw['full'].text((49, 11), time_str[3], font=self.FONTS['med'], fill=self.COLOURS['white'])
                    self.draw['full'].text((55, 11), time_str[4], font=self.FONTS['med'], fill=self.COLOURS['white'])

                else: # If the first digit of the time is 0. When 0:00-9:59 left in per/qtr, or game start before 10pm.
                    # Hour/minutes.
                    self.draw['full'].text((38, 11), time_str[1], font=self.FONTS['med'], fill=self.COLOURS['white'])
                    # Colon.
                    self.draw['full'].point((44, 15), fill=self.COLOURS['white'])
                    self.draw['full'].point((44, 17), fill=self.COLOURS['white'])
                    # Minutes/seconds.
                    self.draw['full'].text((46, 11), time_str[3], font=self.FONTS['med'], fill=self.COLOURS['white'])
                    self.draw['full'].text((52, 11), time_str[4], font=self.FONTS['med'], fill=self.COLOURS['white'])
        else:
            # Note the month (3 char) and day number.
            month = game['start_datetime_local'].strftime('%b')
            day = game['start_datetime_local'].strftime('%-d')

            # Determine horizontal location, and add the date.
            month_col = 37 if len(day) == 1 else 35
            self.draw['full'].text((month_col, 12), month, font=self.FONTS['sm'], fill=self.COLOURS['white'])
            day_col = 53 if len(day) == 1 else 51
            self.draw['full'].text((day_col, 12), day, font=self.FONTS['sm'], fill=self.COLOURS['white'])

        if game['home_or_away'] == 'home':
            self.draw['full'].text((34, 23), 'V', font=self.FONTS['sm'], fill=self.COLOURS['white'])
            self.draw['full'].text((38, 23), 'S', font=self.FONTS['sm'], fill=self.COLOURS['white'])
            self.draw['full'].text((44, 21), game['opponent_abrv'], font=self.FONTS['med_bold'], fill=self.COLOURS['white'])
        else:
            self.draw['full'].text((35, 21), '@', font=self.FONTS['med'], fill=self.COLOURS['white'])
            self.draw['full'].text((43, 21), game['opponent_abrv'], font=self.FONTS['med_bold'], fill=self.COLOURS['white'])


    def add_team_logo_to_image(self, team):
        """ Adds logo for a specific league to the full image.
        League is determined in the extended class specific to each league.
        """

        # TODO: Alt logos. # TODO: Clean.

        # Determine the path of the image to load. Standard path or alt logo.
        logo_path = f'assets/images/{self.LEAGUE}/teams/{team.lower()}.png' if team not in self.alt_logos else f'assets/images/{self.LEAGUE}/teams_alt/{team.lower()}_{self.alt_logos[team]}.png'

        # Load, crop, and resize the league logo.
        team_logo = Image.open(logo_path)
        team_logo = image_utils.crop_image(team_logo)
        team_logo.thumbnail((30, 30))

        # Determine placement, centre within the left half of the matrix.
        row_location = math.floor(1 + (30 - team_logo.size[0]) / 2)
        col_location = math.ceil(1 + (30 - team_logo.size[1]) / 2)

        # Add it to the centre image.
        self.images['full'].paste(team_logo, (row_location, col_location))


    def transition_image(self, direction, image_already_combined=False):
        """ Transitions between image and blank screen or vise versa.
        Practically, this means the transition between games (one direction). Transition is set in config.yaml.

        Args:
            direction (str): Direction of the transition. 'in' or 'out'.
            image_already_combined (bool, optional): If the image was build directly to the full image. If true, skip building it here. Defaults to False.
        """

        # TODO: remove none full.

        # 'Cut' transition.
        if self.settings['transition'] == 'cut':
            if direction == 'in':
                # Build combined image if needed.
                if not image_already_combined:
                    self.images['full'].paste(self.images['left'], (-19, 1))
                    self.images['full'].paste(self.images['centre'], (22, 1))
                    self.images['full'].paste(self.images['right'], (43, 1))
                
                # Since there's no animation of any sort, an out transition is not needed. Simply display the image on the matrix.
                matrix.SetImage(self.images['full'])
        
        # 'Fade' transition.
        elif self.settings['transition'] == 'fade':
            # Define the 'fade rule', that is the steps between 0 (transparent) and 255 (opaque).
            fade = (255, -1, -15) if direction == 'in' else (0, 256, 15)

            # Build combined image if needed.
            if not image_already_combined:
                self.images['full'].paste(self.images['left'], (-19, 1))
                self.images['full'].paste(self.images['centre'], (22, 1))
                self.images['full'].paste(self.images['right'], (43, 1))

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
                        self.images['full'].paste(self.images['left'], (-19 + col_offset, 1))
                        self.images['full'].paste(self.images['centre'], (22 + col_offset, 1))
                        self.images['full'].paste(self.images['right'], (43 + col_offset, 1))          
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
                        self.images['full'].paste(self.images['left'], (-19 + col_offset, 1))
                        self.images['full'].paste(self.images['centre'], (22 + col_offset, 1))
                        self.images['full'].paste(self.images['right'], (43 + col_offset, 1))       
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