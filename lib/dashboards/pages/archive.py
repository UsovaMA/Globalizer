from dash import html

from components.tables import create_dash_table_from_dataframe


def render_archive(df):
    return html.Div(children=[
        html.P("*[c] - непрерывные параметры, [d] - дискретные параметры",
                style={'text-align': 'right', 'color': '#212121', 'font-size': '0.8em'}),
        html.H1('Архив всех испытаний', style={'textAlign': 'left'}),
        html.Div(
            [create_dash_table_from_dataframe(df)],
            style={'maxWidth': '95%', 'maxHeight': '700px', "overflow": "scroll"}
        ),
        html.Div(id='archive_figure', style={'width': '95%'})
    ], style={"background-color": "#FFFFFF", "border": "20px solid #FFFFFF", })
