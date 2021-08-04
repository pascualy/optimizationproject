from offgridoptimizer import Project, Product, validate_config
from offgridoptimizer.config_schema import get_location_options
from jsonschema import ValidationError
import copy
import ipysheet
from ipysheet import sheet, cell, hold_cells, row, column, easy
import ipywidgets as widgets
from datetime import date

from ipywidgets import Layout, Button, Box, FloatText, Textarea, Dropdown, Label, IntSlider
from ipywidgets import HTML, Layout, Dropdown, Output, Textarea, VBox, Label


def try_cast_float(x):
    try:
        return float(x)
    except ValueError:
        return x


class Sheet:
    def __init__(self, rows, columns):
        self.sheet = sheet(rows=rows, columns=columns)

    def set_sheet(self):
        easy._last_sheet = self.sheet


class BudgetSheet(Sheet):
    def __init__(self):
        super().__init__(rows=2, columns=3)
        with hold_cells():
            self.header = row(0, ['', 'initial_budget', 'monthly_budget'], font_weight='bold')
            self.header_dollars = cell(1, 0, 'Dollars ($)', font_weight='bold')
            self.data = row(1, ['', ''], column_start=1)

    def update(self, initial, monthly):
        self.set_sheet()
        with hold_cells():
            self.data.value = [initial, monthly]


class ProductSheet(Sheet):
    def __init__(self):
        super().__init__(rows=10, columns=8)
        with hold_cells():
            self.header = row(0, [header for col, header in enumerate(Product.headers())], font_weight='bold')

        self.rows = []

        self.add_product_row_button = widgets.Button(description='Add Row')
        out = widgets.Output()

        self.add_product_row_button.on_click(self.add_row)

    def update(self, products):
        self.set_sheet()
        with hold_cells():
            self.sheet.rows = 1
            self.rows = []
            self.sheet.rows = len(products) + 1
            for row_num, product in enumerate(products):
                info = [data if not isinstance(data, list) else data for col, data in enumerate(product.parameters())]
                self.rows.append(row(row_num + 1, info))

    def add_row(self, btn):
        self.sheet.rows += 1


# class DemandSheet(Sheet):
#     def __init__(self):
#         super().__init__(rows=3, columns=13)
#         with hold_cells():
#             self.demand_types = column(0, ['', 'monthly_electricity_demand', 'monthly_heat_demand'], font_weight='bold')
#             month_strs = [date(1900, month, month).strftime('%B') for month in range(1, 13)]
#             self.demand_header = row(0, month_strs, column_start=1, font_weight='bold')
#             self.demand_elec = row(1, ['' for _ in range(12)], column_start=1)
#             self.demand_heat = row(2, ['' for _ in range(12)], column_start=1)
#
#     def update(self, elec_demand, heat_demand):
#         self.set_sheet()
#         with hold_cells():
#             self.demand_elec.value = elec_demand
#             self.demand_heat.value = heat_demand


class CostSheet(Sheet):
    def __init__(self):
        super().__init__(rows=8, columns=2)
        with hold_cells():
            self.cost_header = column(0, ["Total Opening Cost", "Total Maintenance Cost",
                                          "Total Incremental Cost", "Total Grid Cost", "Total Revenue", "Total Cost"],
                                      row_start=1, font_weight='bold')
            self.cost_header_dollars = cell(0, 1, "Dollar ($)", font_weight='bold')
            self.cost_values = column(1, ["", "", "", "", "", ""], row_start=1)

    def update(self, costs):
        self.cost_values.value = [v for _, v in costs]


class SelectedProductsSheet(Sheet):
    def __init__(self):
        super().__init__(rows=1, columns=2)
        with hold_cells():
            self.sproducts_sheet_headers = row(0, ['Product Name', 'Quantity'], font_weight='bold')

        self.sproducts = []

    def update(self, selected_products):
        self.sheet.rows = 1
        self.sheet.rows = 1 + len(selected_products)
        self.set_sheet()
        self.sheet.sproducts = []
        for idx, sproduct in enumerate(selected_products):
            self.sproducts.append(row(idx + 1, sproduct))


def header(text):
    return HTML(f"<h2>{text}</h2>", layout=Layout(height='auto'))


def default_layout(border='solid 2px'):
    return Layout(
        display='flex',
        flex_flow='column',
        border=border,
        align_items='stretch',
        width='100%')


def interface_box(items):
    return Box(items, layout=default_layout())


# class GridSheet(Sheet):
#     def __init__(self):
#         super().__init__(rows=2, columns=3)
#         with hold_cells():
#             self.header = row(0, ['', 'grid_cost_kwh'], font_weight='bold')
#             self.header_dollars = cell(1, 0, 'Dollars ($)', font_weight='bold')
#             self.data = row(1, [''], column_start=1)
#
#     def update(self, grid_cost_kwh):
#         self.set_sheet()
#         with hold_cells():
#             self.data.value = [grid_cost_kwh]


class OffGridOptimizer:
    def __init__(self, default_config_path='./configs/logan/config.json'):
        self.default_config_path = default_config_path

        # Sheets for Input Interface
        self.products_sheet = ProductSheet()
        self.budget_sheet = BudgetSheet()
        # self.demand_sheet = DemandSheet()
        # self.grid_sheet = GridSheet()

        # Sheets for Output Interface
        self.cost_sheet = CostSheet()
        self.selected_products_sheet = SelectedProductsSheet()

        # Location Drop-Down

        self.location_dropdown = widgets.Dropdown(
            options=get_location_options(),
            value=get_location_options()[0],
            description='Location:',
            disabled=False,
        )

        # Buttons
        self.btn_default_config = widgets.Button(description='Load Default',
                                                 disabled=False,
                                                 button_style='',
                                                 tooltip='Click me',
                                                 icon='check')
        self.btn_default_config.on_click(self.load_sheets)
        # self.btn_upload_config = widgets.FileUpload(accept='csv', multiple=False)

        self.btn_optimize = widgets.Button(description='Optimize!',
                                           disabled=False,
                                           button_style='',
                                           tooltip='Click me',
                                           icon='check',
                                           align_items='stretch')
        self.btn_optimize.on_click(self.optimize)

        self.error_text = HTML("", layout=Layout(height='auto'))
        # Input Interface
        self.input_items = [
            header("Off-Grid Optimizer"),

            self.location_dropdown,
            self.btn_default_config,
            widgets.HBox([widgets.VBox([header("Budget"), self.budget_sheet.sheet], layout=default_layout(border=None))]),
            header("Products"), widgets.VBox([self.products_sheet.sheet, self.products_sheet.add_product_row_button]),
            widgets.HBox([self.btn_optimize, self.error_text])
        ]
        self.input = interface_box(self.input_items)

        # Output Interface
        self.output_items = [
            HTML("<h2>Results</h2>", layout=Layout(height='auto')),
            self.cost_sheet.sheet,
            self.selected_products_sheet.sheet
        ]
        self.output = interface_box(self.output_items)

        # Combined Interface
        self.interface = interface_box([self.input, self.output])

        self.project = None

    def load_sheets(self, btn):
        self.project = Project.project_from_config_path(self.default_config_path)
        project = self.project
        products = project.products

        self.products_sheet.update(products=products)
        self.budget_sheet.update(initial=project.initial_budget, monthly=project.monthly_budget)
        # self.demand_sheet.update(elec_demand=[project.monthly_electricity_demand[month] for month in range(1, 13)],
        #                          heat_demand=[project.monthly_heat_demand[month] for month in range(1, 13)])
        # self.grid_sheet.update(grid_cost_kwh=self.project.grid.grid_cost_kwh)

    def sheets_to_config(self):
        headers = Product.headers()
        initial, monthly = self.budget_sheet.data.value
        transforms = {
            "opening_cost": try_cast_float,
            "incremental_cost": try_cast_float,
            "maintenance_cost": try_cast_float,
            "amortization": try_cast_float,
            "capacity": try_cast_float
        }
        return {
            "allow_grid": False,
            "location": self.location_dropdown.value,
            "budget": {
                "initial": float(initial),
                "monthly": float(monthly)
            },
            "products": [{k: (v if k not in transforms else transforms[k](v))
                          for k, v in zip(headers, product.value)} for product in self.products_sheet.rows]
        }

    def validate_sheets(self):
        config = self.sheets_to_config()
        try:
            validate_config(config)
        except ValidationError as e:
            self.error_text.value = f"<h4><font color='red'>{str(e.message)}<h4>"
            raise e

        return config

    def optimize(self, btn):
        self.error_text.value = ""
        try:
            config = self.validate_sheets()
        except ValidationError:
            return

        self.project = Project.project_from_config(config)
        self.project.optimize()

        self.cost_sheet.update(costs=self.project.costs())
        self.selected_products_sheet.update(selected_products=self.project.selected_products())

    def set_sheet(self, current_sheet):
        easy._last_sheet = current_sheet

    def add_row(self, _):
        self.products_sheet.add_row()
