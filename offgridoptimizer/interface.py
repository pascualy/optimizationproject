from offgridoptimizer import Project, Product

import ipysheet
from ipysheet import sheet, cell, hold_cells, row, column, easy
import ipywidgets as widgets
import datetime

from ipywidgets import Layout, Button, Box, FloatText, Textarea, Dropdown, Label, IntSlider
from ipywidgets import HTML, Layout, Dropdown, Output, Textarea, VBox, Label


# def product_config_to_sheet(products, sheets):


class OffGridOptimizer:
    def __init__(self, default_config_path='./configs/logan/config.json'):
        self.default_config_path = default_config_path

        # Product Sheet and Cells
        self.products_sheet = sheet(rows=10, columns=8)
        with hold_cells():
            self.product_header = row(0, [header for col, header in enumerate(Product.headers())])

        self.product_rows = []

        # Budget Sheet and Cells
        self.budget_sheet = sheet(rows=2, columns=3)
        with hold_cells():
            self.budget_header = row(0, ['', 'initial_budget', 'monthly_budget'])
            self.budget_data = row(1, ['Dollars ($)', '', ''])

        # Demand Sheet and Cells
        self.demand_sheet = sheet(rows=3, columns=13)
        with hold_cells():
            mydate = datetime.datetime.now()
            self.demand_types = column(0, ['', 'monthly_electricity_demand', 'monthly_heat_demand'])
            month_strs = [datetime.date(1900, month, month).strftime('%B') for month in range(1, 13)]
            self.demand_header = row(0, month_strs, column_start=1)
            self.demand_elec = row(1, ['' for month in range(1, 13)], column_start=1)
            self.demand_heat = row(2, ['' for month in range(1, 13)], column_start=1)

        self.grid_sheet = sheet(rows=3, columns=2)

        self.btn_default_config = widgets.Button(description='Load Default',
                                                 disabled=False,
                                                 button_style='',
                                                 tooltip='Click me',
                                                 icon='check')
        self.btn_default_config.on_click(self.load_sheets)
        self.btn_upload_config = widgets.FileUpload(
            accept='csv',
            multiple=False)

        self.btn_optimize = widgets.Button(description='Optimize!',
                                           disabled=False,
                                           button_style='',
                                           tooltip='Click me',
                                           icon='check')
        self.btn_optimize.on_click(self.optimize)

        self.layout = Layout(
            display='flex',
            flex_flow='row',
            justify_content='space-between'
        )

        self.items = [
            HTML("<h2>Off-Grid Optimizer</h2>", layout=Layout(height='auto')),
            self.btn_default_config,
            self.btn_upload_config,
            HTML("<h2>Demand</h2>", layout=Layout(height='auto')),
            self.demand_sheet,
            HTML("<h2>Budget</h2>", layout=Layout(height='auto')),
            self.budget_sheet,
            HTML("<h2>Products</h2>", layout=Layout(height='auto')),
            self.products_sheet,
            self.btn_optimize
        ]

        self.form = Box(self.items, layout=Layout(
            display='flex',
            flex_flow='column',
            border='solid 2px',
            align_items='stretch',
            width='100%'
        ))

        self.project = None

    def load_sheets(self, btn):
        # this loading process can definitely be improved....
        self.project = Project.project_from_config_path(self.default_config_path)
        project = self.project

        products = project.products
        self.set_sheet(self.products_sheet)
        with hold_cells():
            self.products_sheet.rows = 1
            self.products_sheet.rows = len(products) + 1
            for row_num, product in enumerate(products):
                info = [data if not isinstance(data, list) else data for col, data in enumerate(product.parameters())]
                self.product_rows.append(row(row_num + 1, info))

        self.set_sheet(self.budget_sheet)
        with hold_cells():
            self.budget_data.value[1] = project.initial_budget
            self.budget_data.value[2] = project.monthly_budget

        self.set_sheet(self.demand_sheet)
        with hold_cells():
            self.demand_elec.value = [project.monthly_electricity_demand[month] for month in range(1, 13)]
            self.demand_heat.value = [project.monthly_heat_demand[month] for month in range(1, 13)]

    def sheets_to_config(self):
        headers = Product.headers()
        _, initial, monthly = self.budget_data.value

        return {
            "demand": {
                "monthly_electricity_demand": self.demand_elec.value,
                "monthly_heat_demand": self.demand_heat.value
            },
            "budget": {
                "initial": initial,
                "monthly": monthly
            },
            "grid": {
                "grid_cost_kwh": 1,
                "grid_cost_env": 1
            },
            "products": [{k: v for k, v in zip(headers, product.value)} for product in self.product_rows]
        }

    def optimize(self, btn):
        config = self.sheets_to_config()
        self.project = Project.project_from_config(config)
        self.project.optimize()

    def set_sheet(self, current_sheet):
        easy._last_sheet = current_sheet

