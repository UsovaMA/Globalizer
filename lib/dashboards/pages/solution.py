import plotly.express as px
from dash import dcc, html


def render_problem_description(task_name, parameters_names,
                               float_parameters_names, discrete_parameters_names,
                               functional_count):
        return html.Div(children=[
            html.H2('ОПИСАНИЕ ЗАДАЧИ',
                    style={'textAlign': 'left'}),
            html.Br(),
            html.P(f"Название задачи: {task_name}", style={'color': '#212121'}),
            html.P(f"Размерность: {len(parameters_names)}", style={'color': '#212121'}),
            html.P(f"Количество параметров: непрерывные = {len(float_parameters_names)},\
                дискретные = {len(discrete_parameters_names)}", style={'color': '#212121'}),
            html.P(f"Количество функционалов: целевые функции (критерии) = 1, ограничения = {functional_count - 1}",
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
        ], style={'width': '55%', "background-color": "#FFFFFF", "border": "20px solid #FFFFFF"})

def render_parameters_description(parameter_eps, parameter_r, parameter_iters_limit, parameter_start_point):
    return html.Div(children=[
        html.H2('ПАРАМЕТРЫ МЕТОДА ОПТИМИЗАЦИИ',
                style={'textAlign': 'left'}),
        html.Br(),
        html.P(f"Заданная точность решения: eps = {parameter_eps}",
                style={'color': '#212121'}),
        html.P(f"Параметр надежности: r = {parameter_r}",
                style={'color': '#212121'}),
        html.P(f"Ограничение на количество итераций: iters_limit = {parameter_iters_limit}",
                style={'color': '#212121'}),
        html.P(f"Стартовая точка: start_point = {parameter_start_point}",
                style={'color': '#212121'}),
    ], style={'width': '45%', "background-color": "#FFFFFF", "border": "20px solid #FFFFFF"})

def render_solution_description(best_value, best_float_point_dictionary, best_discrete_point_dictionary,
                                best_trial_number, accuracy,
                                trial_number, global_iter_number, local_iter_number):
    return html.Div(children=[
        html.H2('НАЙДЕННОЕ РЕШЕНИЕ', style={'textAlign': 'left'}),
        html.P(f"{round(best_value, 6)}", style={'font-size': '2.0em', 'color': 'black'}),
        html.P(f"Лучшая точка: {best_float_point_dictionary}, {best_discrete_point_dictionary}",
            style={'color': '#212121'}),
        html.P(f'Номер лучшего испытания: {best_trial_number}', style={'color': '#212121'}),
        html.P(f"Достигнутая точность: {round(accuracy, 6)}", style={'color': '#212121'}),
        html.P([f"Общее число испытаний: {trial_number}", html.Br(), f"(кол-во итераций глобального метода - {global_iter_number},\
            кол-во итераций локального метода - {local_iter_number})"], style={'color': '#212121'}),
        
        html.P("*[c] - непрерывные параметры, [d] - дискретные параметры",
            style={'color': '#212121', 'font-size': '0.8em'}),
    ], style={'width': '45%', "background-color": "#FFFFFF", "border": "20px solid #FFFFFF"})

def render_optimization_time(solve_time, dfSDI_original, optimization_time, current_color):
    return html.Div(children=[
        html.H2('Время оптимизации', style={'textAlign': 'left'}),
        html.P(f"Общее время оптимизации: {round(solve_time, 3)} сек.", style={'color': '#212121'}),
        html.Div(children=[
            dcc.Graph(
                figure={
                    "data": [{
                        "x": dfSDI_original['trial'],
                        "y": optimization_time,
                        'type': 'lines',
                        'marker': {'color': current_color}
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

def render_iteration_characteristic(dfSDI, functional_count, current_color):
    return html.Div([
        html.H2('Обновление лучшего значения целевой функции', style={'textAlign': 'left'}),
        html.Div(children=[
            html.Div(children=[
                dcc.Graph(
                    figure=((px.scatter(
                        dfSDI.loc[dfSDI['index'].values == functional_count - 1],
                        x='trial',
                        y='objective_func',
                        color_discrete_sequence=[current_color],
                        marginal_y="histogram",
                        trendline="expanding",
                        trendline_options={'function': 'min'})).update_layout(
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
