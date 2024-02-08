import math
import time
import datetime as dt


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

    # Jump cut transition.    
    if transition_type == 'cut':
        if transition_direction == 'in':
            matrix.SetImage(scoreboard_image.image)
        elif transition_direction == 'out':
            scoreboard_image.clear_image() # For a cut, the 'transition' out is just clearing the image. No need to set the matrix as that would result in a moment with nothing on screen.
    
    # Fade transition. Determines even steps of brightness between current brightness and 0 and iterates over them.
    elif transition_type == 'fade':
        if transition_direction == 'in':
            led_brightness_new = determine_brightness()
            led_fade_step_size = deterime_fade_step_size(led_brightness_new)
            for brightness in range(0, led_brightness_new, led_fade_step_size):
                matrix.brightness = brightness
                matrix.SetImage(scoreboard_image.image)
                time.sleep(.025)

        elif transition_direction == 'out':
            led_brightness_cur = matrix.brightness
            led_fade_step_size = deterime_fade_step_size(led_brightness_cur)
            for brightness in range(led_brightness_cur, 0, -led_fade_step_size):
                matrix.brightness = brightness
                matrix.SetImage(scoreboard_image.image)
                time.sleep(.025)
            scoreboard_image.clear_image() # If fading out, also clear the image and set that on the matrix.
            matrix.SetImage(scoreboard_image.image)
    
    # To implement...
    elif transition_type == 'scroll-up':
        if transition_direction == 'in':
            pass
        elif transition_direction == 'out':
            pass

    elif transition_type == 'scroll-down':
        if transition_direction == 'in':
            pass
        elif transition_direction == 'out':
            pass

    elif transition_type == 'modern':
        if transition_direction == 'in':
            pass
        elif transition_direction == 'out':
            pass
        

def determine_brightness() -> int:
    """ Determines matrix brightness based on the time of day.

    Returns:
        brightness (int): The maximum brightness for the LED display.
    """

    # Max brihgtness is the current hour divided by 12 and multiplied by 100. For pm times, the difference between 24 and the time is used.
    # If this results in a birhgtness less than 15, set brightnes to 15.
    hour = int(dt.datetime.now().strftime('%H'))
    brightness = math.ceil(100 * hour / 12 if hour <= 12 else 100 * (24 - hour) / 12)
    brightness = brightness if brightness >= 15 else 15

    return brightness


def deterime_fade_step_size(brightness) -> int:
    """ Determines step size for fading fading brightness from 0->x or x->0.

    Args:
        brightness (int): Brightness of the matrix.

    Returns:
        int: Step size when fading brightness from 0->x or x->0.
    """

    return math.ceil(brightness / 15)