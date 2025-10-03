# Semanticize Usage Example

This guide shows how to use Semanticize with OpenRouter (or any OpenAI-compatible API).

## Step 1: Setup API Configuration

```bash
$ semanticize setup
=== Semanticize API Setup ===

Select provider:
  1. OpenRouter
  2. OpenAI
  3. Custom (any OpenAI-compatible API)

Enter choice [1-3]: 1
Base URL [https://openrouter.ai/api/v1]:
API Key: [your-api-key-here]
Example model: anthropic/claude-3.5-sonnet
Model name: anthropic/claude-3.5-sonnet

✓ Configuration saved successfully!
  Location: .semanticize/config.json

You can now run 'semanticize init' to analyze your codebase.
```

## Step 2: Initialize Your Project

```bash
$ cd /path/to/your/project
$ semanticize init
Initializing Semanticize...
Created .semanticize

=== Phase 1: Discovery ===
Discovered 15 files
Building dependency graph...

=== Phase 2: Deep Analysis ===
[========================================>] 100% (15/15 files)

=== Phase 3: Synthesis ===
Generating technical project summary...
Generating developer project summary...
Generating executive project summary...

✓ Initialization complete!
  - Analyzed 15 files
  - Created documentation at 3 abstraction levels
  - Documentation stored in .semanticize

Run 'semanticize launch' to view the documentation
```

## Step 3: Handle Interruptions (if needed)

If initialization is interrupted (API quota, network issue, etc.):

```bash
$ semanticize fix
Checking project state...

Current state:
Files: 8/15 complete

Incomplete files (7):
  - src/utils.py: missing developer, executive
  - src/api.py: missing technical, developer, executive
  ...

Continue fixing? [y/N] y

=== Completing File Documentation (7 files) ===
[1/7] src/utils.py: developer, executive
  ✓ developer
  ✓ executive
...

✓ Project is now fully initialized!
  Run 'semanticize launch' to view the documentation
```

## Step 4: View Documentation

```bash
$ semanticize launch
Starting Semanticize viewer at http://localhost:8080
Press Ctrl+C to stop
```

Open your browser to http://localhost:8080 and explore:
- **File tree** on the left
- **Code/English toggle** in the center
- **Technical/Developer/Executive** level tabs
- **Dependencies/Dependents** on the right

## Step 5: Update After Changes

After modifying code:

```bash
$ semanticize update
Updating documentation...

=== Phase 1: Change Detection ===
Detected 2 changed files

=== Phase 2: Propagation ===
src/api.py: technical, developer
src/utils.py: technical
Propagation complete: 3 files affected

=== Phase 3: Regeneration ===
[1/3] Updating src/api.py...
[2/3] Updating src/utils.py...
[3/3] Updating src/main.py...

=== Phase 4: Inconsistency Check ===
No inconsistencies detected

✓ Update complete!
  - Updated 3 files
```

## Step 6: Check Consistency

```bash
$ semanticize check
✓ No inconsistencies detected
```

## Example OpenRouter Models

- `anthropic/claude-3.5-sonnet` (recommended)
- `anthropic/claude-3-opus`
- `openai/gpt-4`
- `openai/gpt-4-turbo`
- `google/gemini-pro-1.5`

## Tips

1. **Start small**: Test on a small project first to understand the system
2. **Use `fix` liberally**: If anything interrupts initialization, just run `semanticize fix`
3. **Monitor costs**: Check your API provider's pricing and set usage limits
4. **Ignore unnecessary files**: Add patterns to `.semanticize/.semanticizeignore`
5. **Bootstrap with context**: Use `--given-description` to provide project context

## Troubleshooting

### "API query failed"
- Check your API key is correct
- Verify you have credits/quota remaining
- Test your API connection manually

### "Too many files"
- Add ignore patterns in `.semanticize/.semanticizeignore`
- Or use `.gitignore` which is automatically respected

### Slow initialization
- Normal for large codebases
- Each file requires 3 LLM calls (technical, developer, executive)
- Plus additional calls for edges between files
- Use `fix` command to pause and resume

## Configuration File Format

The `.semanticize/config.json` looks like:

```json
{
  "base_url": "https://openrouter.ai/api/v1",
  "api_key": "sk-or-v1-...",
  "model": "anthropic/claude-3.5-sonnet",
  "use_legacy_cli": false
}
```

You can edit this manually if needed, then re-run your commands.
