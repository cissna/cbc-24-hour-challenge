"""Launch command implementation."""

from pathlib import Path
import webbrowser
import threading
import time

from ..viewer.server import create_app


def run(project_root: Path, port: int = 8080):
    """Run the launch command."""
    semanticize_dir = project_root / '.semanticize'
    if not semanticize_dir.exists():
        print("Error: Not a Semanticize project. Run 'semanticize init' first.")
        return

    app = create_app(project_root)

    # Open browser after a short delay
    def open_browser():
        time.sleep(1)
        webbrowser.open(f'http://localhost:{port}')

    threading.Thread(target=open_browser, daemon=True).start()

    print(f"Starting Semanticize viewer at http://localhost:{port}")
    print("Press Ctrl+C to stop")

    app.run(host='localhost', port=port, debug=False)
