from PIL import Image, ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from datetime import datetime, timezone
import requests
import json
import time
import math

def getTeamData():
    """Get team names and abreviations from the NHL API, return information as a list of dictionaries.

    Returns:
        teams (list of dictionaries): Each dict contains the longform name and abbreviation of a single NHL team.
    """
    
    # Call the NHL Teams API. Store as a JSON object.
    teamsResponse = requests.get(url="https://statsapi.web.nhl.com/api/v1/teams")
    teamsJson = teamsResponse.json()

    # Decalare an empty list to hold the team dicts.
    teams = []

    # For each team, build a dict recording it's name and abbreviation. Append this to the end of the teams list.
    for team in teamsJson['teams']:
        teamDict = {
                'Team Name': team['name'],
                'Team Abbreviation': team['abbreviation']
        }
        # Append dict to the end of the teams list.
        teams.append(teamDict)
    
    return teams

def getGameData(teams):
    """Get game data for all of todays games from the NHL API, returns games as a list of dictionaries.

    Args:
        teams (list of dictionaries): Team names and abberivations. Needed as the game API doen't return team abbreviations.

    Returns:
        games (list of dictionaries): All game info needed to display on scoreboard. Teams, scores, start times, game clock, etc.
    """

    # Call the NHL API for today's game info. Save the rsult as a JSON object.
    gamesResponse = requests.get(url="https://statsapi.web.nhl.com/api/v1/schedule?expand=schedule.linescore")
    gamesJson = gamesResponse.json()

    # Decalare an empty list to hold the games dicts.
    games = []

    # For each game, build a dict recording it's information. Append this to the end of the teams list.
    if gamesJson['dates']: # If games today.
        for game in gamesJson['dates'][0]['games']:

            # Prep the period data for consistancy. This data doesn't exist in the API responce until game begins.
            if 'linescore' in game and 'currentPeriodOrdinal' in game['linescore']:
                perName = game['linescore']['currentPeriodOrdinal']
                perTimeRem = game['linescore']['currentPeriodTimeRemaining']
            else:
                perName = "Not Started"
                perTimeRem = "Not Started"

            # Prep the dict data.
            gameDict = {
                'Game ID': game['gamePk'],
                'Home Team': game['teams']['home']['team']['name'],
                # Since the schedule API doesn't have team abreviatiosn, we'll have to get that from the team dict.
                'Home Abbreviation': [t['Team Abbreviation'] for t in teams if t['Team Name'] == game['teams']['home']['team']['name']][0],
                'Away Team': game['teams']['away']['team']['name'],
                 # Since the schedule API doesn't have team abreviatiosn, we'll have to get that from the team dict.
                'Away Abbreviation': [t['Team Abbreviation'] for t in teams if t['Team Name'] == game['teams']['away']['team']['name']][0],
                'Home Score': game['teams']['home']['score'],
                'Away Score': game['teams']['away']['score'],
                'Start Time UTC':  datetime.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ'), # Extracts the startime from what's given by the API.
                'Start Time Local': utcToLocal(datetime.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ')), # Converts the UTC start time to the RPi's local timezone.
                'Status': game['status']['abstractGameState'],
                'Detailed Status': game['status']['detailedState'],
                'Period Number': game['linescore']['currentPeriod'],
                'Period Name': perName,
                'Period Time Remaining': perTimeRem
            }

            # Append the dict to the games list.
            games.append(gameDict)

            # Sort list by Game ID. Ensures order doesn't cahnge as games end.
            games.sort(key=lambda x:x['Game ID'])
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

def utcToLocal(utc_dt):
    """Returns a time object converted to the local timezone set on the RPi."""
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

def checkGoalScorer(game, gameOld):
    """Checks if a team has scored.

    Args:
        game (dict): All information for a specific game.
        gameOld (dict): Same information from one update cycle ago.

    Returns:
        scoringTeam (string): If either team has scored. both/home/away/none.
    """

    # Check if either team has score by compare the score of the last cycle. Set scoringTeam accordingly.
    if game['Away Score'] > gameOld['Away Score'] and game['Home Score'] == gameOld['Home Score']:
        scoringTeam = "away"
    elif game['Away Score'] == gameOld['Away Score'] and game['Home Score'] > gameOld['Home Score']:
        scoringTeam = "home"
    elif game['Away Score'] > gameOld['Away Score'] and game['Home Score'] > gameOld['Home Score']:
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
    displayLogos(game['Away Abbreviation'],game['Home Abbreviation'])

    # Add "Today" to the image.
    draw.text((firstMiddleCol+1,0), "T", font=fontMedReg, fill=fillWhite)
    draw.text((firstMiddleCol+5,2), "o", font=fontSmallReg, fill=fillWhite)
    draw.text((firstMiddleCol+9,2), "d", font=fontSmallReg, fill=fillWhite)
    draw.text((firstMiddleCol+13,2), "a", font=fontSmallReg, fill=fillWhite)
    draw.text((firstMiddleCol+17,2), "y", font=fontSmallReg, fill=fillWhite)

    # Add "@" to the image.
    draw.text((firstMiddleCol+6,8), "@", font=fontLargeReg, fill=fillWhite)

    # Extract the start time in 12 hour format.
    startTime = game['Start Time Local']
    startTime = startTime.time().strftime('%I:%M')
    startTime = str(startTime) # Cast to a string for easier parsing.

    # Add the start time to the image. Adjust placement for times before/after 10pm local time.
    if startTime[0] == "1": # 10pm or later.
        # Hour.
        draw.text((firstMiddleCol,22), startTime[0], font=fontSmallReg, fill=fillWhite)
        draw.text((firstMiddleCol+5,22), startTime[1], font=fontSmallReg, fill=fillWhite)
        # Colon (manual dots since the font's colon looks funny).
        draw.rectangle(((firstMiddleCol+10,25),(firstMiddleCol+10,25)), fill=fillWhite)
        draw.rectangle(((firstMiddleCol+10,27),(firstMiddleCol+10,27)), fill=fillWhite)
        # Minutes.
        draw.text((firstMiddleCol+12,22), startTime[3], font=fontSmallReg, fill=fillWhite) # Skipping startTime[2] as that would be the colon.
        draw.text((firstMiddleCol+17,22), startTime[4], font=fontSmallReg, fill=fillWhite)

    else: # 9pm or earlier.
        # Hour.
        draw.text((firstMiddleCol+3,22), startTime[1], font=fontSmallReg, fill=fillWhite)
        # Colon (manual dots since the font's colon looks funny).
        draw.rectangle(((firstMiddleCol+8,25),(firstMiddleCol+8,25)), fill=fillWhite)
        draw.rectangle(((firstMiddleCol+8,27),(firstMiddleCol+8,27)), fill=fillWhite)
        # Minutes.
        draw.text((firstMiddleCol+10,22), startTime[3], font=fontSmallReg, fill=fillWhite)
        draw.text((firstMiddleCol+15,22), startTime[4], font=fontSmallReg, fill=fillWhite)

def buildGameInProgress(game, gameOld, scoringTeam):
    """Adds all aspects of the game in progress screen to the image object.

    Args:
        game (dict): All information for a specific game.
        gameOld (dict): The same information, but from one cycle ago.
        scoringTeam (string): If the home team, away team, or both, or neither scored.
    """

    # Add the logos of the teams inivolved to the image.
    displayLogos(game['Away Abbreviation'],game['Home Abbreviation'])

    # Add the period to the image.
    displayPeriod(game['Period Number'], game['Period Name'], game['Period Time Remaining'])

    # Add the current score to the image. Note if either team scored.
    displayScore(game['Away Score'], game['Home Score'], scoringTeam)

def buildGameOver(game, scoringTeam):
    """Adds all aspects of the game over screen to the image object.

    Args:
        game (dict): All information for a specific game.
        scoringTeam (string): If the home team, away team, or both, or neither scored.
    """

    # Add the logos of the teams involved to the image.
    displayLogos(game['Away Abbreviation'],game['Home Abbreviation'])

    # Add "Final" to the image.
    draw.text((firstMiddleCol+1,0), "F", font=fontMedReg, fill=fillWhite)
    draw.text((firstMiddleCol+5,2), "i", font=fontSmallReg, fill=fillWhite)
    draw.text((firstMiddleCol+9,2), "n", font=fontSmallReg, fill=fillWhite)
    draw.text((firstMiddleCol+14,2), "a", font=fontSmallReg, fill=fillWhite)
    draw.text((firstMiddleCol+17,2), "l", font=fontSmallReg, fill=fillWhite)

    # Check if the game ended in overtime or a shootout.
    # If so, add that to the image.
    if game['Period Name'] == "OT" or game['Period Name'] == "SO":
        draw.text((firstMiddleCol+6,9), game['Period Name'], font=fontMedReg, fill=fillWhite)
    elif game['Period Number'] > 4: # If the game ended in 2OT or later.
        draw.text((firstMiddleCol+3,9), game["Period Name"], font=fontMedReg, fill=fillWhite)

    # Add the current score to the image.
    displayScore(game['Away Score'],game['Home Score'], scoringTeam)

def buildGamePostponed(game):
    """Adds all aspects of the postponed screen to the image object.

    Args:
        game (dict): All information for a specific game.
    """
    
    # Add the logos of the teams involved to the image.
    displayLogos(game['Away Abbreviation'],game['Home Abbreviation'])

    # Add "PPD" to the image.
    draw.text((firstMiddleCol+2,0), "PPD", font=fontMedReg, fill=fillWhite)

def buildNoGamesToday():
    """Adds all aspects of the no games today screen to the image object."""

    # Add the NHL logo to the image.
    nhlLogo = Image.open("assets/images/NHL_Logo_Simplified.png")
    nhlLogo = cropImage(nhlLogo)
    nhlLogo.thumbnail((40,30))
    image.paste(nhlLogo, (1, 1))

    # Add "No Games Today" to the image.
    draw.text((32,0), "No", font=fontMedReg, fill=fillWhite)
    draw.text((32,10), "Games", font=fontMedReg, fill=fillWhite)
    draw.text((32,20), "Today", font=fontMedReg, fill=fillWhite)

def buildLoading():
    """Adds all aspects of the loading screen to the image object."""

    # Add the NHL logo to the image.
    nhlLogo = Image.open("assets/images/NHL_Logo_Simplified.png")
    nhlLogo = cropImage(nhlLogo)
    nhlLogo.thumbnail((40,30))
    image.paste(nhlLogo, (1, 1))

    # Add "Now Loading" to the image.
    draw.text((29,8), "Now", font=fontSmallReg, fill=fillWhite)
    draw.text((29,15), "Loading", font=fontSmallReg, fill=fillWhite)

def displayLogos(awayTeam, homeTeam):
    """Adds the logos of the home and away teams to the image object, making sure to not overlap text and center logos.

    Args:
        awayTeam (string): Abbreviation of the away team.
        homeTeam (string): Abbreviation of the home team.
    """

    # Difine the max width and height that a logo can be.
    logoSize = (40,30)

    # Load, crop, and resize the away team logo.
    awayLogo = Image.open("assets/images/team logos/png/" + awayTeam + ".png")
    awayLogo = cropImage(awayLogo)
    awayLogo.thumbnail(logoSize)

    # Load, crop, and resize the home team logo.
    homeLogo = Image.open("assets/images/team logos/png/" + homeTeam + ".png")
    homeLogo = cropImage(homeLogo)
    homeLogo.thumbnail(logoSize)

    # Record the width and heights of the logos.
    awayLogoWidth, awayLogoHeight = awayLogo.size
    homeLogoWidth, homeLogoHeight = homeLogo.size

    # Add the logos to the image.
    # Logos will be bounded by the text region, and be centered vertically.
    image.paste(awayLogo, (21-awayLogoWidth, math.floor((32-awayLogoHeight)/2)))
    image.paste(homeLogo, (43, math.floor((32-homeLogoHeight)/2)))

def displayPeriod(periodNumber, periodName, timeRemaining):
    """Adds the current period to the image object.

    Args:
        periodNumber (int): [description]
        periodName (string): [description]
        timeRemaining (string): [description]
    """

    # If the first period, add "1st" to the image.
    if periodNumber == 1:
        draw.text((firstMiddleCol+5,0), "1", font=fontMedReg, fill=fillWhite)
        draw.text((firstMiddleCol+9,0), "s", font=fontSmallReg, fill=fillWhite)
        draw.text((firstMiddleCol+13,0), "t", font=fontSmallReg, fill=fillWhite)

    # If the second period, add "2nd" to the image.
    elif periodNumber == 2:
        draw.text((firstMiddleCol+4,0), "2", font=fontMedReg, fill=fillWhite)
        draw.text((firstMiddleCol+10,0), "n", font=fontSmallReg, fill=fillWhite)
        draw.text((firstMiddleCol+14,0), "d", font=fontSmallReg, fill=fillWhite)

    # If the third period, add "3rd" to the image.
    elif periodNumber == 3:
        draw.text((firstMiddleCol+4,0), "3", font=fontMedReg, fill=fillWhite)
        draw.text((firstMiddleCol+10,0), "r", font=fontSmallReg, fill=fillWhite)
        draw.text((firstMiddleCol+14,0), "d", font=fontSmallReg, fill=fillWhite)

    # If in overtime/shootout, add that to the image.
    elif periodName == "OT" or periodName == "SO":
        draw.text((firstMiddleCol+5,0), periodName, font=fontMedReg, fill=fillWhite)

    # Otherwise, we're in 2OT or later. Add that to the image.
    else:
        draw.text((firstMiddleCol+3,0), periodName, font=fontMedReg, fill=fillWhite)

    # If not in the SO, and the period not over, add the time remaining in the period to the image.
    if periodName != "SO":
        if timeRemaining != "END":
            displayTimeRemaing(timeRemaining) # Adds the time remaining in the period to the image.

        # If not in the SO and the time remaining is "END", then we know that we're in intermission. Don't add time remaininig to the image.
        else:
            draw.text((firstMiddleCol+2,8), "INT", font=fontMedReg, fill=fillWhite)

def displayTimeRemaing(timeRemaining):
    """Adds the remaining time in the period to the image. Takes into account diffent widths of time remaining.

    Args:
        timeRemaining (string): The time remaining in the period in "MM:SS" format. For times less than 10 minutes, the minutes should have a leading zero (e.g 09:59).
    """

    # If time left is 20:00 (period about to start), add the time to the image with specific spacing.
    if timeRemaining[0] == "2": # If the first digit of the time is 2.
        # Minutes.
        draw.text((firstMiddleCol+1,9), timeRemaining[0], font=fontSmallReg, fill=fillWhite)
        draw.text((firstMiddleCol+5,9), timeRemaining[1], font=fontSmallReg, fill=fillWhite)
        # Colon.
        draw.rectangle(((firstMiddleCol+10,12),(firstMiddleCol+10,12)), fill=fillWhite)
        draw.rectangle(((firstMiddleCol+10,14),(firstMiddleCol+10,14)), fill=fillWhite)
        # Seconds.
        draw.text((firstMiddleCol+12,9), timeRemaining[3], font=fontSmallReg, fill=fillWhite) # Skipping "2" as it's the colon.
        draw.text((firstMiddleCol+16,9), timeRemaining[4], font=fontSmallReg, fill=fillWhite)
    
    # If time left is between 10 and 20 minutes, add the time to the image with different spacing.
    elif timeRemaining[0] == "1": # If the first digit of the time is 1.
        # Minutes.
        draw.text((firstMiddleCol,9), timeRemaining[0], font=fontSmallReg, fill=fillWhite)
        draw.text((firstMiddleCol+5,9), timeRemaining[1], font=fontSmallReg, fill=fillWhite)
        # Colon.
        draw.rectangle(((firstMiddleCol+10,12),(firstMiddleCol+10,12)), fill=fillWhite)
        draw.rectangle(((firstMiddleCol+10,14),(firstMiddleCol+10,14)), fill=fillWhite)
        # Seconds.
        draw.text((firstMiddleCol+12,9), timeRemaining[3], font=fontSmallReg, fill=fillWhite)
        draw.text((firstMiddleCol+17,9), timeRemaining[4], font=fontSmallReg, fill=fillWhite)

    # Otherwise, time is less than 10 minutes. Add the time to the image with spacing for a single digit minute.
    else:
        # Minutes.
        draw.text((firstMiddleCol+3,9), timeRemaining[1], font=fontSmallReg, fill=fillWhite)
        # Colon.
        draw.rectangle(((firstMiddleCol+8,12),(firstMiddleCol+8,12)), fill=fillWhite)
        draw.rectangle(((firstMiddleCol+8,14),(firstMiddleCol+8,14)), fill=fillWhite)
        # Seconds.
        draw.text((firstMiddleCol+10,9), timeRemaining[3], font=fontSmallReg, fill=fillWhite)
        draw.text((firstMiddleCol+15,9), timeRemaining[4], font=fontSmallReg, fill=fillWhite)

def displayScore(awayScore, homeScore, scoringTeam = "none"):
    """Add the score for both teams to the image object.

    Args:
        awayScore (int): Score of the away team.
        homeScore (int): Score of the home team.
        scoringTeam (str, optional): The team that scored if applicable. Options: "away", "home", "both", "none". Defaults to "none".
    """

    # Add the hypen to the image.
    draw.text((firstMiddleCol+9,20), "-", font=fontSmallBold, fill=fillWhite)

    # If no team scored, add both scores to the image.
    if scoringTeam == "none":
        draw.text((firstMiddleCol+1,17), str(awayScore), font=fontLargeBold, fill=fillWhite)
        draw.text((firstMiddleCol+13,17), str(homeScore), font=fontLargeBold, fill=(fillWhite))
    
    # If either or both of the teams scored, add that number to the immage in red.
    elif scoringTeam == "away":
        draw.text((firstMiddleCol+1,17), str(awayScore), font=fontLargeBold, fill=fillRed)
        draw.text((firstMiddleCol+13,17), str(homeScore), font=fontLargeBold, fill=fillWhite)
    elif scoringTeam == "home":
        draw.text((firstMiddleCol+1,17), str(awayScore), font=fontLargeBold, fill=fillWhite)
        draw.text((firstMiddleCol+13,17), str(homeScore), font=fontLargeBold, fill=fillRed)
    elif scoringTeam == "both":
        draw.text((firstMiddleCol+1,17), str(awayScore), font=fontLargeBold, fill=fillRed)
        draw.text((firstMiddleCol+13,17), str(homeScore), font=fontLargeBold, fill=fillRed)

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
            draw.text(location, score, font=fontLargeBold, fill=(255, n, n, 255))
            draw.text(secondLocation, secondScore, font=fontLargeBold, fill=(255, n, n, 255))
            matrix.SetImage(image)
            time.sleep(.015)
    
    # If one team has scored.
    else:
        # Fade number to white.
        for n in range(50, 256):
            draw.text(location, score, font=fontLargeBold, fill=(255, n, n, 255))
            matrix.SetImage(image)
            time.sleep(.015)

def runScoreboard():
    """Runs the scoreboard geting scores and other game data and cycles through them in an infinite loop."""

    # Initial calculation and setting of the max brightness.
    maxBrightness, fadeStep = getMaxBrightness(int(datetime.now().strftime("%H")))
    matrix.brightness = maxBrightness

    # Build the loading screen.
    buildLoading()
    matrix.SetImage(image) # Set the matrix to the image.

    networkError = False

    # Try to get team and game data. Max of 100 attempts before it gives up.
    for i in range(100):
        try:
            teams = getTeamData()
            games = getGameData(teams)
            gamesOld = games # Needed for checking logic on initial loop.
            networkError = False
            break

        # In the event that the NHL API cannot be reached, set the bottom right LED to red.
        # TODO: Make this more robust for specific fail cases.
        except:
            networkError = True
            if i >= 10:
                draw.rectangle(((63,31),(63,31)), fill=fillRed)
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
    draw.rectangle(((0,0),(63,31)), fill=fillBlack)
    matrix.SetImage(image)

    while True:
        
        # Update the maxBrightness and fadeSteps.
        maxBrightness, fadeStep = getMaxBrightness(int(datetime.now().strftime("%H")))

        # If there's games today.
        if games:

            # Loop through both the games and gamesOld arrays.
            for game, gameOld in zip(games, gamesOld):

                # Check if either team has scored.
                scoringTeam = checkGoalScorer(game, gameOld)

                # If the game is postponed, build the postponed screen.
                if game['Detailed Status'] == "Postponed":
                    buildGamePostponed(game)

                # If the game has yet to begin, build the game not started screen.
                elif game['Status'] == "Preview":
                    buildGameNotStarted(game)

                # If the game is over, build the final score screen.
                elif game['Status'] == "Final":
                    buildGameOver(game, scoringTeam)
                
                # Otherwise, the game is in progress. Build the game in progress screen.
                # If the home or away team has scored, take note of that.
                else:
                    buildGameInProgress(game, gameOld, scoringTeam)

                # Set bottom right LED to red if there's a network error.
                if networkError:
                    draw.rectangle(((63,31),(63,31)), fill=fillRed)

                # Fade up to the image.
                for brightness in range(0,maxBrightness,fadeStep):
                    matrix.brightness = brightness
                    matrix.SetImage(image)
                    time.sleep(.025)
                
                # If a team has scored, fade the red number to white.
                if scoringTeam == "away":
                    displayGoalFade(str(game['Away Score']), (22,17))
                elif scoringTeam == "home":
                    displayGoalFade(str(game['Home Score']), (34,17))
                elif scoringTeam == "both":
                    displayGoalFade(str(game['Away Score']), (22,17), str(game['Home Score']), (34,17), True) # True indicates that both teams have scored.

                # Hold the screen before fading.
                time.sleep(cycleTime)

                # Fade down to black.
                for brightness in range(maxBrightness,0,-fadeStep):
                    matrix.brightness = brightness
                    matrix.SetImage(image)
                    time.sleep(.025)

                # Make the screen totally blank between fades.
                draw.rectangle(((0,0),(63,31)), fill=fillBlack) 
                matrix.SetImage(image)

        # If there's no games, build the no games today sceen, then wait 10 minutes before checking again.
        else:
            buildNoGamesToday()
            matrix.SetImage(image)
            time.sleep(600)
            draw.rectangle(((0,0),(63,31)), fill=fillBlack)
        
        # Refresh the game data.
        # Record the data of the last cycle in gamesOld to check for goals.
        try:
            gamesOld = games
            games = getGameData(teams)
            networkError = False
        except:
            print("Network Error")
            networkError = True

if __name__ == "__main__":

    # This creates the options, matrix, and image objects, as well as some globals that will be needed throughout the code.
    # Note a huge fan of the ammount of globals, but they work fine in a small scope project like this.

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
    fontSmallReg = ImageFont.load("assets/fonts/PIL/Tamzen5x9r.pil")
    fontSmallBold = ImageFont.load("assets/fonts/PIL/Tamzen5x9b.pil")
    fontMedReg = ImageFont.load("assets/fonts/PIL/Tamzen6x12r.pil")
    fontMedBold = ImageFont.load("assets/fonts/PIL/Tamzen6x12b.pil")
    fontLargeReg = ImageFont.load("assets/fonts/PIL/Tamzen8x15r.pil")
    fontLargeBold = ImageFont.load("assets/fonts/PIL/Tamzen8x15b.pil")

    # Declare text colours that are needed.
    fillWhite = 255,255,255,255
    fillBlack = 0,0,0,255
    fillRed = 255,50,50,255

    # Define the first col that can be used for center text.
    # i.e. the first col you can use without worry of logo overlap.
    firstMiddleCol = 21

    # Define the number of seconds to sit on each game.
    cycleTime = 3.5

    # Run the scoreboard.
    runScoreboard()