from __future__ import annotations
from typing import Iterable, Tuple
from dash import html

def leader_card(title: str, rows: Iterable[Tuple[str, str, str]]) -> html.Div:
    """
    Renderiza una tarjeta de líder.
    rows: iterable de (rank_str, "Jugador", "Métrica") con team en subtítulo embebido si quieres.
    """
    items = []
    for rank, who, metric in rows:
        items.append(html.Div(className="leader-row", children=[
            html.Span(rank, className="rank"),
            html.Div(className="who", children=[
                html.Div(who.split(" | ")[0], className="pname"),
                html.Div(who.split(" | ")[1] if " | " in who else "—", className="tname"),
            ]),
            html.Span(metric, className="metric"),
        ]))
    return html.Div(className="leader-card leader", children=[
        html.H4(title),
        html.Div(className="leader-list", children=items or html.Div("Sin datos", className="muted"))
    ])
