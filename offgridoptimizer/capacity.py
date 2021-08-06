import csv
import itertools
import pathlib
from datetime import datetime

from offgridoptimizer import hour_of_year, convert_time


class Capacity:
    def __init__(self, hourly_solar_capacity=None, hourly_wind_capacity=None):
        self.hourly_solar_capacity = hourly_solar_capacity
        self.hourly_wind_capacity = hourly_wind_capacity

    @classmethod
    def data_from_csv(cls, solar_capacity_path, wind_capacity_path):
        def process(path):
            with open(path) as fp:
                table = csv.DictReader(row for row in fp if not row.startswith('#'))
                # data = [{"time": hour_of_year(convert_time(row)), "efficiency": float(row['electricity'])} for row in table]
                data = {hour_of_year(convert_time(row)): float(row['electricity']) for row in table}

            return data

        solar_capacity = process(solar_capacity_path)
        wind_capacity = process(wind_capacity_path)

        return Capacity(hourly_solar_capacity=solar_capacity, hourly_wind_capacity=wind_capacity)

    @classmethod
    def from_location(cls, location):
        project_root = pathlib.Path(__file__).parent.parent
        tlocation = location.replace(",", "_").lower()
        solar_capacity_path = project_root / 'data' / 'capacity_data' / f'ninja_pv_{tlocation}.csv'
        wind_capacity_path = project_root / 'data' / 'capacity_data' / f'ninja_wind_{tlocation}.csv'
        return Capacity.data_from_csv(solar_capacity_path=solar_capacity_path, wind_capacity_path=wind_capacity_path)

    def lookup(self, hour, energy_type):
        if energy_type == 'wind':
            return self.hourly_wind_capacity[hour]
        elif energy_type == 'solar':
            return self.hourly_solar_capacity[hour]
        else:
            assert False, "Only energy types available are wind and solar"
