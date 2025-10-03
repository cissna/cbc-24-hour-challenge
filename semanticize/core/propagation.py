"""Change propagation algorithm."""

from pathlib import Path
from typing import Set, Dict, List, Tuple
from .graph import CodeGraph
from .storage import Storage
from .llm import LLMInterface, PromptBuilder


class Propagator:
    """Handles change propagation through the dependency graph."""

    def __init__(self, graph: CodeGraph, storage: Storage, llm: LLMInterface):
        self.graph = graph
        self.storage = storage
        self.llm = llm
        self.prompt_builder = PromptBuilder()

    def determine_update_levels(self, file: Path, old_content: str, new_content: str) -> Dict[str, bool]:
        """Determine which abstraction levels need updating for a changed file."""
        levels_to_update = {
            'technical': False,
            'developer': False,
            'executive': False
        }

        # Check if technical level needs update
        prompt = self.prompt_builder.build_update_check_prompt(
            file, old_content, new_content, 'technical'
        )
        response = self.llm.query(prompt).strip().upper()
        levels_to_update['technical'] = 'YES' in response

        if levels_to_update['technical']:
            # Check developer level
            prompt = self.prompt_builder.build_update_check_prompt(
                file, old_content, new_content, 'developer'
            )
            response = self.llm.query(prompt).strip().upper()
            levels_to_update['developer'] = 'YES' in response

            if levels_to_update['developer']:
                # Check executive level
                prompt = self.prompt_builder.build_update_check_prompt(
                    file, old_content, new_content, 'executive'
                )
                response = self.llm.query(prompt).strip().upper()
                levels_to_update['executive'] = 'YES' in response

        return levels_to_update

    def should_propagate_through_edge(self, source: Path, target: Path, change_summary: str) -> bool:
        """Check if changes should propagate through an edge."""
        # Read the technical edge description (source of truth)
        edge_desc = self.storage.read_edge_doc(source, target, 'technical')
        if not edge_desc:
            return False

        prompt = self.prompt_builder.build_propagation_check_prompt(
            edge_desc, source, change_summary
        )
        response = self.llm.query(prompt).strip().upper()
        return 'YES' in response

    def propagate_changes(self, changed_files: Set[Path], change_summaries: Dict[Path, str]) -> Set[Path]:
        """Propagate changes through the graph.

        Args:
            changed_files: Set of files that changed
            change_summaries: Summary of changes for each file

        Returns:
            Set of all files that need updating (including the originally changed files)
        """
        files_to_update = set(changed_files)
        visited_edges = set()
        queue = list(changed_files)

        while queue:
            current_file = queue.pop(0)
            change_summary = change_summaries.get(current_file, "File content changed")

            # Get all edges where this file is the source
            for edge in self.graph.get_all_edges():
                if edge.source != current_file:
                    continue

                edge_key = (edge.source, edge.target)
                if edge_key in visited_edges:
                    continue

                visited_edges.add(edge_key)

                # Check if we should propagate through this edge
                if self.should_propagate_through_edge(edge.source, edge.target, change_summary):
                    # Mark the target file for update
                    if edge.target not in files_to_update:
                        files_to_update.add(edge.target)
                        queue.append(edge.target)
                        # Create a change summary for the propagated change
                        change_summaries[edge.target] = f"Dependency {edge.source} was modified"

        return files_to_update

    def detect_inconsistencies(self, file: Path, dependencies: List[Path]) -> List[str]:
        """Detect inconsistencies in file relationships."""
        inconsistencies = []

        for dep in dependencies:
            # Check if dependency still exists
            if not self.graph.has_file(dep):
                inconsistencies.append(
                    f"File {file} depends on {dep} which no longer exists in the codebase"
                )

            # Check if edge description exists
            if not self.storage.edge_doc_exists(file, dep, 'technical'):
                inconsistencies.append(
                    f"File {file} depends on {dep} but no relationship documentation exists"
                )

        return inconsistencies
