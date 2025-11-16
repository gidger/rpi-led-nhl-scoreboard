from setup.session_setup import session
from datetime import datetime as dt
from datetime import timezone as tz


def get_games(date):
        """ Loads NHL game data for the provided date.

        Args:
            date (date): Date that game data should be pulled for.

        Returns:
            list: List of dicts of game data.
        """
        
        # Create an empty list to hold the game dicts.
        games = []

        # Call the NHL API for the date specified and store the JSON results.
        url = 'https://api-web.nhle.com/v1/score/'
        games_response = session.get(url=f"{url}{date.strftime(format='%Y-%m-%d')}")
        games_json = games_response.json()['games']

        # For each game, build a dict recording current game details.
        if games_json: # If games today.
            for game in games_json:
                # Append the dict to the games list. We only want to get regular season (gameType = 2) and playoff (3) games.
                # Note that 19 and 20 may need to be included. These were used for the 4 Nations Face-Off round robin & finals and will be evaluated again in the future.
                if game['gameType'] in [2, 3]:
                    games.append({
                        'game_id': game['id'],
                        'home_abrv': game['homeTeam']['abbrev'],
                        'away_abrv': game['awayTeam']['abbrev'],
                        'home_score': game['homeTeam'].get('score'), # Doesn't exist until game starts.
                        'away_score': game['awayTeam'].get('score'),
                        'start_datetime_utc': dt.strptime(game['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc),
                        'start_datetime_local': dt.strptime(game['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None), # Convert UTC to local time.
                        'status': game['gameState'],
                        'has_started': True if game['gameState'] in ['LIVE', 'CRIT', 'OFF', 'FINAL'] else False,
                        'period_num': game.get('period'), # Doesn't until game starts.
                        'period_type': game.get('periodDescriptor', {}).get('periodType'), # periodDescriptor doesn't exist until game starts.
                        'period_time_remaining': game.get('clock', {}).get('timeRemaining'), # clock doesn't exist until game starts.
                        'is_intermission': game.get('clock', {}).get('inIntermission'),
                        # Will set the remaining later, default to False and None for now.
                        'home_team_scored': False,
                        'away_team_scored': False,
                        'scoring_team': None
                    })

        return games


def get_next_game(team):
     
    # TODO: Clean.

    url = f'https://api-web.nhle.com/v1/club-schedule-season/{team}/now'
    schedule_response = session.get(url=url)
    schedule_json = schedule_response.json()['games']

    upcoming_games = [game for game in schedule_json if game['gameState'] in ('FUT', 'PRE', 'LIVE', 'CRIT')]

    cur_date = dt.today().astimezone().date()

    next_game_details = upcoming_games[0]

    next_game = {
        'home_or_away': 'away' if next_game_details['homeTeam']['abbrev'] != team else 'home',
        'opponent_abrv': next_game_details['homeTeam']['abbrev'] if next_game_details['homeTeam']['abbrev'] != team else next_game_details['awayTeam']['abbrev'],
        'start_datetime_utc': dt.strptime(next_game_details['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc),
        'start_datetime_local': dt.strptime(next_game_details['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None),
        'is_today': True if dt.strptime(next_game_details['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=tz.utc).astimezone(tz=None).date() == cur_date else False,
        'has_started': True if next_game_details['gameState'] in ('LIVE', 'CRIT') else False
    }

    return(next_game)