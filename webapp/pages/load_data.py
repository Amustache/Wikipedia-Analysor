import json

import dash
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc

from get_from_wikipedia import get_from_wikipedia

dash.register_page(__name__, path="/")

layout = dbc.Container([
    html.H2("Input your Wikipedia pages"),
    html.P("Can be either a full link, or a page name. One article per row."),
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
    dbc.Textarea(id="result_query", className="mb-3", placeholder="..."),
    # html.H3("Or, upload a file"),
    # html.H3("Or, provide a link to a Google Sheet"),
])


@callback(
    Output("data", "data"),
    [Input("submit_text", "n_clicks"), Input("input_text", "value")],
)
def process(n, value):
    if n is not None:
        target_links = value.split("\n")
        queries = get_from_wikipedia(target_links)

        # import json
        # with open('webapp/samples/results.json', 'w', encoding='utf8') as f:
        #     json.dump(queries, f, ensure_ascii=False, indent=4)

        return queries

@callback(
    Output("result_query", "value"),
    Output("url", "pathname"),
    Input("data", "data"),
    Input('url', 'pathname')
)
def show_query(data, pathname):
    if data is not None:
        return json.dumps(data, indent=2), "individual"
    else:
        return None, pathname
