from __future__ import annotations
from dash import html, dcc
import dash

def main_nav(active_path: str = "/") -> html.Div:
    """
    Construye un menú superior con las páginas registradas.
    La página 'standings' será la Home en "/".
    """
    pages = sorted(dash.page_registry.values(), key=lambda p: p.get("order", 100))
    links = []
    for p in pages:
        href = p["path"]
        label = p.get("name", p["module"].split(".")[-1].capitalize())
        is_active = (href == active_path)
        links.append(
            dcc.Link(
                label,
                href=href,
                className=f"nav-link{' active' if is_active else ''}"
            )
        )

    return html.Div(
        className="topbar",
        children=[
            html.Div("⚽ FIFTH REFEREE", className="brand"),
            html.Div(links, className="nav-links")
        ]
    )
