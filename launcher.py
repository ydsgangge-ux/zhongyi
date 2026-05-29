import subprocess
import sys
import os
import signal
import time
import webbrowser
import threading

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend")
VENV = os.path.join(BACKEND, "venv")
VENV_PYTHON = os.path.join(VENV, "Scripts", "python.exe")
VENV_PIP = os.path.join(VENV, "Scripts", "pip.exe")
NODE_MODULES = os.path.join(FRONTEND, "node_modules")
CONFIG_FILE = os.path.join(BACKEND, "data", "config.json")
DIST_DIR = os.path.join(FRONTEND, "dist")

processes = []


def check_command(cmd):
    try:
        subprocess.run(
            [cmd, "--version"],
            capture_output=True,
            timeout=10,
        )
        return True
    except Exception:
        return False


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
            shell=True,
            check=True,
        )

    print("[INFO] Building frontend...")
    subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND,
        shell=True,
        check=True,
    )


def start_backend():
    print("[INFO] Starting server (port 5328)...")
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = VENV
    env["PATH"] = os.path.join(VENV, "Scripts") + ";" + env.get("PATH", "")

    p = subprocess.Popen(
        [VENV_PYTHON, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=BACKEND,
        env=env,
    )
    processes.append(p)
    return p


def open_browser():
    time.sleep(3)
    print("[INFO] Opening browser...")
    webbrowser.open("http://localhost:8000")


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
        input("Press Enter to exit...")
        sys.exit(1)

    if not check_command("node"):
        print("[ERROR] Node.js not found. Please install Node.js 18+")
        input("Press Enter to exit...")
        sys.exit(1)

    setup_backend()
    build_frontend()

    if not os.path.exists(CONFIG_FILE):
        print()
        print("[WARN] No config.json found. Please configure API keys first.")
        print("       Visit http://localhost:8000/settings after startup.")
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
    print("  Web:       http://localhost:8000")
    print("  API Docs:  http://localhost:8000/docs")
    print("  Settings:  http://localhost:8000/settings")
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
