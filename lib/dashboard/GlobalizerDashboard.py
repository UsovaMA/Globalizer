import dash
from dash import html
from dash import dcc
from dash import dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_daq as daq

import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import numpy as np

from scipy.interpolate import griddata
from sklearn.neural_network import MLPRegressor
from scipy import interpolate

import json
import base64

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "1rem 1rem",
    "font-size": "1.1em",
    "background-color": "#333333",
}

CONTENT_STYLE = {
    "margin-left": "8%",
    "margin-right": "8%",
    "font-size": "1.1em"
}

def create_dash_table_from_dataframe(dataframe):
    column_renames = {
        'objective_func': 'значение целевой функции',
        'trial': 'номер испытания',
        'index': 'индекс точки'
    }

    # Формируем список колонок вручную
    columns = []
    for col_id in dataframe.columns:
        # Если в словаре есть новое имя — берем его, иначе оставляем исходный заголовок
        display_name = column_renames.get(col_id, col_id) 
        
        columns.append({
            "name": display_name, 
            "id": col_id
        })

    return dash_table.DataTable(
        dataframe.to_dict('records'),
        columns,
        filter_action="native",
        id='datatable-interactivity',
        sort_action="native",
        row_selectable="multi",
        selected_rows=[],
        sort_mode="multi",
        page_size=12
    )

class StaticDashboard():
    def __init__(self, data_path, mode='Release'):
        self.__app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX], title='GlobalizerDashboard')
        self.__app.config['suppress_callback_exceptions'] = True

        self.__mode = mode

        self.__init = False
        with open(data_path) as json_data:
            self.__data = json.load(json_data)

        self.__color_themes_dict = {
            "Ice" : px.colors.sequential.ice,
            "Viridis" : px.colors.sequential.Viridis,
            "Bluered" : px.colors.sequential.Bluered,
            "Electric" : px.colors.sequential.Electric,
            "Jet": px.colors.sequential.Jet,
            "Plasma": px.colors.sequential.Plasma,
            "RdBu_r": px.colors.sequential.RdBu_r
        }
        self.__color_scale_names = list(self.__color_themes_dict.keys())
        self.__current_color_scale = px.colors.sequential.ice
        self.__current_color = px.colors.sequential.ice[0]

        self.__figure_type_names = ['3D поверхность', 'линии уровня']
        self.__calculation_type_names = ['интерполяция', 'аппроксимация', '- (по точкам испытаний)']

        self.__dfSDI = None
        self.__dfSDI_original = None

        self.__task_name = None
        self.__functional_count = 1
        self.__float_parameters_names = None
        self.__discrete_parameters_names = None
        self.__float_parameters_bounds = None
        self.__parameter_eps = None
        self.__parameter_r = None
        self.__parameter_iters_limit = None
        self.__parameter_start_point = None

        self.__trial_number = None
        self.__global_iter_number = None
        self.__local_iter_number = None
        self.__accuracy = None
        self.__solve_time = None

        self.__optimization_time = None

        self.__best_trial_number = None
        self.__best_value = None
        self.__best_float_point_dictionary = None
        self.__best_discrete_point_dictionary = None

        self.__importance = None

        self.__app.callback(
            Output("page-content", "children"),
            Input("url", "pathname"),
            Input('color-theme', "value"),
            Input('elimination-of-emissions', 'on')
        )(self.__render_page_content)

        self.__app.callback(
            Output('discrete_scatter_figure', 'figure'),
            Input('dsf-parameter-name', 'value')
        )(self.__update_discrete_scatter_figure)

        self.__app.callback(
            Output('continuous_scatter_figure', 'figure'),
            Input('csf-parameter-name', 'value')
        )(self.__update_continuous_scatter_figure)

        self.__app.callback(
            Output('surface_or_lines_level_figure', 'figure'),
            Input('sllf-xaxis-parameter-name', 'value'),
            Input('sllf-yaxis-parameter-name', 'value'),
            Input('sllf-figure-type', 'value'),
            Input('sllf-calculation-type', 'value'),
            Input('additional-figures', 'on'),
        )(self.__update_surface_or_lines_level_figure)

        self.__app.callback(
            Output('multidimensional_figure', 'figure'),
            Input('mdf-parameter-names', 'value')
        )(self.__update_multidimensional_figure)

        self.__app.callback(
            Output('data_from_json_file', 'children'),
            Input('upload-data', 'contents')
        )(self.__read_data_from_json)

        self.__app.callback(
            Output('archive_figure', "children"),
            Input('datatable-interactivity', "derived_virtual_data"),
            Input('datatable-interactivity', "derived_virtual_selected_rows")
        )(self.__update_archive_figure)

    def launch(self):
        self.__read_and_prepare_data(self.__data)

        self.__app.layout = html.Div([
            dcc.Location(id="url"),
            self.__create_sidebar_navigator(),
            self.__create_content_page()
        ], style={"background-color": "#FBFBFB"})

        self.__app.run(debug=True)

    def __fix_optimization_times(self):
        isFirst = 1
        first_not_zero_time = 0
        update_times = []
        for elem in self.__optimization_time:
            if elem != 0 and isFirst:
                first_not_zero_time = elem
                isFirst = 0
            if elem != 0:
                elem -= first_not_zero_time
            update_times.append(elem)
        self.__optimization_time = update_times

    def __read_and_prepare_data(self, data):
        self.__parameter_eps = data['Parameters'][0]['eps']
        self.__parameter_r = data['Parameters'][0]['r']
        self.__parameter_iters_limit = data['Parameters'][0]['iters_limit']
        self.__parameter_start_point = data['Parameters'][0]['start_point']

        self.__task_name = data['Task'][0]['name']
        self.__functional_count = len(data['SearchDataItem'][0]["function_values"])

        self.__dfSDI = pd.DataFrame(data['SearchDataItem'])
        self.__dfSDI = self.__dfSDI.rename(columns={'__z': 'objective_func'})

        self.__float_parameters_names = [f"{x} [c]" for x in [*pd.DataFrame(data['Task'][0]['float_variables'])]]
        self.__discrete_parameters_names = [f"{x} [d]" for x in [*pd.DataFrame(data['Task'][0]['discrete_variables'])]]
        self.__parameters_names = self.__float_parameters_names + self.__discrete_parameters_names
        self.__float_parameters_bounds = data['Task'][0]['float_variables']

        # TODO: fix like this
        self.__accuracy = float(pd.DataFrame(data['solution'])['solution_accuracy'].squeeze())
        self.__trial_number = int(pd.DataFrame(data['solution'])['number_of_trials'].squeeze())
        self.__global_iter_number = int(pd.DataFrame(data['solution'])['number_of_global_trials'].squeeze())
        self.__local_iter_number = int(pd.DataFrame(data['solution'])['number_of_local_trials'].squeeze())
        self.__solve_time = float(pd.DataFrame(data['solution'])['solving_time'].squeeze())
        self.__best_trial_number = int(pd.DataFrame(data['solution'])['num_iteration_best_trial'].iloc[0][0])
        '''
        self.__accuracy = float(pd.DataFrame(data['solution'])['solution_accuracy'])
        self.__trial_number = int(pd.DataFrame(data['solution'])['number_of_trials'])
        self.__global_iter_number = int(pd.DataFrame(data['solution'])['number_of_global_trials'])
        self.__local_iter_number = int(pd.DataFrame(data['solution'])['number_of_local_trials'])
        self.__solve_time = float(pd.DataFrame(data['solution'])['solving_time'])
        self.__best_trial_number = int(pd.DataFrame(data['solution'])['num_iteration_best_trial'][0][0])
        '''

        best_trials = pd.DataFrame(data['best_trials']).rename(columns={'__z': 'objective_func'})


        accuracy_in_signs = 0
        accuracy_copy = self.__accuracy
        while accuracy_copy < 1:
            accuracy_copy *= 10
            accuracy_in_signs += 1

        self.__best_value = best_trials['objective_func'][0]
        self.__best_float_point_dictionary = dict(zip(self.__float_parameters_names,
            [round(elem, accuracy_in_signs) for elem in best_trials['float_variables'][0]]))
        self.__best_discrete_point_dictionary = dict(zip(self.__discrete_parameters_names,
            best_trials['discrete_variables'][0]))

        self.__optimization_time = self.__dfSDI["creation_time"].to_list()

        FVs = pd.DataFrame(
            self.__dfSDI['float_variables'].to_list(),
            columns=self.__float_parameters_names,
            index=self.__dfSDI.index
        )

        DVs = pd.DataFrame(
            self.__dfSDI['discrete_variables'].to_list(),
            columns=self.__discrete_parameters_names,
            index=self.__dfSDI.index
        )

        self.__dfSDI = self.__dfSDI[["objective_func", "x", "delta", "globalR", "localR", "index"]]
        self.__dfSDI = pd.concat([DVs, self.__dfSDI], axis=1, join='inner')
        self.__dfSDI = pd.concat([FVs, self.__dfSDI], axis=1, join='inner')

        self.__dfSDI.insert(loc=0, column='trial', value=np.arange(1, len(self.__dfSDI) + 1))

        self.__dfSDI_original = self.__dfSDI.copy()

        self.__dfSDI.drop(self.__dfSDI[self.__dfSDI['objective_func'] >= 1.797692e+308].index, inplace=True)
        self.__dfSDI.drop(self.__dfSDI[self.__dfSDI['index'] == - 2].index, inplace=True)

        self.__fix_optimization_times()
        self.__calculate_parameters_importance()

        del self.__data
        self.__data = None

    def __calculate_parameters_importance(self):
        min_obj_func = min(self.__dfSDI['objective_func'])
        max_obj_func = max(self.__dfSDI['objective_func'])

        self.__importance = []
        for parameter in self.__parameters_names:
            uniq_parameter_values = self.__dfSDI[parameter].unique()
            importance_value = 0
            for value in uniq_parameter_values:
                data = self.__dfSDI.loc[self.__dfSDI[parameter] == value]
                importance_value += (max(data['objective_func']) - min(data['objective_func']))
            importance_value = importance_value / (len(uniq_parameter_values) * (max_obj_func - min_obj_func))
            self.__importance.append(round(importance_value, 2))

    def __create_sidebar_navigator(self):
        return html.Div([
    dbc.Navbar(
        dbc.Container(
            [
                # 1. Логотип
                dbc.NavbarBrand(
                    html.Img(src='assets/globalizer_dash_light.png', alt='image', height="90px")
                ),

                # 2. Навигация и элементы управления в одной строке
                dbc.Nav(
                    [
                        dbc.NavLink("Решение", href="/", active="exact"),
                        dbc.NavLink("Аналитика", href="/analytics", active="exact"),
                        dbc.NavLink("Архив", href="/archive", active="exact"),

                        # Элемент, который отодвинет всё правое меню к краю
                        dbc.NavItem(dbc.NavLink("Документация", href="https://globalizer-documentation.readthedocs.io/en/latest/"), className="ms-auto"),
                        dbc.NavLink("Github", href="https://github.com/OptimLLab/Globalizer"),

                        # 3. Блок управления 
                        dbc.NavItem(
                            html.Div(
                                style={'display': 'flex', 'align-items': 'center', 'gap': '15px'} 
                                , children=[
                                
                                html.Div(
                                    [
                                        html.P(f"Отфильтровать выбросы", style={'color': '#989898', 'font-size': '0.8em', 'margin-bottom': '0'}),
                                        daq.BooleanSwitch(id='elimination-of-emissions', on=False, color='red')
                                    ],
                                    style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'}
                                ),

                                html.Div(
                                    [
                                        html.P(f"Цветосхема", style={'color': '#989898', 'font-size': '0.8em', 'margin-bottom': '0'}),
                                        dcc.Dropdown(
                                            self.__color_scale_names,
                                            "Ice",
                                            id='color-theme',
                                            clearable=False,
                                            style={'width': '120px'} 
                                        )
                                    ],
                                    style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'}
                                ),
                            ])
                        ),
                    ], 
                    navbar=True,
                    className="w-100 justify-content-start"
                ),
            ]
        ), 
        sticky="bottom", 
        color="primary", 
        dark=True,
        className="py-2 align-items-center" 
    )
])

    def __create_content_page(self):
        return html.Div(id="page-content", style=CONTENT_STYLE)

    def __render_problem_description(self):
        return html.Div(children=[
            html.H2('ОПИСАНИЕ ЗАДАЧИ',
                    style={'textAlign': 'left'}),
            html.Br(),
            html.P(f"Название задачи: {self.__task_name}", style={'color': '#212121'}),
            html.P(f"Размерность: {len(self.__float_parameters_names + self.__discrete_parameters_names)}", style={'color': '#212121'}),
            html.P(f"Количество параметров: непрерывные = {len(self.__float_parameters_names)},\
                дискретные = {len(self.__discrete_parameters_names)}", style={'color': '#212121'}),
            html.P(f"Количество функционалов: целевые функции (критерии) = 1, ограничения = {self.__functional_count - 1}",
                style={'color': '#212121'}),

            dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Перетащите файл или ',
                        html.A('Выберите файл')
                    ]),
                    style={
                        'width': '95%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    multiple=True
            ),
            html.Div(id='data_from_json_file')
        ], style={'width': '55%', "background-color": "#FFFFFF", "border": "20px solid #FFFFFF"})

    def __render_parameters_description(self):
        return html.Div(children=[
            html.H2('ПАРАМЕТРЫ МЕТОДА ОПТИМИЗАЦИИ',
                    style={'textAlign': 'left'}),
            html.Br(),
            html.P(f"Заданная точность решения: eps = {self.__parameter_eps}",
                   style={'color': '#212121'}),
            html.P(f"Параметр надежности: r = {self.__parameter_r}",
                   style={'color': '#212121'}),
            html.P(f"Ограничение на количество итераций: iters_limit = {self.__parameter_iters_limit}",
                   style={'color': '#212121'}),
            html.P(f"Стартовая точка: start_point = {self.__parameter_start_point}",
                   style={'color': '#212121'}),
        ], style={'width': '45%', "background-color": "#FFFFFF", "border": "20px solid #FFFFFF"})

    def __render_solution_description(self):
        return html.Div(children=[
            html.H2('НАЙДЕННОЕ РЕШЕНИЕ', style={'textAlign': 'left'}),
            html.P(f"{round(self.__best_value, 6)}", style={'font-size': '2.0em', 'color': 'black'}),
            html.P(f"Лучшая точка: {self.__best_float_point_dictionary}, {self.__best_discrete_point_dictionary}",
                style={'color': '#212121'}),
            html.P(f'Номер лучшего испытания: {self.__best_trial_number}', style={'color': '#212121'}),
            html.P(f"Достигнутая точность: {round(self.__accuracy, 6)}", style={'color': '#212121'}),
            html.P([f"Общее число испытаний: {self.__trial_number}", html.Br(), f"(кол-во итераций глобального метода - {self.__global_iter_number},\
                кол-во итераций локального метода - {self.__local_iter_number})"], style={'color': '#212121'}),
            
            html.P(f"*[c] - непрерывные параметры, [d] - дискретные параметры",
                style={'color': '#212121', 'font-size': '0.8em'}),
        ], style={'width': '45%', "background-color": "#FFFFFF", "border": "20px solid #FFFFFF"})

    def __render_optimization_time(self):
        return html.Div(children=[
            html.H2('Время оптимизации', style={'textAlign': 'left'}),
            html.P(f"Общее время оптимизации: {round(self.__solve_time, 3)} сек.", style={'color': '#212121'}),
            html.Div(children=[
                dcc.Graph(
                    figure={
                        "data": [{
                            "x": self.__dfSDI_original['trial'],
                            "y": self.__optimization_time,
                            'type': 'lines',
                            'marker': {'color': self.__current_color}
                        }],
                        "layout": {
                            'paper_bgcolor': '#FFFFFF',
                            'plot_bgcolor': '#FFFFFF',
                            'xaxis': {'anchor': 'y', 'title': {'text': 'номер испытания'}},
                            'yaxis': {'anchor': 'x', 'title': {'text': 'время перед запуском испытания, сек.'}}
                        },
                    },
                    config={'displayModeBar': True},
                )
            ])
        ], style={'width': '55%', "background-color": "#FFFFFF", "border": "20px solid #FFFFFF", })

    def __hide_IQR(self, hide=False):
        if hide:
            Q1 = self.__dfSDI['objective_func'].quantile(0.25)
            Q3 = self.__dfSDI['objective_func'].quantile(0.75)
            mid = self.__dfSDI['objective_func'].median()
            IQR = Q3 - Q1
            up = mid + 1.5 * IQR
            self.__dfSDI = self.__dfSDI[(self.__dfSDI['objective_func'] <= up)]
        else:
            del self.__dfSDI
            self.__dfSDI = self.__dfSDI_original.copy()
            self.__dfSDI.drop(self.__dfSDI[self.__dfSDI['objective_func'] >= 1.797692e+308].index, inplace=True)
            self.__dfSDI.drop(self.__dfSDI[self.__dfSDI['index'] == -2].index, inplace=True)

    def __render_iteration_characteristic(self):
        return html.Div([
            html.H2('Обновление лучшего значения целевой функции', style={'textAlign': 'left'}),
            html.Div(children=[
                html.Div(children=[
                    dcc.Graph(
                        figure=((px.scatter(
                            self.__dfSDI.loc[self.__dfSDI['index'].values == self.__functional_count - 1],
                            x='trial',
                            y='objective_func',
                            color_discrete_sequence=[self.__current_color],
                            marginal_y="histogram",
                            trendline="expanding",
                            trendline_options=dict(function="min"))).update_layout(
                                legend={'orientation': "h", 'y': -0.25},
                                xaxis={'anchor': 'x', 'title': {'text': 'номер испытания'}},
                                yaxis={'anchor': 'y', 'title': {'text': 'значение целевой функции'}},
                                paper_bgcolor='#FFFFFF',
                                plot_bgcolor='#FFFFFF'
                            )
                        ),
                        config={
                            'displayModeBar': True,  # True, False, 'hover'
                        },
                    )
                ], style={'width': '100%'}),
            ], style={'display': 'flex', 'flexDirection': 'row'}),
        ], style={"background-color": "#FFFFFF", "border": "20px solid #FFFFFF", })

    def __scatter_matrix_figure(self):
        fig = px.scatter_matrix(
            self.__dfSDI.loc[self.__dfSDI['index'].values == self.__functional_count - 1],
            dimensions=self.__parameters_names,
            color="objective_func",
            labels={"objective_func": "значения<br>целевой<br>функции"},
            opacity=0.7,
            color_continuous_scale=self.__current_color_scale,
            width=len(self.__parameters_names) * 240,
            height=len(self.__parameters_names) * 240
        )
        fig.update_traces(diagonal_visible=False)
        fig.update_layout(paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF')
        return fig

    def __render_parameters_dependence(self):
        return html.Div([
            html.H2('Матрица графиков рассеяния', style={'textAlign': 'left'}),
            html.Div(children=[
                html.Div(children=[
                    dcc.Graph(
                        figure=self.__scatter_matrix_figure(),
                        config={'displayModeBar': True},
                    )
                ], style={'width': '100%'}),
            ], style={'maxWidth': '100%', 'maxHeight': '600px', "overflow": "scroll"}),
            html.P(f'** Показывает связь между разными парами переменных, цвет опредяет группы точек, соответствующих большим и меньшим значениям целевой функции', style={'text-align': 'right', 'color': '#212121', 'font-size': '0.8em'}),    
        ], style={'width': '100%', "background-color": "#FFFFFF", "border": "20px solid #FFFFFF", 'height': '750px'})

    def __render_parameters_importance(self):
        return html.Div([
            html.H2('Значимость параметров', style={'textAlign': 'left'}),
            html.Div([
                dcc.Graph(
                    figure={
                        'data': [
                            {'x': self.__parameters_names,
                             'y': self.__importance,
                             'orientation': 'v',
                             'type': 'bar',
                             'text': self.__importance,
                             'textposition': 'outside',
                             'textfont': "black",
                             'text_auto': '.2s',
                             'marker': {
                                 'color': self.__current_color,
                                 'line': {'color': self.__current_color, 'width': '1'}
                             }
                             },
                        ],
                        'layout': {
                            'xaxis': {
                                'anchor': 'y',
                                'tickfont': {'size': '10'},
                                'tickangle': -90
                            },
                            'yaxis': {
                                'range': [0, 1],
                                'anchor': 'x',
                                'title': {'text': 'вклад'},
                                'tickfont': {'size': '10'}
                            },
                            'title': "Значимость по вкладу</br></br>в разброс значений целевой функции",
                            'paper_bgcolor': '#FFFFFF',
                            'plot_bgcolor': '#FFFFFF',
                            'margin': dict(t=130, b=200, r=100)
                        }
                    },
                    config={
                        'scrollZoom': True,  # True, False
                        'showTips': True,  # True, False
                        'displayModeBar': True,  # True, False, 'hover'
                    },
                )
            ])
        ], style={'width': '40%', "background-color": "#FFFFFF", "border": "20px solid #FFFFFF"})

    def __render_multidimensional_representation(self):
        return html.Div(children=[
            html.H2('Многомерная визуализация', style={'textAlign': 'left'}),
            html.Div(children=[
                html.Div(children=[
                    html.Br(),
                    html.Label('Параметры для визуализации'),
                    dcc.Dropdown(
                        self.__parameters_names,
                        self.__parameters_names,
                        id='mdf-parameter-names',
                        multi=True
                    ),
                ], style={'width': '15%'}),
                html.Div(children=[
                    dcc.Graph(
                        id='multidimensional_figure',
                        config={'displayModeBar': True},
                    )
                ], style={'width': '85%'}),
            ], style={'display': 'flex', 'flexDirection': 'row', 'height': '90%'})
        ], style={"background-color": "#FFFFFF", "border": "20px solid #FFFFFF"})

    def __render_surface_and_level_lines(self):
        return html.Div(children=[
            html.H2('Визуализация в окрестности лучшего решения', style={'textAlign': 'left'}),
            html.Div([
                html.Div(children=[
                    html.Br(),
                    html.Label('Тип графика'),
                    dcc.Dropdown(
                        self.__figure_type_names,
                        self.__figure_type_names[0],
                        id='sllf-figure-type',
                    ),
                    html.Label('Режим построения целевой функции'),
                    dcc.Dropdown(
                        self.__calculation_type_names,
                        self.__calculation_type_names[0],
                        id='sllf-calculation-type',
                    ),
                    html.Label('Параметр на X-оси'),
                    dcc.Dropdown(
                        self.__float_parameters_names,
                        self.__float_parameters_names[0],
                        id='sllf-xaxis-parameter-name',
                    ),
                    html.Label('Параметр на Y-оси'),
                    dcc.Dropdown(
                        self.__float_parameters_names,
                        self.__float_parameters_names[1],
                        id='sllf-yaxis-parameter-name',
                    ),
                    html.Label('Показать доп.графики'),
                    html.Td(
                        daq.BooleanSwitch(id='additional-figures', on=True, color="#3E59A5")
                    )
                ], style={'width': '20%'}),
                html.Div(children=[
                    dcc.Graph(
                        id='surface_or_lines_level_figure',
                        config={'displayModeBar': True},
                    )
                ], style={'width': '75%'}),
            ], style={'display': 'flex', 'flexDirection': 'row', 'width': '90%', 'height': '600px'}),
        ], style={"background-color": "#FFFFFF", "border": "20px solid #FFFFFF", })

    def __render_objective_function_values_scatter(self):
        # TODO: fix like this

        if not self.__discrete_parameters_names:
            return html.Div(children=[
                    html.H2('Распределение значений целевой функции', style={'textAlign': 'left'}),
                    dcc.Tab(label='Непрерывные параметры', children=[
                        html.Div([
                            html.Div(children=[
                                html.Br(),
                                html.Label('Параметр на X-оси'),
                                dcc.Dropdown(
                                    self.__float_parameters_names,
                                    self.__float_parameters_names[0],
                                    id='csf-parameter-name',
                                    style={'width': '60%'}
                                ),
                                dcc.Graph(
                                    id='continuous_scatter_figure',
                                    config={'displayModeBar': True},
                                )
                            ], style={'width': '100%'}),
                        ], style={'display': 'flex', 'flexDirection': 'row', 'width': '90%', 'height': '70%'}),
                    ])
                ], style={'width': '60%', "background-color": "#FFFFFF", "border": "20px solid #FFFFFF", })
        else:
            return html.Div(children=[
                html.H2('Распределение значений целевой функции', style={'textAlign': 'left'}),
                dcc.Tabs([
                    dcc.Tab(label='Непрерывные параметры', children=[
                        html.Div([
                            html.Div(children=[
                                html.Br(),
                                html.Label('Параметр на X-оси'),
                                dcc.Dropdown(
                                    self.__float_parameters_names,
                                    self.__float_parameters_names[0],
                                    id='csf-parameter-name',
                                    style={'width': '60%'}
                                ),
                                dcc.Graph(
                                    id='continuous_scatter_figure',
                                    config={'displayModeBar': True},
                                )
                            ], style={'width': '100%'}),
                        ], style={'display': 'flex', 'flexDirection': 'row', 'width': '90%', 'height': '70%'}),
                    ]),
                    dcc.Tab(label='Дискретные параметры', children=[
                        html.Div([
                            html.Div(children=[
                                html.Br(),
                                html.Label('Параметр на X-оси'),
                                dcc.Dropdown(
                                    self.__discrete_parameters_names,
                                    self.__discrete_parameters_names[0],
                                    id='dsf-parameter-name',
                                    style={'width': '60%'}
                                ),
                                dcc.Graph(
                                    id='discrete_scatter_figure',
                                    config={'displayModeBar': True},
                                )
                            ], style={'width': '100%'}),
                        ], style={'display': 'flex', 'flexDirection': 'row', 'width': '90%', 'height': '70%'}),
                    ])
                ], style={'width': '90%'})
            ], style={'width': '60%', "background-color": "#FFFFFF", "border": "20px solid #FFFFFF", })

    def __render_archive(self, df):
        return html.Div(children=[
            html.P(f"*[c] - непрерывные параметры, [d] - дискретные параметры",
                   style={'text-align': 'right', 'color': '#212121', 'font-size': '0.8em'}),
            html.H1('Архив всех испытаний', style={'textAlign': 'left'}),
            html.Div(
                [create_dash_table_from_dataframe(df)],
                style={'maxWidth': '95%', 'maxHeight': '700px', "overflow": "scroll"}
            ),
            html.Div(id='archive_figure', style={'width': '95%'})
        ], style={"background-color": "#FFFFFF", "border": "20px solid #FFFFFF", })

    def __render_page_content(self, pathname, color_theme, hide):
        self.__hide_IQR(hide)
        self.__current_color_scale = self.__color_themes_dict[color_theme]
        self.__current_color = self.__current_color_scale[0]
        if pathname == "/":
            return [
                html.Div([
                    self.__render_parameters_description(),
                    self.__render_problem_description(),
                ], style={'display': 'flex', 'flexDirection': 'row'}),
                html.Div([
                    self.__render_solution_description(),
                    self.__render_optimization_time()
                ], style={'display': 'flex', 'flexDirection': 'row'}),
                self.__render_iteration_characteristic(),
            ]

        elif pathname == "/archive":
            if self.__mode == 'Release':
                return [
                    self.__render_archive(
                        self.__dfSDI_original[['trial'] + self.__parameters_names + ["objective_func"] + ["index"]]
                    )
                ]
            elif self.__mode == 'Debug':
                return [
                    self.__render_archive(
                        self.__dfSDI_original
                    )
                ]
        elif pathname == "/analytics":
            return [
                html.Div(children=[
                    html.P(f"*[c] - непрерывные параметры, [d] - дискретные параметры",
                        style={'text-align': 'right', 'color': '#212121', 'font-size': '0.8em'}),
                ], style={"background-color": "#FFFFFF", "border": "20px solid #FFFFFF"}),
                self.__render_surface_and_level_lines(),
                self.__render_multidimensional_representation(),
                html.Div([
                    self.__render_objective_function_values_scatter(),
                    self.__render_parameters_importance()
                ], style={'display': 'flex', 'flexDirection': 'row'}),
                html.Div([
                    self.__render_parameters_dependence(),
                ], style={'display': 'flex', 'flexDirection': 'row'}),
            ]

        # If the user tries to reach a different page, return a 404 message
        return dbc.Jumbotron(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"Путь к файлу {pathname} не распознан..."),
            ]
        )

    def __update_discrete_scatter_figure(self, xaxis_column_name=None):
        if xaxis_column_name == None:
            xaxis_column_name = self.__discrete_parameters_names[0]

        fig = px.violin(
            self.__dfSDI.loc[self.__dfSDI['index'].values == self.__functional_count - 1],
            x=xaxis_column_name,
            y='objective_func',
            title="Разброс значений целевой функции<br>в зависимости от выбранного параметра",
            color_discrete_sequence=[self.__current_color]
        )
        fig.update_xaxes(title=xaxis_column_name)
        fig.update_yaxes(title='значение целевой функции')
        fig.update_layout(paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', showlegend=False)
        return fig

    def __update_continuous_scatter_figure(self, xaxis_column_name=None):
        if xaxis_column_name == None:
            xaxis_column_name = self.__float_parameters_names[0]

        fig = px.scatter(
            self.__dfSDI.loc[self.__dfSDI['index'].values == self.__functional_count - 1],
            x=xaxis_column_name,
            y='objective_func',
            color=self.__dfSDI.loc[self.__dfSDI['index'].values == self.__functional_count - 1]['trial'][::-1],
            color_continuous_scale=list(reversed(self.__current_color_scale)),
            title="Разброс значений целевой функции<br>в зависимости от выбранного параметра",
            opacity=0.3
        )
        fig.update_xaxes(title=xaxis_column_name)
        fig.update_yaxes(title='значение целевой функции')
        fig.update_layout(paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', showlegend=False,
            coloraxis_colorbar=dict(title="номера<br>испытаний"))
        return fig

    def __calculate_data(self, xaxis_column_name, yaxis_column_name, calc):
        if xaxis_column_name == None:
            xaxis_column_name = self.__float_parameters_names[0]
        if yaxis_column_name == None:
            xaxis_column_name = self.__float_parameters_names[1]

        df = self.__dfSDI.copy()

        # берем окрестность лучшего сочетания дискретных параметров
        if self.__discrete_parameters_names:
            for param in self.__discrete_parameters_names:
                df = df.loc[df[param] == self.__best_discrete_point_dictionary[param]]
    
        # берем окрестность лучших прочих непрерывных параметров
        for param in self.__parameters_names:
            if (xaxis_column_name != param and yaxis_column_name != param and param not in self.__discrete_parameters_names):
                df = df.loc[abs(df[param] - self.__best_float_point_dictionary[param]) < self.__parameter_eps * 10]

        # берем только допустимые точки
        if self.__functional_count > 1:
            df = df.loc[df['index'].values == self.__functional_count - 1]

        x = np.array(df[xaxis_column_name].values)
        y = np.array(df[yaxis_column_name].values)
        z = np.array(df['objective_func'].values)

        xi = None
        yi = None
        Z = None

        bounds_x = list(self.__float_parameters_bounds[
            (self.__float_parameters_names).index(xaxis_column_name)
        ].values())[0]
        bounds_y = list(self.__float_parameters_bounds[
            (self.__float_parameters_names).index(yaxis_column_name)
        ].values())[0]

        if calc == 'интерполяция':
            #if not self.__discrete_parameters_names:
            points = np.array(list(zip(x, y)))
            values = np.array(z)

            _, unique_indices = np.unique(points, axis=0, return_index=True)

            # Оставляем только уникальные координаты
            x_unique = points[unique_indices, 0]
            y_unique = points[unique_indices, 1]
            z_unique = values[unique_indices]

            if len(self.__float_parameters_names) > 2:
                interp = interpolate.Rbf(x_unique, y_unique, z_unique, function='linear')
            else:
                interp = interpolate.Rbf(x_unique, y_unique, z_unique)
                        
            xi = np.linspace(bounds_x[0], bounds_x[1], 150)
            yi = np.linspace(bounds_y[0], bounds_y[1], 150)
            xi, yi = np.meshgrid(xi, yi)
            Z = interp(xi, yi)
            #else:
            #    xi = np.linspace(bounds_x[0], bounds_x[1], 150)
            #    yi = np.linspace(bounds_y[0], bounds_y[1], 150)
            #   X, Y = np.meshgrid(xi, yi)
            #   Z = griddata((x, y), z, (X, Y), method='cubic')  # "nearest", "linear", "natural", and "cubic" methods
            '''
            points = [list(x), list(y)]
            points = list(map(list, zip(*points)))

            interp = interpolate.Rbf(*zip(*points), z)
            
            xi = np.linspace(bounds_x[0], bounds_x[1], 150)
            yi = np.linspace(bounds_y[0], bounds_y[1], 150)
            xi, yi = np.meshgrid(xi, yi)
            Z = interp(xi, yi)
            '''

        elif calc == 'аппроксимация':
            nn = MLPRegressor(
                activation='logistic',   # can be tanh, identity, logistic, relu
                solver='lbfgs',          # can be lbfgs, sgd , adam
                alpha=0.001,
                hidden_layer_sizes=(40,),
                max_iter=10000,
                tol=10e-6,
                random_state=10
            )

            points = [list(x), list(y)]
            points = list(map(list, zip(*points)))

            nn.fit(points, z)
            xi = np.linspace(bounds_x[0], bounds_x[1], 150)
            yi = np.linspace(bounds_y[0], bounds_y[1], 150)
            xi, yi = np.meshgrid(xi, yi)

            xy = np.c_[xi.ravel(), yi.ravel()]

            Z = nn.predict(xy)
            Z = Z.reshape(150, 150)

        del df

        x_noncomput = []
        y_noncomput = []

        x_unaccept = []
        y_unaccept = []


        # невычислимые точки
        df = self.__dfSDI.copy()
        df = df.loc[df['index'].values == -3]

        if not df.empty:
            x_noncomput = np.array(df[xaxis_column_name].values)
            y_noncomput = np.array(df[yaxis_column_name].values)
            
        del df

        # недопустимые точки
        if self.__functional_count > 1:
            df = self.__dfSDI.copy()
            #df = df.loc[df['index'].values != self.__functional_count - 1 & df['index'].values != -3]
            indices_to_exclude = [self.__functional_count - 1, -3]
            df = df.loc[~df['index'].isin(indices_to_exclude)]
            if not df.empty:
                x_unaccept = np.array(df[xaxis_column_name].values)
                y_unaccept = np.array(df[yaxis_column_name].values)
            del df

        return bounds_x, bounds_y, x, y, z, xi, yi, Z, x_unaccept, y_unaccept, x_noncomput, y_noncomput

    def __surface_figure(self, xaxis_column_name, yaxis_column_name, calc, show_additional_figs, xi, yi, Z, x, y, z, x_unaccept, y_unaccept):
        if calc == 'интерполяция' or calc == 'аппроксимация':
            surface = go.Surface(x=xi, y=yi, z=Z,
                colorscale=self.__current_color_scale,
                opacity=1,
                colorbar=dict(title="значения<br>целевой<br>функции")
            )
            fig = go.Figure(data=[surface])

            if show_additional_figs:
                fig.update_traces(contours_z=dict(
                    show=True,
                    usecolormap=True,
                    highlightcolor="limegreen",
                    project_z=True
                ))
            bz_min = float(np.min(Z))
        elif calc == '- (по точкам испытаний)':
            surface = go.Mesh3d(x=x, y=y, z=z,
                showscale=True,
                intensity=z,
                colorscale=self.__current_color_scale,
                opacity=1
            )
            fig = go.Figure(data=[surface])
            bz_min = float(np.min(z))
                            
        fig.add_scatter3d(x=x, y=y, z=z,
            mode='markers',
            name='точки испытаний',
            marker=dict(size=2, color='blue', opacity=0.7)
        )

        fig.add_scatter3d(
            x=[self.__best_float_point_dictionary[xaxis_column_name]],
            y=[self.__best_float_point_dictionary[yaxis_column_name]],
            z=[self.__best_value],
            name='лучшая точка',
            mode='markers',
            marker=dict(size=3, color='red', opacity=1)
        )
        
        
        fig.add_trace(go.Scatter3d(
            x=x_unaccept,
            y=y_unaccept,
            z=[bz_min] * len(x_unaccept),
            mode='markers',
            marker=dict(size=1, color='black', opacity=0.5),
            name='точки с нарушенными ограничениями'
        ))

        if not self.__discrete_parameters_names:
            fig.update_layout(
                title=f'Поверхность целевой функции<br>в сечении лучшего решения ({calc})',
                scene=dict(xaxis_title=xaxis_column_name, yaxis_title=yaxis_column_name, zaxis_title='значение целевой функции'),
                paper_bgcolor='#FFFFFF',
                plot_bgcolor='#FFFFFF',
                showlegend=False,
                height=590,
                template="none",
                title_x=0.1,
                title_xanchor='left'
            )
        else:
            fig.update_layout(
                title=f'Поверхность целевой функции<br>в сечении лучшего решения ({calc})<br>с дискретными параметрами<br>'+str(self.__best_discrete_point_dictionary),
                scene=dict(xaxis_title=xaxis_column_name, yaxis_title=yaxis_column_name, zaxis_title='значение целевой функции'),
                paper_bgcolor='#FFFFFF',
                plot_bgcolor='#FFFFFF',
                showlegend=False,
                height=590,
                template="none",
                title_x=0.1,
                title_xanchor='left'
            )
        return fig

    def __lines_level_figure(self, xaxis_column_name, yaxis_column_name, calc, show_additional_figs, bounds_x, bounds_y, xi, yi, Z, x, y, z, x_unaccept, y_unaccept):
        if calc == 'интерполяция' or calc == 'аппроксимация':
            fig = go.Figure(data=[go.Contour(x=xi[0], y=yi[:, 0], z=Z,
                colorscale=self.__current_color_scale,
                colorbar=dict(title='значения<br>целевой<br>функции')
            )])
        elif calc == '- (по точкам испытаний)':
            fig = go.Figure(data=[go.Contour(x=x, y=y, z=z,
                colorscale=self.__current_color_scale,
                colorbar=dict(title='значения<br>целевой<br>функции', titleside='right')
            )])

        if self.__functional_count > 1:
            fig.add_scatter(x=x_unaccept, y=y_unaccept,
                mode='markers',
                name='точки с нарушенными ограничениями',
                marker=dict(size=2, color='black', opacity=0.5)
            )

        fig.add_scatter(x=x, y=y,
            mode='markers',
            name='точки испытаний',
            marker=dict(size=3, color='blue', opacity=0.7)
        )
        fig.add_scatter(
            x=[self.__best_float_point_dictionary[xaxis_column_name]],
            y=[self.__best_float_point_dictionary[yaxis_column_name]],
            mode='markers',
            name='лучшая точка',
            marker=dict(size=4, color='red', opacity=1)
        )

        if not self.__discrete_parameters_names:
            fig.update_layout(
                title=f'Линии уровня целевой функции<br>в сечении лучшего решения ({calc})',
                paper_bgcolor='#FFFFFF',
                plot_bgcolor='#FFFFFF',
                showlegend=True,
                height=590,
                legend={'orientation': "h"},
                xaxis_range=[bounds_x[0], bounds_x[1]], yaxis_range=[bounds_y[0], bounds_y[1]],
                xaxis_title=xaxis_column_name,
                yaxis_title=yaxis_column_name
            )
        else:
            fig.update_layout(
                title=f'Линии уровня целевой функции<br>в сечении лучшего решения ({calc})<br>с дискретными параметрами<br>' + str(self.__best_discrete_point_dictionary),
                paper_bgcolor='#FFFFFF',
                plot_bgcolor='#FFFFFF',
                showlegend=True,
                height=590,
                legend={'orientation': "h"},
                xaxis_range=[bounds_x[0], bounds_x[1]], yaxis_range=[bounds_y[0], bounds_y[1]],
                xaxis_title=xaxis_column_name,
                yaxis_title=yaxis_column_name
            )

        if show_additional_figs:
            fig.add_trace(go.Histogram(
                y=y,
                xaxis='x2',
                marker=dict(color=self.__current_color),
                name='гистограмма значений ' + yaxis_column_name
            ))
            fig.add_trace(go.Histogram(
                x=x,
                yaxis='y2',
                marker=dict(color=self.__current_color),
                name='гистограмма значений ' + xaxis_column_name
            ))
            fig.update_layout(
                xaxis_domain=[0, 0.85],
                yaxis_domain=[0, 0.85],
                xaxis2=dict(zeroline=False, domain=[0.85, 1], showgrid=False),
                yaxis2=dict(zeroline=False, domain=[0.85, 1], showgrid=False),
                bargap=0,
                hovermode='closest',
            )
        return fig

    def __update_surface_or_lines_level_figure(self, xaxis_column_name=None, yaxis_column_name=None, type='3D поверхность',
        calc='интерполяция', show_additional_figs=True):
        bounds_x, bounds_y, x, y, z, xi, yi, Z, x_unaccept, y_unaccept, x_noncomput, y_noncomput = self.__calculate_data(xaxis_column_name, yaxis_column_name, calc)
        if type == '3D поверхность':
            return self.__surface_figure(xaxis_column_name, yaxis_column_name, calc, show_additional_figs,
                xi, yi, Z, x, y, z, x_unaccept, y_unaccept)
        elif type == 'линии уровня':
            return self.__lines_level_figure(xaxis_column_name, yaxis_column_name, calc, show_additional_figs,
                bounds_x, bounds_y, xi, yi, Z, x, y, z, x_unaccept, y_unaccept)

    def __update_multidimensional_figure(self, xaxis_column_name=None):
        df = self.__dfSDI.copy()

        # берем только допустимые вычисленные точки
        if self.__functional_count > 1:
            df = df.loc[df['index'].values == self.__functional_count - 1]

        if xaxis_column_name == None:
            xaxis_column_name = self.__parameters_names
        xaxis_column_name = ['objective_func'] + xaxis_column_name

        xaxis_column_name_dict = {}
        for name in xaxis_column_name:
            if name in self.__discrete_parameters_names:
                df[name + '_cat'] = df[name].astype('category').cat.codes
                replace = name + '_cat'
            else:
                replace = name
            xaxis_column_name_dict[replace] = name

        fig = px.parallel_coordinates(
            df,
            color="objective_func",
            dimensions=xaxis_column_name_dict.keys(),
            labels=xaxis_column_name_dict,
            color_continuous_scale=self.__current_color_scale
        )

        fig.update_layout(
            xaxis=dict(title='параметры', ticktext=xaxis_column_name),
            yaxis=dict(title='значение целевой функции'),
            paper_bgcolor='#FFFFFF',
            plot_bgcolor='#FFFFFF',
            coloraxis_colorbar_title="значения<br>целевой<br>функции"
        )

        fig.update_traces(unselected_line_opacity=0.5, selector=dict(type='parcoords'))

        del df
        return fig

    def __read_data_from_json(self, contents):
        if self.__init and (contents is not None):
            content_type, content_string = contents[0].split(',')
            decoded = base64.b64decode(content_string)
            self.__data = json.loads(decoded)
            self.launch()
        else:
            self.__init = True
        return html.Div(id='hidden-div', style={'display':'none'})

    def __update_archive_figure(self, rows, derived_virtual_selected_rows):
        if derived_virtual_selected_rows is None:
            derived_virtual_selected_rows = []

        dff = self.__dfSDI if rows is None else pd.DataFrame(rows)

        ids = []
        check = list(~dff['trial'].isin(self.__dfSDI['trial']))
        for i in range(len(dff)):
           if check[i]:
               ids.append(i)

        colors = ['#31B37C' if i in derived_virtual_selected_rows else
                  "red" if i in ids else
                  self.__current_color
                  for i in range(len(dff))]

        return [
            dcc.Graph(
                figure={
                    "data": [
                        {
                            "x": dff['trial'],
                            "y": dff['objective_func'],
                            "type": "bar",
                            "marker": {"color": colors},
                        }
                    ],
                    "layout": {
                        "xaxis": {"automargin": True, "title": "trial"},
                        "yaxis": {
                            "automargin": True,
                            "title": {"text": "значение<br>целевой<br>функции"}
                        },
                        "height": 250,
                        "margin": {"t": 10, "l": 10, "r": 10},
                        "paper_bgcolor": '#FFFFFF',
                        "plot_bgcolor": '#FFFFFF'
                    },
                },
            )
        ]
