from .project import Project
from .product import Product

import gurobipy as gp

MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]


class OffGridOptimizer:
    def __init__(self, model_name, demand=None, budget=None, products=None, grid=None):
        self._model = gp.Model(model_name)

        self._demand = demand
        self._demand_constraints = []

        self._budget = budget
        self._budget_constraints = []

        self._products = Product.create_products(product_list=products, model=self._model)
        self._product_constraints = []

        self._project: Project = Project(products=products, grid=grid)

    @property
    def grid(self):
        return self._project.grid

    @grid.setter
    def grid(self, new_grid):
        self._project.grid = new_grid
        self.update_demand_constraints()

    @property
    def demand(self):
        return self._demand

    @demand.setter
    def demand(self, new_demand):
        self._demand = new_demand
        self.update_demand_constraints()

    def update_demand_constraints(self):
        self.remove_constraints(self._demand_constraints)
        # add monthly demand constraints
        electricity_demand = self.demand["electricity_demand"]
        heat_demand = self.demand["heat_demand"]
        self._demand_constraints = self._project.set_demand_constraints(self._model, electricity_demand, heat_demand)

    @property
    def products(self):
        return self._products

    @products.setter
    def products(self, new_products):
        self.remove_constraints(self._product_constraints)
        self._project.products = new_products
        self._project.set_product_constraints(self._model)
        self.set_objective()

    @property
    def budget(self):
        return self._budget

    @budget.setter
    def budget(self, new_budget):
        self.remove_constraints(self._budget_constraints)
        self._budget = new_budget
        self._budget_constraints = self._project.set_budget_constraints(self._model,
                                                                        initial_budget=self.budget["initial"],
                                                                        monthly_budget=self.budget["monthly"])

    def remove_constraints(self, constraints):
        for c in constraints:
            self._model.remove(c)

    def set_objective(self):
        self._model.setObjective(self._project.objective(), gp.GRB.MINIMIZE)

    def optimize(self):
        self._model.optimize()

    def print_results(self):
        print('results!')

