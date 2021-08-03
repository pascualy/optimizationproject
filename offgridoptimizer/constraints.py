from offgridoptimizer import Product
MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
HOURS = list(range(24))


class Constraint:
    def __init__(self, project):
        self.project = project
        self.constraints = []

    def update_constraints(self):
        raise NotImplementedError()

    def clear_constraints(self):
        m = self.project.model
        for c in self.constraints:
            m.remove(c)


class DemandConstraint(Constraint):
    def __init__(self, project):
        super().__init__(project)
        self.update_constraints()

    def update_constraints(self):
        self.clear_constraints()
        p = self.project
        m = p.model
        for month in MONTHS:
            for hour in HOURS:
                total_electricity_capacity = p.electricity_capacity(month=month, hour=hour) + \
                                             p.storage_consumed(month=month, hour=hour) + \
                                             p.grid_capacity(month=month, hour=hour)
                self.constraints.append(m.addConstr(total_electricity_capacity >=
                                                    p.electricity_demand(month=month, hour=hour)))

                # self.constraints.append(m.addConstr(p.grid_capacity(month=month, hour=hour) <=
                #                                     p.electricity_demand(month=month, hour=hour)))
                # self.constraints.append(m.addConstr(p.heat_capacity(month=month, hour=hour) +
                #                                     g.heat_usage_by_month(month=month, hour=hour) >=
                #                                     p.heat_demand(month=month, hour=hour)))


class ProductConstraint(Constraint):
    def __init__(self, project):
        super().__init__(project)
        self.update_constraints()

    def update_constraints(self):
        self.clear_constraints()
        proj = self.project
        model = proj.model
        # if any units of an energy type are installed, require at least 1 opening cost to be paid
        # (e.g., one large and one small solar panel results in a single solar opening cost)
        M = 2 ** 32
        for product in proj.products:
            c = model.addConstr(sum(p.x for p in proj.products_by_type(product.et)) * M >= product.y)
            self.constraints.append(c)

        # force at only one opening cost to be paid per energy type
        # (e.g., one large and one small solar panel results in a single solar opening cost)
        for et in Product.ENERGY_TYPES:
            c = model.addConstr(sum(p.x for p in proj.products_by_type(et)) <= 1)
            self.constraints.append(c)

        total_storage_capacity = sum(product.ca * product.y for product in proj.products if
                                     product.et == Product.STORAGE)
        times = []
        for month in MONTHS:
            for hour in HOURS:
                times.append((month, hour))
                total_stored = sum(proj.electricity_stored(month=m, hour=h) for m, h in times)
                total_consumed = sum(proj.storage_consumed(month=m, hour=h) for m, h in times)

                existing_storage = total_stored - total_consumed
                model.addConstr(0 <= existing_storage)
                model.addConstr(existing_storage <= total_storage_capacity)
                # TODO: This causes the optimization to start with "batteries" full
                # if month == 1 and hour == 0:
                #
                #     model.addConstr(proj.electricity_stored(month=1, hour=0) == total_storage_capacity)
                #     model.addConstr(self.project.electricity_stored(month, hour) <=
                #                     total_storage_capacity +
                #                     self.project.electricity_capacity(month, hour) +
                #                     self.project.storage_consumed(month, hour) +
                #                     self.project.grid_capacity(month, hour) -
                #                     self.project.electricity_demand(month, hour))
                # else:
                # # TODO product.x needs to be 1 if ANY storage has been selected (done). this may be a problem with cost calculation too...
                model.addConstr(self.project.electricity_stored(month, hour) <=
                                self.project.electricity_capacity(month, hour) +
                                self.project.storage_consumed(month, hour) +
                                self.project.grid_capacity(month, hour) -
                                self.project.electricity_demand(month, hour))


class BudgetConstraint(Constraint):
    def __init__(self, project):
        super().__init__(project)
        self.update_constraints()

    def update_constraints(self):
        self.clear_constraints()
        p = self.project
        m = p.model
        self.constraints = [m.addConstr(p.capital_costs() <= p.initial_budget),
                            m.addConstr(p.operational_costs() <= p.monthly_budget)]
