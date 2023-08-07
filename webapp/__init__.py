from dash import Dash, html, dcc
import dash
import dash_bootstrap_components as dbc


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], use_pages=True)

app.layout = dbc.Container([
    dcc.Store(id='data', storage_type='session'),
    dcc.Location(id='url', refresh=True),

    # Header
    html.H1("Wikipedia Analysor"),
    html.Hr(),
    dbc.Alert(
        children="",
        id="alert",
        color="warning",
        is_open=False,
        duration=4000,
    ),

    # Debug
    html.Div(
        [
            html.Div(
                dcc.Link(
                    f"{page['name']} - {page['path']}", href=page["relative_path"]
                )
            )
            for page in dash.page_registry.values()
        ]
    ),

    dash.page_container,
])

if __name__ == '__main__':
    app.run(debug=True)
