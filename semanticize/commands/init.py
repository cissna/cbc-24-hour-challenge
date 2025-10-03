"""Initialize command implementation."""

from pathlib import Path
from datetime import datetime
import sys
from typing import Optional

from ..core.discovery import FileDiscovery
from ..core.dependency import DependencyDetector
from ..core.graph import CodeGraph
from ..core.storage import Storage
from ..core.llm import LLMInterface, PromptBuilder
from ..core.state import StateManager


def run(project_root: Path, given_description: Optional[Path] = None):
    """Run the init command."""
    print("Initializing Semanticize...")

    # Initialize components
    discovery = FileDiscovery(project_root)
    detector = DependencyDetector(project_root)
    graph = CodeGraph()
    storage = Storage(project_root)

    # Create .semanticize directory
    storage.initialize()
    print(f"Created {storage.semanticize_dir}")

    # Initialize LLM with config
    llm = LLMInterface(storage.semanticize_dir)
    prompt_builder = PromptBuilder()
    state_manager = StateManager(storage.semanticize_dir)

    # Load context if provided
    context = None
    if given_description:
        print(f"Loading context from {given_description}")
        with open(given_description, 'r', encoding='utf-8') as f:
            context = f.read()

    # Phase 1: Discovery
    print("\n=== Phase 1: Discovery ===")
    files = discovery.discover_files()
    print(f"Discovered {len(files)} files")

    if not files:
        print("No files to analyze. Exiting.")
        return

    # Build dependency graph
    print("Building dependency graph...")
    dep_graph = detector.build_dependency_graph(files)

    # Mark files as discovered in state
    state_manager.mark_files_discovered(files)

    # Calculate total lines for progress
    total_lines = sum(discovery.count_lines(f) for f in files)
    processed_lines = 0

    # Get topological order (dependencies first)
    ordered_files = detector.get_topological_order(files)

    # Phase 2: Deep Analysis
    print(f"\n=== Phase 2: Deep Analysis ===")
    file_descriptions = {'technical': {}, 'developer': {}, 'executive': {}}

    for i, file in enumerate(ordered_files, 1):
        file_lines = discovery.count_lines(file)
        progress = int((processed_lines / total_lines) * 100) if total_lines > 0 else 0

        # Progress bar
        bar_length = 40
        filled = int((progress / 100) * bar_length)
        bar = '=' * filled + '>' + ' ' * (bar_length - filled - 1)
        print(f"\r[{bar}] {progress}% ({i}/{len(files)} files)", end='', flush=True)

        # Add to graph
        file_stat = (project_root / file).stat()
        graph.add_node(file, datetime.fromtimestamp(file_stat.st_mtime), file_lines)

        # Read file content
        try:
            file_content = storage.read_source_file(file)
        except Exception as e:
            print(f"\nWarning: Could not read {file}: {e}")
            continue

        # Get dependencies
        dependencies = dep_graph.get(file, [])
        for dep in dependencies:
            graph.add_edge(file, dep)

        # Generate documentation at all three levels
        # Start with technical (most comprehensive)
        prompt = prompt_builder.build_file_analysis_prompt(
            file, file_content, 'technical', dependencies, context
        )
        try:
            _, technical_doc = llm.query_with_retry(prompt, f"{file}.technical.md")
            storage.write_file_doc(file, 'technical', technical_doc)
            file_descriptions['technical'][file] = technical_doc
            graph.mark_file_levels(file, True, False, False)
            state_manager.mark_file_level_complete(file, 'technical')
        except Exception as e:
            print(f"\nError analyzing {file} (technical): {e}")
            print("Run 'semanticize fix' to resume from this point.")
            return

        # Developer level
        prompt = prompt_builder.build_file_analysis_prompt(
            file, file_content, 'developer', dependencies, context
        )
        try:
            _, developer_doc = llm.query_with_retry(prompt, f"{file}.developer.md")
            storage.write_file_doc(file, 'developer', developer_doc)
            file_descriptions['developer'][file] = developer_doc
            graph.mark_file_levels(file, True, True, False)
            state_manager.mark_file_level_complete(file, 'developer')
        except Exception as e:
            print(f"\nError analyzing {file} (developer): {e}")
            print("Run 'semanticize fix' to resume from this point.")
            return

        # Executive level
        prompt = prompt_builder.build_file_analysis_prompt(
            file, file_content, 'executive', dependencies, context
        )
        try:
            _, executive_doc = llm.query_with_retry(prompt, f"{file}.executive.md")
            storage.write_file_doc(file, 'executive', executive_doc)
            file_descriptions['executive'][file] = executive_doc
            graph.mark_file_levels(file, True, True, True)
            state_manager.mark_file_level_complete(file, 'executive')
        except Exception as e:
            print(f"\nError analyzing {file} (executive): {e}")
            print("Run 'semanticize fix' to resume from this point.")
            return

        # Generate edge descriptions
        for dep in dependencies:
            if dep in graph.get_all_files():
                try:
                    dep_content = storage.read_source_file(dep)

                    # Technical edge
                    prompt = prompt_builder.build_edge_analysis_prompt(
                        file, dep, file_content, dep_content, 'technical'
                    )
                    _, edge_doc = llm.query_with_retry(prompt, f"{file}--TO--{dep}.technical.md")
                    storage.write_edge_doc(file, dep, 'technical', edge_doc)

                    # Developer edge
                    prompt = prompt_builder.build_edge_analysis_prompt(
                        file, dep, file_content, dep_content, 'developer'
                    )
                    _, edge_doc = llm.query_with_retry(prompt, f"{file}--TO--{dep}.developer.md")
                    storage.write_edge_doc(file, dep, 'developer', edge_doc)

                    # Executive edge
                    prompt = prompt_builder.build_edge_analysis_prompt(
                        file, dep, file_content, dep_content, 'executive'
                    )
                    _, edge_doc = llm.query_with_retry(prompt, f"{file}--TO--{dep}.executive.md")
                    storage.write_edge_doc(file, dep, 'executive', edge_doc)

                    graph.mark_edge_levels(file, dep, True, True, True)
                    state_manager.mark_edge_complete(file, dep)

                except Exception as e:
                    print(f"\nError analyzing edge {file} -> {dep}: {e}")

        processed_lines += file_lines

    print()  # New line after progress bar

    # Phase 3: Synthesis
    print("\n=== Phase 3: Synthesis ===")

    # Generate project-level summaries for all levels
    for level in ['technical', 'developer', 'executive']:
        print(f"Generating {level} project summary...")
        prompt = prompt_builder.build_project_summary_prompt(
            file_descriptions[level], level
        )
        try:
            _, project_doc = llm.query_with_retry(prompt, f"description.{level}.md")
            storage.write_project_doc(level, project_doc)
            state_manager.mark_project_summary_complete(level)
        except Exception as e:
            print(f"Error generating {level} project summary: {e}")
            print("Run 'semanticize fix' to resume from this point.")
            return

    # Mark as fully initialized
    state_manager.mark_initialized()

    print(f"\n✓ Initialization complete!")
    print(f"  - Analyzed {len(files)} files")
    print(f"  - Created documentation at 3 abstraction levels")
    print(f"  - Documentation stored in {storage.semanticize_dir}")
    print(f"\nRun 'semanticize launch' to view the documentation")
