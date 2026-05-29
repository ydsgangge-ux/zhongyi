import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(backend_dir)
sys.path.insert(0, parent_dir)

from backend.tui.app import TCMApp

if __name__ == "__main__":
    app = TCMApp()
    app.run()
