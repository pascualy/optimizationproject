import pytest
import json
import pathlib

from offgridoptimizer import Project, Grid, load_and_validate, one_day_each_month, everyday_one_month, hours_each_month

MONTHS_IN_YEAR = 365
HOURS_IN_DAY = 24
HOURS_IN_YEAR = MONTHS_IN_YEAR * HOURS_IN_DAY

LEAP_DAY_HOUR = 1416
DAYLIGHT_SAVINGS_SPRING = 1634
SOMETHING_ELSE = 1586


def test_project(config_name, hours):


    config = load_and_validate(f'../configs/{config_name}.json')
    budget = config['budget']
    project = Project(product_list=config['products'],

                      initial_budget=budget['initial'],
                      monthly_budget=budget['monthly'],
                      location=config['location'],
                      allow_grid=True,
                      hours=hours)

    # model_save_name = 'saved_model.sol'
    # if pathlib.Path('saved_model.sol').exists():
    #     project.model.read(model_save_name)
    #     project.model.update()

    print('Optimizing')
    project.optimize()
    project.print_results()
    df = project.results_df()

    idx = 0
    filename = f'{config_name}_{config["location"]}_{idx}.pickle'
    while pathlib.Path(filename).exists():
        idx += 1
        filename = f'{config_name}_{config["location"]}_{idx}.pickle'

    df.to_pickle(filename)

    # project.model.write(model_save_name)

    print(f'GC: {project.grid.grid_installed.x} {config["allow_grid"]}')
    z = []
    times = []
    # for h in hours:
    #     z += [((h),
    #            round(project.energy_stored(h, True), 4),
    #            round(project.grid_capacity(h,True), 4),
    #            round(project.energy_sold(h, True), 4),
    #            ' ',
    #            round(project.storage_consumed(h, True), 4),
    #            round(project.electricity_capacity(h, True), 4),
    #            ' ',
    #            round(project.electricity_demand(h), 4),
    #            ' ',
    #            round(sum(project.energy_stored(x, True) for x  in times), 4),
    #            round(sum(project.storage_consumed(x,True) for x  in times), 4),
    #            round(sum(project.energy_sold(x, True) for x in times), 4),
    #            ' ',
    #            round(sum(project.energy_stored(x, True) for x in times) - sum(project.storage_consumed(x, True) for x in times) - sum(project.energy_sold(x, True) for x in times), 4))]
    #     times.append(h)
    # # ((1, 7), 0.0, 0.0, 3525.154838709677, 0.0, 10, 0.0, 0.0)
    # for a in z:
    #     print(a)
        # if a[0][1] == 16:
        #     break
    # times = []
    # for month in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
    #     for hour in list(range(24)):
    #         times.append((month, hour))
    #         total_stored = sum(project.electricity_stored(m, h, True) for m, h in times[:-1])
    #         total_consumed = sum(project.storage_consumed(m, h, True) for m, h in times[:-1])
    #         print((total_stored, total_consumed))


hours = list(range(0, HOURS_IN_YEAR, 2))
print(hours)
try:
    hours.remove(LEAP_DAY_HOUR)
    hours.remove(DAYLIGHT_SAVINGS_SPRING)
    hours.remove(SOMETHING_ELSE)
except ValueError:
    pass

# test_project('logan_low_budget', hours)
test_project('logan_medium_budget', hours)
# test_project('logan_lower_budget', hours)
# test_project('logan_sedona_az', hours)
# test_project('logan_yakima_wa', hours)

#
# spring = [3, 4, 5]
# summer = [6, 7, 8]
# fall = [9, 10, 11]
# winter = [12, 1, 2]
# for idx, season in enumerate([spring, summer, fall, winter]):
#     print(f'Season {idx}')
#     test_project('logan_medium_budget', hours_each_month(season))
