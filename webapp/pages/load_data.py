import base64
import csv


from dash import callback, dash_table, dcc, html, Input, Output, State
import dash
import dash_bootstrap_components as dbc
import requests


from wikiscrapper.helpers import DEFAULT_DURATION, DEFAULT_LANGS
from wikiscrapper.WikiQuery import WikiQuery


dash.register_page(__name__, path="/")

with open("example_input", "r") as f:
    placeholder = f.read()

controls = dbc.Card(
    [
        dbc.CardBody(
            dbc.Form(
                [
                    html.Legend("Input your Wikipedia pages"),
                    html.Div(
                        [
                            dbc.Label("One link per line", html_for="input_text"),
                            dbc.Textarea(
                                id="input_text",
                                className="mb-2",
                                placeholder=placeholder,
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            dbc.Label("Or, upload a file", html_for="input_file"),
                            dcc.Upload(
                                id="input_file",
                                className="mb-2",
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
                        ]
                    ),
                    html.Div(
                        [
                            dbc.Label("Or, provide a link to a Google Sheet", html_for="input_gsheet"),
                            dbc.Input(
                                id="input_gsheet",
                                className="mb-2",
                                placeholder="https://docs.google.com/spreadsheets/d/ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefgh/edit",
                                type="text",
                            ),
                        ]
                    ),
                    dbc.Collapse(
                        html.Div(
                            [
                                html.Legend("More options"),
                                dbc.Row(
                                    [
                                        dbc.Label("Target languages", html_for="target_languages", width=4),
                                        dbc.Col(
                                            dbc.Input(
                                                id="target_languages",
                                                className="mb-2",
                                                placeholder="Please use shortcodes",
                                                value=",".join(DEFAULT_LANGS),
                                                type="text",
                                            ),
                                            width=8,
                                        ),
                                    ],
                                ),
                                dbc.Row(
                                    [
                                        dbc.Label("Target duration", html_for="target_duration", width=4),
                                        dbc.Col(
                                            dbc.Input(
                                                id="target_duration",
                                                className="mb-2",
                                                placeholder="In days",
                                                value=str(DEFAULT_DURATION),
                                                type="text",
                                            ),
                                            width=8,
                                        ),
                                    ],
                                ),
                            ]
                        ),
                        id="collapse",
                        is_open=False,
                        className="mb-3",
                    ),
                    html.Div(
                        [
                            dbc.Button(
                                "More options",
                                id="collapse-button",
                                className="mb-3 me-2",
                                color="secondary",
                                n_clicks=0,
                            ),
                            dbc.Button(
                                "Submit",
                                id="submit",
                                className="mb-3 me-2",
                                color="primary",
                                n_clicks=0,
                            ),
                        ],
                        className="float-end",
                    ),
                ]
            )
        )
    ]
)

columns = {
    "lang": "Language",
    "title": "Title",
}

results = dbc.Card(
    [
        dbc.CardBody(
            dash_table.DataTable(
                id="datatable",
                data=None,  # Dynamic
                columns=[{"name": v, "id": k} for k, v in columns.items()],
                style_cell={
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "maxWidth": 0,
                },
                tooltip_data=None,  # Dynamic
                tooltip_duration=None,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                row_selectable="multi",
                selected_columns=[],
                selected_rows=[],
                page_action="native",
                page_current=0,
                page_size=10,
            )
        ),
        dbc.CardFooter(
            [
                html.Div(
                    [
                        dbc.Progress(id="progress", animated=True, striped=True),
                        html.P(id="result"),
                    ],
                    id="loading",
                ),
                html.Div(
                    [
                        html.A(dbc.Button("Global dashboard", size="lg", className="me-1"), href="dashboard"),
                        html.A(dbc.Button("Article dashboard", size="lg", className="me-1"), href="individual"),
                        # dbc.Button("Download resulting query", id="queries-dl", size="lg", className="me-1"),
                    ],
                    id="buttons",
                    className="float-end",
                ),
            ]
        ),
    ]
)

layout = html.Div(
    [
        dbc.Row([dbc.Col(controls, md=4), dbc.Col(results, md=8)]),
    ]
)


@callback(
    Output("collapse", "is_open"),
    [Input("collapse-button", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output("data", "data"),
    Output("submit", "n_clicks"),
    Input("submit", "n_clicks"),
    Input("input_text", "value"),
    Input("input_file", "contents"),
    Input("input_gsheet", "value"),
    State("input_file", "filename"),
    State("input_file", "last_modified"),
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
def process_input(
    set_progress,
    n,
    input_text,
    input_file_content,
    input_gsheet,
    input_file_name,
    input_file_date,
):
    if n is not None and n > 0:
        if input_text is not None:
            target_links = input_text.split("\n")
        elif input_file_content is not None:
            content_type, content_string = input_file_content.split(",")
            target_links = base64.b64decode(content_string).decode().replace("\r", "").split("\n")
        elif input_gsheet is not None:
            csv_url = input_gsheet.replace("edit", "export?format=csv")

            res = requests.get(url=csv_url)
            if res.status_code != 200:
                return None, None
            else:
                res.encoding = res.apparent_encoding  # So that we get properly encoded results
                target_links = [link[0] for link in csv.reader(res.text.strip().split("\n"))]
        else:
            target_links = None

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

        set_progress(
            (
                total_todo,
                total_todo,
                "100 %",
                "Done!",
            )
        )

        res = query.export_json()
        return res, 0
    else:
        return None, 0
