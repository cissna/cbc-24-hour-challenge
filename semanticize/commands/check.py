"""Check command implementation."""

from pathlib import Path
import sys

from ..core.storage import Storage


def run(project_root: Path):
    """Run the check command."""
    semanticize_dir = project_root / '.semanticize'
    if not semanticize_dir.exists():
        print("Error: Not a Semanticize project. Run 'semanticize init' first.")
        sys.exit(1)

    storage = Storage(project_root)
    inconsistencies = storage.get_inconsistencies()

    if inconsistencies:
        print("⚠ Inconsistencies detected:\n")
        print(inconsistencies)
        print(f"\nFull details in {storage.get_inconsistencies_path()}")
        sys.exit(1)
    else:
        print("✓ No inconsistencies detected")
        sys.exit(0)
