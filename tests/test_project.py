import pytest
import json

from offgridoptimizer import Project, Grid

def test_project():
    with open('../configs/logan/config.json') as fp:
        config = json.load(fp)

    grid_config = config['grid']
    budget = config['budget']
    demand = config['demand']
    grid = Grid(grid_config['grid_cost_kwh'], grid_config['grid_cost_env'])
    project = Project(product_list=config['products'],
                      grid_cost_kwh=grid_config['grid_cost_kwh'],
                      grid_cost_env=grid_config['grid_cost_env'],
                      initial_budget=budget['initial'],
                      monthly_budget=budget['monthly'],
                      monthly_electricity_demand=demand['monthly_electricity_demand'],
                      monthly_heat_demand=demand['monthly_heat_demand'])
    project.optimize()
    project.print_results()

test_project()


# TODO Project class should keep track of constraints and allow updating products/budget/demand