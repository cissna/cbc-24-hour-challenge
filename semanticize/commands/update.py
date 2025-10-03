"""Update command implementation."""

from pathlib import Path
from datetime import datetime
from typing import Set, Dict

from ..core.discovery import FileDiscovery
from ..core.dependency import DependencyDetector
from ..core.graph import CodeGraph
from ..core.storage import Storage
from ..core.llm import LLMInterface, PromptBuilder
from ..core.propagation import Propagator


def run(project_root: Path):
    """Run the update command."""
    semanticize_dir = project_root / '.semanticize'
    if not semanticize_dir.exists():
        print("Error: Not a Semanticize project. Run 'semanticize init' first.")
        return

    print("Updating documentation...")

    # Initialize components
    discovery = FileDiscovery(project_root)
    detector = DependencyDetector(project_root)
    storage = Storage(project_root)
    llm = LLMInterface()
    prompt_builder = PromptBuilder()

    # Phase 1: Change Detection
    print("\n=== Phase 1: Change Detection ===")
    current_files = set(discovery.discover_files())
    changed_files = set()
    change_summaries = {}

    # Build a simple graph from existing docs to check what we have
    graph = CodeGraph()

    # Check each current file
    for file in current_files:
        # Check if documentation exists
        if not storage.file_doc_exists(file, 'technical'):
            print(f"New file detected: {file}")
            changed_files.add(file)
            change_summaries[file] = "New file added"
            continue

        # Check if content changed (simple hash comparison)
        current_content = storage.read_source_file(file)
        # We'll compare by checking if we need to update
        # For simplicity, we'll read the old doc and compare file timestamps

        file_stat = (project_root / file).stat()
        current_mtime = datetime.fromtimestamp(file_stat.st_mtime)

        # Check doc file timestamp
        doc_path = storage.get_file_doc_path(file, 'technical')
        if doc_path.exists():
            doc_mtime = datetime.fromtimestamp(doc_path.stat().st_mtime)
            if current_mtime > doc_mtime:
                print(f"Modified file detected: {file}")
                changed_files.add(file)
                change_summaries[file] = "File content modified"

    if not changed_files:
        print("No changes detected.")
        return

    print(f"Detected {len(changed_files)} changed files")

    # Rebuild dependency graph
    dep_graph = detector.build_dependency_graph(list(current_files))
    for file in current_files:
        file_stat = (project_root / file).stat()
        line_count = discovery.count_lines(file)
        graph.add_node(file, datetime.fromtimestamp(file_stat.st_mtime), line_count)
        for dep in dep_graph.get(file, []):
            graph.add_edge(file, dep)

    # Phase 2: Propagation
    print("\n=== Phase 2: Propagation ===")
    propagator = Propagator(graph, storage, llm)

    # Determine which levels need updating for each changed file
    files_to_update = {}
    for file in changed_files:
        try:
            current_content = storage.read_source_file(file)
            old_doc = storage.read_file_doc(file, 'technical')
            old_content = current_content if not old_doc else ""  # Simplified

            levels = propagator.determine_update_levels(file, old_content, current_content)
            files_to_update[file] = levels
            print(f"{file}: {', '.join([k for k, v in levels.items() if v]) or 'no updates'}")
        except Exception as e:
            print(f"Error checking {file}: {e}")

    # Propagate changes through graph
    all_affected_files = propagator.propagate_changes(changed_files, change_summaries)
    print(f"Propagation complete: {len(all_affected_files)} files affected")

    # Add propagated files with default level updates
    for file in all_affected_files:
        if file not in files_to_update:
            files_to_update[file] = {
                'technical': True,
                'developer': True,
                'executive': True
            }

    # Phase 3: Regeneration
    print("\n=== Phase 3: Regeneration ===")
    total_files = len(files_to_update)

    for i, (file, levels) in enumerate(files_to_update.items(), 1):
        print(f"[{i}/{total_files}] Updating {file}...")

        try:
            file_content = storage.read_source_file(file)
            dependencies = dep_graph.get(file, [])

            # Update each required level
            if levels.get('technical'):
                prompt = prompt_builder.build_file_analysis_prompt(
                    file, file_content, 'technical', dependencies
                )
                _, doc = llm.query_with_retry(prompt, f"{file}.technical.md")
                storage.write_file_doc(file, 'technical', doc)

            if levels.get('developer'):
                prompt = prompt_builder.build_file_analysis_prompt(
                    file, file_content, 'developer', dependencies
                )
                _, doc = llm.query_with_retry(prompt, f"{file}.developer.md")
                storage.write_file_doc(file, 'developer', doc)

            if levels.get('executive'):
                prompt = prompt_builder.build_file_analysis_prompt(
                    file, file_content, 'executive', dependencies
                )
                _, doc = llm.query_with_retry(prompt, f"{file}.executive.md")
                storage.write_file_doc(file, 'executive', doc)

            # Update edge descriptions if this file has new/changed dependencies
            for dep in dependencies:
                if dep in current_files:
                    try:
                        dep_content = storage.read_source_file(dep)

                        for level in ['technical', 'developer', 'executive']:
                            prompt = prompt_builder.build_edge_analysis_prompt(
                                file, dep, file_content, dep_content, level
                            )
                            _, edge_doc = llm.query_with_retry(prompt, f"{file}--TO--{dep}.{level}.md")
                            storage.write_edge_doc(file, dep, level, edge_doc)
                    except Exception as e:
                        print(f"  Warning: Could not update edge {file} -> {dep}: {e}")

        except Exception as e:
            print(f"  Error updating {file}: {e}")

    # Phase 4: Inconsistency Detection
    print("\n=== Phase 4: Inconsistency Check ===")
    inconsistencies_found = False

    for file in current_files:
        dependencies = dep_graph.get(file, [])
        issues = propagator.detect_inconsistencies(file, dependencies)

        for issue in issues:
            print(f"⚠ {issue}")
            storage.add_inconsistency(
                f"Dependency issue in {file}",
                [file],
                issue,
                change_summaries.get(file, "Unknown change")
            )
            inconsistencies_found = True

    if not inconsistencies_found:
        storage.clear_inconsistencies()
        print("No inconsistencies detected")

    print(f"\n✓ Update complete!")
    print(f"  - Updated {len(files_to_update)} files")
    if inconsistencies_found:
        print(f"  - ⚠ Inconsistencies detected (see .semanticize/inconsistencies.md)")
