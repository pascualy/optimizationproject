from typing import List
from enum import Enum

from tabulate import tabulate
import gurobipy as gp

EQUIVALENT_KEYS = {
    "name": "name",
    "ut": "utility_type",
    "et": "energy_type",
    "oc": "opening_cost",
    "ic": "incremental_cost",
    "mc": "maintenance_cost",
    "ca": "monthly_capacity",
    "am": "amoritization"
}


class Product:
    HEAT = 'heat'
    ELEC = 'electricity'
    ENERGY_TYPES = ['solar', 'wind', 'geothermal', 'biomass']

    def __init__(self, name: str, utility_type: str, energy_type: str, opening_cost: float, incremental_cost: float,
                 maintenance_cost: float, monthly_capacity: List[float], amoritization: float):
        self.name = name
        self.ut = utility_type        # H or E
        self.et = energy_type         # ENERGY_TYPES
        self.oc = opening_cost        # Dollars Per Opening
        self.ic = incremental_cost    # Dollars Per Product
        self.mc = maintenance_cost    # Annual Maintenance Cost
        self.amoritization = amoritization
        self.ec = 0 # Per KwH TODO: Calculate environmental cost based on energy type
        self.ca = {month + 1: capacity for month, capacity in enumerate(monthly_capacity)}  # KwH per Month
        self.x = None  # Whether opening cost must be paid
        self.y = None  # How many units of this product to install

    def init_dvs(self, model):
        """
        Initialize this Product's decision variables with a provided Gurobi Model

        :param model: a gurobi.Model to create our decision variables within
        :return:
        """
        self.x = model.addVar(vtype=gp.GRB.BINARY)
        self.y = model.addVar(vtype=gp.GRB.INTEGER)

    @classmethod
    def create_products(cls, product_list, model=None):
        products = []
        for p in product_list:
            p = {EQUIVALENT_KEYS[k] if k in EQUIVALENT_KEYS else k: v for k,v in p.items()}
            products.append(Product(**p))

            if model:
                products[-1].init_dvs(model)

        return products
