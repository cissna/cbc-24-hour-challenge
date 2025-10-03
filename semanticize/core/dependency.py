"""Dependency detection using AST parsing."""

import ast
from pathlib import Path
from typing import List, Set, Tuple, Optional
import os


class DependencyDetector:
    """Detects dependencies between Python files using AST."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def extract_dependencies(self, file_path: Path) -> List[Path]:
        """Extract dependencies from a Python file."""
        if not file_path.suffix == '.py':
            return []

        try:
            with open(self.project_root / file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())

            dependencies = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dep = self._resolve_import(alias.name, file_path)
                        if dep:
                            dependencies.add(dep)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dep = self._resolve_import(node.module, file_path, node.level)
                        if dep:
                            dependencies.add(dep)

            return sorted(list(dependencies))

        except (SyntaxError, UnicodeDecodeError, PermissionError):
            return []

    def _resolve_import(self, module_name: str, current_file: Path, level: int = 0) -> Optional[Path]:
        """Resolve an import to a file path within the project."""
        # Handle relative imports
        if level > 0:
            current_dir = current_file.parent
            for _ in range(level - 1):
                current_dir = current_dir.parent

            module_parts = module_name.split('.') if module_name else []
            target_path = current_dir

            for part in module_parts:
                target_path = target_path / part

            # Try as a file
            file_path = target_path.with_suffix('.py')
            if (self.project_root / file_path).exists():
                return file_path

            # Try as a package
            package_path = target_path / '__init__.py'
            if (self.project_root / package_path).exists():
                return package_path

            return None

        # Handle absolute imports within the project
        module_parts = module_name.split('.')

        # Try to resolve as a file in the project
        for i in range(len(module_parts), 0, -1):
            potential_path = Path(*module_parts[:i])

            # Try as a file
            file_path = potential_path.with_suffix('.py')
            if (self.project_root / file_path).exists():
                return file_path

            # Try as a package
            package_path = potential_path / '__init__.py'
            if (self.project_root / package_path).exists():
                return package_path

        return None

    def build_dependency_graph(self, files: List[Path]) -> dict:
        """Build a dependency graph for all files."""
        graph = {}

        for file in files:
            dependencies = self.extract_dependencies(file)
            graph[file] = dependencies

        return graph

    def get_topological_order(self, files: List[Path]) -> List[Path]:
        """Get files in topological order (dependencies first)."""
        graph = self.build_dependency_graph(files)
        visited = set()
        order = []

        def visit(file: Path):
            if file in visited:
                return
            visited.add(file)

            for dep in graph.get(file, []):
                if dep in graph:  # Only visit files in our file list
                    visit(dep)

            order.append(file)

        for file in files:
            visit(file)

        return order
