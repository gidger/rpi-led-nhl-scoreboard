import math
import time
import datetime as dt
from utils import data_utils


def display_image(matrix, scoreboard_image, transition_type, display_duration, goal_fade_animation=None, away_score=None, home_score=None, away_team_scored=None, home_team_scored=None) -> None:
    """ Displays an image on the matrix with whatever tranitions were specified. Will also fade a goal if the user enabled that option.

    Args:
        matrix (matrix): Matrix object.
        scoreboard_image (NHLScoreboardImageGenerator): NHLScoreboardImageGenerator object that builds images.
        transition_type (str): Transition type to use.
        display_duration (int): How long to stay on a single image for.
        goal_fade_animation (bool, optional): If the score should fade back to white following a goal. Defaults to None.
        away_score (int, optional): Away team score. Defaults to None.
        home_score (int, optional): Home team score. Defaults to None.
        away_team_scored (bool, optional): If the away team has scored since the previous data load. Defaults to None.
        home_team_scored (bool, optional): If the home team has scored since the previous data load. Defaults to None.
    """

    # Transition image in.
    transition(matrix, scoreboard_image, transition_type=transition_type, transition_direction='in')

    # If goal was scored, and goal_fade_animation=True, fade the score from red to white.
    if goal_fade_animation and (away_team_scored or home_team_scored):
        goal_fade(matrix, scoreboard_image, away_score, home_score, away_team_scored, home_team_scored)
    
    # Stay on the image, then transition out.
    time.sleep(display_duration)
    transition(matrix, scoreboard_image, transition_type=transition_type, transition_direction='out')


def goal_fade(matrix, scoreboard_image, away_score, home_score, away_team_scored, home_team_scored):
    """ Fades score from red to white after goal is scored.

    Args:
        matrix (matrix): Matrix object.
        scoreboard_image (NHLScoreboardImageGenerator): NHLScoreboardImageGenerator object that builds images.
        away_score (int): Away team score.
        home_score (int): Home team score.
        away_team_scored (bool): If the away team has scored since the previous data load.
        home_team_scored (bool): If the home team has scored since the previous data load.
    """

    # Stay on red for two seconds.
    time.sleep(2)

    # Since we know that for this situation the green (1th element of colour tuple) and blue (2th element of colour tuple) values are the same, we can just look at one to determine range that we must fade.
    # Don't like this solution. Try to make this more dynaimc and accept any two colours.
    # Fade from red to white. Iterate through the colours and set the image, very short pause in between to look like a smooth fade.
    for n in range(scoreboard_image.COLOUR_RED[2], scoreboard_image.COLOUR_WHITE[2]):
        scoreboard_image.add_scores(away_score, home_score, away_team_scored, home_team_scored, goal_fade_colour_override=(255, n, n, 255))
        matrix.SetImage(scoreboard_image.image)
        time.sleep(.015)


def transition(matrix, scoreboard_image, transition_type, transition_direction) -> None:
    """ Transitions the new image onto the matrix. Transition used depends on user setting in config.yaml.

    Args:
        matrix (matrix): Matrix object.
        scoreboard_image (NHLScoreboardImageGenerator): NHLScoreboardImageGenerator object that builds images.
        transition_type (str): Which transition to use.
        transition_direction (str): If the transition should be in or out.
    """

    # Record the current brightness and list of brightnesses to use when fading.
    led_brightness_cur = matrix.brightness
    brightness_steps = generate_brightness_fade_list(led_brightness_cur, 15)

    # If required, determine the new brightness and updated list of brightnesses to use when fading.
    if transition_direction == 'in':
        led_brightness_new = determine_brightness()
        brightness_steps = generate_brightness_fade_list(led_brightness_new, 15)

    # Jump cut transition.    
    if transition_type == 'cut':
        if transition_direction == 'in':
            matrix.brightness = led_brightness_new
            matrix.SetImage(scoreboard_image.image)
        elif transition_direction == 'out':
            scoreboard_image.clear_image() # For a cut, the 'transition' out is just clearing the image. No need to set the matrix as that would result in a moment with nothing on screen.
    
    # Fade transition.
    elif transition_type == 'fade':
        if transition_direction == 'in':
            for brightness in brightness_steps:
                matrix.brightness = brightness
                matrix.SetImage(scoreboard_image.image)
                time.sleep(.02)

        elif transition_direction == 'out':
            brightness_steps.reverse()
            for brightness in brightness_steps:
                matrix.brightness = brightness
                matrix.SetImage(scoreboard_image.image)
                time.sleep(.02)
            scoreboard_image.clear_image() # If fading out, also clear the image and set that on the matrix.
            matrix.SetImage(scoreboard_image.image)
    
    # Vertical scroll transition.
    elif transition_type == 'scroll-vertical':
        if transition_direction == 'in':
            matrix.brightness = led_brightness_new
            for y in range(32, -1, -1):
                matrix.SetImage(scoreboard_image.image, 0, y)
                time.sleep(.02)

        elif transition_direction == 'out':
            for y in range(0, -33, -1):
                matrix.SetImage(scoreboard_image.image, 0, y)
                time.sleep(.02)
            scoreboard_image.clear_image() # Clear the image so it doesn't show up with the next image.

    # Horizontal scroll transition.
    # Horizonal transitions not yet ready for use.
    elif transition_type == 'scroll-horizontal':
        if transition_direction == 'in':
            matrix.brightness = led_brightness_new
            for x in range(32, -1, -1):
                matrix.SetImage(scoreboard_image.image, x, 0)
                time.sleep(.02)

        elif transition_direction == 'out':
            for x in range(0, -33, -1):
                matrix.SetImage(scoreboard_image.image, x, 0)
                time.sleep(.02)
            scoreboard_image.clear_image() # Clear the image so it doesn't show up with the next image.
    
    # Vertical modern (fade/scroll combo) transition.
    elif transition_type == 'modern-vertical':
        if transition_direction == 'in':
            for y, brightness in zip(range(14, -1, -1), brightness_steps):
                matrix.brightness = brightness
                matrix.SetImage(scoreboard_image.image, 0, y)
                time.sleep(.025)

        elif transition_direction == 'out':
            brightness_steps.reverse()
            for y, brightness in zip(range(0, -15, -1), brightness_steps):
                matrix.brightness = brightness
                matrix.SetImage(scoreboard_image.image, 0, y)
                time.sleep(.025)
            scoreboard_image.clear_image() # If fading out, also clear the image and set that on the matrix.
            matrix.SetImage(scoreboard_image.image)
            time.sleep(.2) # Hold a moment with nothing displayed.

    # Horizontal modern (fade/scroll combo) transition.
    # Horizonal transitions not yet ready for use.
    elif transition_type == 'modern-horizontal':
        if transition_direction == 'in':
            for x, brightness in zip(range(14, -1, -1), brightness_steps):
                matrix.brightness = brightness
                matrix.SetImage(scoreboard_image.image, x, 0)
                time.sleep(.025)

        elif transition_direction == 'out':
            brightness_steps.reverse()
            for x, brightness in zip(range(0, -15, -1), brightness_steps):
                matrix.brightness = brightness
                matrix.SetImage(scoreboard_image.image, x, 0)
                time.sleep(.025)
            scoreboard_image.clear_image() # If fading out, also clear the image and set that on the matrix.
            matrix.SetImage(scoreboard_image.image)
            time.sleep(.2) # Hold a moment with nothing displayed.
        

def determine_brightness() -> int:
    """ Determines matrix brightness based on details specified in config file.

    Returns:
        brightness (int): The brightness for the LED display.
    """

    # Grab the brightness settings from the config file.
    config = data_utils.read_yaml('config.yaml')['scoreboard_behaviour']
    brightness_mode = config['brightness_mode']
    max_brightness = config.get('max_brightness', 100) # If there's no max_brightness specifed, set to 100.

    # If the mode is set to 'auto', set max_brightness to 100 regardless of what's in the config file.
    if brightness_mode == 'auto':
        max_brightness = 100

    # If mode is static, just return the max_brightness.
    if brightness_mode == 'static':
        return max_brightness

    # Otherwise, determine the brightness based on max_brightness and time.
    elif brightness_mode in ['scaled', 'auto']:
        # Brightness is the current hour divided by 12 and multiplied by 100. For pm times, the difference between 24 and the time is used.
        # If this results in a birhgtness less than 15, set brightnes to 15.
        hour = int(dt.datetime.now().strftime('%H'))
        brightness = math.ceil(max_brightness * hour / 12 if hour <= 12 else max_brightness * (24 - hour) / 12)
        brightness = brightness if brightness >= 15 else 15

    return brightness


def generate_brightness_fade_list(brightness, step_count=15) -> list:
    """ Determines brightnesses to itterate throguh when fading. Returns as a list.

    Args:
        brightness (int): Brightness of the matrix.
        step_count (int): How many steps there should be in the fade, i.e., the number of elements in the returned list.

    Returns:
        list: List of brightnesses that will be used to fade brightness.
    """ 

    # Determine the brightness step size and generate a list of brigtnesses between brightness_step_size and brightness.
    brightness_step_size = brightness / step_count
    brightness_steps = [step * brightness_step_size for step in range(1, step_count + 1)]
    
    return brightness_steps