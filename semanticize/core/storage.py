"""Storage layer for markdown documentation files."""

from pathlib import Path
from typing import Optional, List
import os


class Storage:
    """Handles reading and writing markdown documentation files."""

    LEVELS = ['technical', 'developer', 'executive']

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.semanticize_dir = project_root / '.semanticize'
        self.files_dir = self.semanticize_dir / 'files'
        self.edges_dir = self.semanticize_dir / 'edges'

    def initialize(self):
        """Create the .semanticize directory structure."""
        self.semanticize_dir.mkdir(exist_ok=True)
        self.files_dir.mkdir(exist_ok=True)
        self.edges_dir.mkdir(exist_ok=True)

    def get_file_doc_path(self, file_path: Path, level: str) -> Path:
        """Get the path to a file's documentation."""
        # Mirror the directory structure
        doc_path = self.files_dir / file_path.parent
        doc_path.mkdir(parents=True, exist_ok=True)
        return doc_path / f"{file_path.name}.{level}.md"

    def get_edge_doc_path(self, source: Path, target: Path, level: str) -> Path:
        """Get the path to an edge's documentation."""
        # Convert paths to safe filenames
        source_str = str(source).replace('/', '.')
        target_str = str(target).replace('/', '.')
        edge_name = f"{source_str}--TO--{target_str}.{level}.md"
        return self.edges_dir / edge_name

    def get_project_doc_path(self, level: str) -> Path:
        """Get the path to project-level documentation."""
        return self.semanticize_dir / f"description.{level}.md"

    def get_inconsistencies_path(self) -> Path:
        """Get the path to the inconsistencies file."""
        return self.semanticize_dir / "inconsistencies.md"

    def write_file_doc(self, file_path: Path, level: str, content: str):
        """Write documentation for a file."""
        doc_path = self.get_file_doc_path(file_path, level)
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def write_edge_doc(self, source: Path, target: Path, level: str, content: str):
        """Write documentation for an edge."""
        doc_path = self.get_edge_doc_path(source, target, level)
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def write_project_doc(self, level: str, content: str):
        """Write project-level documentation."""
        doc_path = self.get_project_doc_path(level)
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def read_file_doc(self, file_path: Path, level: str) -> Optional[str]:
        """Read documentation for a file."""
        doc_path = self.get_file_doc_path(file_path, level)
        if doc_path.exists():
            with open(doc_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def read_edge_doc(self, source: Path, target: Path, level: str) -> Optional[str]:
        """Read documentation for an edge."""
        doc_path = self.get_edge_doc_path(source, target, level)
        if doc_path.exists():
            with open(doc_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def read_project_doc(self, level: str) -> Optional[str]:
        """Read project-level documentation."""
        doc_path = self.get_project_doc_path(level)
        if doc_path.exists():
            with open(doc_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def file_doc_exists(self, file_path: Path, level: str) -> bool:
        """Check if documentation exists for a file."""
        return self.get_file_doc_path(file_path, level).exists()

    def edge_doc_exists(self, source: Path, target: Path, level: str) -> bool:
        """Check if documentation exists for an edge."""
        return self.get_edge_doc_path(source, target, level).exists()

    def add_inconsistency(self, title: str, files: List[Path], reason: str, change_summary: str):
        """Add an inconsistency to the tracking file."""
        inconsistencies_path = self.get_inconsistencies_path()

        # Read existing content
        existing = ""
        if inconsistencies_path.exists():
            with open(inconsistencies_path, 'r', encoding='utf-8') as f:
                existing = f.read()

        # Append new inconsistency
        with open(inconsistencies_path, 'a', encoding='utf-8') as f:
            if not existing:
                f.write("# Inconsistencies\n\n")

            f.write(f"## Inconsistency: {title}\n")
            f.write(f"**Files Involved**: {', '.join(str(f) for f in files)}\n")
            f.write(f"**Reason**: {reason}\n")
            f.write(f"**Change Summary**: {change_summary}\n")
            f.write("---\n\n")

    def clear_inconsistencies(self):
        """Clear all inconsistencies."""
        inconsistencies_path = self.get_inconsistencies_path()
        if inconsistencies_path.exists():
            inconsistencies_path.unlink()

    def get_inconsistencies(self) -> Optional[str]:
        """Get current inconsistencies."""
        inconsistencies_path = self.get_inconsistencies_path()
        if inconsistencies_path.exists():
            with open(inconsistencies_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return content if content else None
        return None

    def read_source_file(self, file_path: Path) -> str:
        """Read the actual source code file."""
        with open(self.project_root / file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def get_file_hash(self, file_path: Path) -> str:
        """Get a simple hash/timestamp for change detection."""
        import hashlib
        try:
            with open(self.project_root / file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
