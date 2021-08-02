import csv
import itertools
import pathlib
from datetime import datetime


def convert_time(item):
    return datetime.strptime(item['local_time'], "%Y-%m-%d %H:%M")


class Capacity:
    def __init__(self, hourly_solar_capacity=None, hourly_wind_capacity=None):
        self.hourly_solar_capacity = hourly_solar_capacity
        self.hourly_wind_capacity = hourly_wind_capacity

    @classmethod
    def data_from_csv(cls, solar_capacity_path, wind_capacity_path):

        with open(solar_capacity_path) as fp:
            table = csv.DictReader(row for row in fp if not row.startswith('#'))
            solar_capacity = [{"time": convert_time(row), "efficiency": float(row['electricity'])} for row in table]

        with open(wind_capacity_path) as fp:
            table = csv.DictReader(row for row in fp if not row.startswith('#'))
            wind_capacity = [{"time": convert_time(row), "efficiency": float(row['electricity'])} for row in table]

        return Capacity(hourly_solar_capacity=solar_capacity, hourly_wind_capacity=wind_capacity)

    @classmethod
    def from_location(cls, location):
        project_root = pathlib.Path(__file__).parent.parent
        solar_capacity_path = project_root / 'configs' / 'capacity_data' / f'ninja_pv_{location}.csv'
        wind_capacity_path = project_root / 'configs' / 'capacity_data' / f'ninja_wind_{location}.csv'
        return Capacity.data_from_csv(solar_capacity_path=solar_capacity_path, wind_capacity_path=wind_capacity_path)

    def lookup(self, month, hour, energy_type):
        if energy_type == 'wind':
            data = self.hourly_wind_capacity
        elif energy_type == 'solar':
            data = self.hourly_solar_capacity
        else:
            assert False, "Only energy types available are wind and solar"

        items = [item for item in data if item['time'].month == month and item['time'].hour == hour]
        return sum(item['efficiency'] for item in items) / len(items)
