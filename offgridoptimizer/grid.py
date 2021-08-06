import gurobipy as gp
import csv
from datetime import datetime
import pathlib

from offgridoptimizer import convert_time, hour_of_year

NUM_HOURS = 24


class Grid:
    MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    def __init__(self, project, hourly_grid, allow_grid, model=None):
        self.project = project
        self.hourly_usage = None
        self.grid_installed = None
        self.hourly_grid = hourly_grid
        self.hourly_grid_sale = {k: v * 0.001 for k, v in hourly_grid.items()}
        self.artificial_grid_cost_kwh = 200  # TODO: change this to large value
        self.allow_grid = allow_grid
        if model:
            self.init_dvs(model)

        if allow_grid is False:
            model.addConstr(self.grid_installed == 0)

    def init_dvs(self, model):
        self.hourly_usage = {hour: model.addVar() for hour in self.project.hours}
        self.grid_installed = model.addVar(vtype=gp.GRB.BINARY)  # TODO add binary variable for grid installed

    def artificial_total_grid_cost(self, concretize=False):
        return sum(g * self.artificial_grid_cost_kwh for hour, g in self.hourly_usage.items()) if not concretize else \
            sum(g.x * self.artificial_grid_cost_kwh for hour, g in self.hourly_usage.items())

    def actual_total_grid_cost(self, concretize=False):
        return sum(g * self.hourly_grid[hour] for hour, g in self.hourly_usage.items()) if not concretize else \
                    sum(g.x * self.hourly_grid[hour] for hour, g in self.hourly_usage.items())

    def electricity_usage(self, hour, concretize=False):
        return self.hourly_usage[hour] if concretize is False else self.hourly_usage[hour].x

    def heat_usage_by_month(self, hour):
        return self.hourly_usage[hour]  # TODO: seperate decision variable for "heat" usage?

    @classmethod
    def data_from_csv(cls, grid_path, allow_grid, model=None, project=None):
        with open(grid_path) as fp:
            table = csv.DictReader(row for row in fp if not row.startswith('#'))
            hourly_grid = {hour_of_year(convert_time(row)): float(row['grid_cost']) for row in table}

        return Grid(hourly_grid=hourly_grid, allow_grid=allow_grid, model=model, project=project)

    @classmethod
    def from_location(cls, location, allow_grid, model=None, project=None):
        project_root = pathlib.Path(__file__).parent.parent
        tlocation = location.replace(",", "_").lower()
        grid_path = project_root / 'data' / 'grid_data' / f'grid_{tlocation}.csv'
        return Grid.data_from_csv(grid_path=grid_path, allow_grid=allow_grid, model=model, project=project)
