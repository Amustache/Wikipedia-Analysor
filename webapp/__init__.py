import os


from dash import Dash, dcc, DiskcacheManager, html
import dash
import dash_bootstrap_components as dbc


# Cache for background callback
if "REDIS_URL" in os.environ:
    # Use Redis & Celery if REDIS_URL set as an env variable
    from celery import Celery

    celery_app = Celery(__name__, broker=os.environ["REDIS_URL"], backend=os.environ["REDIS_URL"])
    background_callback_manager = CeleryManager(celery_app)
else:
    # Diskcache for non-production apps when developing locally
    import diskcache

    cache = diskcache.Cache("./cache")
    background_callback_manager = DiskcacheManager(cache)

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    use_pages=True,
    suppress_callback_exceptions=True,
    background_callback_manager=background_callback_manager,
)

app.layout = dbc.Container(
    [
        dcc.Store(id="data", storage_type="session"),
        dcc.Location(id="url", refresh=True),
        dcc.Download(id="download"),
        # Header
        html.Center(html.A(html.H1("Wikipedia Analysor"), href="/")),
        html.Hr(),
        dbc.Alert(
            children="",
            id="alert",
            color="warning",
            is_open=False,
            duration=4000,
        ),
        dash.page_container,
        # Footer
        html.Hr(),
        html.Center(
            html.P(
                [
                    "Made with ❤️, available on ",
                    html.A("GitHub", href="https://github.com/Amustache/Wikipedia-Analysor", target="_blank"),
                ]
            )
        ),
    ],
    fluid=True,
)

# Debug
if __name__ == "__main__":
    app.run(debug=True)
