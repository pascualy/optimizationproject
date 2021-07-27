import pytest
import json

from offgridoptimizer import Project, Grid, load_and_validate

def test_project():
    config = load_and_validate('../configs/logan/config.json')

    grid_config = config['grid']
    budget = config['budget']
    demand = config['demand']
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