#!/usr/bin/env python3
"""
Script to generate state.json from existing .semanticize directory.

This allows you to use 'semanticize fix' on a partially completed
initialization that was done before state tracking was added.
"""

import json
import sys
from pathlib import Path


def create_state_from_existing(semanticize_dir: Path):
    """Generate state.json by scanning existing documentation."""

    files_dir = semanticize_dir / 'files'
    edges_dir = semanticize_dir / 'edges'

    if not semanticize_dir.exists():
        print(f"Error: {semanticize_dir} does not exist")
        sys.exit(1)

    print(f"Scanning {semanticize_dir}...")

    # Track file states
    file_states = {}

    # Scan files directory
    if files_dir.exists():
        for doc_file in files_dir.rglob('*.md'):
            # Parse filename: path/to/file.py.technical.md
            relative_to_files = doc_file.relative_to(files_dir)

            # Determine the level
            if doc_file.name.endswith('.technical.md'):
                level = 'technical'
                original_name = doc_file.name[:-len('.technical.md')]
            elif doc_file.name.endswith('.developer.md'):
                level = 'developer'
                original_name = doc_file.name[:-len('.developer.md')]
            elif doc_file.name.endswith('.executive.md'):
                level = 'executive'
                original_name = doc_file.name[:-len('.executive.md')]
            else:
                continue

            # Reconstruct the original file path
            file_path = str(relative_to_files.parent / original_name)

            # Initialize file state if needed
            if file_path not in file_states:
                file_states[file_path] = {
                    'path': file_path,
                    'technical_done': False,
                    'developer_done': False,
                    'executive_done': False,
                    'edges_done': []
                }

            # Mark level as done
            file_states[file_path][f'{level}_done'] = True

    # Scan edges directory
    edges_by_source = {}
    if edges_dir.exists():
        for edge_file in edges_dir.glob('*.technical.md'):
            # Parse edge filename: source.path--TO--target.path.technical.md
            edge_name = edge_file.stem.replace('.technical', '')

            if '--TO--' not in edge_name:
                continue

            source_str, target_str = edge_name.split('--TO--')

            # Convert back to paths
            source_path = source_str.replace('.', '/')
            target_path = target_str.replace('.', '/')

            if source_path not in edges_by_source:
                edges_by_source[source_path] = []

            edges_by_source[source_path].append(target_path)

    # Add edges to file states
    for source_path, targets in edges_by_source.items():
        if source_path in file_states:
            file_states[source_path]['edges_done'] = targets

    # Check project summaries
    project_summaries = {
        'technical': (semanticize_dir / 'description.technical.md').exists(),
        'developer': (semanticize_dir / 'description.developer.md').exists(),
        'executive': (semanticize_dir / 'description.executive.md').exists()
    }

    # Build state object
    state = {
        'initialized': False,  # Set to False so 'fix' will complete it
        'files_discovered': True,
        'file_states': file_states,
        'project_summaries': project_summaries,
        'last_updated': None
    }

    # Write state.json
    state_file = semanticize_dir / 'state.json'
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

    # Print summary
    print(f"\n✓ Created {state_file}")
    print(f"\nSummary:")
    print(f"  Total files: {len(file_states)}")

    complete_files = sum(1 for s in file_states.values()
                        if s['technical_done'] and s['developer_done'] and s['executive_done'])
    print(f"  Complete files: {complete_files}")
    print(f"  Incomplete files: {len(file_states) - complete_files}")

    # Show incomplete files
    incomplete = []
    for path, state in file_states.items():
        missing = []
        if not state['technical_done']:
            missing.append('technical')
        if not state['developer_done']:
            missing.append('developer')
        if not state['executive_done']:
            missing.append('executive')
        if missing:
            incomplete.append((path, missing))

    if incomplete:
        print(f"\n  Incomplete files:")
        for path, missing in incomplete[:10]:
            print(f"    - {path}: missing {', '.join(missing)}")
        if len(incomplete) > 10:
            print(f"    ... and {len(incomplete) - 10} more")

    missing_summaries = [k for k, v in project_summaries.items() if not v]
    if missing_summaries:
        print(f"\n  Missing project summaries: {', '.join(missing_summaries)}")

    print(f"\nYou can now run 'semanticize fix' to complete the initialization!")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        semanticize_dir = Path(sys.argv[1])
    else:
        # Default to .semanticize in current directory
        semanticize_dir = Path.cwd() / '.semanticize'

    create_state_from_existing(semanticize_dir)
