from datetime import datetime
from constants import NUM_HOURS_IN_DAY, NUM_MINUTES_IN_HOUR, NUM_SECONDS_IN_MINUTE

def is_at_most_X_hours_apart(date1: datetime, date2: datetime, x: int):
    return ((date1.timestamp() - date2.timestamp()) >= NUM_SECONDS_IN_MINUTE * NUM_MINUTES_IN_HOUR * x)

def is_same_day(date1: datetime, date2: datetime):
    if date1.day == date2.day and date1.month == date2.month and date1.year == date2.year:
        return True
    return False

def is_at_least_X_days_apart(date1: datetime, date2: datetime, x: int):
    return ((date1.timestamp() - date2.timestamp()) >= NUM_SECONDS_IN_MINUTE * NUM_MINUTES_IN_HOUR * NUM_HOURS_IN_DAY *x )