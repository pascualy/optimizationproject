import pytest
import json

from offgridoptimizer import Project, Grid, load_and_validate, one_day_each_month

def test_project():
    config = load_and_validate('../configs/logan.json')

    hours = one_day_each_month()
    assert 1416 not in hours
    budget = config['budget']
    project = Project(product_list=config['products'],

                      initial_budget=budget['initial'],
                      monthly_budget=budget['monthly'],
                      location=config['location'],
                      allow_grid=True,
                      hours=hours)
    print('Optimizing')
    project.optimize()
    project.print_results()
    project.results_df()

    print(f'GC: {project.grid.grid_installed.x} {config["allow_grid"]}')
    z = []
    times = []
    for h in hours:
        z += [((h),
               round(project.energy_stored(h, True), 4),
               round(project.grid_capacity(h,True), 4),
               round(project.storage_sold(h,True), 4),
               ' ',
               round(project.storage_consumed(h, True), 4),
               round(project.electricity_capacity(h, True), 4),
               ' ',
               round(project.electricity_demand(h), 4),
               ' ',
               round(sum(project.energy_stored(x, True) for x  in times), 4),
               round(sum(project.storage_consumed(x,True) for x  in times), 4),
               round(sum(project.storage_sold(x, True) for x in times), 4),
               ' ',
               round(sum(project.energy_stored(x, True) for x in times) - sum(project.storage_consumed(x, True) for x in times) - sum(project.storage_sold(x, True) for x in times),4))]
        times.append(h)
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