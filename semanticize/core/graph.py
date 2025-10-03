"""Graph data structure for managing file relationships."""

from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FileNode:
    """Represents a file in the graph."""
    path: Path
    last_modified: datetime
    line_count: int
    has_technical: bool = False
    has_developer: bool = False
    has_executive: bool = False


@dataclass
class Edge:
    """Represents a relationship between two files."""
    source: Path
    target: Path
    has_technical: bool = False
    has_developer: bool = False
    has_executive: bool = False


class CodeGraph:
    """Manages the graph of files and their relationships."""

    def __init__(self):
        self.nodes: Dict[Path, FileNode] = {}
        self.edges: Dict[tuple, Edge] = {}  # Key: (source, target)

    def add_node(self, path: Path, last_modified: datetime, line_count: int):
        """Add a file node to the graph."""
        self.nodes[path] = FileNode(
            path=path,
            last_modified=last_modified,
            line_count=line_count
        )

    def add_edge(self, source: Path, target: Path):
        """Add an edge between two files."""
        key = (source, target)
        if key not in self.edges:
            self.edges[key] = Edge(source=source, target=target)

    def get_dependencies(self, file: Path) -> List[Path]:
        """Get all files that the given file depends on."""
        return [edge.target for edge in self.edges.values() if edge.source == file]

    def get_dependents(self, file: Path) -> List[Path]:
        """Get all files that depend on the given file."""
        return [edge.source for edge in self.edges.values() if edge.target == file]

    def mark_file_levels(self, file: Path, technical: bool, developer: bool, executive: bool):
        """Mark which abstraction levels exist for a file."""
        if file in self.nodes:
            self.nodes[file].has_technical = technical
            self.nodes[file].has_developer = developer
            self.nodes[file].has_executive = executive

    def mark_edge_levels(self, source: Path, target: Path, technical: bool, developer: bool, executive: bool):
        """Mark which abstraction levels exist for an edge."""
        key = (source, target)
        if key in self.edges:
            self.edges[key].has_technical = technical
            self.edges[key].has_developer = developer
            self.edges[key].has_executive = executive

    def has_file(self, path: Path) -> bool:
        """Check if a file exists in the graph."""
        return path in self.nodes

    def get_all_files(self) -> List[Path]:
        """Get all files in the graph."""
        return list(self.nodes.keys())

    def get_all_edges(self) -> List[Edge]:
        """Get all edges in the graph."""
        return list(self.edges.values())
