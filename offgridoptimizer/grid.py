import gurobipy as gp


class Grid:
    MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    def __init__(self, grid_cost_kwh, grid_cost_env, model=None):
        self.monthly_usage = None
        self.grid_cost_kwh = grid_cost_kwh
        self.grid_cost_env = grid_cost_env
        if model:
            self.init_dvs(model)

    def init_dvs(self, model):
        self.monthly_usage = {month: model.addVar(vtype=gp.GRB.INTEGER) for month in self.MONTHS}

    def total_grid_cost(self, concretize=False):
        return sum(monthly_grid if not concretize else monthly_grid.x * (self.grid_cost_kwh + self.grid_cost_env) for monthly_grid in self.monthly_usage.values())

    def elec_usage_by_month(self, month):
        return self.monthly_usage[month]

    def heat_usage_by_month(self, month):
        return self.monthly_usage[month]  # TODO: seperate decision variable for "heat" usage?
