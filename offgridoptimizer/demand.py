import csv
import itertools
import pathlib
from datetime import datetime


def convert_time(item):
    return datetime.strptime(item['local_time'], "%m-%d-%Y %H:%M")


class Demand:
    def __init__(self, hourly_demand=None):
        self.hourly_demand = hourly_demand

    @classmethod
    def data_from_csv(cls, demand_path):
        with open(demand_path) as fp:
            table = csv.DictReader(row for row in fp if not row.startswith('#'))
            hourly_demand = {(convert_time(row).month, convert_time(row).hour): float(row['demand']) for row in table}

        return Demand(hourly_demand=hourly_demand)

    @classmethod
    def from_location(cls, location):
        tlocation = location.replace(",", "_").lower()
        project_root = pathlib.Path(__file__).parent.parent
        demand_path = project_root / 'data' / 'demand_data' / f'demand_{tlocation}.csv'
        return Demand.data_from_csv(demand_path=demand_path)
