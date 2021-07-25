import gurobipy as gp
from offgridoptimizer import Product, Grid, Project, OffGridOptimizer

import argparse


def main(config_path):
    import json
    with open(config_path) as fp:
        config = json.load(fp)

    demand = config["demand"]
    budget = config["budget"]
    products = config["products"]
    grid = config["grid"]

    # eco = OffGridOptimizer(model_name="model", demand=demand, budget=budget, products=products, grid=grid)
    # eco.optimize()
    # eco.print_results()


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Off-Grid Optimizer')
    parser.add_argument('config_path', type=str)
    args = parser.parse_args()

    main(args.config_path)
