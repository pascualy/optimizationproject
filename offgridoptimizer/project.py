from typing import List
from . import Product, Grid
from offgridoptimizer.constraints import DemandConstraint, ProductConstraint, BudgetConstraint

from tabulate import tabulate

import gurobipy as gp


MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]


def list2dict(l):
    return {month + 1: demand for month, demand in enumerate(l)}


class Project:
    def __init__(self, product_list, grid_cost_kwh, grid_cost_env, initial_budget, monthly_budget, monthly_electricity_demand, monthly_heat_demand):
        self.model = gp.Model('Project')

        self.grid = Grid(grid_cost_kwh, grid_cost_env, model=self.model)
        self.products = Product.create_products(product_list, model=self.model)
        self.product_constraint = ProductConstraint(self)

        self.initial_budget = initial_budget
        self.monthly_budget = monthly_budget
        self.budget_constraint = BudgetConstraint(self)

        self.monthly_electricity_demand = list2dict(monthly_electricity_demand)
        self.monthly_heat_demand = list2dict(monthly_heat_demand)
        self.demand_constraint = DemandConstraint(self)

        self.set_objective()

    def products_by_type(self, energy_type):
        return [product for product in self.products if product.et == energy_type]

    #################
    # Project Costs #
    #################

    def total_opening_cost(self, concretize=False):
        return sum(product.x if not concretize else product.x.x * product.oc for product in self.products)

    def total_maintenance_cost(self, concretize=False):
        return sum(product.y if not concretize else product.y.x * product.mc for product in self.products)

    def total_incremental_cost(self, concretize=False):
        return sum(product.y if not concretize else product.y.x * product.ic for product in self.products)

    def total_environmental_cost(self, concretize=False):
        return sum(product.y if not concretize else product.y.x * product.ec for product in self.products)

    def capital_costs(self, concretize=False):
        return sum(product.oc * product.x if not concretize else product.x.x +
                   product.ic * product.y if not concretize else product.y.x for product in self.products)

    def operational_costs(self, concretize=False):
        return sum(product.mc * product.y if not concretize else product.y.x for product in self.products) + \
                self.grid.total_grid_cost(concretize=concretize)


    ####################
    # Project Capacity #
    ####################

    def elec_capacity_by_month(self, month):
        return self._capacity_by_month(month, Product.ELEC)

    def heat_capacity_by_month(self, month):
        return self._capacity_by_month(month, Product.HEAT)

    def _capacity_by_month(self, month, utilty_type):
        return sum(product.ca[month] * product.y for product in self.products if product.ut == utilty_type)

    #######################
    # Project Constraints #
    #######################

    def set_demand_constraints(self, electricity_demand, heat_demand):
        self.demand.update_constraints(electricity_demand, heat_demand)
        self.set_objective()

    def set_product_constraints(self, products, grid=None):
        self.products = new_products
        if grid:
            self.grid = grid

        self.product_constraint.update_constraints()
        self.set_objective()

    def set_budget_constraints(self, initial_budget, monthly_budget):
        self.initial_budget = initial_budget
        self.monthly_budget = monthly_budget
        self.budget.update_constraints()
        self.set_objective()

    #####################
    # Project Objective #
    #####################

    def set_objective(self):
        return self.model.setObjective(self.total_opening_cost() +
                                       self.total_maintenance_cost() +
                                       self.total_incremental_cost() +
                                       self.total_environmental_cost() +
                                       self.grid.total_grid_cost(), gp.GRB.MINIMIZE)

    def optimize(self):
        self.model.optimize()

    def print_results(self):
        headers = ['Product Name', 'Quantity']
        selected_products = tabulate([(p.name, p.y.x) for p in self.products] +
                                     [("grid", sum(x.x for x in self.grid.monthly_usage.values()))], headers=headers)
        print(selected_products)

        print('\n\n')

        cost_headers = ["Cost", "Dollars ($)"]
        costs = [("Total Opening Cost", self.total_opening_cost(concretize=True)),
                 ("Total Maintenance Cost", self.total_maintenance_cost(concretize=True)),
                 ("Total Incremental Cost", self.total_incremental_cost(concretize=True)),
                 ("Total Environmental Cost", self.total_environmental_cost(concretize=True)),
                 ("Total Grid Cost", self.grid.total_grid_cost(concretize=True))]
        final_costs = tabulate(costs, headers=cost_headers)
        print(final_costs)