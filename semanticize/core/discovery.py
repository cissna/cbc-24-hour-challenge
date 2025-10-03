"""File discovery and ignore pattern handling."""

import os
from pathlib import Path
from typing import List, Set
import pathspec


class FileDiscovery:
    """Handles file discovery and ignore patterns."""

    DEFAULT_IGNORE_PATTERNS = [
        # Version control
        '.git/', '.svn/', '.hg/',
        # Python
        '__pycache__/', '*.pyc', '*.pyo', '*.pyd', '.Python',
        'build/', 'develop-eggs/', 'dist/', 'downloads/', 'eggs/', '.eggs/',
        'lib/', 'lib64/', 'parts/', 'sdist/', 'var/', 'wheels/',
        '*.egg-info/', '.installed.cfg', '*.egg',
        'venv/', 'env/', 'ENV/', '.venv/',
        # Node
        'node_modules/', 'npm-debug.log', 'yarn-error.log',
        # IDE
        '.idea/', '.vscode/', '*.swp', '*.swo', '*~',
        # OS
        '.DS_Store', 'Thumbs.db',
        # Build outputs
        '*.so', '*.dylib', '*.dll', '*.o', '*.a',
        # Media and binary
        '*.jpg', '*.jpeg', '*.png', '*.gif', '*.ico', '*.svg',
        '*.mp4', '*.avi', '*.mov', '*.mp3', '*.wav',
        '*.pdf', '*.zip', '*.tar.gz', '*.rar',
        # Semanticize
        '.semanticize/',
    ]

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ignore_patterns = self._load_ignore_patterns()

    def _load_ignore_patterns(self) -> pathspec.PathSpec:
        """Load ignore patterns from .gitignore and .semanticizeignore."""
        patterns = self.DEFAULT_IGNORE_PATTERNS.copy()

        # Load .gitignore
        gitignore_path = self.project_root / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                patterns.extend([line.strip() for line in f if line.strip() and not line.startswith('#')])

        # Load .semanticizeignore
        semanticize_ignore = self.project_root / '.semanticize' / '.semanticizeignore'
        if semanticize_ignore.exists():
            with open(semanticize_ignore, 'r') as f:
                patterns.extend([line.strip() for line in f if line.strip() and not line.startswith('#')])

        return pathspec.PathSpec.from_lines('gitwildmatch', patterns)

    def discover_files(self) -> List[Path]:
        """Discover all code files in the project."""
        files = []

        for root, dirs, filenames in os.walk(self.project_root):
            # Convert to relative path for matching
            rel_root = Path(root).relative_to(self.project_root)

            # Filter directories
            dirs[:] = [d for d in dirs if not self.ignore_patterns.match_file(str(rel_root / d) + '/')]

            # Filter files
            for filename in filenames:
                rel_path = rel_root / filename
                if not self.ignore_patterns.match_file(str(rel_path)):
                    abs_path = self.project_root / rel_path
                    # Only include text files (simple heuristic: check if it's a code file)
                    if self._is_code_file(abs_path):
                        files.append(rel_path)

        return sorted(files)

    def _is_code_file(self, file_path: Path) -> bool:
        """Determine if a file is a code file worth analyzing."""
        # Common code file extensions
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
            '.sql', '.sh', '.bash', '.zsh', '.yaml', '.yml', '.json', '.xml',
            '.html', '.css', '.scss', '.sass', '.md', '.txt', '.toml', '.ini',
            '.R', '.m', '.jl', '.lua', '.vim', '.el',
        }

        if file_path.suffix.lower() in code_extensions:
            return True

        # Check if it's a text file by trying to read it
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)
            return True
        except (UnicodeDecodeError, PermissionError):
            return False

    def add_ignore_pattern(self, pattern: str):
        """Add a pattern to .semanticizeignore."""
        semanticize_dir = self.project_root / '.semanticize'
        semanticize_dir.mkdir(exist_ok=True)

        ignore_file = semanticize_dir / '.semanticizeignore'
        with open(ignore_file, 'a') as f:
            f.write(f"{pattern}\n")

        # Reload patterns
        self.ignore_patterns = self._load_ignore_patterns()

    def count_lines(self, file_path: Path) -> int:
        """Count lines in a file."""
        try:
            with open(self.project_root / file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0
