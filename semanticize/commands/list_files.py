"""List files command to show what would be discovered."""

from pathlib import Path
from ..core.discovery import FileDiscovery


def run(project_root: Path, show_ignored: bool = False):
    """List files that would be analyzed."""
    discovery = FileDiscovery(project_root)

    print("Discovering files...")
    files = discovery.discover_files()

    print(f"\n{'='*60}")
    print(f"Files that WILL be analyzed: {len(files)}")
    print(f"{'='*60}\n")

    for i, file in enumerate(files, 1):
        print(f"{i:3}. {file}")

    if show_ignored:
        print(f"\n{'='*60}")
        print("Testing ignored patterns...")
        print(f"{'='*60}\n")

        # Show some common patterns and if they're ignored
        test_patterns = [
            '*.json',
            '*.md',
            'package.json',
            'README.md',
            'node_modules/',
            'frontend/public/',
        ]

        for pattern in test_patterns:
            # Create a test file path
            if pattern.endswith('/'):
                test_path = pattern + 'test.txt'
            else:
                test_path = pattern

            matched = discovery.ignore_patterns.match_file(test_path)
            status = "✓ IGNORED" if matched else "✗ INCLUDED"
            print(f"{status:12} {pattern}")

    print(f"\n{'='*60}")
    print(f"Ignore patterns loaded from:")
    print(f"  - Built-in defaults")

    gitignore = project_root / '.gitignore'
    if gitignore.exists():
        print(f"  - .gitignore (exists)")
    else:
        print(f"  - .gitignore (not found)")

    semanticize_ignore = project_root / '.semanticize' / '.semanticizeignore'
    if semanticize_ignore.exists():
        print(f"  - .semanticize/.semanticizeignore (exists)")
        print(f"\n    Contents:")
        with open(semanticize_ignore, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    print(f"      {line}")
    else:
        print(f"  - .semanticize/.semanticizeignore (not found)")

    print(f"{'='*60}\n")
