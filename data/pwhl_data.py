from setup.session_setup import session
from datetime import datetime as dt
from datetime import timezone as tz


def get_games(date):
    """ Placeholder: Loads PWHL game data for the provided date.

    Args:
        date (date): Date that game data should be pulled for.

    Returns:
        list: List of dicts of game data. (Currently placeholder — implement API calls.)
    """

    # TODO: Implement PWHL API calls and parsing. Return list of game dicts matching the structure
    # used by the scenes (same keys as `nhl_data.get_games`).
    return []


def get_next_game(team):
    """ Placeholder: Loads next game details for the supplied PWHL team.

    Args:
        team (str): Team abbreviation to pull next game details for.

    Returns:
        dict or None: Dict of next game details or None if not found.
    """

    # TODO: Implement PWHL schedule API call and parsing.
    return None


def get_standings():
    """ Placeholder: Loads current PWHL standings.

    Returns:
        dict: Standings structure compatible with the existing scenes (placeholder).
    """

    # TODO: Implement PWHL standings API call and parsing. Return structure similar to nhl_data.get_standings().
    return {
        'rank_method': 'Points',
        'division': {},
        'wildcard': {},
        'conference': {},
        'league': {}
    }
