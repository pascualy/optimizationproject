from offgridoptimizer import Product
MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]



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
        for hour in p.hours:
            total_electricity_capacity = p.electricity_capacity(hour=hour) + \
                                         p.storage_consumed(hour=hour) + \
                                         p.grid_capacity(hour=hour)
            self.constraints.append(m.addConstr(total_electricity_capacity >=
                                                p.electricity_demand(hour=hour)))


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

        c = model.addConstr(proj.grid.grid_installed * M >= sum(proj.grid_capacity(hour=hour) for hour in self.project.hours))
        self.constraints.append(c)

        c = model.addConstr(proj.storage_installed * M >=
                            sum(product.ca * product.y for product in proj.products if
                                product.et == Product.STORAGE))
        self.constraints.append(c)

        c = model.addConstr(proj.storage_installed * M >=
                            sum(proj.storage_consumed(hour=hour) for hour in self.project.hours))
        self.constraints.append(c)

        # force at only one opening cost to be paid per energy type
        # (e.g., one large and one small solar panel results in a single solar opening cost)
        for et in Product.ENERGY_TYPES:
            c = model.addConstr(sum(p.x for p in proj.products_by_type(et)) <= 1)
            self.constraints.append(c)

        total_storage_capacity = sum(product.ca * product.y for product in proj.products if
                                     product.et == Product.STORAGE)
        times = []
        for hour in self.project.hours:
            times.append(hour)
            total_stored = sum(proj.energy_stored(hour=h) for h in times)
            total_consumed = sum(proj.storage_consumed(hour=h) for h in times)
            total_sold = sum(proj.storage_sold(hour=h) for h in times)

            existing_storage = total_stored - total_consumed - total_sold

            M = 2**32
            model.addConstr(-(1 - proj.storage_installed) * M <= existing_storage)
            model.addConstr(existing_storage <= total_storage_capacity)
            # TODO: This causes the optimization to start with "batteries" full
            if hour == 0:
                inital_storage_level = total_storage_capacity * 0
                model.addConstr(proj.energy_stored(hour=0) == inital_storage_level)
                model.addConstr(self.project.energy_stored(hour) <=
                                inital_storage_level +
                                self.project.electricity_capacity(hour) +
                                self.project.storage_consumed(hour) +
                                self.project.grid_capacity(hour) -
                                self.project.electricity_demand(hour) -
                                self.project.storage_sold(hour))
            else:
                # # TODO product.x needs to be 1 if ANY storage has been selected (done). this may be a problem with cost calculation too...
                model.addConstr(self.project.energy_stored(hour) <=
                                self.project.electricity_capacity(hour) +
                                self.project.storage_consumed(hour) +
                                self.project.grid_capacity(hour) -
                                self.project.electricity_demand(hour) -
                                self.project.storage_sold(hour))

            model.addConstr(
                self.project.storage_consumed(hour) <=
                self.project.grid_capacity(hour) +
                existing_storage +
                self.project.electricity_capacity(hour) -
                self.project.storage_sold(hour) -
                self.project.electricity_demand(hour)
            )


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
