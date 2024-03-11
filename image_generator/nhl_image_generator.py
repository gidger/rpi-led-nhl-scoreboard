from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw, ImageFont
import time
import math
from utils import image_utils

class NHLScoreboardImageGenerator:
    """ NHL scoreboard image to be displayed on LED matrix. """

    def __init__(self, rows, cols, h_buffer) -> None:
        """ Creates constants that need to be refereced as well as Image and ImageDraw objects to control the image.

        Args:
            rows (int): Number of rows on the LED matrix.
            cols (int): Number of cols on the LED matrix.
        """

        # Package up the image dimensions as a tuple for easy reference later.
        self.H_BUFFER = h_buffer
        self.IMAGE_DIMS = (cols + 2 * self.H_BUFFER, rows)

        # Fonts.
        self.FONT_SML = ImageFont.load('assets/fonts/pil/Tamzen5x9r.pil')
        self.FONT_SML_BOLD = ImageFont.load('assets/fonts/pil/Tamzen5x9b.pil')
        self.FONT_MD = ImageFont.load('assets/fonts/pil/Tamzen6x12r.pil')
        self.FONT_MD_BOLD = ImageFont.load('assets/fonts/pil/Tamzen6x12b.pil')
        self.FONT_LRG = ImageFont.load('assets/fonts/pil/Tamzen8x15r.pil')
        self.FONT_LRG_BOLD = ImageFont.load('assets/fonts/pil/Tamzen8x15b.pil')

        # Text colours.
        self.COLOUR_WHITE = (255, 255, 255, 255)
        self.COLOUR_BLACK = (0, 0, 0, 255)
        self.COLOUR_RED = (255, 50, 50, 255)

        # Define the first col that can be used for center text (i.e., the first col you can use without worry of overlapping a team logo).
        self.LEFTMOST_MIDDLE_COL = 21 + self.H_BUFFER

        # Size for logos to be displayed.
        self.LOGO_SIZE = (40, 30)

        # Create an Image object that will be displayed on the matrix and an ImageDraw object to write shapes and text onto the Image.
        self.image = Image.new('RGB', self.IMAGE_DIMS)
        self.draw = ImageDraw.Draw(self.image)


    def clear_image(self) -> None:
        """ 'Clears' the image by adding a black rectange over the entire image. """

        self.draw.rectangle(((0, 0), self.IMAGE_DIMS), fill=(0,0,0,0))


    def build_loading(self) -> None:
        """ Adds all aspects of the loading screen to the image object. """
        
        # Add the NHL logo and 'Now Loading' the image.
        self.add_nhl_logo()
        self.draw.text((self.H_BUFFER + 29, 8), 'Now', font=self.FONT_SML, fill=self.COLOUR_WHITE)
        self.draw.text((self.H_BUFFER + 29, 16), 'Loading', font=self.FONT_SML, fill=self.COLOUR_WHITE)


    def build_no_games(self, date) -> None:
        """ Adds all aspects of the no games today screen to the image object

        Args:
            date (date): Date to display that there's no games on.
        """

        # Add the NHL logo to the image.
        self.add_nhl_logo()

        # Add 'No Games' and the date to the image
        self.draw.text((self.H_BUFFER + 32, 0), 'No', font=self.FONT_MD, fill=self.COLOUR_WHITE)
        self.draw.text((self.H_BUFFER + 32, 10), 'Games', font=self.FONT_MD, fill=self.COLOUR_WHITE)
        self.draw.text((self.H_BUFFER + 32, 21), date.strftime('%b %-d'), font=self.FONT_SML, fill=self.COLOUR_WHITE)


    def build_game_not_started(self, game) -> None:
        """ Adds all aspects of the game not started screen to the image object.

        Args:
            game (dict): All information for a specific game.
        """

        # Add the logos of the teams inivolved to the image.
        self.add_team_logos(game['away_team'], game['home_team'])

        # Add 'Today' to the image.
        self.draw.text((self.LEFTMOST_MIDDLE_COL + 1, 0), 'T', font=self.FONT_MD, fill=self.COLOUR_WHITE)
        self.draw.text((self.LEFTMOST_MIDDLE_COL + 5, 2), 'o', font=self.FONT_SML, fill=self.COLOUR_WHITE)
        self.draw.text((self.LEFTMOST_MIDDLE_COL + 9, 2), 'd', font=self.FONT_SML, fill=self.COLOUR_WHITE)
        self.draw.text((self.LEFTMOST_MIDDLE_COL + 13, 2), 'a', font=self.FONT_SML, fill=self.COLOUR_WHITE)
        self.draw.text((self.LEFTMOST_MIDDLE_COL + 17, 2), 'y', font=self.FONT_SML, fill=self.COLOUR_WHITE)

        # Add '@' to the image.
        self.draw.text((self.LEFTMOST_MIDDLE_COL + 6, 8), '@', font=self.FONT_LRG, fill=self.COLOUR_WHITE)

        # Extract the start time in 12 hour format and add to the image.
        start_time = game['start_time'].time().strftime('%I:%M')
        self.add_time(game['status'], start_time)


    def build_game_in_progress(self, game) -> None:
        """ Adds all aspects of the game in progress screen to the image object.

        Args:
            game (dict): All information for a specific game.
        """

        # Add the logos of the teams inivolved to the image.
        self.add_team_logos(game['away_team'], game['home_team'])

        # Add the period and time remaining to the image. If in intermission or SO, don't display a time.
        self.add_period(game['period_num'], game['period_type'], game['is_intermission'])
        if not game['is_intermission'] and game['period_type'] != 'SO':
            self.add_time(game['status'], game['period_time_remaining'])        

        # Add the current score to the image, noting if either team scored since previous data pull.
        self.add_scores(game['away_score'], game['home_score'], game['away_team_scored'], game['home_team_scored'])


    def build_game_over(self, game) -> None:
        """ Adds all aspects of the game over screen to the image object.

        Args:
            game (dict): All information for a specific game.
        """

        # Add the logos of the teams involved to the image.
        self.add_team_logos(game['away_team'], game['home_team'])

        # Add 'Final' to the image.
        self.draw.text((self.LEFTMOST_MIDDLE_COL + 1, 0), 'F', font=self.FONT_MD, fill=self.COLOUR_WHITE)
        self.draw.text((self.LEFTMOST_MIDDLE_COL + 5, 2), 'i', font=self.FONT_SML, fill=self.COLOUR_WHITE)
        self.draw.text((self.LEFTMOST_MIDDLE_COL + 9, 2), 'n', font=self.FONT_SML, fill=self.COLOUR_WHITE)
        self.draw.text((self.LEFTMOST_MIDDLE_COL + 14, 2), 'a', font=self.FONT_SML, fill=self.COLOUR_WHITE)
        self.draw.text((self.LEFTMOST_MIDDLE_COL + 17, 2), 'l', font=self.FONT_SML, fill=self.COLOUR_WHITE)

        # If game ended in a SO or the first OT, add that to the image.
        if game['period_type'] == 'SO' or (game['period_type'] == 'OT' and game['period_num'] == 4): # If the game ended in OT a SO or later.
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 6, 9), game['period_type'], font=self.FONT_MD, fill=self.COLOUR_WHITE)

        # Or if in 2OT or later. Calculate the number of OT periods and add that to the image.
        elif game['period_type'] == 'OT':
            per = f"{game['period_num'] - 3}{game['period_type']}"
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 3, 9), per, font=self.FONT_MD, fill=self.COLOUR_WHITE)

        # Add the current score to the image, noting if either team scored since previous data pull.
        self.add_scores(game['away_score'], game['home_score'], game['away_team_scored'], game['home_team_scored'])


    def add_nhl_logo(self) -> None:
        """ Adds the NHL logo to the image object. """
        
        # Load, crop, and resize the NHL logo. Then add to image.
        nhl_logo = Image.open('assets/images/logos/png/NHL.png')
        nhl_logo = image_utils.crop_image(nhl_logo)
        nhl_logo.thumbnail(self.LOGO_SIZE)
        self.image.paste(nhl_logo, (self.H_BUFFER + 1, 1))


    def add_team_logos(self, away_team, home_team) -> None:
        """ Adds the logos of the home and away teams to the image object, making sure to not overlap logos and center text.

        Args:
            away_team (string): Abbreviation of the away team.
            home_team (string): Abbreviation of the home team.
        """

        # Load, crop, and resize the away team logo.
        away_logo = Image.open(f'assets/images/logos/png/{away_team}.png')
        away_logo = image_utils.crop_image(away_logo)
        away_logo.thumbnail(self.LOGO_SIZE)

        # Load, crop, and resize the home team logo.
        home_logo = Image.open(f'assets/images/logos/png/{home_team}.png')
        home_logo = image_utils.crop_image(home_logo)
        home_logo.thumbnail(self.LOGO_SIZE)

        # Record the width and heights of the logos.
        away_logo_width, away_logo_height = away_logo.size
        home_logo_width, home_logo_height = home_logo.size

        # Add the logos to the image. Logos will be bounded by the text region, and be centered vertically.
        self.image.paste(away_logo, (self.LEFTMOST_MIDDLE_COL - away_logo_width, math.floor((self.IMAGE_DIMS[1] - away_logo_height) / 2))) # TODO: Revise this logic to be cleaner.
        self.image.paste(home_logo, ((self.IMAGE_DIMS[0] - self.LEFTMOST_MIDDLE_COL), math.floor((self.IMAGE_DIMS[1] - home_logo_height) / 2)))


    def add_time(self, status, time_str) -> None:
        """ Adds time to the image object. Both for upcoming games and games in progress.

        Args:
            status (string): Status of the game.
            time_str (string): Time to display, as a string in 'HH:MM' or 'MM:SS' format.
        """

        # Offset position vertically for games that haven't started.
        vertical_offset = 13 if status not in ['LIVE', 'CRIT'] else 0

        # If the first digit of the time is 2. Should only occure when 20 mins left in period, never for start time.
        if time_str[0] == "2":
            # Minutes.
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 1, 9 + vertical_offset), time_str[0], font=self.FONT_SML, fill=self.COLOUR_WHITE)
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 5, 9 + vertical_offset), time_str[1], font=self.FONT_SML, fill=self.COLOUR_WHITE)
            # Colon (manual dots since the font's colon looks funny).
            self.draw.rectangle(((self.LEFTMOST_MIDDLE_COL + 10, 12 + vertical_offset),(self.LEFTMOST_MIDDLE_COL + 10, 12 + vertical_offset)), fill=self.COLOUR_WHITE)
            self.draw.rectangle(((self.LEFTMOST_MIDDLE_COL + 10, 14 + vertical_offset),(self.LEFTMOST_MIDDLE_COL + 10, 14 + vertical_offset)), fill=self.COLOUR_WHITE)
            # Seconds.
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 12, 9 + vertical_offset), time_str[3], font=self.FONT_SML, fill=self.COLOUR_WHITE) # Skipping time_str[2] as that would be the colon.
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 16, 9 + vertical_offset), time_str[4], font=self.FONT_SML, fill=self.COLOUR_WHITE)

        # If the first digit of the time is 1. When 10:00-19:59 left in period, or game start on or after 10pm.
        elif time_str[0] == "1":
            # Hours/minutes.
            self.draw.text((self.LEFTMOST_MIDDLE_COL, 9 + vertical_offset), time_str[0], font=self.FONT_SML, fill=self.COLOUR_WHITE)
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 5, 9 + vertical_offset), time_str[1], font=self.FONT_SML, fill=self.COLOUR_WHITE)
            # Colon.
            self.draw.rectangle(((self.LEFTMOST_MIDDLE_COL + 10, 12 + vertical_offset), (self.LEFTMOST_MIDDLE_COL + 10, 12 + vertical_offset)), fill=self.COLOUR_WHITE)
            self.draw.rectangle(((self.LEFTMOST_MIDDLE_COL + 10, 14 + vertical_offset), (self.LEFTMOST_MIDDLE_COL + 10, 14 + vertical_offset)), fill=self.COLOUR_WHITE)
            # Minutes/seconds.
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 12, 9 + vertical_offset), time_str[3], font=self.FONT_SML, fill=self.COLOUR_WHITE)
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 17, 9 + vertical_offset), time_str[4], font=self.FONT_SML, fill=self.COLOUR_WHITE)

        else: # If the first digit of the time is 0. When 0:00-9:59 left in period, or game start before 10pm.
            # Hours/minutes.
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 3, 9 + vertical_offset), time_str[1], font=self.FONT_SML, fill=self.COLOUR_WHITE)
            # Colon.
            self.draw.rectangle(((self.LEFTMOST_MIDDLE_COL + 8, 12 + vertical_offset),(self.LEFTMOST_MIDDLE_COL + 8, 12 + vertical_offset)), fill=self.COLOUR_WHITE)
            self.draw.rectangle(((self.LEFTMOST_MIDDLE_COL + 8, 14 + vertical_offset),(self.LEFTMOST_MIDDLE_COL + 8, 14 + vertical_offset)), fill=self.COLOUR_WHITE)
            # Minutes/seconds.
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 10, 9 + vertical_offset), time_str[3], font=self.FONT_SML, fill=self.COLOUR_WHITE)
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 15, 9 + vertical_offset), time_str[4], font=self.FONT_SML, fill=self.COLOUR_WHITE)


    def add_period(self, per_number, per_type, is_intermission) -> None:
        """ Adds the current period to the image object.

        Args:
            per_number (int): Period number.
            per_type (string): Text descriptor of the period
            is_intermission (bool): If currently in an intermission.
        """

        # If intermission, add "INT" to the image.
        if is_intermission:
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 2, 8), 'INT', font=self.FONT_MD, fill=self.COLOUR_WHITE)

        # If the first period, add "1st" to the image.
        if per_number == 1:
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 5, 0), '1', font=self.FONT_MD, fill=self.COLOUR_WHITE)
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 9, 0), 's', font=self.FONT_SML, fill=self.COLOUR_WHITE)
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 13, 0), 't', font=self.FONT_SML, fill=self.COLOUR_WHITE)

        # If the second period, add "2nd" to the image.
        elif per_number == 2:
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 4, 0), '2', font=self.FONT_MD, fill=self.COLOUR_WHITE)
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 10, 0), 'n', font=self.FONT_SML, fill=self.COLOUR_WHITE)
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 14, 0), 'd', font=self.FONT_SML, fill=self.COLOUR_WHITE)

        # If the third period, add "3rd" to the image.
        elif per_number == 3:
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 4, 0), '3', font=self.FONT_MD, fill=self.COLOUR_WHITE)
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 10, 0), 'r', font=self.FONT_SML, fill=self.COLOUR_WHITE)
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 14, 0), 'd', font=self.FONT_SML, fill=self.COLOUR_WHITE)

        # If in shootout or first OT, add that to the image.
        elif per_type == 'SO' or (per_type == 'OT' and per_number == 4):
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 5, 0), per_type, font=self.FONT_MD, fill=self.COLOUR_WHITE)

        # Otherwise, we're in 2OT, or later. Calculate the number of OT periods and add that to the image.
        elif per_type == 'OT':
            per = f'{per_number - 3}{per_type}'
            self.draw.text((self.LEFTMOST_MIDDLE_COL + 2, 0), per, font=self.FONT_MD, fill=self.COLOUR_WHITE)


    def add_scores(self, away_score, home_score, away_team_scored=None, home_team_scored=None, goal_fade_colour_override=None) -> None:
        """ Adds the score for both teams to the image object.

        Args:
            away_score (int): Away team score.
            home_score (int): Home team score.
            away_team_scored (bool, optional): If the away team scored since the previous data pull. Defaults to None.
            home_team_scored (bool, optional): If the home team scored since the previous data pull.. Defaults to None.
            goal_fade_colour_override (tuple, optional): Colour to override the score team with, used for goal fading. Defaults to None.
        """

        # If the away team scored and there's no colour override specified, set the away colour to red.  If the override is specified, set the away colour to the override.
        if away_team_scored and not goal_fade_colour_override:
            away_colour = self.COLOUR_RED
        elif away_team_scored and goal_fade_colour_override:
            away_colour = goal_fade_colour_override
        else: # Othwise, just white.
            away_colour = self.COLOUR_WHITE

        # If the home team scored and there's no colour override specified, set the away colour to red.  If the override is specified, set the away colour to the override.
        if home_team_scored and not goal_fade_colour_override:
            home_colour = self.COLOUR_RED
        elif home_team_scored and goal_fade_colour_override:
            home_colour = goal_fade_colour_override
        else: # Othwise, just white.
            home_colour = self.COLOUR_WHITE

        # Add the hypen to the image.
        self.draw.text((self.LEFTMOST_MIDDLE_COL + 9, 20), "-", font=self.FONT_SML_BOLD, fill=self.COLOUR_WHITE)

        # Add the scores to the image.
        self.draw.text((self.LEFTMOST_MIDDLE_COL + 1, 17), str(away_score), font=self.FONT_LRG_BOLD, fill=away_colour)
        self.draw.text((self.LEFTMOST_MIDDLE_COL + 13, 17), str(home_score), font=self.FONT_LRG_BOLD, fill=home_colour)

    def add_error_notifier(self) -> None:
        """ Sets the bottom right LED red. """

        self.draw.rectangle(((63 + scoreboard_image.H_BUFFER, 31), (63 + scoreboard_image.H_BUFFER, 31)), fill=self.COLOUR_RED)