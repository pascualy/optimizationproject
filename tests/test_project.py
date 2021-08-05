import pytest
import json

from offgridoptimizer import Project, Grid, load_and_validate

def test_project():
    config = load_and_validate('../configs/logan/logan.json')

    budget = config['budget']
    project = Project(product_list=config['products'],

                      initial_budget=budget['initial'],
                      monthly_budget=budget['monthly'],
                      location=config['location'],
                      allow_grid=config['allow_grid'])
    project.optimize()
    project.print_results()

    print(f'GC: {project.grid.grid_installed.x} {config["allow_grid"]}')
    z = []
    times = []
    for m in range(1, 13):
        for h in range(0, 24):
            z += [((m, h),
                   round(project.energy_stored(m, h, True)),
                   round(project.grid_capacity(m, h, True)),
                   round(project.storage_sold(m,h, True)),
                   ' ',
                   round(project.storage_consumed(m, h, True)),
                   round(project.electricity_capacity(m, h, True)),
                   ' ',
                   round(project.electricity_demand(m, h)),
                   ' ',
                   round(sum(project.energy_stored(x, y, True) for x, y in times)),
                   round(sum(project.storage_consumed(x,y,True) for x, y in times)),
                   round(sum(project.storage_sold(x, y, True) for x, y in times)),
                   ' ',
                   round(sum(project.energy_stored(x, y, True) for x, y in times) - sum(project.storage_consumed(x, y, True) for x, y in times) - sum(project.storage_sold(x, y, True) for x, y in times)))]
            times.append((m,h))
    # ((1, 7), 0.0, 0.0, 3525.154838709677, 0.0, 10, 0.0, 0.0)
    for a in z:
        print(a)
        # if a[0][1] == 16:
        #     break
    # times = []
    # for month in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
    #     for hour in list(range(24)):
    #         times.append((month, hour))
    #         total_stored = sum(project.electricity_stored(m, h, True) for m, h in times[:-1])
    #         total_consumed = sum(project.storage_consumed(m, h, True) for m, h in times[:-1])
    #         print((total_stored, total_consumed))
    x=5
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