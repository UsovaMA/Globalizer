import dash_bootstrap_components as dbc
import dash_daq as daq
from dash import dcc, html


def create_sidebar(color_scale_names, logo_url):
    """Create the dashboard navigation bar and global controls.

    Args:
        color_scale_names: Available color-scale names for the theme selector.

    Returns:
        A Dash component containing navigation links and dashboard controls.
    """
    return dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand(
                html.Img(
                    src=logo_url,
                    alt='GlobalizerLogo',
                    height='90px',
                )
            ),
            dbc.Nav(
                [
                    dbc.NavLink("Решение", href="/", active="exact"),
                    dbc.NavLink("Аналитика", href="/analytics", active="exact"),
                    dbc.NavLink("Архив", href="/archive", active="exact"),
                    dbc.NavItem(
                        dbc.NavLink(
                            "Документация",
                            href=(
                                "https://globalizer-documentation."
                                "readthedocs.io/en/latest/"
                            ),
                        ),
                        className="ms-auto",
                    ),
                    dbc.NavLink(
                        "Github",
                        href="https://github.com/OptimLLab/Globalizer",
                    ),
                    dbc.NavItem(
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.P(
                                            "Отфильтровать выбросы",
                                            style={
                                                'color': '#989898',
                                                'font-size': '0.8em',
                                                'margin-bottom': '0',
                                            },
                                        ),
                                        daq.BooleanSwitch(
                                            id='elimination-of-emissions',
                                            on=False,
                                            color='red',
                                        ),
                                    ],
                                    style={
                                        'display': 'flex',
                                        'flex-direction': 'column',
                                        'align-items': 'center',
                                    },
                                ),
                                html.Div(
                                    [
                                        html.P(
                                            "Цветосхема",
                                            style={
                                                'color': '#989898',
                                                'font-size': '0.8em',
                                                'margin-bottom': '0',
                                            },
                                        ),
                                        dcc.Dropdown(
                                            options=color_scale_names,
                                            value="Ice",
                                            id='color-theme',
                                            clearable=False,
                                            style={'width': '120px'},
                                        ),
                                    ],
                                    style={
                                        'display': 'flex',
                                        'flex-direction': 'column',
                                        'align-items': 'center',
                                    },
                                ),
                            ],
                            style={
                                'display': 'flex',
                                'align-items': 'center',
                                'gap': '15px',
                            },
                        )
                    ),
                ],
                navbar=True,
                className="w-100 justify-content-start",
            ),
        ]),
        sticky="bottom",
        color="primary",
        dark=True,
        className="py-2 align-items-center",
    )
