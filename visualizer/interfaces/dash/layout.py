# interfaces/dash/layout.py
from __future__ import annotations
from typing import List
import dash
from dash import html, dcc, Input, Output, callback

# ------------------------------------------------------------
# Helpers de navegación (navbar)
# ------------------------------------------------------------
def _nav_link(label: str, href: str, active: bool) -> html.Div:
    """Link de navegación con clase 'active' si coincide la ruta actual."""
    return dcc.Link(
        label,
        href=href,
        className=f"nav-link{' active' if active else ''}",
    )

def _build_nav(active_path: str = "/") -> html.Div:
    """
    Construye el menú superior a partir de las páginas registradas.
    Usa la clave 'order' si la defines al registrar páginas para ordenar el menú.
    """
    pages: List[dict] = sorted(
        dash.page_registry.values(),
        key=lambda p: p.get("order", 100)
    )
    links = []
    for p in pages:
        href = p["path"]
        label = p.get("name", p["module"].split(".")[-1].capitalize())
        links.append(_nav_link(label, href, active=(href == active_path)))

    return html.Div(
        className="topbar",
        children=[
            html.Div("⚽ FIFTH REFEREE", className="brand"),
            html.Div(links, className="nav-links"),
        ],
    )

# ------------------------------------------------------------
# Layout raíz (shell multipágina)
# ------------------------------------------------------------
def make_layout() -> html.Div:
    """
    Shell global:
      - dcc.Location para reaccionar a la URL
      - Navbar (inyectado por callback para marcar ruta activa)
      - Contenedor principal con dash.page_container
      - Stores globales compartidos por las páginas
    """
    return html.Div(
        className="shell",
        children=[
            # URL para routing
            dcc.Location(id="url"),

            # Navbar dinámico (se renderiza vía callback)
            html.Div(id="topbar-wrap"),

            # Contenido de página
            html.Div(className="content container", children=[dash.page_container]),

            # Stores globales (no repetir en cada página)
            dcc.Store(id="season-id"),
            dcc.Store(id="standings-cache"),
            dcc.Store(id="analytics-cache"),
        ],
    )

# ------------------------------------------------------------
# Callback: renderiza el navbar con el link activo
# ------------------------------------------------------------
@callback(
    Output("topbar-wrap", "children"),
    Input("url", "pathname"),
    prevent_initial_call=False,
)
def _render_topbar(pathname: str | None):
    """Reconstruye el navbar cuando cambia la ruta."""
    return _build_nav(active_path=(pathname or "/"))
