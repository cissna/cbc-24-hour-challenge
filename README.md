# Semanticize: English-First Codebase Explorer

## Vision

Semanticize transforms how developers and non-technical stakeholders understand codebases by providing natural language explanations alongside traditional code views. It maintains a living, semantic understanding of your codebase that evolves with every commit.

## Core Concept

Instead of forcing users to decipher code to understand a system, Semanticize presents code files as human-readable documentation at multiple levels of abstraction. More importantly, it understands and explains how files relate to each other, creating a semantic graph of your entire codebase.

## Key Features

### 📖 Multi-Level English Views
Every code file can be viewed at three levels of abstraction:
- **Technical Level**: Detailed explanation of what the code does and how it does it
- **Developer Level**: Big-picture overview for quick understanding
- **Executive Level**: High-level summary for non-technical stakeholders

### 🕸️ Semantic File Relationships
- Automatically detects dependencies and connections between files
- Provides natural language explanations of how files interact
- Shows bidirectional relationships (depends on / depended by)

### 🔄 Living Documentation
- Updates automatically with every git commit
- Intelligently determines which file descriptions need updating based on changes
- Maintains consistency across the entire codebase understanding
- Alerts when semantic inconsistencies are detected

### 🎯 Context-Aware Understanding
Each file is understood in two ways:
1. **Isolated**: What the file does on its own
2. **Contextual**: How it fits into the larger system

## How It Works

1. **Initial Analysis**: On first run, Semanticize analyzes your entire codebase, building a dependency graph and generating initial descriptions

2. **Change Detection**: When code is committed, Semanticize:
   - Identifies which files changed
   - Determines which connected files might be affected
   - Updates descriptions only where necessary

3. **Smart Updates**: The system evaluates whether changes in connected files actually impact a file's meaning before regenerating descriptions

4. **Version History**: All explanations are versioned alongside your git commits

## Target Audience

- **New Developers**: Quickly understand unfamiliar codebases
- **Senior Developers**: Get rapid context when jumping between projects
- **Technical Leads**: Ensure architectural consistency
- **Non-Technical Stakeholders**: Understand what the codebase does without reading code

## Technical Approach

- Leverages LLMs for natural language generation
- Uses programmatic analysis for dependency detection
- Maintains a semantic graph database of file relationships
- Integrates with git for change tracking

## Scope

Designed for small-to-medium codebases. For larger systems, Semanticize can focus on specific sections while using `OUTSIDE_CONTEXT.md` files to maintain awareness of the broader system.

## Interface

A clean web interface featuring:
- **Left Panel**: File explorer (similar to VSCode)
- **Center Panel**: Code or English view toggle
- **Right Panel**: Connected files list with expandable relationship descriptions

## Future Vision

Semanticize aims to make codebases as readable as documentation, ensuring that the question "what does this code do?" always has an up-to-date, accurate answer at the appropriate level of detail for any audience.

---

*Making code speak your language.*