from PIL import Image, ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions
import datetime as dt
import requests
import json
import time
import math

# Initial setup
# This creates the options, matrix, and image objects, as well as some globals that will be needed throughout the code.
# Not a huge fan of the ammount of globals, but they work fine in a small scope project like this.

# Configure options for the matrix
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.gpio_slowdown= 2
options.hardware_mapping = 'adafruit-hat-pwm'

# Define a matrix object from the options.
matrix = RGBMatrix(options = options)

# Define an image object that will be printed to the matrix.
image = Image.new("RGB", (64, 32))

# Define a draw object. This will be used to draw shapes and text to the image.
draw = ImageDraw.Draw(image)

# Declare fonts that are used throughout.
FONT_SML = ImageFont.load("assets/fonts/PIL/Tamzen5x9r.pil")
FONT_SML_BOLD = ImageFont.load("assets/fonts/PIL/Tamzen5x9b.pil")
FONT_MD = ImageFont.load("assets/fonts/PIL/Tamzen6x12r.pil")
FONT_MD_BOLD = ImageFont.load("assets/fonts/PIL/Tamzen6x12b.pil")
FONT_LRG = ImageFont.load("assets/fonts/PIL/Tamzen8x15r.pil")
FONT_LRG_BOLD = ImageFont.load("assets/fonts/PIL/Tamzen8x15b.pil")

# Declare text colours that are needed.
COLOUR_WHITE = 255,255,255,255
COLOUR_BLACK = 0,0,0,255
COLOUR_RED = 255,50,50,255

# Define the first col that can be used for center text.
# i.e. the first col you can use without worry of logo overlap.
LEFTMOST_MIDDLE_COL = 21

# Define the number of seconds to sit on each game.
CYCLE_TIME = 3.5

# Time of day to start reporting on that days games. This is so in the morning you can catch up on last night's scores. Default 12 noon.
ROLLOVER_TIME = dt.time(12, 0, 0)

BASE_URL = 'https://api-web.nhle.com/v1/score/'


def load_game_data():
    """Get game data for all of todays games from the NHL API, returns games as a list of dictionaries.

    Args:
        teams (list of dictionaries): Team names and abberivations. Needed as the game API doen't return team abbreviations.

    Returns:
        games (list of dictionaries): All game info needed to display on scoreboard. Teams, scores, start times, game clock, etc.
    """

    # Call the NHL API for today's game info. Save the rsult as a JSON object.
    cur_datetime = dt.datetime.today()
    cur_time = cur_datetime.time()

    # If it isn't past the rollover time, report on data from the previous day.
    report_date = cur_datetime if cur_time > ROLLOVER_TIME else cur_datetime - dt.timedelta(days=1)

    games_response = requests.get(url=f"{BASE_URL}{report_date.strftime(format='%Y-%m-%d')}")
    games_json = games_response.json()['games']

    # Decalare an empty list to hold the games dicts.
    games = []

    # For each game, build a dict recording it's information. Append this to the end of the teams list.
    if games_json: # If games today.
        for game in games_json:

            game_dict =  {
                'game_id': game['id'],
                'home_team': game['homeTeam']['abbrev'],
                'away_team': game['awayTeam']['abbrev'],
                'home_score': game['homeTeam'].get('score'),
                'away_score': game['awayTeam'].get('score'),
                'start_time': dt.datetime.strptime(game['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc).astimezone(tz=None),
                'status': game['gameState'],
                'period_num': game.get('period'), # Doesn't exist for games not started yet.
                'period_type': game.get('periodDescriptor', {}).get('periodType'), # If periodDesciprtor doesn't exist, then return an empty dict so second .get can execute.
                'period_time_remaining': game.get('clock', {}).get('timeRemaining'),
                'is_intermission': game.get('clock', {}).get('inIntermission')
                }

            # Append the dict to the games list. We only want to get regular season (2) and playoff (3) games, so any other games are not added.
            if game['gameType'] in [2, 3]:
                games.append(game_dict)

        # Sort list by Game ID. Ensures order doesn't cahnge as games end.
        games.sort(key=lambda x:x['game_id']) # Consider changing score change logic to be based around game IDs so we don't need this sort.

    return games

def getMaxBrightness(time):
    """ Calculates the maximum brightness and fade step incremements based on the time of day.

    Args:
        time (int): Hour of the day. Can be 0-23.

    Returns:
        maxBrightness (int): The maximum brightness for the LED display.
        fadeStep (int): The increments that the display should fade up and down by.
    """
    
    # If the time is midnight, set the time to 1am to avoid the display fulling turning off.
    if time == 0:
        time = 1

    # Max brihgtness is the time divided by 12 and multiplied by 100. For pm times, the difference between 24 and the time is used.
    # This means that max brightness is at noon, with the lowest from 11pm through 1am (because of the above edge case).
    maxBrightness = math.ceil(100 * time / 12 if time <= 12 else 100 * (24-time)/12)
    
    # If the previous calculation results in a birhgtness less than 15, set brightnes to 15.
    maxBrightness = maxBrightness if maxBrightness >= 15 else 15

    # Fade step divides the maxBrightness into 15 segments. Floor since you can't have fractional brightness.
    fadeStep = math.ceil(maxBrightness/15)

    return maxBrightness, fadeStep

def cropImage(image):
    """Crops all transparent space around an image. Returns that cropped image."""

    # Get the bounding box of the image. Aka, boundries of what's non-transparent.
    bbox = image.getbbox()

    # Crop the image to the contents of the bounding box.
    image = image.crop(bbox)

    # Determine the width and height of the cropped image.
    (width, height) = image.size
    
    # Create a new image object for the output image.
    croppedImage = Image.new("RGB", (width, height), (0,0,0,255))

    # Paste the cropped image onto the new image.
    croppedImage.paste(image)

    return croppedImage

def checkGoalScorer(game, gameOld):
    """Checks if a team has scored.

    Args:
        game (dict): All information for a specific game.
        gameOld (dict): Same information from one update cycle ago.

    Returns:
        scoringTeam (string): If either team has scored. both/home/away/none.
    """

    # Safety check to not try this comparison if any of the scores are None.
    if None in [game['away_score'], gameOld['away_score'], game['home_score'], gameOld['home_score']]:
        return 'none'

    # Check if either team has score by compare the score of the last cycle. Set scoringTeam accordingly.
    if game['away_score'] > gameOld['away_score'] and game['home_score'] == gameOld['home_score']:
        scoringTeam = "away"
    elif game['away_score'] == gameOld['away_score'] and game['home_score'] > gameOld['home_score']:
        scoringTeam = "home"
    elif game['away_score'] > gameOld['away_score'] and game['home_score'] > gameOld['home_score']:
        scoringTeam = "both"
    else:
        scoringTeam = "none"

    return scoringTeam

def buildGameNotStarted(game):
    """Adds all aspects of the game not started screen to the image object.

    Args:
        game (dict): All information for a specific game.
    """

    # Add the logos of the teams inivolved to the image.
    displayLogos(game['away_team'],game['home_team'])

    # Add "Today" to the image.
    draw.text((LEFTMOST_MIDDLE_COL+1,0), "T", font=FONT_MD, fill=COLOUR_WHITE)
    draw.text((LEFTMOST_MIDDLE_COL+5,2), "o", font=FONT_SML, fill=COLOUR_WHITE)
    draw.text((LEFTMOST_MIDDLE_COL+9,2), "d", font=FONT_SML, fill=COLOUR_WHITE)
    draw.text((LEFTMOST_MIDDLE_COL+13,2), "a", font=FONT_SML, fill=COLOUR_WHITE)
    draw.text((LEFTMOST_MIDDLE_COL+17,2), "y", font=FONT_SML, fill=COLOUR_WHITE)

    # Add "@" to the image.
    draw.text((LEFTMOST_MIDDLE_COL+6,8), "@", font=FONT_LRG, fill=COLOUR_WHITE)

    # Extract the start time in 12 hour format.
    startTime = game['start_time']
    startTime = startTime.time().strftime('%I:%M')
    startTime = str(startTime) # Cast to a string for easier parsing.

    # Add the start time to the image. Adjust placement for times before/after 10pm local time.
    if startTime[0] == "1": # 10pm or later.
        # Hour.
        draw.text((LEFTMOST_MIDDLE_COL,22), startTime[0], font=FONT_SML, fill=COLOUR_WHITE)
        draw.text((LEFTMOST_MIDDLE_COL+5,22), startTime[1], font=FONT_SML, fill=COLOUR_WHITE)
        # Colon (manual dots since the font's colon looks funny).
        draw.rectangle(((LEFTMOST_MIDDLE_COL+10,25),(LEFTMOST_MIDDLE_COL+10,25)), fill=COLOUR_WHITE)
        draw.rectangle(((LEFTMOST_MIDDLE_COL+10,27),(LEFTMOST_MIDDLE_COL+10,27)), fill=COLOUR_WHITE)
        # Minutes.
        draw.text((LEFTMOST_MIDDLE_COL+12,22), startTime[3], font=FONT_SML, fill=COLOUR_WHITE) # Skipping startTime[2] as that would be the colon.
        draw.text((LEFTMOST_MIDDLE_COL+17,22), startTime[4], font=FONT_SML, fill=COLOUR_WHITE)

    else: # 9pm or earlier.
        # Hour.
        draw.text((LEFTMOST_MIDDLE_COL+3,22), startTime[1], font=FONT_SML, fill=COLOUR_WHITE)
        # Colon (manual dots since the font's colon looks funny).
        draw.rectangle(((LEFTMOST_MIDDLE_COL+8,25),(LEFTMOST_MIDDLE_COL+8,25)), fill=COLOUR_WHITE)
        draw.rectangle(((LEFTMOST_MIDDLE_COL+8,27),(LEFTMOST_MIDDLE_COL+8,27)), fill=COLOUR_WHITE)
        # Minutes.
        draw.text((LEFTMOST_MIDDLE_COL+10,22), startTime[3], font=FONT_SML, fill=COLOUR_WHITE)
        draw.text((LEFTMOST_MIDDLE_COL+15,22), startTime[4], font=FONT_SML, fill=COLOUR_WHITE)

def buildGameInProgress(game, gameOld, scoringTeam):
    """Adds all aspects of the game in progress screen to the image object.

    Args:
        game (dict): All information for a specific game.
        gameOld (dict): The same information, but from one cycle ago.
        scoringTeam (string): If the home team, away team, or both, or neither scored.
    """

    # Add the logos of the teams inivolved to the image.
    displayLogos(game['away_team'],game['home_team'])

    # Add the period to the image.
    displayPeriod(game['period_num'], game['period_type'], game['period_time_remaining'], game['is_intermission'])

    # Add the current score to the image. Note if either team scored.
    displayScore(game['away_score'], game['home_score'], scoringTeam)

def buildGameOver(game, scoringTeam):
    """Adds all aspects of the game over screen to the image object.

    Args:
        game (dict): All information for a specific game.
        scoringTeam (string): If the home team, away team, or both, or neither scored.
    """

    # Add the logos of the teams involved to the image.
    displayLogos(game['away_team'],game['home_team'])

    # Add "Final" to the image.
    draw.text((LEFTMOST_MIDDLE_COL+1,0), "F", font=FONT_MD, fill=COLOUR_WHITE)
    draw.text((LEFTMOST_MIDDLE_COL+5,2), "i", font=FONT_SML, fill=COLOUR_WHITE)
    draw.text((LEFTMOST_MIDDLE_COL+9,2), "n", font=FONT_SML, fill=COLOUR_WHITE)
    draw.text((LEFTMOST_MIDDLE_COL+14,2), "a", font=FONT_SML, fill=COLOUR_WHITE)
    draw.text((LEFTMOST_MIDDLE_COL+17,2), "l", font=FONT_SML, fill=COLOUR_WHITE)

    # Check if the game ended in overtime or a shootout.
    # If so, add that to the image.
    if game['period_type'] == "OT" or game['period_type'] == "SO":
        draw.text((LEFTMOST_MIDDLE_COL+6,9), game['period_type'], font=FONT_MD, fill=COLOUR_WHITE)
    elif game['period_num'] > 4: # If the game ended in 2OT or later.
        draw.text((LEFTMOST_MIDDLE_COL+3,9), game["period_type"], font=FONT_MD, fill=COLOUR_WHITE)

    # Add the current score to the image.
    displayScore(game['away_score'],game['home_score'], scoringTeam)

def buildNoGamesToday():
    """Adds all aspects of the no games today screen to the image object."""

    # Add the NHL logo to the image.
    nhlLogo = Image.open("assets/images/logos/png/NHL.png")
    nhlLogo = cropImage(nhlLogo)
    nhlLogo.thumbnail((40,30))
    image.paste(nhlLogo, (1, 1))

    # Add "No Games Today" to the image.
    draw.text((32,0), "No", font=FONT_MD, fill=COLOUR_WHITE)
    draw.text((32,10), "Games", font=FONT_MD, fill=COLOUR_WHITE)
    draw.text((32,20), "Today", font=FONT_MD, fill=COLOUR_WHITE)

def buildLoading():
    """Adds all aspects of the loading screen to the image object."""

    # Add the NHL logo to the image.
    nhlLogo = Image.open("assets/images/logos/png/NHL.png")
    nhlLogo = cropImage(nhlLogo)
    nhlLogo.thumbnail((40,30))
    image.paste(nhlLogo, (1, 1))

    # Add "Now Loading" to the image.
    draw.text((29,8), "Now", font=FONT_SML, fill=COLOUR_WHITE)
    draw.text((29,15), "Loading", font=FONT_SML, fill=COLOUR_WHITE)

def displayLogos(awayTeam, homeTeam):
    """Adds the logos of the home and away teams to the image object, making sure to not overlap text and center logos.

    Args:
        awayTeam (string): Abbreviation of the away team.
        homeTeam (string): Abbreviation of the home team.
    """

    # Difine the max width and height that a logo can be.
    logoSize = (40,30)

    # Load, crop, and resize the away team logo.
    awayLogo = Image.open("assets/images/logos/png/" + awayTeam + ".png")
    awayLogo = cropImage(awayLogo)
    awayLogo.thumbnail(logoSize)

    # Load, crop, and resize the home team logo.
    homeLogo = Image.open("assets/images/logos/png/" + homeTeam + ".png")
    homeLogo = cropImage(homeLogo)
    homeLogo.thumbnail(logoSize)

    # Record the width and heights of the logos.
    awayLogoWidth, awayLogoHeight = awayLogo.size
    homeLogoWidth, homeLogoHeight = homeLogo.size

    # Add the logos to the image.
    # Logos will be bounded by the text region, and be centered vertically.
    image.paste(awayLogo, (21-awayLogoWidth, math.floor((32-awayLogoHeight)/2)))
    image.paste(homeLogo, (43, math.floor((32-homeLogoHeight)/2)))

def displayPeriod(periodNumber, periodName, timeRemaining, is_intermission):
    """Adds the current period to the image object.

    Args:
        periodNumber (int): [description]
        periodName (string): [description]
        timeRemaining (string): [description]
    """

    # If the first period, add "1st" to the image.
    if periodNumber == 1:
        draw.text((LEFTMOST_MIDDLE_COL+5,0), "1", font=FONT_MD, fill=COLOUR_WHITE)
        draw.text((LEFTMOST_MIDDLE_COL+9,0), "s", font=FONT_SML, fill=COLOUR_WHITE)
        draw.text((LEFTMOST_MIDDLE_COL+13,0), "t", font=FONT_SML, fill=COLOUR_WHITE)

    # If the second period, add "2nd" to the image.
    elif periodNumber == 2:
        draw.text((LEFTMOST_MIDDLE_COL+4,0), "2", font=FONT_MD, fill=COLOUR_WHITE)
        draw.text((LEFTMOST_MIDDLE_COL+10,0), "n", font=FONT_SML, fill=COLOUR_WHITE)
        draw.text((LEFTMOST_MIDDLE_COL+14,0), "d", font=FONT_SML, fill=COLOUR_WHITE)

    # If the third period, add "3rd" to the image.
    elif periodNumber == 3:
        draw.text((LEFTMOST_MIDDLE_COL+4,0), "3", font=FONT_MD, fill=COLOUR_WHITE)
        draw.text((LEFTMOST_MIDDLE_COL+10,0), "r", font=FONT_SML, fill=COLOUR_WHITE)
        draw.text((LEFTMOST_MIDDLE_COL+14,0), "d", font=FONT_SML, fill=COLOUR_WHITE)

    # If in overtime/shootout, add that to the image.
    elif periodName == "OT" or periodName == "SO":
        draw.text((LEFTMOST_MIDDLE_COL+5,0), periodName, font=FONT_MD, fill=COLOUR_WHITE)

    # Otherwise, we're in 2OT or later. Add that to the image.
    else:
        draw.text((LEFTMOST_MIDDLE_COL+3,0), periodName, font=FONT_MD, fill=COLOUR_WHITE)

    if is_intermission:
        draw.text((LEFTMOST_MIDDLE_COL+2,8), "INT", font=FONT_MD, fill=COLOUR_WHITE)
    elif periodName != 'SO':
        displayTimeRemaing(timeRemaining) # Adds the time remaining in the period to the image.

    # # If not in the SO, and the period not over, add the time remaining in the period to the image.
    # if periodName != "SO":
    #     if timeRemaining != "END":
    #         displayTimeRemaing(timeRemaining) # Adds the time remaining in the period to the image.

    #     # If not in the SO and the time remaining is "END", then we know that we're in intermission. Don't add time remaininig to the image.
    #     else:
    #         draw.text((LEFTMOST_MIDDLE_COL+2,8), "INT", font=FONT_MD, fill=COLOUR_WHITE)

    

def displayTimeRemaing(timeRemaining):
    """Adds the remaining time in the period to the image. Takes into account diffent widths of time remaining.

    Args:
        timeRemaining (string): The time remaining in the period in "MM:SS" format. For times less than 10 minutes, the minutes should have a leading zero (e.g 09:59).
    """

    # If time left is 20:00 (period about to start), add the time to the image with specific spacing.
    if timeRemaining[0] == "2": # If the first digit of the time is 2.
        # Minutes.
        draw.text((LEFTMOST_MIDDLE_COL+1,9), timeRemaining[0], font=FONT_SML, fill=COLOUR_WHITE)
        draw.text((LEFTMOST_MIDDLE_COL+5,9), timeRemaining[1], font=FONT_SML, fill=COLOUR_WHITE)
        # Colon.
        draw.rectangle(((LEFTMOST_MIDDLE_COL+10,12),(LEFTMOST_MIDDLE_COL+10,12)), fill=COLOUR_WHITE)
        draw.rectangle(((LEFTMOST_MIDDLE_COL+10,14),(LEFTMOST_MIDDLE_COL+10,14)), fill=COLOUR_WHITE)
        # Seconds.
        draw.text((LEFTMOST_MIDDLE_COL+12,9), timeRemaining[3], font=FONT_SML, fill=COLOUR_WHITE) # Skipping "2" as it's the colon.
        draw.text((LEFTMOST_MIDDLE_COL+16,9), timeRemaining[4], font=FONT_SML, fill=COLOUR_WHITE)
    
    # If time left is between 10 and 20 minutes, add the time to the image with different spacing.
    elif timeRemaining[0] == "1": # If the first digit of the time is 1.
        # Minutes.
        draw.text((LEFTMOST_MIDDLE_COL,9), timeRemaining[0], font=FONT_SML, fill=COLOUR_WHITE)
        draw.text((LEFTMOST_MIDDLE_COL+5,9), timeRemaining[1], font=FONT_SML, fill=COLOUR_WHITE)
        # Colon.
        draw.rectangle(((LEFTMOST_MIDDLE_COL+10,12),(LEFTMOST_MIDDLE_COL+10,12)), fill=COLOUR_WHITE)
        draw.rectangle(((LEFTMOST_MIDDLE_COL+10,14),(LEFTMOST_MIDDLE_COL+10,14)), fill=COLOUR_WHITE)
        # Seconds.
        draw.text((LEFTMOST_MIDDLE_COL+12,9), timeRemaining[3], font=FONT_SML, fill=COLOUR_WHITE)
        draw.text((LEFTMOST_MIDDLE_COL+17,9), timeRemaining[4], font=FONT_SML, fill=COLOUR_WHITE)

    # Otherwise, time is less than 10 minutes. Add the time to the image with spacing for a single digit minute.
    else:
        # Minutes.
        draw.text((LEFTMOST_MIDDLE_COL+3,9), timeRemaining[1], font=FONT_SML, fill=COLOUR_WHITE)
        # Colon.
        draw.rectangle(((LEFTMOST_MIDDLE_COL+8,12),(LEFTMOST_MIDDLE_COL+8,12)), fill=COLOUR_WHITE)
        draw.rectangle(((LEFTMOST_MIDDLE_COL+8,14),(LEFTMOST_MIDDLE_COL+8,14)), fill=COLOUR_WHITE)
        # Seconds.
        draw.text((LEFTMOST_MIDDLE_COL+10,9), timeRemaining[3], font=FONT_SML, fill=COLOUR_WHITE)
        draw.text((LEFTMOST_MIDDLE_COL+15,9), timeRemaining[4], font=FONT_SML, fill=COLOUR_WHITE)

def displayScore(awayScore, homeScore, scoringTeam = "none"):
    """Add the score for both teams to the image object.

    Args:
        awayScore (int): Score of the away team.
        homeScore (int): Score of the home team.
        scoringTeam (str, optional): The team that scored if applicable. Options: "away", "home", "both", "none". Defaults to "none".
    """

    # Add the hypen to the image.
    draw.text((LEFTMOST_MIDDLE_COL+9,20), "-", font=FONT_SML_BOLD, fill=COLOUR_WHITE)

    # If no team scored, add both scores to the image.
    if scoringTeam == "none":
        draw.text((LEFTMOST_MIDDLE_COL+1,17), str(awayScore), font=FONT_LRG_BOLD, fill=COLOUR_WHITE)
        draw.text((LEFTMOST_MIDDLE_COL+13,17), str(homeScore), font=FONT_LRG_BOLD, fill=(COLOUR_WHITE))
    
    # If either or both of the teams scored, add that number to the immage in red.
    elif scoringTeam == "away":
        draw.text((LEFTMOST_MIDDLE_COL+1,17), str(awayScore), font=FONT_LRG_BOLD, fill=COLOUR_RED)
        draw.text((LEFTMOST_MIDDLE_COL+13,17), str(homeScore), font=FONT_LRG_BOLD, fill=COLOUR_WHITE)
    elif scoringTeam == "home":
        draw.text((LEFTMOST_MIDDLE_COL+1,17), str(awayScore), font=FONT_LRG_BOLD, fill=COLOUR_WHITE)
        draw.text((LEFTMOST_MIDDLE_COL+13,17), str(homeScore), font=FONT_LRG_BOLD, fill=COLOUR_RED)
    elif scoringTeam == "both":
        draw.text((LEFTMOST_MIDDLE_COL+1,17), str(awayScore), font=FONT_LRG_BOLD, fill=COLOUR_RED)
        draw.text((LEFTMOST_MIDDLE_COL+13,17), str(homeScore), font=FONT_LRG_BOLD, fill=COLOUR_RED)

def displayGoalFade(score, location, secondScore = "", secondLocation = (0,0), both=False):
    """Adds a red number to the image and fades it to white.
       Note that this is the only time that the matrix is updated in a build or display function.

    Args:
        score (int): The score that needs to be printed.
        location (tuple): Where to add that score to the image.
        secondScore (str, optional): If a second score also needs to be printed, that number. Defaults to "".
        secondLocation (tuple, optional): Location for that second score. Defaults to (0,0).
        both (bool, optional): If both teams have scored. Defaults to False.
    """

    # Print that a team score. This is only for testing.
    print("***\n\nGoal!\n\n***")

    time.sleep(1.5)

    # If both teams have scored.
    if both == True:  
        # Fade both numbers to white.
        for n in range(50, 256):
            draw.text(location, score, font=FONT_LRG_BOLD, fill=(255, n, n, 255))
            draw.text(secondLocation, secondScore, font=FONT_LRG_BOLD, fill=(255, n, n, 255))
            matrix.SetImage(image)
            time.sleep(.015)
    
    # If one team has scored.
    else:
        # Fade number to white.
        for n in range(50, 256):
            draw.text(location, score, font=FONT_LRG_BOLD, fill=(255, n, n, 255))
            matrix.SetImage(image)
            time.sleep(.015)

def run_scoreboard():
    """Runs the scoreboard geting scores and other game data and cycles through them in an infinite loop."""

    # Initial calculation and setting of the max brightness.
    maxBrightness, fadeStep = getMaxBrightness(int(dt.datetime.now().strftime("%H")))
    matrix.brightness = maxBrightness

    # Build the loading screen.
    buildLoading()
    matrix.SetImage(image) # Set the matrix to the image.

    networkError = False

    # Try to get team and game data. Max of 100 attempts before it gives up.
    for i in range(100):
        try:
            games = load_game_data()
            gamesOld = games # Needed for checking logic on initial loop.
            networkError = False
            break

        # In the event that the NHL API cannot be reached, set the bottom right LED to red.
        # TODO: Make this more robust for specific fail cases.
        except:
            networkError = True
            if i >= 10:
                draw.rectangle(((63,31),(63,31)), fill=COLOUR_RED)
                matrix.SetImage(image)
            time.sleep(1)

    # Wait one extra second on the loading screen. Users thoguht it was too quick.
    time.sleep(1)

    # Fade out.
    for brightness in range(maxBrightness,0,-fadeStep):
        matrix.brightness = brightness
        matrix.SetImage(image)
        time.sleep(.025)

    # "Wipe" the image by writing over the entirity with a black rectangle.
    draw.rectangle(((0,0),(63,31)), fill=COLOUR_BLACK)
    matrix.SetImage(image)

    while True:
        
        # Update the maxBrightness and fadeSteps.
        maxBrightness, fadeStep = getMaxBrightness(int(dt.datetime.now().strftime("%H")))

        # Adjusting cycle time for single game situation.
        if len(games) == 1:
            CYCLE_TIME = 10
        else:
            CYCLE_TIME = 3.5

        # If there's games today.
        if games:

            # Loop through both the games and gamesOld arrays.
            for game, gameOld in zip(games, gamesOld):

                # Check if either team has scored.
                

                # # # If the game is postponed, build the postponed screen.
                # if game['status'] == "Postponed":
                #     buildGamePostponed(game)

                # INTERMISSION LOGIC if game['is_']

                # If the game has yet to begin, build the game not started screen.
                if game['status'] in ['FUT', 'PRE']:
                    buildGameNotStarted(game)

                # If the game is over, build the final score screen.
                elif game['status'] in ['OFF', 'FINAL']:
                    scoringTeam = checkGoalScorer(game, gameOld)
                    buildGameOver(game, scoringTeam)
                
                # Otherwise, the game is in progress. Build the game in progress screen.
                # If the home or away team has scored, take note of that.
                elif game['status'] in ['LIVE', 'CRIT']:
                    scoringTeam = checkGoalScorer(game, gameOld)
                    buildGameInProgress(game, gameOld, scoringTeam)

                else:
                    print(f"Unexpected gameState encountered: {game['status']}")

                # Set bottom right LED to red if there's a network error.
                if networkError:
                    draw.rectangle(((63,31),(63,31)), fill=COLOUR_RED)

                # Fade up to the image.
                for brightness in range(0,maxBrightness,fadeStep):
                    matrix.brightness = brightness
                    matrix.SetImage(image)
                    time.sleep(.025)
                

                if game['status'] in ['LIVE', 'CRIT', 'FINAL']:
                    # If a team has scored, fade the red number to white.
                    if scoringTeam == "away":
                        displayGoalFade(str(game['away_score']), (22,17))
                    elif scoringTeam == "home":
                        displayGoalFade(str(game['home_score']), (34,17))
                    elif scoringTeam == "both":
                        displayGoalFade(str(game['away_score']), (22,17), str(game['home_score']), (34,17), True) # True indicates that both teams have scored.

                # Hold the screen before fading.
                time.sleep(CYCLE_TIME)

                # Fade down to black.
                for brightness in range(maxBrightness,0,-fadeStep):
                    matrix.brightness = brightness
                    matrix.SetImage(image)
                    time.sleep(.025)

                # Make the screen totally blank between fades.
                draw.rectangle(((0,0),(63,31)), fill=COLOUR_BLACK) 
                matrix.SetImage(image)

        # If there's no games, build the no games today sceen, then wait 10 minutes before checking again.
        else:
            buildNoGamesToday()
            matrix.brightness = maxBrightness
            matrix.SetImage(image)
            time.sleep(600)
            draw.rectangle(((0,0),(63,31)), fill=COLOUR_BLACK)
        
        # Refresh the game data.
        # Record the data of the last cycle in gamesOld to check for goals.
        try:
            gamesOld = games
            games = load_game_data()
            networkError = False
        except:
            print("Network Error")
            networkError = True

if __name__ == "__main__":
    run_scoreboard()