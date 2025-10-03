"""State tracking for partial initialization."""

import json
from pathlib import Path
from typing import Optional, Dict, Set, List
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FileState:
    """State of a single file's documentation."""
    path: str
    technical_done: bool = False
    developer_done: bool = False
    executive_done: bool = False
    edges_done: List[str] = None  # List of target files whose edges are complete

    def __post_init__(self):
        if self.edges_done is None:
            self.edges_done = []

    def is_complete(self) -> bool:
        """Check if all levels are done."""
        return self.technical_done and self.developer_done and self.executive_done

    def missing_levels(self) -> List[str]:
        """Get list of missing levels."""
        missing = []
        if not self.technical_done:
            missing.append('technical')
        if not self.developer_done:
            missing.append('developer')
        if not self.executive_done:
            missing.append('executive')
        return missing


@dataclass
class ProjectState:
    """Overall project initialization state."""
    initialized: bool = False
    files_discovered: bool = False
    file_states: Dict[str, FileState] = None
    project_summaries: Dict[str, bool] = None  # level -> done
    last_updated: Optional[str] = None

    def __post_init__(self):
        if self.file_states is None:
            self.file_states = {}
        if self.project_summaries is None:
            self.project_summaries = {
                'technical': False,
                'developer': False,
                'executive': False
            }


class StateManager:
    """Manages initialization state tracking."""

    STATE_FILE = 'state.json'

    def __init__(self, semanticize_dir: Path):
        self.state_path = semanticize_dir / self.STATE_FILE
        self.state = self.load()

    def load(self) -> ProjectState:
        """Load state from disk."""
        if not self.state_path.exists():
            return ProjectState()

        try:
            with open(self.state_path, 'r') as f:
                data = json.load(f)

            # Convert file_states dict back to FileState objects
            if 'file_states' in data and data['file_states']:
                data['file_states'] = {
                    path: FileState(**state_data)
                    for path, state_data in data['file_states'].items()
                }

            return ProjectState(**data)
        except Exception:
            return ProjectState()

    def save(self):
        """Save state to disk."""
        # Convert FileState objects to dicts
        data = asdict(self.state)
        data['last_updated'] = datetime.now().isoformat()

        with open(self.state_path, 'w') as f:
            json.dump(data, f, indent=2)

    def mark_files_discovered(self, files: List[Path]):
        """Mark that files have been discovered."""
        self.state.files_discovered = True
        for file in files:
            file_str = str(file)
            if file_str not in self.state.file_states:
                self.state.file_states[file_str] = FileState(path=file_str)
        self.save()

    def mark_file_level_complete(self, file: Path, level: str):
        """Mark a specific level as complete for a file."""
        file_str = str(file)
        if file_str not in self.state.file_states:
            self.state.file_states[file_str] = FileState(path=file_str)

        if level == 'technical':
            self.state.file_states[file_str].technical_done = True
        elif level == 'developer':
            self.state.file_states[file_str].developer_done = True
        elif level == 'executive':
            self.state.file_states[file_str].executive_done = True

        self.save()

    def mark_edge_complete(self, source: Path, target: Path):
        """Mark an edge as complete."""
        source_str = str(source)
        target_str = str(target)

        if source_str not in self.state.file_states:
            self.state.file_states[source_str] = FileState(path=source_str)

        if target_str not in self.state.file_states[source_str].edges_done:
            self.state.file_states[source_str].edges_done.append(target_str)

        self.save()

    def mark_project_summary_complete(self, level: str):
        """Mark project summary as complete for a level."""
        self.state.project_summaries[level] = True
        self.save()

    def mark_initialized(self):
        """Mark project as fully initialized."""
        self.state.initialized = True
        self.save()

    def get_incomplete_files(self) -> List[tuple]:
        """Get list of (file_path, missing_levels) for incomplete files."""
        incomplete = []
        for file_str, state in self.state.file_states.items():
            missing = state.missing_levels()
            if missing:
                incomplete.append((Path(file_str), missing))
        return incomplete

    def get_missing_edges(self, dependencies: Dict[Path, List[Path]]) -> List[tuple]:
        """Get list of (source, target) for missing edges."""
        missing = []
        for source, targets in dependencies.items():
            source_str = str(source)
            if source_str not in self.state.file_states:
                # All edges are missing
                for target in targets:
                    missing.append((source, target))
            else:
                edges_done = set(self.state.file_states[source_str].edges_done)
                for target in targets:
                    if str(target) not in edges_done:
                        missing.append((source, target))
        return missing

    def get_missing_project_summaries(self) -> List[str]:
        """Get list of missing project summary levels."""
        return [
            level for level, done in self.state.project_summaries.items()
            if not done
        ]

    def is_complete(self) -> bool:
        """Check if initialization is complete."""
        if not self.state.files_discovered:
            return False

        # Check all files are complete
        for state in self.state.file_states.values():
            if not state.is_complete():
                return False

        # Check project summaries
        if not all(self.state.project_summaries.values()):
            return False

        return True

    def get_progress_summary(self) -> str:
        """Get a human-readable progress summary."""
        if not self.state.files_discovered:
            return "Discovery phase not started"

        total_files = len(self.state.file_states)
        complete_files = sum(1 for s in self.state.file_states.values() if s.is_complete())

        incomplete = self.get_incomplete_files()
        missing_summaries = self.get_missing_project_summaries()

        summary = f"Files: {complete_files}/{total_files} complete\n"

        if incomplete:
            summary += f"\nIncomplete files ({len(incomplete)}):\n"
            for file, missing_levels in incomplete[:10]:  # Show first 10
                summary += f"  - {file}: missing {', '.join(missing_levels)}\n"
            if len(incomplete) > 10:
                summary += f"  ... and {len(incomplete) - 10} more\n"

        if missing_summaries:
            summary += f"\nMissing project summaries: {', '.join(missing_summaries)}\n"

        return summary
