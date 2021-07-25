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
        g = p.grid
        med = p.monthly_electricity_demand
        mhd = p.monthly_heat_demand
        for i in MONTHS:
            self.constraints.extend([
                m.addConstr(p.elec_capacity_by_month(i) + g.elec_usage_by_month(i) >= med[i]),
                m.addConstr(p.heat_capacity_by_month(i) + g.heat_usage_by_month(i) >= mhd[i])
            ])


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
        M = 2 * 32
        for product in proj.products:
            c = model.addConstr(sum(p.x for p in proj.products_by_type(product.et)) * M >= product.y)
            self.constraints.append(c)

        # force at only one opening cost to be paid per energy type
        # (e.g., one large and one small solar panel results in a single solar opening cost)
        for et in Product.ENERGY_TYPES:
            c = model.addConstr(sum(p.x for p in proj.products_by_type(et)) <= 1)
            self.constraints.append(c)


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
