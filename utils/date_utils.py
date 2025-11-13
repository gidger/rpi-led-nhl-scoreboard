from datetime import datetime, timedelta


def determine_dates_to_display_games(start, end):
    """ Determines the dates to pull data and display games for.

    Args:
        start (str): Rollover start time as dictated in config.yaml.
        end (str): Rollover end time as dictated in config.yaml.

    Returns:
        list: List of days to display games for. Will have 1 or 2 elements. 
    """

    # Get the current date and time.
    cur_datetime = datetime.today()
    cur_date = cur_datetime.date()
    cur_time = cur_datetime.time()

    # Convert the provided rollover start and end times to time objects.
    start_time = datetime.strptime(start, '%H:%M').time()
    end_time = datetime.strptime(end, '%H:%M').time()

    # Empty list to store the days.
    dates_to_display = []

    # Determine the days to display.
    # If before the rollover start, yesterday.
    if cur_time < start_time:
        dates_to_display.append(cur_date - timedelta(days=1))
    # If between rollover start and end, yesterday and today.
    elif cur_time >= start_time and cur_time < end_time:
        dates_to_display.append(cur_date - timedelta(days=1))
        dates_to_display.append(cur_date)
    # If after rollover end, today only.
    else:
        dates_to_display.append(cur_date)

    return dates_to_display