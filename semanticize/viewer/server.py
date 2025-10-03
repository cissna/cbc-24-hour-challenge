"""Flask server for web viewer."""

from flask import Flask, render_template, send_from_directory, jsonify
from pathlib import Path
from urllib.parse import unquote
import json
import markdown


def create_app(project_root: Path):
    """Create Flask app for viewing documentation."""
    app = Flask(__name__)
    app.config['PROJECT_ROOT'] = project_root
    app.config['SEMANTICIZE_DIR'] = project_root / '.semanticize'

    @app.route('/')
    def index():
        """Serve the main viewer page."""
        return render_template('index.html')

    @app.route('/api/tree')
    def get_tree():
        """Get file tree structure."""
        files_dir = app.config['SEMANTICIZE_DIR'] / 'files'
        tree = build_tree(files_dir, files_dir)
        return jsonify(tree)

    @app.route('/api/file/<path:filepath>')
    def get_file(filepath):
        """Get file documentation."""
        result = {
            'code': None,
            'technical': None,
            'developer': None,
            'executive': None,
            'dependencies': [],
            'dependents': []
        }

        # Read source code
        source_path = app.config['PROJECT_ROOT'] / filepath
        if source_path.exists():
            with open(source_path, 'r', encoding='utf-8') as f:
                result['code'] = f.read()

        # Read documentation
        file_path = Path(filepath)
        for level in ['technical', 'developer', 'executive']:
            doc_path = get_doc_path(app.config['SEMANTICIZE_DIR'], file_path, level)
            if doc_path.exists():
                with open(doc_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                    result[level] = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])

        # Get relationships
        result['dependencies'] = get_relationships(app.config['SEMANTICIZE_DIR'], file_path, 'dependencies')
        result['dependents'] = get_relationships(app.config['SEMANTICIZE_DIR'], file_path, 'dependents')

        return jsonify(result)

    @app.route('/api/edge/<path:source>/<path:target>')
    def get_edge(source, target):
        """Get edge documentation."""
        result = {
            'technical': None,
            'developer': None,
            'executive': None
        }

        # URL decode the paths
        source = unquote(source)
        target = unquote(target)

        source_path = Path(source)
        target_path = Path(target)

        for level in ['technical', 'developer', 'executive']:
            edge_path = get_edge_path(app.config['SEMANTICIZE_DIR'], source_path, target_path, level)
            if edge_path.exists():
                with open(edge_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                    result[level] = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])

        return jsonify(result)

    return app


def build_tree(base_dir: Path, current_dir: Path) -> dict:
    """Build a tree structure of files."""
    tree = {
        'name': current_dir.name if current_dir != base_dir else 'files',
        'path': str(current_dir.relative_to(base_dir)) if current_dir != base_dir else '',
        'children': []
    }

    if not current_dir.exists():
        return tree

    items = sorted(current_dir.iterdir(), key=lambda x: (not x.is_dir(), x.name))

    for item in items:
        if item.is_dir():
            tree['children'].append(build_tree(base_dir, item))
        elif item.suffix == '.md' and '.technical.md' in item.name:
            # Extract the original filename
            original_name = item.name.replace('.technical.md', '')
            relative_path = item.relative_to(base_dir).parent / original_name
            tree['children'].append({
                'name': original_name,
                'path': str(relative_path),
                'is_file': True
            })

    return tree


def get_doc_path(semanticize_dir: Path, file_path: Path, level: str) -> Path:
    """Get documentation path for a file."""
    return semanticize_dir / 'files' / file_path.parent / f"{file_path.name}.{level}.md"


def get_edge_path(semanticize_dir: Path, source: Path, target: Path, level: str) -> Path:
    """Get edge documentation path."""
    source_str = str(source).replace('/', '.')
    target_str = str(target).replace('/', '.')
    edge_name = f"{source_str}--TO--{target_str}.{level}.md"
    return semanticize_dir / 'edges' / edge_name


def get_relationships(semanticize_dir: Path, file_path: Path, rel_type: str) -> list:
    """Get file relationships."""
    edges_dir = semanticize_dir / 'edges'
    relationships = []

    if not edges_dir.exists():
        return relationships

    file_str = str(file_path).replace('/', '.')

    for edge_file in edges_dir.glob('*.technical.md'):
        edge_name = edge_file.stem.replace('.technical', '')

        if rel_type == 'dependencies' and edge_name.startswith(file_str + '--TO--'):
            target = edge_name.replace(file_str + '--TO--', '').replace('.', '/')
            relationships.append(target)
        elif rel_type == 'dependents' and '--TO--' + file_str in edge_name:
            source = edge_name.split('--TO--')[0].replace('.', '/')
            relationships.append(source)

    return relationships
