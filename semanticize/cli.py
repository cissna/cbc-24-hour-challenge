"""CLI entry point for Semanticize."""

import sys
import argparse
from pathlib import Path

from . import __version__
from .commands import init, update, check, launch, setup, fix


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Semanticize: Semantic codebase understanding system',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--version', action='version', version=f'semanticize {__version__}')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Setup command
    subparsers.add_parser('setup', help='Configure API settings')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize a new Semanticize project')
    init_parser.add_argument(
        '--given-description',
        type=Path,
        help='Path to existing project description to bootstrap analysis'
    )

    # Update command
    subparsers.add_parser('update', help='Update documentation after code changes')

    # Check command
    subparsers.add_parser('check', help='Check for inconsistencies')

    # Fix command
    subparsers.add_parser('fix', help='Resume partial initialization')

    # Launch command
    launch_parser = subparsers.add_parser('launch', help='Launch web viewer')
    launch_parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Port to run the web server on (default: 8080)'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Get project root (current directory)
    project_root = Path.cwd()

    # Execute command
    try:
        if args.command == 'setup':
            setup.run(project_root)
        elif args.command == 'init':
            init.run(project_root, args.given_description)
        elif args.command == 'update':
            update.run(project_root)
        elif args.command == 'check':
            check.run(project_root)
        elif args.command == 'fix':
            fix.run(project_root)
        elif args.command == 'launch':
            launch.run(project_root, args.port)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
