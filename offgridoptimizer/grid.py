import gurobipy as gp

NUM_HOURS = 24

class Grid:
    MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    def __init__(self, grid_cost_kwh, grid_cost_env, model=None):
        self.monthly_usage = None
        self.grid_cost_kwh = grid_cost_kwh
        self.artificial_grid_cost_kwh = 10000000
        if model:
            self.init_dvs(model)

        self.excess = {month: [model.addVar(vtype=gp.GRB.BINARY) for _ in range(NUM_HOURS)] for month in self.MONTHS}

    def init_dvs(self, model):
        self.monthly_usage = {month: [model.addVar() for _ in range(NUM_HOURS)] for month in self.MONTHS}

    def artificial_total_grid_cost(self, concretize=False):
        return sum(sum(hour for hour in monthly_grid) * self.artificial_grid_cost_kwh if not concretize else
                   sum(hour.x for hour in monthly_grid) * self.artificial_grid_cost_kwh
                   for monthly_grid in self.monthly_usage.values())

    def actual_total_grid_cost(self, concretize=False):
        return sum(sum(hour for hour in monthly_grid) * self.grid_cost_kwh if not concretize else
                   sum(hour.x for hour in monthly_grid) * self.grid_cost_kwh
                   for monthly_grid in self.monthly_usage.values())

    def electricity_usage(self, month, hour, concretize=False):
        return self.monthly_usage[month][hour] if concretize == False else self.monthly_usage[month][hour].x

    def heat_usage_by_month(self, month):
        return self.monthly_usage[month]  # TODO: seperate decision variable for "heat" usage?

    def excess_capacity(self, month, hour, concretize=False):
        return self.excess[month][hour] if concretize == False else self.excess[month][hour].x
