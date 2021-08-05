import gurobipy as gp
import csv
from datetime import datetime
import pathlib

NUM_HOURS = 24


def convert_time(item):
    return datetime.strptime(item['local_time'], "%Y-%m-%d %H:%M")


class Grid:
    MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    def __init__(self, hourly_grid, allow_grid, model=None):
        self.monthly_usage = None
        self.grid_installed = None
        self.hourly_grid = hourly_grid
        self.hourly_grid_sale = {k: v * 0.1 for k, v in hourly_grid.items()}
        self.artificial_grid_cost_kwh = 200  # TODO: change this to large value
        self.allow_grid = allow_grid
        if model:
            self.init_dvs(model)

        if allow_grid is False:
            model.addConstr(self.grid_installed == 0)

    def init_dvs(self, model):
        self.monthly_usage = {month: [model.addVar() for _ in range(NUM_HOURS)] for month in self.MONTHS}
        self.grid_installed = model.addVar(vtype=gp.GRB.BINARY)  # TODO add binary variable for grid installed

    def artificial_total_grid_cost(self, concretize=False):
        return sum(sum(hour for hour in monthly_grid) * self.artificial_grid_cost_kwh if not concretize else
                   sum(hour.x for hour in monthly_grid) * self.artificial_grid_cost_kwh
                   for monthly_grid in self.monthly_usage.values())

    def actual_total_grid_cost(self, concretize=False):
        return sum(sum(g * self.hourly_grid[month, hour] for hour, g in enumerate(monthly_grid)) if not concretize else
                   sum(g.x * self.hourly_grid[month, hour] for hour, g in enumerate(monthly_grid))
                   for month, monthly_grid in self.monthly_usage.items())

    def electricity_usage(self, month, hour, concretize=False):
        return self.monthly_usage[month][hour] if concretize is False else self.monthly_usage[month][hour].x

    def heat_usage_by_month(self, month):
        return self.monthly_usage[month]  # TODO: seperate decision variable for "heat" usage?

    @classmethod
    def data_from_csv(cls, grid_path, allow_grid, model=None):
        with open(grid_path) as fp:
            table = csv.DictReader(row for row in fp if not row.startswith('#'))
            hourly_demand = {(convert_time(row).month, convert_time(row).hour): float(row['grid_cost']) for row in table}

        return Grid(hourly_grid=hourly_demand, allow_grid=allow_grid, model=model)

    @classmethod
    def from_location(cls, location, allow_grid, model=None):
        project_root = pathlib.Path(__file__).parent.parent
        tlocation = location.replace(",", "_").lower()
        grid_path = project_root / 'data' / 'grid_data' / f'grid_{tlocation}.csv'
        return Grid.data_from_csv(grid_path=grid_path, allow_grid=allow_grid, model=model)
