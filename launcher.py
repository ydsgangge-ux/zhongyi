import subprocess
import sys
import os
import signal
import time
import webbrowser
import threading
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend")
VENV = os.path.join(BACKEND, "venv")
NODE_MODULES = os.path.join(FRONTEND, "node_modules")
CONFIG_FILE = os.path.join(BACKEND, "data", "config.json")
DIST_DIR = os.path.join(FRONTEND, "dist")

PORT = 5328

is_windows = sys.platform.startswith("win")

if is_windows:
    VENV_PYTHON = os.path.join(VENV, "Scripts", "python.exe")
    VENV_PIP = os.path.join(VENV, "Scripts", "pip.exe")
    VENV_ACTIVATE = os.path.join(VENV, "Scripts", "activate")
else:
    VENV_PYTHON = os.path.join(VENV, "bin", "python")
    VENV_PIP = os.path.join(VENV, "bin", "pip")
    VENV_ACTIVATE = os.path.join(VENV, "bin", "activate")

processes = []


def check_command(cmd):
    found = shutil.which(cmd)
    return found is not None


def setup_backend():
    if not os.path.exists(VENV):
        print("[INFO] Creating Python virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", VENV], check=True)

    req_file = os.path.join(BACKEND, "requirements.txt")
    if os.path.exists(req_file):
        print("[INFO] Checking backend dependencies...")
        subprocess.run([VENV_PIP, "install", "-r", req_file], check=True)


def build_frontend():
    if not os.path.exists(NODE_MODULES):
        print("[INFO] Installing frontend dependencies...")
        subprocess.run(
            ["npm", "install"],
            cwd=FRONTEND,
            shell=is_windows,
            check=True,
        )

    if not os.path.exists(DIST_DIR) or not os.listdir(DIST_DIR):
        print("[INFO] Building frontend...")
        subprocess.run(
            ["npm", "run", "build"],
            cwd=FRONTEND,
            shell=is_windows,
            check=True,
        )
    else:
        print("[INFO] Frontend already built.")


def start_backend():
    print(f"[INFO] Starting server (port {PORT})...")
    env = os.environ.copy()
    if is_windows:
        env["PATH"] = os.path.join(VENV, "Scripts") + ";" + env.get("PATH", "")
    else:
        env["PATH"] = os.path.join(VENV, "bin") + ":" + env.get("PATH", "")

    p = subprocess.Popen(
        [VENV_PYTHON, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(PORT)],
        cwd=BACKEND,
        env=env,
    )
    processes.append(p)
    return p


def open_browser():
    time.sleep(3)
    print(f"[INFO] Opening browser...")
    webbrowser.open(f"http://localhost:{PORT}")


def cleanup(signum=None, frame=None):
    print("\n[INFO] Shutting down...")
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=5)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    print("[INFO] All services stopped.")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("=" * 44)
    print("   TCM AI Health Advisor - Quick Start")
    print("=" * 44)
    print()

    if not check_command("python"):
        print("[ERROR] Python not found. Please install Python 3.11+")
        print("       Install: https://python.org/downloads/")
        input("Press Enter to exit...")
        sys.exit(1)

    if not check_command("node"):
        print("[ERROR] Node.js not found. Please install Node.js 18+")
        print("       Install: https://nodejs.org/")
        input("Press Enter to exit...")
        sys.exit(1)

    setup_backend()
    build_frontend()

    if not os.path.exists(CONFIG_FILE):
        print()
        print("[WARN] No API key configured.")
        print(f"       Visit http://localhost:{PORT}/settings after startup.")
        print()

    print()
    print("=" * 44)
    print("  Starting server...")
    print("=" * 44)
    print()

    start_backend()

    threading.Thread(target=open_browser, daemon=True).start()

    print()
    print("=" * 44)
    print("  Server started!")
    print("=" * 44)
    print()
    print(f"  Web:       http://localhost:{PORT}")
    print(f"  API Docs:  http://localhost:{PORT}/docs")
    print(f"  Settings:  http://localhost:{PORT}/settings")
    print()
    print("  Press Ctrl+C to stop")
    print()

    try:
        while True:
            for p in list(processes):
                ret = p.poll()
                if ret is not None:
                    print(f"[WARN] Process exited with code {ret}. Restarting...")
                    processes.remove(p)
                    start_backend()
            time.sleep(2)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()