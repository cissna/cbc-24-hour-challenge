"""Fix command to resume partial initialization."""

from pathlib import Path
from datetime import datetime

from ..core.discovery import FileDiscovery
from ..core.dependency import DependencyDetector
from ..core.storage import Storage
from ..core.llm import LLMInterface, PromptBuilder
from ..core.state import StateManager


def run(project_root: Path):
    """Run the fix command to complete partial initialization."""
    semanticize_dir = project_root / '.semanticize'
    if not semanticize_dir.exists():
        print("Error: Not a Semanticize project. Run 'semanticize init' first.")
        return

    print("Checking project state...")

    # Initialize components
    storage = Storage(project_root)
    state_manager = StateManager(semanticize_dir)
    llm = LLMInterface(semanticize_dir)
    prompt_builder = PromptBuilder()

    # Check if already complete
    if state_manager.is_complete():
        print("✓ Project is already fully initialized!")
        return

    # Show current state
    print("\nCurrent state:")
    print(state_manager.get_progress_summary())

    # Ask for confirmation
    response = input("\nContinue fixing? [y/N] ")
    if response.lower() != 'y':
        print("Cancelled.")
        return

    # Re-discover files
    discovery = FileDiscovery(project_root)
    detector = DependencyDetector(project_root)

    files = discovery.discover_files()
    dep_graph = detector.build_dependency_graph(files)

    # Update state with any new files
    state_manager.mark_files_discovered(files)

    # Phase 1: Complete file documentation
    incomplete_files = state_manager.get_incomplete_files()

    if incomplete_files:
        print(f"\n=== Completing File Documentation ({len(incomplete_files)} files) ===")

        for i, (file, missing_levels) in enumerate(incomplete_files, 1):
            print(f"[{i}/{len(incomplete_files)}] {file}: {', '.join(missing_levels)}")

            try:
                file_content = storage.read_source_file(file)
                dependencies = dep_graph.get(file, [])

                for level in missing_levels:
                    prompt = prompt_builder.build_file_analysis_prompt(
                        file, file_content, level, dependencies
                    )
                    try:
                        _, doc = llm.query_with_retry(prompt, f"{file}.{level}.md")
                        storage.write_file_doc(file, level, doc)
                        state_manager.mark_file_level_complete(file, level)
                        print(f"  ✓ {level}")
                    except Exception as e:
                        print(f"  ✗ {level}: {e}")
                        print("    Fix interrupted. Run 'semanticize fix' again to continue.")
                        return

            except Exception as e:
                print(f"  Error reading file: {e}")
                continue

    # Phase 2: Complete edges
    missing_edges = state_manager.get_missing_edges(dep_graph)

    if missing_edges:
        print(f"\n=== Completing Edge Documentation ({len(missing_edges)} edges) ===")

        for i, (source, target) in enumerate(missing_edges, 1):
            print(f"[{i}/{len(missing_edges)}] {source} -> {target}")

            try:
                source_content = storage.read_source_file(source)
                target_content = storage.read_source_file(target)

                for level in ['technical', 'developer', 'executive']:
                    prompt = prompt_builder.build_edge_analysis_prompt(
                        source, target, source_content, target_content, level
                    )
                    try:
                        _, edge_doc = llm.query_with_retry(prompt, f"{source}--TO--{target}.{level}.md")
                        storage.write_edge_doc(source, target, level, edge_doc)
                    except Exception as e:
                        print(f"  ✗ {level}: {e}")
                        print("    Fix interrupted. Run 'semanticize fix' again to continue.")
                        return

                state_manager.mark_edge_complete(source, target)
                print(f"  ✓ all levels")

            except Exception as e:
                print(f"  Error: {e}")
                continue

    # Phase 3: Complete project summaries
    missing_summaries = state_manager.get_missing_project_summaries()

    if missing_summaries:
        print(f"\n=== Completing Project Summaries ===")

        # Build file descriptions from existing docs
        file_descriptions = {'technical': {}, 'developer': {}, 'executive': {}}

        for file in files:
            for level in ['technical', 'developer', 'executive']:
                doc = storage.read_file_doc(file, level)
                if doc:
                    file_descriptions[level][file] = doc

        for level in missing_summaries:
            print(f"Generating {level} project summary...")
            prompt = prompt_builder.build_project_summary_prompt(
                file_descriptions[level], level
            )
            try:
                _, project_doc = llm.query_with_retry(prompt, f"description.{level}.md")
                storage.write_project_doc(level, project_doc)
                state_manager.mark_project_summary_complete(level)
                print(f"  ✓ {level}")
            except Exception as e:
                print(f"  ✗ {level}: {e}")
                print("    Fix interrupted. Run 'semanticize fix' again to continue.")
                return

    # Mark as complete
    state_manager.mark_initialized()

    print(f"\n✓ Project is now fully initialized!")
    print(f"  Run 'semanticize launch' to view the documentation")
