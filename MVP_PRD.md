# Product Requirements Document (PRD) - UPDATED
## Semanticize: Semantic Codebase Understanding System

### 1. Executive Summary

Semanticize is a backend system that maintains a living, semantic understanding of codebases through structured markdown documentation at three levels of abstraction. It uses a graph-based approach to intelligently propagate changes and maintain consistency across file relationships. The system is designed primarily for AI-generated codebases where maintaining human-readable understanding is crucial. A simple web viewer provides an interface to browse the generated documentation at different abstraction levels.

### 2. Problem Statement

Modern codebases, especially those generated or heavily modified by AI, lack persistent human-readable documentation that stays synchronized with code changes. Different stakeholders need different levels of detail:
- Engineers need comprehensive technical documentation
- Developers need efficient summaries for quick understanding  
- Non-technical stakeholders need high-level overviews

Traditional documentation becomes outdated immediately, and code comments are insufficient for understanding system-wide interactions.

### 3. Core Concept

Semanticize treats codebase understanding as a living graph where:

- **Nodes** are files with three levels of explanations (technical, developer, executive)
- **Edges** are semantic relationships with descriptions at all three levels
- **Changes** propagate through the graph only when semantically relevant
- **The entire system** maintains consistency through intelligent updates
- **Multiple audiences** are served through abstraction levels

The key innovation is the **semantic propagation algorithm with level-aware updates**: when a file changes, the system determines which abstraction levels need updating and propagates changes intelligently through the graph.

### 4. System Architecture

#### 4.1 Storage Structure
```
project/
├── src/
│   ├── main.py
│   ├── utils.py
│   └── models/
│       └── user.py
└── .semanticize/
    ├── description.technical.md    # Project-level technical details
    ├── description.developer.md     # Project-level developer summary
    ├── description.executive.md     # Project-level executive overview
    ├── context.md                  # External context (optional, static)
    ├── inconsistencies.md          # Active inconsistencies (technical level)
    ├── .semanticizeignore          # Dynamic ignore patterns
    ├── files/
    │   ├── src/
    │   │   ├── main.py.technical.md
    │   │   ├── main.py.developer.md
    │   │   ├── main.py.executive.md
    │   │   ├── utils.py.technical.md
    │   │   ├── utils.py.developer.md
    │   │   ├── utils.py.executive.md
    │   │   └── models/
    │   │       ├── user.py.technical.md
    │   │       ├── user.py.developer.md
    │   │       └── user.py.executive.md
    └── edges/
        ├── src.main.py--TO--src.utils.py.technical.md
        ├── src.main.py--TO--src.utils.py.developer.md
        ├── src.main.py--TO--src.utils.py.executive.md
        ├── src.main.py--TO--src.models.user.py.technical.md
        ├── src.main.py--TO--src.models.user.py.developer.md
        └── src.main.py--TO--src.models.user.py.executive.md
```

**Storage Structure Rationale**: The markdown files mirror the directory structure for intuitive navigation. Edges use a consistent naming pattern for bidirectional relationships. During runtime, this is loaded into an in-memory graph data structure for efficient traversal and update decisions.

#### 4.2 Abstraction Levels Defined

**Technical Level**
- Comprehensive explanation of what the code does and how
- Near line-by-line equivalent detail
- Includes implementation details, algorithms, data structures
- For edges: Precise function calls, parameters, return values
- Target audience: Engineers needing complete understanding

**Developer Level**
- Function and class level summaries
- Big-picture understanding for quick comprehension
- Focus on what components do, less on how
- For edges: High-level interaction patterns
- Target audience: Developers working with the code

**Executive Level**
- One sentence to two paragraphs maximum
- What the component accomplishes, no implementation details
- Business value and purpose focused
- For edges: Simple relationship descriptions
- Target audience: Non-technical stakeholders

#### 4.3 Document Types with Abstraction Levels

**Project Descriptions (description.*.md)**
- Three separate files for each abstraction level
- Technical: Architecture details, packages used, design patterns
- Developer: System overview, main components, how they fit together
- Executive: What the project does, its purpose, no technical details

**File Descriptions (files/*/*.*.md)**
- Three separate files per code file
- Each level provides appropriate depth
- Inconsistency warnings included at all levels when detected

**Edge Descriptions (edges/*.*.md)**
- Three separate files per relationship
- Technical: "auth.py calls utils.hash_password(password: str) -> str, expects SHA256 hash"
- Developer: "Authentication module uses utility functions for password hashing"
- Executive: "User login system connects to security components"

**inconsistencies.md**
- Single file at technical level only
- Detailed technical explanations of issues
- Referenced by file descriptions at all levels
- **Format**:
```markdown
## Inconsistency: Authentication Flow Broken
**Files Involved**: src/auth.py, src/user.py
**Triggered By**: Removal of hash_password() from src/utils.py
**Reason**: auth.py expects hash_password() to exist in utils.py for user login, but this function was removed in the latest changes. The authentication flow can no longer hash passwords before comparison.
**Change Summary**: utils.py was refactored to remove cryptographic functions, breaking downstream authentication logic.
---
```

### 5. Functional Requirements

#### 5.1 CLI Interface (Updated)

**Primary Commands:**
```bash
# Initialize a new project
semanticize init [--given-description path/to/existing.md]

# Update after code changes
semanticize update

# Check consistency status
semanticize check

# Launch web viewer
semanticize launch

# Version and help
semanticize --version
semanticize --help
```

**Given Description Option**: The `--given-description` flag allows bootstrapping with an existing description to save time and tokens on large codebases. It trusts the provided description as ground truth and uses it as context while analyzing files, significantly reducing the analysis burden.

Note: Abstraction levels are not exposed in CLI as they're for information retrieval only.

#### 5.2 Core Operations with Multi-Level Support

**Initialization (`semanticize init`)**

Updated process for three levels:

1. **Discovery Phase** (unchanged)
   - Scan project directory structure
   - Apply ignore rules
   - Build file list with line counts for progress tracking

2. **Deep Analysis Phase**
   - Process files starting from dependency leaves
   - For each file, generate all three abstraction levels:
     - Start with technical (most comprehensive)
     - Derive developer level from technical understanding
     - Distill executive level from developer understanding
   - Create edge descriptions at all three levels

3. **Synthesis Phase**
   - Generate project-level descriptions at all three levels
   - Technical: Full architectural documentation
   - Developer: System overview and component relationships
   - Executive: What the system does and why

4. **Progress Reporting**
   - Show weighted progress bar: `[=====>    ] 45% (23/51 files)`
   - Weight by file size (lines of code)
   - Update in real-time

**Update (`semanticize update`)**

Enhanced propagation with level-aware updates:

1. **Change Detection** (unchanged)
   - Identify which files changed

2. **Level Determination**
   For each changed file, LLM evaluates:
   ```
   a) Do we need to update the technical level?
   b) If yes to (a), do we need to update developer level?
   c) If yes to (b), do we need to update executive level?
   ```

3. **Propagation Algorithm with Detailed Example**
   ```
   For each changed file F:
     Determine update levels needed for F
     For each edge E connected to F:
       Read E's technical description (source of truth)
       Analyze: "Given the changes to F, would the relationship change?"
       If YES:
         Determine which levels of E need updating
         Update E's descriptions at required levels
         Add connected file to propagation queue
       If NO:
         Do not propagate further on this path
   ```
   
   **Example Scenario**: File A imports a print function from File B
   1. Developer fixes a math typo in File A
   2. System examines edge A--TO--B: "File A uses print_result() from File B for output"
   3. System evaluates: "Does fixing a math typo affect how A uses B's print function?"
   4. Answer: No - the relationship remains the same
   5. System does NOT examine File B or any of its dependencies
   6. Propagation stops, saving time and preserving accuracy

4. **Regeneration Phase**
   - Regenerate required levels for marked files
   - Use technical level as source of truth
   - Maintain consistency across levels
   - **Consistency Instructions**:
     - "Maintain all accurate information from the previous version"
     - "Update only what has changed due to code modifications"
     - "Do not remove correct information or introduce variations for style"
     - "Focus on accuracy over variety in phrasing"

5. **Inconsistency Handling**
   - Detect at technical level
   - If inconsistency found, mark all levels of affected file
   - Include warning in all three abstraction levels

#### 5.3 Web Viewer (MVP)

**Launch Command**: `semanticize launch`
- Starts local web server (e.g., http://localhost:8080)
- No integration with CLI beyond launch
- Read-only viewer for markdown files

**Interface Layout**:
```
+------------------+---------------------------+------------------+
|                  |                           |                  |
|  File Explorer   |     Content Viewer        | Relationships    |
|                  |                           |                  |
|  - src/          | [Technical|Developer|Exec] |  Depends on:    |
|    - main.py     |                           |  - utils.py     |
|    - utils.py    |  main.py                  |    [expand]      |
|                  |                           |                  |
|                  |  This file handles the    |  Depended by:   |
|                  |  main application entry   |  (none)          |
|                  |  point...                 |                  |
|                  |                           |                  |
+------------------+---------------------------+------------------+
```

**Features**:
- Left panel: File tree navigation
- Center panel: 
  - Toggle between Code view and English view
  - In English view, tabs for Technical/Developer/Executive
  - Markdown rendering with syntax highlighting
- Right panel:
  - List of connected files
  - Expandable to show edge descriptions
  - Level selector applies to edge descriptions too

**Technical Implementation**:
- Simple static file server
- Client-side JavaScript for navigation
- No backend API needed - reads markdown directly
- Responsive design for readability

### 6. Technical Implementation Updates

#### 6.1 Level-Aware Update Intelligence

**Update Decision Tree**:
```
1. File changed: Analyze scope of changes
2. Technical update needed? 
   - YES: Continue to step 3
   - NO: No updates needed, stop
3. Developer update needed?
   - YES: Continue to step 4
   - NO: Update technical only, stop
4. Executive update needed?
   - YES: Update all three levels
   - NO: Update technical and developer only
```

**Rationale**: Changes flow upward through abstraction levels. Technical changes don't always affect developer understanding, and developer changes don't always affect executive summaries.

#### 6.2 Dependency Detection Strategy

**For Python (MVP Focus):**

1. **Explicit Dependencies**
   - Use Python's `ast` module to parse import statements
   - Track both `import` and `from...import` patterns
   - Handle relative and absolute imports
   - Build directed graph of explicit dependencies

2. **Semantic Dependencies**
   - LLM analysis to find non-import relationships
   - Examples: shared constants, implicit protocols, duck typing
   - Mark these separately from explicit imports
   - Include in edge descriptions with relationship type

3. **Graph Construction**
   - Nodes: All Python files in project
   - Edges: Both explicit and semantic dependencies
   - Attributes: Relationship descriptions, last updated timestamp
   - Stored in memory during operation, persisted to markdown

**Future Language Support:**
- Design allows language-agnostic operation
- LLMs can understand most languages
- Only dependency detection needs language-specific logic

#### 6.3 LLM Integration Details

**Output Format Validation**
All LLM responses must follow:
```
[filename]:
```markdown
[content here]
```

The system:
- Allows LLM to "think out loud" before the marker
- Validates presence of filename and code fence markers
- Retries with clarification if format is incorrect (max 3 attempts)
- Prevents partial updates on failure

#### 6.4 Prompt Engineering for Levels

**Technical Level Prompts**:
- "Provide comprehensive technical documentation"
- "Include implementation details, algorithms, data structures"
- "Explain HOW the code works, not just what it does"

**Developer Level Prompts**:
- "Summarize at function and class level"
- "Focus on component purposes and interactions"
- "Assume reader understands programming but not this specific code"

**Executive Level Prompts**:
- "Explain in 1-2 paragraphs maximum"
- "No technical jargon or implementation details"
- "Focus on business value and purpose"
- "Assume reader has no programming knowledge"

#### 6.5 Consistency Across Levels

**Generation Order**:
1. Always generate technical first (most complete information)
2. Use technical content to inform developer level
3. Use developer content to inform executive level

**Update Consistency**:
- When updating multiple levels, provide previous versions
- Instruction: "Maintain consistency with technical level as source of truth"
- Validate that higher levels don't contradict lower levels

#### 6.6 Dynamic Ignore System

**Default Behavior:**
- Respect all .gitignore patterns
- Common non-code patterns (*.jpg, *.png, etc.)
- Build directories and cache folders

**AI-Driven Ignoring:**
- Before analyzing a file, LLM can recognize non-code content
- Automatically adds to .semanticizeignore
- Example: "Detected binary file", "Detected data file"
- Prevents wasted tokens on irrelevant files

**Manual Overrides:**
- Users can edit .semanticizeignore directly
- Can force inclusion of normally ignored files
- Useful for configuration files that affect code behavior

### 7. MVP Scope (Updated)

#### 7.1 Included in MVP

**Core Functionality**:
- Three abstraction levels for all documents
- Python language support with AST-based dependency detection
- Level-aware update propagation
- CLI interface (no level selection needed)
- Basic web viewer with level toggle
- Technical level as source of truth
- Inconsistency detection at technical level
- Gemini CLI integration for LLM operations
- Progress reporting with weighted progress bar
- Dynamic ignore system

**Web Viewer MVP**:
- Local-only server
- File tree navigation
- Code/English toggle
- Technical/Developer/Executive tabs
- Relationship panel with expandable descriptions
- Static file serving (no backend API)

**Performance Targets**:
- < 5 minutes for 100-file codebase initial analysis
- < 30 seconds per commit for updates
- Efficient propagation to minimize unnecessary regeneration

#### 7.2 Future Enhancements

- Search across all levels
- Level-specific customization
- Export single level documentation
- API for retrieving specific levels
- Visualization of relationships at different levels
- Mobile-optimized web viewer
- Multiple LLM provider support
- Real-time file watching
- Git hook templates

### 8. Success Criteria (Updated)

1. **Level Appropriateness**: Each abstraction level serves its target audience
2. **Consistency**: All three levels tell the same story at different depths
3. **Update Efficiency**: Only necessary levels regenerate
4. **Technical Accuracy**: Technical level captures all important details
5. **Executive Clarity**: Executive level readable by non-programmers
6. **Navigation**: Web viewer allows easy browsing at preferred level
7. ** Performance**: Meets targets for analysis and update times

### 9. Error Handling

**LLM Failures:**
- Clear error message indicating which file failed
- No partial updates - transaction-like behavior
- Suggestion to retry with --verbose flag
- Log problematic prompts for debugging

**Malformed LLM Responses:**
- Retry with clarified format instructions
- Maximum 3 retry attempts
- Save raw response for debugging
- Clear error message if all retries fail

**File System Issues:**
- Skip inaccessible files with warning
- Continue processing other files
- Report summary of skipped files at end
- Non-zero exit code if critical files skipped

**Large File Handling:**
- Warn when files exceed token limits
- Attempt chunking strategies (future enhancement)
- Allow manual splitting of large files
- Document limitations in error message

### 10. Integration Patterns

**Manual Trigger (MVP):**
```bash
# Developer manually runs after changes
$ semanticize update
```

**Git Hook Integration (User Configured):**
```bash
# In .git/hooks/post-commit
#!/bin/sh
semanticize update
```

**AI Tool Integration:**
```bash
# AI coding assistant checks before making changes
$ semanticize check || echo "Warning: Inconsistencies detected"
# AI can read inconsistencies.md to understand issues
```

**File Watcher (Future):**
```bash
# Automatic updates on file save
$ semanticize watch
```

### 11. Examples of Multi-Level Documentation

**File: src/auth.py**

*Technical Level*:
```markdown
This module implements user authentication using SHA256 password hashing. The authenticate_user function accepts username (str) and password (str), retrieves the user record from the database using UserModel.get_by_username(), hashes the provided password using utils.hash_password(), and compares it with stored hash using constant-time comparison to prevent timing attacks...
```

*Developer Level*:
```markdown
Handles user authentication for the application. Main functions include authenticate_user() for login verification and register_user() for new account creation. Uses secure password hashing from utils module and interfaces with User model for data persistence.
```

*Executive Level*:
```markdown
Manages user login and registration, ensuring passwords are securely stored and verified.
```

**Edge: src/auth.py--TO--src/utils.py**

*Technical Level*:
```markdown
auth.py imports hash_password(password: str) -> str and constant_time_compare(a: str, b: str) -> bool from utils.py. Uses hash_password in register_user() line 45 and authenticate_user() line 67. Expects SHA256 hex digest output.
```

*Developer Level*:
```markdown
Authentication module uses utility functions for password hashing and secure comparison operations.
```

*Executive Level*:
```markdown
User security features rely on shared utility components.
```

---
