import datetime as dt


def determine_report_date(cur_date, cur_time, rollover_time) -> dt.date:
    """ Determines the current date data should be retrieved for.

    Args:
        cur_date (date): Current date.
        cur_time (time): Current time.
        rollover_time (time): Date rollover time specified in config.yaml.

    Returns:
        date: Date to get data for.
    """
    
    # If it isn't past the rollover time, report on data from the previous day.
    report_date = cur_date if cur_time > rollover_time else cur_date - dt.timedelta(days=1)
    return report_date