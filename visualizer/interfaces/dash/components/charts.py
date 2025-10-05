from __future__ import annotations
from typing import Optional
import plotly.express as px
import pandas as pd
import plotly.io as pio

pio.templates.default = "plotly_dark"

def bar(df: pd.DataFrame, x: str, y: str, title: str) -> "plotly.graph_objs._figure.Figure":
    fig = px.bar(df, x=x, y=y, title=title)
    fig.update_layout(
        margin=dict(t=60, r=20, l=20, b=60),
        legend_title_text="",
        xaxis_tickangle=-45
    )
    fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y}<extra></extra>")
    return fig
