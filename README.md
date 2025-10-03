# Semanticize

Semantic codebase understanding system that maintains living documentation at three levels of abstraction.

## Overview

Semanticize analyzes your codebase and generates comprehensive documentation at three levels:
- **Technical**: Detailed implementation-level documentation for engineers
- **Developer**: Function/class-level summaries for developers working with the code
- **Executive**: High-level business purpose for non-technical stakeholders

The system uses a graph-based approach to intelligently propagate changes and maintain consistency across the entire codebase.

## Prerequisites

- Python 3.8+
- API key for an OpenAI-compatible LLM service (OpenRouter, OpenAI, etc.)

## Installation

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# From the project directory
pip install -e .
```

## Quick Start

### 1. Configure API

```bash
semanticize setup
```

Choose your provider (OpenRouter, OpenAI, or custom) and enter your API credentials.

### 2. Initialize a project

```bash
# Navigate to your codebase
cd /path/to/your/project

# Initialize Semanticize
semanticize init

# Or bootstrap with existing description
semanticize init --given-description path/to/description.md
```

If initialization is interrupted, resume with:
```bash
semanticize fix
```

### 3. Update after code changes

```bash
semanticize update
```

### 4. Check for inconsistencies

```bash
semanticize check
```

### 5. Launch web viewer

```bash
semanticize launch
```

Opens a web interface at http://localhost:8080 where you can:
- Browse files in a tree view
- Toggle between code and documentation
- Switch between abstraction levels
- View file relationships

## Commands

- **`semanticize setup`**: Configure API settings (base URL, API key, model)
- **`semanticize init`**: Analyze codebase and generate initial documentation
- **`semanticize fix`**: Resume partial/interrupted initialization
- **`semanticize update`**: Update documentation after code changes
- **`semanticize check`**: Check for documentation inconsistencies
- **`semanticize launch`**: Start web viewer

## How It Works

1. **Discovery**: Scans your codebase and identifies files to analyze
2. **Analysis**: Uses LLM to generate documentation at all three levels
3. **Graph Building**: Creates a dependency graph with relationships
4. **Propagation**: When files change, intelligently updates only affected documentation
5. **Consistency**: Detects and tracks inconsistencies in the codebase

## Directory Structure

```
your-project/
├── src/
│   └── your code...
└── .semanticize/
    ├── config.json           # API configuration
    ├── state.json            # Initialization state tracking
    ├── description.technical.md
    ├── description.developer.md
    ├── description.executive.md
    ├── inconsistencies.md
    ├── files/
    │   └── [mirrors your source structure]
    └── edges/
        └── [relationship documentation]
```

## Features

- **Three abstraction levels** for different audiences
- **OpenAI-compatible API** - works with OpenRouter, OpenAI, and any compatible service
- **State tracking** - resume interrupted initialization with `fix` command
- **Intelligent propagation** - only updates what's necessary
- **Dependency tracking** via AST analysis (Python)
- **Inconsistency detection** when code and docs diverge
- **Web viewer** for easy browsing
- **Dynamic ignore** system respects .gitignore

## Migrating from Partial Initialization

If you have an existing `.semanticize` directory from before state tracking was added, you can generate a state file:

```bash
# From the project root (where .semanticize exists)
python scripts/create_state_from_existing.py

# Or specify the path
python scripts/create_state_from_existing.py /path/to/your/project/.semanticize
```

This will scan your existing documentation and create `state.json`, then you can run:

```bash
semanticize fix
```

to complete any missing documentation.

## Development

This project was created for the CBC 24-hour challenge.

See [MVP_PRD.md](MVP_PRD.md) for full product requirements.