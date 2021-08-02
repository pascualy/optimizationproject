import json

from typing import List
from . import Product, Grid
from offgridoptimizer.constraints import DemandConstraint, ProductConstraint, BudgetConstraint
from offgridoptimizer.config_schema import load_and_validate, validate_config
from offgridoptimizer.capacity import Capacity

from tabulate import tabulate

import gurobipy as gp

GP_ENV = gp.Env(empty=True)
# GP_ENV.setParam('LogToConsole', 0)
GP_ENV.start()

MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]


def list2dict(l):
    return {month + 1: demand for month, demand in enumerate(l)}


class Project:
    def __init__(self, product_list, grid_cost_kwh, initial_budget,
                 monthly_budget, monthly_electricity_demand, monthly_heat_demand, location):
        self.monthly_electricity_demand = list2dict(monthly_electricity_demand)
        self.monthly_heat_demand = list2dict(monthly_heat_demand)
        self.efficiency = Capacity.from_location(location)

        self.model = gp.Model('Project', env=GP_ENV)
        self.grid = Grid(grid_cost_kwh, model=self.model)
        self.products = Product.create_products(product_list, model=self.model)
        self.product_constraint = ProductConstraint(self)

        self.initial_budget = initial_budget
        self.monthly_budget = monthly_budget
        self.budget_constraint = BudgetConstraint(self)
        self.demand_constraint = DemandConstraint(self)

        self.set_objective()

    def products_by_type(self, energy_type):
        return [product for product in self.products if product.et == energy_type]

    #################
    # Project Costs #
    #################

    def total_opening_cost(self, concretize=False):
        return sum((product.x if not concretize else product.x.x) * product.oc for product in self.products)

    def total_maintenance_cost(self, concretize=False):
        return sum((product.y if not concretize else product.y.x) * product.mc for product in self.products)

    def total_incremental_cost(self, concretize=False):
        return sum((product.y if not concretize else product.y.x) * product.ic for product in self.products)

    def capital_costs(self, concretize=False):
        return sum(product.oc * (product.x if not concretize else product.x.x) +
                   product.ic * (product.y if not concretize else product.y.x) for product in self.products)

    def operational_costs(self, concretize=False):
        return sum(product.mc * (product.y if not concretize else product.y.x) for product in self.products)
        # return sum(product.mc * product.y if not concretize else product.y.x for product in self.products) + \
        #         self.grid.actual_total_grid_cost(concretize=concretize)

    ####################
    # Project Capacity #
    ####################
    def electricity_stored(self, month, hour, concretize=False):
        return sum(product.electricity_stored(month=month, hour=hour, concretize=concretize)
                   for product in self.products if product.et == Product.STORAGE)

    def storage_consumed(self, month, hour, concretize=False):
        return sum(product.storage_consumed(month=month, hour=hour, concretize=concretize)
                   for product in self.products if product.et == Product.STORAGE)

    # def storage_capacity(self, month, hour, concretize=False):
    #     return sum(product.capacity(month=month, hour=hour, concretize=concretize)
    #                for product in self.products if product.et == Product.STORAGE)

    def electricity_capacity(self, month, hour, concretize=False):
        if concretize:
            return sum(product.y.x * product.ca * self.efficiency.lookup(month, hour, product.et)
                   for product in self.products if product.ut == Product.ELEC and product.et != Product.STORAGE)
        else:
            return sum(product.y * product.ca * self.efficiency.lookup(month, hour, product.et)
                       for product in self.products if product.ut == Product.ELEC and product.et != Product.STORAGE)

    def heat_capacity(self, month, hour):
        return self._capacity(month, hour, Product.HEAT)

    def grid_capacity(self, month, hour, concretize=False):
        return self.grid.electricity_usage(month, hour, concretize=concretize)

    def _capacity(self, month, hour, utilty_type):
        return sum(product.ca * self.efficiency.lookup(month, hour, product.et)
                   for product in self.products if product.ut == utilty_type)

    def electricity_demand(self, month, hour):
        return self.monthly_electricity_demand[month][hour]

    def heat_demand(self, month, hour):
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
                                       self.grid.artificial_total_grid_cost(), gp.GRB.MINIMIZE)

    def optimize(self):
        self.model.optimize()

    def print_results(self):
        headers = ['Product Name', 'Quantity']
        selected_products = tabulate([(p.name, p.y.x) for p in self.products] +
                                     [("grid", sum(sum(hour.x for hour in x) for x in self.grid.monthly_usage.values()))], headers=headers)
        print(selected_products)

        print('\n\n')

        cost_headers = ["Cost", "Dollars ($)"]
        costs = self.costs()
        final_costs = tabulate(costs, headers=cost_headers)
        print(final_costs)

    def costs(self):
        return (("Total Opening Cost", self.total_opening_cost(concretize=True)),
         ("Total Maintenance Cost", self.total_maintenance_cost(concretize=True)),
         ("Total Incremental Cost", self.total_incremental_cost(concretize=True)),
         ("Total Grid Cost", self.grid.actual_total_grid_cost(concretize=True)))

    def selected_products(self):
        return [(p.name, p.y.x) for p in self.products] + \
        [("grid", sum(sum(x.x for x in month) for month in self.grid.monthly_usage.values()))]

    @classmethod
    def project_from_config_path(cls, config_path):
        config = load_and_validate(config_path)

        return Project.project_from_config(config, validate=False)

    @classmethod
    def project_from_config(cls, config, validate=True):
        if validate:
            validate_config(config)

        grid_config = config['grid']
        budget = config['budget']
        demand = config['demand']
        return Project(product_list=config['products'],
                       grid_cost_kwh=grid_config['grid_cost_kwh'],
                       initial_budget=budget['initial'],
                       monthly_budget=budget['monthly'],
                       monthly_electricity_demand=demand['electricity_demand'],
                       monthly_heat_demand=demand['heat_demand'],
                       location=config['location'])

