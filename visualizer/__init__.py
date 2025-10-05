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
import importlib
import importlib.util

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

def _import_fastapi_app():
    """
    Devuelve la instancia FastAPI `api`.
    1) intenta import por paquete
    2) si falla, carga por ruta de archivo
    """
    tried = []

    # 1) paquete
    for modpath in ("api", "visualizer.api", "interfaces.api"):
        try:
            mod = importlib.import_module(modpath)
            obj = getattr(mod, "api", None)
            if obj is not None:
                return obj
        except Exception as e:
            tried.append((modpath, repr(e)))

    # 2) archivo
    file_candidates = [
        project_root / "api" / "__init__.py",          # api/__init__.py con api=FastAPI
        project_root / "api.py",                       # api.py en root (fallback)
        project_root / "interfaces" / "api.py",        # legacy
    ]
    for path in file_candidates:
        if path.exists():
            try:
                spec = importlib.util.spec_from_file_location("fr_api_mod", str(path))
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                assert spec.loader is not None
                spec.loader.exec_module(mod)
                obj = getattr(mod, "api", None)
                if obj is not None:
                    return obj
                tried.append((str(path), "found module but no attribute 'api'"))
            except Exception as e:
                tried.append((str(path), repr(e)))

    raise ImportError(
        "No pude importar la instancia FastAPI `api`.\n"
        f"Intentos: {tried}\n"
        "➡️ Asegúrate de tener `api/__init__.py` con `api = FastAPI(...)`."
    )


def _import_dash_app():
    """
    Devuelve la instancia Dash `app`.
    1) intenta import por paquete
    2) si falla, carga por ruta de archivo
    """
    tried = []

    # 1) paquete
    for modpath in ("interfaces.dash.app", "interfaces.dash_app", "app"):
        try:
            mod = importlib.import_module(modpath)
            obj = getattr(mod, "app", None)
            if obj is not None:
                return obj
        except Exception as e:
            tried.append((modpath, repr(e)))

    # 2) archivo (tu caso actual: interfaces/dash/app.py)
    file_candidates = [
        project_root / "interfaces" / "dash" / "app.py",
        project_root / "interfaces" / "dash_app.py",   # legacy
        project_root / "app.py",                       # fallback
    ]
    for path in file_candidates:
        if path.exists():
            try:
                spec = importlib.util.spec_from_file_location("fr_dash_app_mod", str(path))
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                assert spec.loader is not None
                spec.loader.exec_module(mod)
                obj = getattr(mod, "app", None)
                if obj is not None:
                    return obj
                tried.append((str(path), "found module but no attribute 'app'"))
            except Exception as e:
                tried.append((str(path), repr(e)))

    raise ImportError(
        "No pude importar la instancia Dash `app`.\n"
        f"Intentos: {tried}\n"
        "➡️ Ten `interfaces/dash/app.py` con `app = dash.Dash(...)`."
    )

# -----------------------------------------------------------------------------
# Servers
# -----------------------------------------------------------------------------
def run_api_server(reload: bool = False):
    try:
        import uvicorn
        from uvicorn import Config, Server

        api_obj = _import_fastapi_app()
        print("🚀 Starting FastAPI server...")

        if reload:
            uvicorn.run(api_obj, host=HOST, port=API_PORT, reload=True, log_level="info")
            return

        config = Config(app=api_obj, host=HOST, port=API_PORT, reload=False, log_level="info")
        server = Server(config)
        if hasattr(server, "install_signal_handlers"):
            server.install_signal_handlers = lambda: None
        server.run()

    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        print("💡 Make sure uvicorn is installed: pip install uvicorn")


def run_dash_app(debug: bool = False, use_reloader: bool = False):
    try:
        if not debug:
            ok = _wait_until_up(f"http://{HOST}:{API_PORT}/docs", timeout_s=20)
            if not ok:
                print("⚠️  API no respondió a tiempo; el dashboard puede mostrar errores al inicio.")

        dash_app = _import_dash_app()
        url = f"http://{HOST}:{DASH_PORT}"
        print("📊 Starting Dash analytics dashboard...")
        print(f"🌐 Dashboard will be available at: {url}")

        if OPEN_BROWSER:
            threading.Thread(target=_open_browser_once, args=(url,), daemon=True).start()

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
