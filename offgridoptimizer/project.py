import json

from typing import List
from . import Product, Grid
from offgridoptimizer.constraints import DemandConstraint, ProductConstraint, BudgetConstraint
from offgridoptimizer.config_schema import load_and_validate, validate_config
from offgridoptimizer.capacity import Capacity
from offgridoptimizer.demand import Demand

from tabulate import tabulate

import gurobipy as gp

GP_ENV = gp.Env(empty=True)
# GP_ENV.setParam('LogToConsole', 0)
GP_ENV.start()

MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]


def list2dict(l):
    return {month + 1: demand for month, demand in enumerate(l)}


class Project:
    def __init__(self, product_list, initial_budget,
                 monthly_budget, location, allow_grid, hours):
        self.hours = hours
        self.demand = Demand.from_location(location)
        self.efficiency = Capacity.from_location(location)

        self.model = gp.Model('Project', env=GP_ENV)

        print('Setting up Energy Sold')
        self.ss = {hour: self.model.addVar() for hour in self.hours}  # Energy sold
        self.storage_installed = self.model.addVar(vtype=gp.GRB.BINARY)

        print('Setting up Grid')
        self.grid = Grid.from_location(location, allow_grid, model=self.model, project=self)

        print('Setting up Products')
        self.products = Product.create_products(product_list, model=self.model, project=self)
        self.product_constraint = ProductConstraint(self)

        self.initial_budget = initial_budget
        self.monthly_budget = monthly_budget

        print('Setting up Budget')
        self.budget_constraint = BudgetConstraint(self)

        print('Setting up Demand')
        self.demand_constraint = DemandConstraint(self)

        self.set_objective()

    def products_by_type(self, energy_type):
        return [product for product in self.products if product.et == energy_type]

    #################
    # Project Costs #
    #################

    def total_opening_cost(self, concretize=False):
        grid_cost = (self.grid.grid_installed * self.grid.grid_opening_cost) if not concretize \
               else (self.grid.grid_installed.x * self.grid.grid_opening_cost)
        product_cost = sum((product.x if not concretize else product.x.x) * product.oc for product in self.products)
        return grid_cost + product_cost

    def total_maintenance_cost(self, concretize=False):
        return sum((product.y if not concretize else product.y.x) * product.mc for product in self.products)

    def total_incremental_cost(self, concretize=False):
        return sum((product.y if not concretize else product.y.x) * product.ic for product in self.products)

    def total_revenue(self, concretize=False):
        return sum([self.grid.hourly_grid_sale[hour] * self.energy_sold(hour, concretize)
             for hour in self.hours])

    def capital_costs(self, concretize=False):
        grid_cost = (self.grid.grid_installed * self.grid.grid_opening_cost) if not concretize \
            else (self.grid.grid_installed.x * self.grid.grid_opening_cost)

        return grid_cost + sum(product.oc * (product.x if not concretize else product.x.x) +
                   product.ic * (product.y if not concretize else product.y.x) for product in self.products)

    def operational_costs(self, concretize=False):
        return sum(product.mc * (product.y if not concretize else product.y.x) for product in self.products)

    ####################
    # Project Capacity #
    ####################
    @property
    def hourly_capacity(self):
        z = {}
        for h in self.hours:
            z[h] = self.electricity_capacity(h, True)

        return z

    @property
    def hourly_storage_level(self):
        z = {}
        times = []
        for hour in self.hours:
            z[hour] = sum(self.energy_stored(h, True) for h in times) - \
                        sum(self.storage_consumed(h, True) for h in times)# - \
                          #sum(self.energy_sold(h, True) for h in times)
            times.append(hour)

        return z

    @property
    def hourly_grid_usage(self):
        z = {}
        for h in self.hours:
            z[h] = self.grid_capacity(h, True)

        return z

    @property
    def hourly_energy_sold(self):
        z = {}
        for h in self.hours:
            z[h] = self.energy_sold(h, True)

        return z

    def energy_stored(self, hour, concretize=False):
        return sum(product.energy_stored(hour=hour, concretize=concretize)
                   for product in self.products if product.et == Product.STORAGE)

    def storage_consumed(self, hour, concretize=False):
        return sum(product.storage_consumed(hour=hour, concretize=concretize)
                   for product in self.products if product.et == Product.STORAGE)

    def energy_sold(self, hour, concretize=False):
        return self.ss[hour] if not concretize else self.ss[hour].x

    # def storage_capacity(self, month, hour, concretize=False):
    #     return sum(product.capacity(month=month, hour=hour, concretize=concretize)
    #                for product in self.products if product.et == Product.STORAGE)

    def electricity_capacity(self, hour, concretize=False):
        if concretize:
            return sum(product.y.x * product.ca * self.efficiency.lookup(hour, product.et)
                   for product in self.products if product.ut == Product.ELEC and product.et != Product.STORAGE)
        else:
            return sum(product.y * product.ca * self.efficiency.lookup(hour, product.et)
                       for product in self.products if product.ut == Product.ELEC and product.et != Product.STORAGE)

    def heat_capacity(self, hour):
        return self._capacity(hour, Product.HEAT)

    def grid_capacity(self, hour, concretize=False):
        return self.grid.electricity_usage(hour, concretize=concretize)

    def _capacity(self, hour, utilty_type):
        return sum(product.ca * self.efficiency.lookup(hour, product.et)
                   for product in self.products if product.ut == utilty_type)

    def electricity_demand(self, hour):
        return self.demand.hourly_demand[hour]

    def heat_demand(self, hour):
        pass

    # def elec_capacity_by_month(self, month):
    #     return self._capacity_by_month(month, Product.ELEC)
    #
    # def heat_capacity_by_month(self, month):
    #     return self._capacity_by_month(month, Product.HEAT)
    #
    # def _capacity_by_month(self, month, utilty_type):
    #     return sum(product.ca[month] * product.y for product in self.products if product.ut == utilty_type)

    #######################
    # Project Constraints #
    #######################

    def set_demand_constraints(self, electricity_demand, heat_demand):
        self.monthly_electricity_demand = electricity_demand
        self.monthly_heat_demand = heat_demand
        self.demand_constraint.update_constraints()
        self.set_objective()

    def set_product_constraints(self, new_products, grid=None):
        self.products = new_products
        if grid:
            self.grid = grid

        self.product_constraint.update_constraints()
        self.set_objective()

    def set_budget_constraints(self, initial_budget, monthly_budget):
        self.initial_budget = initial_budget
        self.monthly_budget = monthly_budget
        self.budget_constraint.update_constraints()
        self.set_objective()

    #####################
    # Project Objective #
    #####################

    def set_objective(self):
        return self.model.setObjective(self.total_opening_cost() +
                                       self.total_maintenance_cost() +
                                       self.total_incremental_cost() +
                                       -self.total_revenue() +
                                       self.grid.artificial_total_grid_cost(), gp.GRB.MINIMIZE)
        # return self.model.setObjective(self.total_opening_cost() +
        #                                self.total_maintenance_cost() +
        #                                self.total_incremental_cost() +
        #                                self.grid.grid_installed * -self.total_revenue() +
        #                                (1 - self.grid.grid_installed) * self.total_revenue() +
        #                                self.grid.artificial_total_grid_cost(), gp.GRB.MINIMIZE)

    def optimize(self):
        print('Optimizing')
        self.model.optimize()

    def print_results(self):
        headers = ['Product Name', 'Quantity']
        selected_products = tabulate([(p.name, p.y.x) for p in self.products] +
                                     [("grid", sum(hour.x for hour in self.grid.hourly_usage.values()))], headers=headers)
        print(selected_products)

        print('\n\n')

        cost_headers = ["Cost", "Dollars ($)"]
        costs = self.costs()
        final_costs = tabulate(costs, headers=cost_headers)
        print(final_costs)

    def costs(self):
        toc = self.total_opening_cost(concretize=True)
        tmc = self.total_maintenance_cost(concretize=True)
        tic = self.total_incremental_cost(concretize=True)
        tgc = self.grid.actual_total_grid_cost(concretize=True)
        tr = self.total_revenue(concretize=True)
        return (("Total Opening Cost", toc),
             ("Total Maintenance Cost", tmc),
             ("Total Incremental Cost", tic),
             ("Total Grid Cost", tgc),
             ("Total Revenue", tr),
             ("Total Cost", toc + tmc + tic + tgc - tr))

    def cost_labels(self):
        return ("Total Opening Cost", "Total Maintenance Cost",
                "Total Incremental Cost", "Total Grid Cost", "Total Revenue", "Total Cost")

    def selected_products(self):
        return [(p.name, p.y.x) for p in self.products] + \
        [("grid", sum(hour.x for hour in self.grid.hourly_usage.values()))]

    @classmethod
    def project_from_config_path(cls, config_path, hours):
        config = load_and_validate(config_path)

        return Project.project_from_config(config, hours, validate=False)

    @classmethod
    def project_from_config(cls, config, hours, validate=True):
        if validate:
            validate_config(config)

        budget = config['budget']
        return Project(product_list=config['products'],
                       initial_budget=budget['initial'],
                       monthly_budget=budget['monthly'],
                       location=config['location'],
                       allow_grid=config['allow_grid'],
                       hours=hours)

    def results_df(self):
        import pandas as pd
        from functools import reduce

        def dict2pd(arg):
            d, col = arg
            return pd.Series(d).rename_axis(['hour']).reset_index(name=col)

        data = [(self.demand.hourly_demand, 'demand'),
                (self.efficiency.hourly_solar_capacity, 'pv_efficiency'),
                (self.efficiency.hourly_wind_capacity, 'wind_efficiency'),
                (self.hourly_capacity, 'capacity'),
                (self.hourly_storage_level, 'storage_level'),
                (self.hourly_energy_sold, 'energy_sold'),
                (self.hourly_grid_usage, 'grid_usage')]

        tdata = map(dict2pd, data)
        df = reduce(lambda df1, df2: pd.merge(df1, df2), tdata)
        df['date'] = pd.Timestamp('2019-01-01') + pd.to_timedelta(df['hour'], unit='H')
        return df

    def parameters_df(self):
        import pandas as pd
        from functools import reduce

        def dict2pd(arg):
            d, col = arg
            return pd.Series(d).rename_axis(['hour']).reset_index(name=col)

        data = [(self.demand.hourly_demand, 'demand'),
                (self.efficiency.hourly_solar_capacity, 'pv_efficiency'),
                (self.efficiency.hourly_wind_capacity, 'wind_efficiency')]

        tdata = map(dict2pd, data)
        df = reduce(lambda df1, df2: pd.merge(df1, df2), tdata)
        df['date'] = pd.Timestamp('2019-01-01') + pd.to_timedelta(df['hour'], unit='H')
        return df


