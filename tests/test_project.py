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
                      monthly_electricity_demand=demand['electricity_demand'],
                      monthly_heat_demand=demand['heat_demand'],
                      location=config['location'])
    project.optimize()
    project.print_results()

    z = [((m,h), project.electricity_stored(m,h, True), project.storage_consumed(m,h, True), project.electricity_capacity(m, h, True), project.grid_capacity(m, h, True), project.electricity_demand(m, h)) for m in range(1, 13) for h in range(0, 24)]
    for a in z:
        print(a)
        if a[0][1] == 16:
            break
    # times = []
    # for month in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
    #     for hour in list(range(24)):
    #         times.append((month, hour))
    #         total_stored = sum(project.electricity_stored(m, h, True) for m, h in times[:-1])
    #         total_consumed = sum(project.storage_consumed(m, h, True) for m, h in times[:-1])
    #         print((total_stored, total_consumed))

test_project()


# TODO Project class should keep track of constraints and allow updating products/budget/demand

(3906.838709677419, 10.0)
(16726.93548387097, 20.0)
(37118.32258064516, 30.0)
(61630.45161290322, 40.0)
(87508.25806451612, 50.0)
(87508.25806451612, 60.0)
(87508.25806451612, 70.0)
(87508.25806451612, 80.0)
(87508.25806451612, 90.0)
(87508.25806451612, 100.0)