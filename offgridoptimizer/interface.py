from offgridoptimizer import Project, Product, validate_config, one_day_each_month, everyday_one_month, hours_each_month
from offgridoptimizer.config_schema import get_location_options, get_config_options
from offgridoptimizer import MONTHS_IN_YEAR, HOURS_IN_DAY, HOURS_IN_YEAR, LEAP_DAY_HOUR, DAYLIGHT_SAVINGS_SPRING, SOMETHING_ELSE

import pathlib
from jsonschema import ValidationError
import copy
import ipysheet
from ipysheet import sheet, cell, hold_cells, row, column, easy
import ipywidgets as widgets
from datetime import date
import pickle

from ipywidgets import Layout, Button, Box, FloatText, Textarea, Dropdown, Label, IntSlider
from ipywidgets import HTML, Layout, Dropdown, Output, Textarea, VBox, Label

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

colors = px.colors.qualitative.Plotly

month_dict = {'January': 1, 'February': 2, 'March': 3, 'April': 4,
                     'May': 5, 'June': 6, 'July': 7, 'August': 8, 'September': 9,
                     'October': 10, 'November': 11, 'December': 12}

def try_cast_float(x):
    try:
        return float(x)
    except ValueError:
        return x

class ProductRow:
    def __init__(self):
        self.row = [widgets.Text(layout={'width': 'max-content'}),
                    widgets.Dropdown(options=['electricity', 'heat'], layout={'width': 'max-content'}),
                    widgets.Dropdown(options=['solar', 'wind', 'storage'], layout={'width': 'max-content'}),
                    widgets.FloatText(layout={'width': 'max-content'}),
                    widgets.FloatText(layout={'width': 'max-content'}),
                    widgets.FloatText(layout={'width': 'max-content'}),
                    widgets.FloatText(layout={'width': 'max-content'}),
                    widgets.FloatText(layout={'width': 'max-content'}),
                    ]

    @classmethod
    def filled(cls, name, utility_type, energy_type, opening_cost, incremental_cost, maintenance_cost, amortization, capacity):
        p = ProductRow()
        p.row[0].value = name
        p.row[1].value = utility_type
        p.row[2].value = energy_type
        p.row[3].value = opening_cost
        p.row[4].value = incremental_cost
        p.row[5].value = maintenance_cost
        p.row[6].value = amortization
        p.row[7].value = capacity

        return p


class ProductTable:
    def __init__(self):
        # header("Products"),
        self.add_product_row_button = widgets.Button(description='Add Row')
        self.add_product_row_button.on_click(self.add_row)

        self.headers = ('name', 'utlity_type', 'energy_type', 'opening_cost', 'incremental_cost',
                        'maintenance_cost', 'amortization', 'capacity')
        self.cols = {h: [] for h in self.headers}
        self.table = widgets.VBox([self.add_product_row_button],
                                  layout=Layout(width='100%', display='inline-flex'))
        self.rows = []

    def add_row(self, btn, product=None):
        if product is None:
            product = ProductRow()

        self.rows.append(product)
        if len(self.rows) == 1:
            # widgets.Text(value=h, layout=Layout(width='80%', display='inline-flex', flex_flow='row'))
            self.table.children += (widgets.HBox([widgets.VBox([HTML(f'<h3>{h}</h3>', layout=Layout(height='auto')),
                                                                self.rows[-1].row[i]]) for i, h in enumerate(self.headers)],
                                                 layout=Layout(width='100%', display='inline-flex', flex_flow='row wrap')),)
        else:
            for vbox, cell in zip(self.table.children[1].children, [self.rows[-1].row[i] for i in range(len(self.headers))]):
                vbox.children += (cell,)
            # self.table.children += (widgets.HBox([self.rows[-1].row[i] for i in range(len(self.headers))],
            #                         layout=Layout(width='75%', display='inline-flex', flex_flow='row')),)

    def update(self, products):
        self.table.children = (self.table.children[0],)
        self.rows = []
        for product in products:
            row = product.parameters()
            self.add_row(None, product=ProductRow.filled(*row))


class SelectedProductRow:
    def __init__(self):
        self.row = [widgets.Text(layout={'width': 'max-content'}),
                    widgets.FloatText(layout={'width': 'max-content'})]

    @classmethod
    def filled(cls, name, quantity):
        p = SelectedProductRow()
        p.row[0].value = name
        p.row[1].value = quantity

        return p


class SelectedProductTable:
    def __init__(self):
        # header("Products"),

        self.headers = ('name', 'quantity')
        self.cols = {h: [] for h in self.headers}
        self.table = widgets.VBox([],
                                  layout=Layout(width='100%', display='inline-flex'))
        self.rows = []

    def add_row(self, btn, product=None):
        if product is None:
            product = SelectedProductRow()

        self.rows.append(product)
        self.table.children += (widgets.HBox([self.rows[-1].row[i] for i in range(len(self.headers))],
                                layout=Layout(width='100%', display='inline-flex', flex_flow='row')),)

    def update(self, products):
        self.table.children = tuple()
        for product in products:
            self.add_row(None, product=SelectedProductRow.filled(*product))


def default_layout(border='solid 2px'):
    return Layout(
        flex='flex-shrink',
        display='flex',
        flex_flow='column',
        border=border,
        align_items='stretch',
        width='100%')


def header(text):
    return HTML(f"<h2>{text}</h2>", layout=Layout(height='auto'))


def text(text):
    return HTML(f"{text}", layout=Layout(height='auto'))


def interface_box(items):
    return Box(items, layout=default_layout())


class OffGridOptimizer:
    def __init__(self, default_config_path='./configs/logan.json'):
        self.default_config_path = default_config_path

        self.selected_product_table = SelectedProductTable()
        self.product_table = ProductTable()

        # Location Drop-Down
        self.location_dropdown = widgets.Dropdown(
            options=get_location_options(),
            value=get_location_options()[0],
            description='Location:',
            disabled=False,
        )

        self.configuration_dropdown = widgets.Dropdown(
            options=get_config_options(),
            value=get_config_options()[0],
            description='Configuration:',
            disabled=False,
        )

        self.allow_grid_check = widgets.Checkbox(value=True,
                                                 description='Allow Grid',
                                                 disabled=False,
                                                 indent=False)

        self.month_checkboxes = [widgets.Checkbox(value=False,
                                       description=k,
                                       disabled=False,
                                       indent=False) for k, v in month_dict.items()]

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
        self.monthly_budget = widgets.FloatText(layout={'width': 'max-content'}, description='monthly_budget: ')
        self.initial_budget = widgets.FloatText(layout={'width': 'max-content'}, description='initial_budget: ')

        self.input_items = [
            header("Parameters"),
            self.configuration_dropdown,
            self.btn_default_config,
            self.location_dropdown,
            self.allow_grid_check,
            widgets.HBox(self.month_checkboxes, layout=Layout(flex='flex-shrink',
                                                              display='flex',
                                                              border=None,
                                                              align_items='stretch',
                                                              width='25%')),
            widgets.HBox([widgets.VBox([header("Budget"),
                                        self.monthly_budget,
                                        self.initial_budget], layout=default_layout(border=None))]),
            header("Products"),
            self.product_table.table,
            widgets.HBox([self.btn_optimize, self.error_text])
        ]
        self.input = interface_box([header("Off-Grid Optimizer"), interface_box(self.input_items)])

        # Output Interface
        self.output_items = [
            HTML("<h2>Results</h2>", layout=Layout(height='auto')),
            header("Selected Products"),
            self.selected_product_table.table,
            header("Totals"),
            widgets.HBox([])
        ]

        self.output = interface_box(self.output_items)

        # Combined Interface
        self.interface = interface_box([self.input, self.output])

        self.project = None

    def load_sheets(self, btn, config=None, hours=None):
        if config:
            self.project = Project.project_from_config(config, hours=hours)
        else:
            file_name = self.configuration_dropdown.value.replace(' ', '_').lower()
            config_path = f'./configs/{file_name}.json'
            self.project = Project.project_from_config_path(config_path, hours=hours_each_month([1]))

        project = self.project
        products = project.products

        self.product_table.update(products=products)
        self.initial_budget.value = self.project.initial_budget
        self.monthly_budget.value = self.project.monthly_budget

    def sheets_to_config(self):
        headers = Product.headers()
        transforms = {
            "opening_cost": try_cast_float,
            "incremental_cost": try_cast_float,
            "maintenance_cost": try_cast_float,
            "amortization": try_cast_float,
            "capacity": try_cast_float
        }
        a = {
            "allow_grid": True,
            "location": self.location_dropdown.value,
            "budget": {
                "initial": float(self.initial_budget.value),
                "monthly": float(self.monthly_budget.value)
            },
            "products": [{k: (v.value if k not in transforms else transforms[k](v.value))
                          for k, v in zip(headers, product.row)} for product in self.product_table.rows]
        }

        return a

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

        months = [idx + 1 for idx, box in enumerate(self.month_checkboxes) if box.value == True]
        if len(months) > 6:
            print('Selected more than 6 months: only analyzing every other hour')
            hours = hours_each_month(months)[::2]
        else:
            hours = hours_each_month(months)

        self.project = Project.project_from_config(config, hours=hours)
        self.project.optimize()
        labels, costs = zip(*self.project.costs())
        labels = [text(value) for value in labels]
        costs = widgets.VBox([widgets.FloatText(layout={'width': 'max-content'}, value=value) for value in costs])
        self.output.children = self.output.children[:-1] + tuple([widgets.HBox([widgets.VBox(labels), costs])])
        self.selected_product_table.update(self.project.selected_products())
        self.plot_results(self.project.results_df())

    def set_sheet(self, current_sheet):
        easy._last_sheet = current_sheet

    def add_row(self, _):
        self.products_sheet.add_row()

    @classmethod
    def plot_results(cls, df, hours=None):
        import pandas as pd
        import plotly.express as px
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        colors = px.colors.qualitative.Plotly

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=df['date'], y=df['demand'], mode='lines', line=dict(color=colors[0]), name='Demand (KwH)'),
            secondary_y=False)
        fig.add_trace(go.Scatter(x=df['date'], y=df['pv_efficiency'] * 100, mode='lines', line=dict(color=colors[1]),
                                 name='Solar Efficiency (%)'),
                      secondary_y=True)
        fig.add_trace(go.Scatter(x=df['date'], y=df['wind_efficiency'] * 100, mode='lines', line=dict(color=colors[2]),
                                 name='Wind Efficiency (%)'),
                      secondary_y=True)
        fig.add_trace(go.Scatter(x=df['date'], y=df['capacity'], mode='lines', line=dict(color=colors[3]),
                                 name='Capacity (KwH)'),
                      secondary_y=False)
        fig.add_trace(go.Scatter(x=df['date'], y=df['storage_level'], mode='lines', line=dict(color=colors[4]),
                                 name='Storage Level (KwH)'),
                      secondary_y=False)
        fig.add_trace(go.Scatter(x=df['date'], y=df['energy_sold'], mode='lines', line=dict(color=colors[5]),
                                 name='Energy Sold (KwH)'),
                      secondary_y=False)
        fig.add_trace(go.Scatter(x=df['date'], y=df['grid_usage'], mode='lines', line=dict(color=colors[6]),
                                 name='Grid Usage (KwH)'),
                      secondary_y=False)

        if hours:
            hours = list(range(1, HOURS_IN_YEAR, 4))
            try:
                hours.remove(LEAP_DAY_HOUR)
                hours.remove(DAYLIGHT_SAVINGS_SPRING)
                hours.remove(SOMETHING_ELSE)
            except ValueError:
                pass

            hours = set(list(range(0, HOURS_IN_YEAR))).difference(hours)

            dt_breaks = pd.DataFrame(hours, columns=['chour'])
            df1 = pd.Timestamp('2019-01-01') + pd.to_timedelta(dt_breaks['chour'], unit='H')
            fig.update_xaxes(
                rangebreaks=[dict(values=df1)]  # hide dates with no values
            )

        fig.update_layout(title_text="Energy System Dynamics")
        fig.update_xaxes(title_text="Time")
        fig.update_yaxes(title_text="<b>Energy</b> (KwH)", secondary_y=False)
        fig.update_yaxes(title_text="<b>Efficiency</b> (%)", secondary_y=True)

        fig.show()

    @classmethod
    def plot_efficiency(cls, df, location='Asheville,NC'):
        import plotly.express as px
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        colors = px.colors.qualitative.Plotly
        fig = make_subplots()
        fig.add_trace(go.Scatter(x=df['date'], y=df['pv_efficiency'] * 100, mode='lines', line=dict(color=colors[1]),
                                 name='Solar Efficiency (%)'))
        fig.add_trace(go.Scatter(x=df['date'], y=df['wind_efficiency'] * 100, mode='lines', line=dict(color=colors[2]),
                                 name='Wind Efficiency (%)'))
        fig.update_layout(title_text=f"Hourly Efficiency of Wind Products in {location.replace(',', ', ')}")
        fig.update_xaxes(title_text="<b>Time</b>")
        fig.update_yaxes(title_text="<b>Efficiency</b> (%)", secondary_y=False)
        fig.show()

    @classmethod
    def plot_demand(cls, df):
        import plotly.express as px
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        colors = px.colors.qualitative.Plotly
        fig = make_subplots()
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['demand'], mode='lines', line=dict(color=colors[0]), name='Demand (KwH)'))
        fig.update_layout(title_text="Hourly Demand of Average Home in Asheville, NC")
        fig.update_xaxes(title_text="Time")
        fig.update_yaxes(title_text="<b>Energy</b> (KwH)", secondary_y=False)
        fig.show()

    def plot_solar_efficiency_month(self, months=None, location='Asheville,NC'):


        month_dict = {'January': 1, 'February': 2, 'March': 3, 'April': 4,
                      'May': 5, 'June': 6, 'July': 7, 'August': 8, 'September': 9,
                      'October': 10, 'November': 11, 'December': 12}
        self.location_dropdown.value = location
        self.load_sheets(None, config=self.sheets_to_config(), hours=[])
        df = self.project.parameters_df()

        fig = make_subplots()

        for idx, month in enumerate(months):
            df['month'] = df['date'].dt.month
            month_num = month_dict[month]
            df1 = df[df['month'] == month_num]

            fig.add_trace(go.Scatter(x=list(range(10*24)), y=df1['pv_efficiency'] * 100, mode='lines', line=dict(color=colors[idx]),
                                     name=month))

        fig.update_layout(title_text=f"Hourly Efficiency of Solar Products in {location.replace(',', ', ')}")
        fig.update_xaxes(title_text="<b>Hour of Month</b>")
        fig.update_yaxes(title_text="<b>Efficiency</b> (%)", secondary_y=False)
        fig.show()

    def plot_wind_efficiency_month(self, months=None, location='Asheville,NC'):
        self.location_dropdown.value = location
        self.load_sheets(None, config=self.sheets_to_config(), hours=[])
        df = self.project.parameters_df()

        fig = make_subplots()

        for idx, month in enumerate(months):
            df['month'] = df['date'].dt.month
            month_num = month_dict[month]
            df1 = df[df['month'] == month_num]
            fig.add_trace(go.Scatter(x=list(range(10*24)), y=df1['wind_efficiency'] * 100, mode='lines', line=dict(color=colors[idx]),
                                     name=month))
        fig.update_layout(title_text=f"Hourly Efficiency of Wind Products in {location.replace(',', ', ')}")
        fig.update_xaxes(title_text="<b>Hour of Month</b>")
        fig.update_yaxes(title_text="<b>Efficiency</b> (%)", secondary_y=False)
        fig.show()

    def plot_demand_month(self, months=None, location='Asheville,NC'):
        import plotly.express as px
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        colors = px.colors.qualitative.Plotly

        self.location_dropdown.value = location
        self.load_sheets(None, config=self.sheets_to_config(), hours=[])
        df = self.project.parameters_df()

        fig = make_subplots()

        for idx, month in enumerate(months):
            df['month'] = df['date'].dt.month
            month_num = month_dict[month]
            df1 = df[df['month'] == month_num]
            fig.add_trace(
                go.Scatter(x=list(range(10*24)), y=df1['demand'], mode='lines', line=dict(color=colors[idx]), name=month))

        fig.update_layout(title_text=f"Hourly Demand (KwH) of Average Home in {location.replace(',', ', ')}")
        fig.update_xaxes(title_text="Hour of Month")
        fig.update_yaxes(title_text="<b>Energy</b> (KwH)", secondary_y=False)
        fig.show()

    def plot(self, ys, month, location, budget, season=None, sellback=None):
        llocation = location.lower().replace(' ', '').replace(',', '_')
        lseason = season.lower() if season else None
        lbudget = budget.lower()
        filename = f'{lbudget}_budget_{llocation}{f"_{lseason}" if season else ""}{"_sellback" if sellback else ""}'
        filepath = pathlib.Path(__file__).parent / f'../experiments/{filename}.pickle'
        df = pd.read_pickle(filepath)

        df['month'] = df['date'].dt.month
        month_num = month_dict[month]
        df = df[df['month'] == month_num]

        if 'pv_efficiency' in ys or 'wind_efficiency' in ys:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.update_yaxes(title_text="<b>Efficiency</b> (%)", secondary_y=True)
        else:
            fig = make_subplots()

        if 'demand' in ys:
            fig.add_trace(go.Scatter(x=df['date'], y=df['demand'], mode='lines', line=dict(color=colors[0]), name='Demand (KwH)'),
                secondary_y=False)

        if 'pv_efficiency' in ys:
            fig.add_trace(go.Scatter(x=df['date'], y=df['pv_efficiency'] * 100, mode='lines', line=dict(color=colors[1]),
                                 name='Solar Efficiency (%)'), secondary_y=True)

        if 'wind_efficiency' in ys:
            fig.add_trace(go.Scatter(x=df['date'], y=df['wind_efficiency'] * 100, mode='lines', line=dict(color=colors[2]),
                                 name='Wind Efficiency (%)'),
                      secondary_y=True)

        if 'capacity' in ys:
            fig.add_trace(go.Scatter(x=df['date'], y=df['capacity'], mode='lines', line=dict(color=colors[3]),
                                 name='Capacity (KwH)'),
                      secondary_y=False)

        if 'storage_level' in ys:
            fig.add_trace(go.Scatter(x=df['date'], y=df['storage_level'], mode='lines', line=dict(color=colors[4]),
                                 name='Storage Level (KwH)'),
                      secondary_y=False)

        if 'energy_sold' in ys:
            fig.add_trace(go.Scatter(x=df['date'], y=df['energy_sold'], mode='lines', line=dict(color=colors[5]),
                                 name='Energy Sold (KwH)'),
                      secondary_y=False)

        if 'grid_usage' in ys:
            fig.add_trace(go.Scatter(x=df['date'], y=df['grid_usage'], mode='lines', line=dict(color=colors[6]),
                                     name='Grid Usage (KwH)'),
                                     secondary_y=False)

        fig.update_layout(title_text=f"Energy System Dynamics: {budget} Budget in {location} during {month} {'with Sellback' if sellback else 'with Net-Metering'}")
        fig.update_xaxes(title_text="Time")
        fig.update_yaxes(title_text="<b>Energy</b> (KwH)", secondary_y=False)


        fig.show()