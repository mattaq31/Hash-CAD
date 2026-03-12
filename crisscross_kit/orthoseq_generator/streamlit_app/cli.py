"""Console entry point for launching the Orthoseq Streamlit app."""

from pathlib import Path
import sys

from streamlit.web.cli import main as streamlit_main


def main():
    app_path = Path(__file__).with_name("orthoseq_app.py")
    sys.argv = ["streamlit", "run", str(app_path)]
    raise SystemExit(streamlit_main())
