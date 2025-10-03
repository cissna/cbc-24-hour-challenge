#!/usr/bin/env python3
"""Quick test to verify ignore patterns work."""

from pathlib import Path
import pathspec

# Test patterns
patterns = [
    '*.json',
    '*.md',
    'node_modules/',
    'frontend/public/**',
]

spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)

# Test files
test_files = [
    'test.json',
    'package.json',
    'frontend/package.json',
    'README.md',
    'src/config.py',
    'node_modules/something.js',
    'frontend/public/index.html',
    'frontend/public/robots.txt',
    'frontend/src/App.js',
]

print("Testing ignore patterns:")
print(f"Patterns: {patterns}\n")

for file in test_files:
    matched = spec.match_file(file)
    status = "IGNORED" if matched else "INCLUDED"
    print(f"{status:10} {file}")
