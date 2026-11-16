"""Public Streamlit Cloud entrypoint: synthetic fixtures only, no file uploads.

Use dashboard/app.py for locally authorized merchant CSV uploads.
"""
import os
import runpy
from pathlib import Path

os.environ["OPENCLAW_PUBLIC_DEMO"] = "1"
runpy.run_path(str(Path(__file__).with_name("app.py")), run_name="__main__")
