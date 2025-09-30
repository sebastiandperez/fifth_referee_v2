"""
Fifth Referee - Main Application Runner
Run this file to start both the API server and Dash analytics dashboard
"""
from __future__ import annotations

import os
import sys
import time
import socket
import threading
import urllib.request
import webbrowser
from pathlib import Path

# -----------------------------------------------------------------------------
# Config (override con variables de entorno)
# -----------------------------------------------------------------------------
HOST         = os.getenv("FR_HOST", "127.0.0.1")
API_PORT     = int(os.getenv("FR_API_PORT", "8000"))
DASH_PORT    = int(os.getenv("FR_DASH_PORT", "8050"))
OPEN_BROWSER = os.getenv("FR_OPEN_BROWSER", "true").lower() in ("1", "true", "yes")

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# -----------------------------------------------------------------------------
# Utils
# -----------------------------------------------------------------------------
def _port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0

def _wait_until_up(url: str, timeout_s: int = 20) -> bool:
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            with urllib.request.urlopen(url, timeout=1.0):
                return True
        except Exception:
            time.sleep(0.4)
    return False

def is_reloader_child() -> bool:
    """Cuando el reloader de Werkzeug está activo, el proceso 'real' expone WERKZEUG_RUN_MAIN='true'."""
    return os.environ.get("WERKZEUG_RUN_MAIN") == "true"

def print_banner():
    # Muestra banner solo una vez: si hay reloader, solo en el child; si no, siempre.
    if os.environ.get("WERKZEUG_RUN_MAIN") not in (None, "true"):
        return
    if os.environ.get("WERKZEUG_RUN_MAIN") is None or is_reloader_child():
        print("=" * 60)
        print("⚽ FIFTH REFEREE - Analytics Platform")
        print("=" * 60)
        print()
        print("✅ All required packages found!")
        print()
        print("🎯 Starting services...")
        print(f"   📡 FastAPI Server: http://{HOST}:{API_PORT}")
        print(f"   📊 Dash Dashboard: http://{HOST}:{DASH_PORT}")
        print(f"   📚 API Docs: http://{HOST}:{API_PORT}/docs")
        print()
        print("🛑 Press Ctrl+C to stop both services")
        print("=" * 60)

def _open_browser_once(url: str):
    """Abre navegador solo una vez (espera a que el servicio esté arriba)."""
    if not OPEN_BROWSER:
        return
    # Si hay reloader de Werkzeug (Dash debug=True), abre solo en el child.
    if os.environ.get("WERKZEUG_RUN_MAIN") in ("true", None):
        if _wait_until_up(url, timeout_s=20):
            try:
                webbrowser.open(url)
            except Exception:
                pass

# -----------------------------------------------------------------------------
# Imports tolerantes
# -----------------------------------------------------------------------------

def _import_api_app():
    import importlib

    # === API ===
    tried_api = []
    for modpath in ("api",):  # <- sólo root/api/__init__.py
        try:
            module = importlib.import_module(modpath)
            api_obj = getattr(module, "api", None)
            if api_obj is not None:
                break
        except Exception as e:
            tried_api.append((modpath, repr(e)))
            api_obj = None
    if api_obj is None:
        raise ImportError(
            "No pude importar la instancia FastAPI `api` desde: api.\n"
            f"Intentos: {tried_api}\n"
            "➡️ Asegúrate de tener `api/__init__.py` con `api = FastAPI(...)`."
        )

    # === Dash ===
    tried_dash = []
    for modpath in ("interfaces.dash_app", "app"):
        try:
            module = importlib.import_module(modpath)
            dash_app = getattr(module, "app", None)
            if dash_app is not None:
                break
        except Exception as e:
            tried_dash.append((modpath, repr(e)))
            dash_app = None
    if dash_app is None:
        raise ImportError(
            "No pude importar la instancia Dash `app` desde: interfaces.dash_app | app.\n"
            f"Intentos: {tried_dash}\n"
            "➡️ Ten `interfaces/dash_app.py` (recomendado) o `app.py` en root con `app = dash.Dash(...)`."
        )

    return api_obj, dash_app

# -----------------------------------------------------------------------------
# Servers
# -----------------------------------------------------------------------------
def run_api_server(reload: bool = False):
    """Run the FastAPI server."""
    try:
        import uvicorn
        from uvicorn import Config, Server

        api_obj, _ = _import_api_app()
        print("🚀 Starting FastAPI server...")

        if reload:
            # En modo solo-API se permite el reload administrado por uvicorn
            uvicorn.run(api_obj, host=HOST, port=API_PORT, reload=True, log_level="info")
            return

        # En hilo → usar Server y deshabilitar signal handlers
        config = Config(app=api_obj, host=HOST, port=API_PORT, reload=False, log_level="info")
        server = Server(config)
        if hasattr(server, "install_signal_handlers"):
            server.install_signal_handlers = lambda: None
        server.run()

    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        print("💡 Make sure uvicorn is installed: pip install uvicorn")

def run_dash_app(debug: bool = False, use_reloader: bool = False):
    """Run the Dash analytics dashboard."""
    try:
        # Si corremos ambos, esperar a que la API responda
        if not debug:
            ok = _wait_until_up(f"http://{HOST}:{API_PORT}/docs", timeout_s=20)
            if not ok:
                print("⚠️  API no respondió a tiempo; el dashboard puede mostrar errores al inicio.")

        _, dash_app = _import_api_app()
        url = f"http://{HOST}:{DASH_PORT}"
        print("📊 Starting Dash analytics dashboard...")
        print(f"🌐 Dashboard will be available at: {url}")

        if OPEN_BROWSER:
            threading.Thread(target=_open_browser_once, args=(url,), daemon=True).start()

        # Importante: cuando corremos API + Dash juntos, NO usar reloader aquí.
        dash_app.run(
            debug=debug,
            port=DASH_PORT,
            host=HOST,
            use_reloader=use_reloader,
        )

    except Exception as e:
        print(f"❌ Error starting Dash app: {e}")
        print("💡 Make sure required packages are installed:")
        print("   pip install dash plotly pandas requests numpy")

# -----------------------------------------------------------------------------
# Entry points
# -----------------------------------------------------------------------------
def main():
    """
    Arranca API y Dash juntos SIN reloaders internos (evita doble ejecución).
    Usa un reloader externo (tu IDE) si lo necesitas para el proyecto completo.
    """
    # Comprobación de dependencias básica
    required = ['uvicorn', 'fastapi', 'dash', 'plotly', 'pandas', 'requests', 'numpy']
    missing = []
    for mod in required:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        print("❌ Missing required packages:")
        for m in missing:
            print(f"   - {m}")
        print(f"\n💡 Install with: pip install {' '.join(missing)}")
        return

    # Puertos libres
    if _port_in_use(HOST, API_PORT):
        print(f"❌ Port {API_PORT} busy (API). Cierra el proceso o cambia FR_API_PORT.")
        return
    if _port_in_use(HOST, DASH_PORT):
        print(f"❌ Port {DASH_PORT} busy (Dash). Cierra el proceso o cambia FR_DASH_PORT.")
        return

    print_banner()

    # API en hilo aparte sin reload
    api_thread = threading.Thread(target=run_api_server, kwargs={'reload': False}, daemon=True)
    api_thread.start()

    # Dash en hilo principal, sin reloader
    try:
        run_dash_app(debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        print("👋 Goodbye!")

def run_api_only():
    """Run only the FastAPI server (con reload para desarrollo)."""
    print("🚀 Starting FastAPI server only...")
    try:
        run_api_server(reload=True)  # recarga caliente
    except KeyboardInterrupt:
        print("\n🛑 Shutting down API server...")

def run_dash_only():
    """
    Run only the Dash dashboard.
    Con debug=True, Werkzeug activa el reloader. _open_browser_once evita doble apertura.
    """
    print("📊 Starting Dash dashboard only...")
    try:
        run_dash_app(debug=True, use_reloader=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Dash app...")

# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv ) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "api":
            run_api_only()
        elif cmd == "dash":
            run_dash_only()
        elif cmd == "help":
            print("Fifth Referee - Usage:")
            print("  python __init__.py        # Run both API and Dash (no reloaders)")
            print("  python __init__.py api    # Run only API server (reload ON)")
            print("  python __init__.py dash   # Run only Dash app (debug + reloader ON)")
            print("  python __init__.py help   # Show this help")
            print("\nEnv overrides:")
            print("  FR_HOST, FR_API_PORT, FR_DASH_PORT, FR_OPEN_BROWSER")
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use 'python __init__.py help' for usage information")
    else:
        main()
