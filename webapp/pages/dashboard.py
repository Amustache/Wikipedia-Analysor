import json


from dash import callback, dcc, html, Input, Output, State
from plotly import express as px
from plotly import graph_objects as go
import dash
import dash_bootstrap_components as dbc
import pandas as pd


from webapp.helpers import create_main_fig, get_color
from wikiscrapper.helpers import DEFAULT_LANGS


dash.register_page(__name__)

layout = html.Div(
    [
        html.H2("Dashboard"),
        html.Br(),
        dbc.Row(
            [
                html.H3("Top 5 pages"),
                html.P("According to their number of page views."),
                html.Ul([], id="top-names"),
                dbc.Col(
                    [
                        dcc.Dropdown(
                            id="top-langs",
                            options=list(DEFAULT_LANGS),
                            value=list(DEFAULT_LANGS)[0],
                            clearable=False,
                        ),
                        html.Ol(id="debug"),
                        dcc.Graph(id="top-graph"),
                    ]
                ),
            ]
        ),
        html.Center(
            [
                html.A(dbc.Button("Global dashboard", size="lg", className="me-1"), href="dashboard"),
                html.A(dbc.Button("Article dashboard", size="lg", className="me-1"), href="individual"),
            ]
        ),
        # dbc.Row([
        #     html.H3("Total page views"),
        #     html.P("All the pages, all the languages."),
        #     dbc.Col([
        #         dcc.Graph(
        #             id="total-graph"
        #         )
        #     ]),
        # ]),
    ],
)


@callback(
    Output("top-graph", "figure"),
    Output("top-graph", "style"),
    Output("debug", "children"),
    Input("top-langs", "value"),
    State("data", "data"),
)
def update_top5(selected_lang, data):
    tops = []
    for person, content in data.items():
        if "error" in content:
            print("error")
            continue

        for lang, obj in content["langs"].items():
            if lang != selected_lang:
                continue

            if len(tops) < 5:
                tops.append(
                    {
                        "name": obj["name"],
                        "pageviews_total": obj["pageviews_total"],
                        "pageviews_en": obj["pageviews"]["items"],  # "timestamp", "views"
                    }
                )
            else:
                # If last object has less pageview, replace
                if obj["pageviews_total"] > tops[-1]["pageviews_total"]:
                    tops[-1] = {
                        "name": obj["name"],
                        "pageviews_total": obj["pageviews_total"],
                        "pageviews_en": obj["pageviews"]["items"],  # "timestamp", "views"
                    }
            tops = sorted(tops, key=lambda x: x["pageviews_total"])

    tops = list(reversed(tops))
    figs = list()
    for top in tops:
        df = pd.read_json(json.dumps(top["pageviews_en"]))
        fig_line = px.line(df, x="timestamp", y="views", hover_name=len(top["pageviews_en"]) * [top["name"]])
        fig_line.update_traces(line_color=get_color(top["name"]))
        figs.append(fig_line)

    try:
        figs = iter(figs)
        figs_data = next(figs).data
    except StopIteration:  # There is no data
        return go.Figure(), {"display": "none"}  # , None

    for fig in figs:
        figs_data += fig.data

    fig_main = go.Figure(data=figs_data)

    fig, style = create_main_fig(fig_main)

    return (
        fig,
        style,
        [html.Li(f"{top['name']}: {top['pageviews_total']} views") for top in tops],
    )
