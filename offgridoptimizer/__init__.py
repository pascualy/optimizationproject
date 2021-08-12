
from datetime import datetime, timedelta


def convert_time(item, fmt="%Y-%m-%d %H:%M"):
    return datetime.strptime(item['local_time'], fmt)


def hour_of_year(dt):
    beginning_of_year = datetime(dt.year, 1, 1, tzinfo=dt.tzinfo)
    return int((dt - beginning_of_year).total_seconds() // 3600)


def date_from_hour(hour):
    return datetime(year=2018, day=1, month=1) + timedelta(hours=hour)

LEAP_DAY_HOUR = 1416
DAYLIGHT_SAVINGS_SPRING = 1634
SOMETHING_ELSE = 1586

def one_day_each_month():
    hours = []
    for month in range(1, 13):
        s = hour_of_year(datetime(year=2018, day=1, month=month))
        hours.extend(list(range(s, s + 24)))

    try:
        hours.remove(LEAP_DAY_HOUR)
    except ValueError:
        pass

    return hours


def everyday_one_month(month):
    hours = []
    m = datetime(year=2018, day=1, month=month)
    day = 1
    cont = True
    while m.month == month and cont:
        for hour in range(24):
            try:
                m = datetime(year=2018, day=day, month=month, hour=hour)
            except ValueError as e:
                print(e)
                cont = False
                break

            hours.append(hour_of_year(m))
        #
        # if day == 25:
        #     break

        day += 2

    hours = list(range(0, HOURS_IN_YEAR, 4))
    print(hours)
    try:
        hours.remove(LEAP_DAY_HOUR)
        hours.remove(DAYLIGHT_SAVINGS_SPRING)
        hours.remove(SOMETHING_ELSE)
    except ValueError:
        pass

    return hours


def hours_each_month(months):
    hours = []
    for month in months:
        m = datetime(year=2018, day=1, month=month)
        day = 1
        cont = True
        while m.month == month and cont:
            for hour in range(24):
                try:
                    m = datetime(year=2018, day=day, month=month, hour=hour)
                except ValueError as e:
                    cont = False
                    break

                hours.append(hour_of_year(m))

            day += 1

    try:
        hours.remove(LEAP_DAY_HOUR)
        hours.remove(DAYLIGHT_SAVINGS_SPRING)
        hours.remove(SOMETHING_ELSE)
    except ValueError:
        pass

    return hours

MONTHS_IN_YEAR = 365
HOURS_IN_DAY = 24
HOURS_IN_YEAR = MONTHS_IN_YEAR * HOURS_IN_DAY




from .grid import Grid
from .product import Product
from .project import Project
from .config_schema import validate_config, load_and_validate
