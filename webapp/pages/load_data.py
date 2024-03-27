import base64
import csv
import json
import os


from dash import callback, dcc, html, Input, Output, State
import dash
import dash_bootstrap_components as dbc
import requests


from wikiscrapper.WikiQuery import WikiQuery


dash.register_page(__name__, path="/")

with open("example_input", "r") as f:
    placeholder = f.read()

layout = dbc.Container(
    [
        html.H2("Input your Wikipedia pages"),
        html.P("Can be either a full link, or a page name. One article per row."),
        html.Br(),
        # Text input
        html.H3("Copy-paste your inputs"),
        dbc.Form(
            [
                dbc.Textarea(
                    id="input_text",
                    className="mb-3",
                    placeholder=placeholder,
                ),
                dbc.Button("Submit", id="submit_text", color="primary"),
            ]
        ),
        html.Br(),
        # File input
        html.H3("Or, upload a file"),
        dcc.Upload(
            id="input_file",
            children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
            },
            # Allow multiple files to be uploaded
            multiple=False,
        ),
        html.Div(id="output-data-upload"),
        html.Br(),
        # GSheet input
        html.H3("Or, provide a link to a Google Sheet"),
        dbc.Form(
            [
                dbc.Input(
                    id="input_gsheet",
                    className="mb-3",
                    placeholder="https://docs.google.com/spreadsheets/d/ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefgh/edit",
                    type="text",
                ),
                dbc.Button("Submit", id="submit_gsheet", color="primary"),
            ]
        ),
        html.Br(),
        html.Div(
            html.Center(
                [
                    dbc.Progress(id="progress", animated=True, striped=True),
                    html.P(id="result"),
                    html.Hr(),
                    html.Div(
                        [
                            html.A(dbc.Button("Global dashboard", size="lg", className="me-1"), href="dashboard"),
                            html.A(dbc.Button("Article dashboard", size="lg", className="me-1"), href="individual"),
                            dbc.Button("Download resulting query", id="queries-dl", size="lg", className="me-1"),
                        ]
                    ),
                ]
            )
        ),
    ]
)


@callback(
    Output("data", "data"),
    Input("submit_text", "n_clicks"),
    Input("input_text", "value"),
    background=True,
    running=[
        (
            Output("progress", "style"),
            {"visibility": "visible"},
            {"visibility": "hidden"},
        ),
    ],
    cancel=[],
    progress=[
        Output("progress", "value"),
        Output("progress", "max"),
        Output("progress", "label"),
        Output("result", "children"),
    ],
    prevent_initial_call=True,
)
def process_text(set_progress, n, value):
    if n is not None:
        target_links = value.split("\n")

        query = WikiQuery(target_links)
        gen, expected = query.update(gen=True)
        total_todo = len(expected)

        for i, todo in enumerate(gen):
            set_progress(
                (
                    i,
                    total_todo,
                    f"{int(100 * i // total_todo)} %",
                    f"Current action: {'/'.join(todo)}",
                )
            )

        print("Done with processing text")

        set_progress(
            (
                total_todo,
                total_todo,
                "100 %",
                "Done!",
            )
        )

        res = query.export_json()
        return res
    else:
        return None


@callback(
    Output("data", "data", allow_duplicate=True),
    Input("input_file", "contents"),
    State("input_file", "filename"),
    State("input_file", "last_modified"),
    prevent_initial_call="initial_duplicate",
)
def process_file(content, name, date):
    if content is not None:
        content_type, content_string = content.split(",")
        target_links = base64.b64decode(content_string).decode().replace("\r", "").split("\n")

        query = WikiQuery(target_links)
        gen, expected = query.update(gen=True)

        for todo in gen:
            print(todo)  # Feedback

        print("Done with processing file")
        res = query.export_json()
        return res
    else:
        return None


@callback(
    Output("data", "data", allow_duplicate=True),
    Input("submit_gsheet", "n_clicks"),
    Input("input_gsheet", "value"),
    prevent_initial_call="initial_duplicate",
)
def process_gsheet(n, value):
    if n is not None:
        csv_url = value.replace("edit", "export?format=csv")

        res = requests.get(url=csv_url)
        if res.status_code != 200:
            return None, None
        else:
            res.encoding = res.apparent_encoding  # So that we get properly encoded results
            target_links = [link[0] for link in csv.reader(res.text.strip().split("\n"))]

        query = WikiQuery(target_links)
        gen, expected = query.update(gen=True)

        for todo in gen:
            print(todo)  # Feedback

        print("Done with processing gsheet")
        res = query.export_json()
        return res
    else:
        return None
