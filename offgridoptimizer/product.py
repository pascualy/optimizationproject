from typing import List
from enum import Enum

from tabulate import tabulate
import gurobipy as gp


NUM_MONTHS = 12
NUM_HOURS = 24

EQUIVALENT_KEYS = {
    "name": "name",
    "ut": "utility_type",
    "et": "energy_type",
    "oc": "opening_cost",
    "ic": "incremental_cost",
    "mc": "maintenance_cost",
    "ca": "monthly_capacity",
    "am": "amortization"
}


class Product:
    STORAGE = 'storage'
    HEAT = 'heat'
    ELEC = 'electricity'
    ENERGY_TYPES = ['solar', 'wind', 'geothermal', 'biomass', 'storage']

    def __init__(self, name: str, utility_type: str, energy_type: str, opening_cost: float, incremental_cost: float,
                 maintenance_cost: float, capacity: List[float], amortization: float):
        self.name = name
        self.ut = utility_type        # H or E
        self.et = energy_type         # ENERGY_TYPES
        self.oc = opening_cost        # Dollars Per Opening
        self.ic = incremental_cost    # Dollars Per Product
        self.mc = maintenance_cost    # Annual Maintenance Cost
        self.am = amortization
        self.ca = capacity  # KwH per Month
        self.x = None  # Whether opening cost must be paid
        self.y = None  # How many units of this product to install

    def init_dvs(self, model, project=None):
        """
        Initialize this Product's decision variables with a provided Gurobi Model

        :param model: a gurobi.Model to create our decision variables within
        :return:
        """
        self.x = model.addVar(vtype=gp.GRB.BINARY)
        self.y = model.addVar(vtype=gp.GRB.INTEGER)

    @classmethod
    def create_products(cls, product_list, model=None, project=None):
        products = []
        for p in product_list:
            p = {EQUIVALENT_KEYS[k] if k in EQUIVALENT_KEYS else k: v for k,v in p.items()}
            if p['energy_type'] == Product.STORAGE:
                products.append(StorageProduct(**p))
            else:
                products.append(Product(**p))

            if model:
                products[-1].init_dvs(project=project, model=model)

        return products

    @classmethod
    def headers(cls):
        return ('name', 'utility_type', 'energy_type', 'opening_cost', 'incremental_cost',
                'maintenance_cost', 'amortization', 'capacity')

    def parameters(self):
        return self.name, self.ut, self.et, self.oc, self.ic, self.mc, self.am, self.ca


class StorageProduct(Product):
    def __init__(self, name: str, utility_type: str, energy_type: str, opening_cost: float, incremental_cost: float,
                 maintenance_cost: float, capacity: List[float], amortization: float):
        super().__init__(name, utility_type, energy_type, opening_cost, incremental_cost,
                         maintenance_cost, capacity, amortization)
        self.b = None  # Excess energy generated per hour
        self.sc = None  # Energy consumed from battery per hour
        self.ss = None

    def init_dvs(self, model, project=None):
        super().init_dvs(model)
        self.b = {hour: model.addVar() for hour in project.hours}  # how much electricity is stored a particular hour
        self.sc = {hour: model.addVar() for hour in project.hours}  # how much electricity is consumed from storage on a particular hour

    def capacity(self, hour, concretize=False):
        return self.b[hour] if not concretize else self.b[hour].x

    def storage_consumed(self, hour, concretize=False):
        return self.sc[hour] if not concretize else self.sc[hour].x

    def energy_stored(self, hour, concretize=False):
        return self.b[hour] if not concretize else self.b[hour].x
