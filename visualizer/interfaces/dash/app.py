from __future__ import annotations
from pathlib import Path
import dash
import plotly.io as pio
from .layout import make_layout

pio.templates.default = "plotly_dark"

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    title="FIFTH REFEREE",
    assets_folder=str(Path(__file__).parent / "assets")
)

server = app.server
app.layout = make_layout()
