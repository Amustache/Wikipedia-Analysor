import csv
import json

import dash
import requests
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc

from get_from_wikipedia import get_from_wikipedia

dash.register_page(__name__, path="/")

layout = dbc.Container([
    html.H2("Input your Wikipedia pages"),
    html.P("Can be either a full link, or a page name. One article per row."),
    html.Hr(),

    # Text input
    html.H3("Copy-paste your inputs"),
    dbc.Form([
        dbc.Label("Text input"),
        dbc.Textarea(
            id="input_text",
            className="mb-3",
            placeholder="https://fr.wikipedia.org/wiki/École_polytechnique_fédérale_de_Lausanne\nen.wikipedia.org/wiki/Jean-Pierre_Hubaux\nMichael Grätzel",
        ),
        dbc.Button("Submit", id="submit_text", color="primary"),
        # dbc.Spinner(id="spinner", color="primary"),
    ]),

    html.Hr(),

    # File input
    html.H3("Or, upload a file"),
    html.Img(src="https://media.tenor.com/hTEZeqwOPWgAAAAd/crumb-cat.gif", width=128),

    html.Hr(),

    # GSheet input
    html.H3("Or, provide a link to a Google Sheet"),
    dbc.Form([
        dbc.Label("Google Sheet input"),
        dbc.Input(id="input_gsheet", className="mb-3",
                  placeholder="https://docs.google.com/spreadsheets/d/ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefgh/edit",
                  type="text"),
        dbc.Button("Submit", id="submit_gsheet", color="primary"),
        # dbc.Spinner(id="spinner", color="primary"),
    ]),

    # Result
    html.Div(
        [
            html.Hr(),
            html.H2("Resulting query"),
            dbc.Textarea(
                id="queries-text",
                className="mb-3",
                placeholder="{}",
            ),
            html.Center([
                html.A(dbc.Button("Dashboard", size="lg", className="me-1"), href="dashboard"),
                html.A(dbc.Button("Individual results", size="lg", className="me-1"), href="individual"),
                dbc.Button("Download result", id="queries-dl", size="lg", className="me-1"),
            ]),
        ],
        id="queries",
    ),
])


@callback(
    Output("data", "data"),
    [Input("submit_text", "n_clicks"), Input("input_text", "value")],
)
def process_text(n, value):
    if n is not None:
        print(value)
        target_links = value.split("\n")
        queries = get_from_wikipedia(target_links)
        print("Done with processing text")
        return queries


# @callback(
#     Output("data", "data", allow_duplicate=True),
#     [Input("submit_file", "n_clicks"), Input("input_file", "value")],
#     prevent_initial_call="initial_duplicate",
# )
# def process_file(n, value):
#     if n is not None:
#         target_links = value.split("\n")
#         queries = get_from_wikipedia(target_links)
#
#         return queries


@callback(
    Output("data", "data", allow_duplicate=True),
    [Input("submit_gsheet", "n_clicks"), Input("input_gsheet", "value")],
    prevent_initial_call="initial_duplicate",
)
def process_gsheet(n, value):
    if n is not None:
        csv_url = value.replace("edit", "export?format=csv")

        res = requests.get(url=csv_url)
        if res.status_code != 200:
            return None
        else:
            res.encoding = res.apparent_encoding  # So that we get properly encoded results
            target_links = [link[0] for link in csv.reader(res.text.strip().split('\n'))]
            print(target_links)

        queries = get_from_wikipedia(target_links)
        print("Done with processing gsheet")
        return queries


@callback(
    Output("queries-text", "value"),
    Output("queries", "style"),
    Input("data", "data"),
)
def show_query(data):
    if data is not None:
        return json.dumps(data, indent=2, ensure_ascii=False), {'display': 'inline'}
    else:
        return None, {'display': 'none'}

@callback(
    Output("download", "data"),
    Input("queries-dl", "n_clicks"),
    Input("data", "data"),
    prevent_initial_call=True,
)
def process_gsheet(n, data):
    if n is not None:
        return dict(
            content=json.dumps(data, indent=2, ensure_ascii=False),
            filename=f"queries_{'date'}.json",
            type="application/json",
        )
