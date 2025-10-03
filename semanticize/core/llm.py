"""LLM interface using gemini subprocess."""

import subprocess
import re
from typing import Optional, Tuple
from pathlib import Path


class LLMInterface:
    """Interface to interact with LLM via gemini CLI."""

    MAX_RETRIES = 3

    def query(self, prompt: str) -> str:
        """Send a prompt to the LLM and get response."""
        try:
            result = subprocess.run(
                ['gemini', '-p', prompt],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                raise Exception(f"Gemini command failed: {result.stderr}")

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            raise Exception("LLM query timed out after 5 minutes")
        except FileNotFoundError:
            raise Exception("gemini command not found. Please ensure gemini CLI is installed and in PATH")

    def extract_markdown_content(self, response: str, filename_hint: Optional[str] = None) -> Optional[str]:
        """Extract markdown content from LLM response.

        Expected format:
        [optional thinking/explanation]
        filename:
        ```markdown
        content here
        ```
        """
        # Look for markdown code fence
        pattern = r'```(?:markdown)?\s*\n(.*?)\n```'
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            return matches[-1].strip()  # Return the last match

        # If no code fence, try to find content after filename marker
        if filename_hint:
            pattern = rf'{re.escape(filename_hint)}:\s*\n(.*)'
            match = re.search(pattern, response, re.DOTALL)
            if match:
                return match.group(1).strip()

        # Last resort: return the whole response if it looks like markdown
        if response.strip().startswith('#') or '\n#' in response:
            return response.strip()

        return None

    def query_with_retry(self, prompt: str, filename_hint: Optional[str] = None) -> Tuple[str, str]:
        """Query LLM with retry logic for format validation.

        Returns:
            Tuple of (raw_response, extracted_content)
        """
        for attempt in range(self.MAX_RETRIES):
            response = self.query(prompt)
            content = self.extract_markdown_content(response, filename_hint)

            if content:
                return response, content

            # Retry with clarification
            if attempt < self.MAX_RETRIES - 1:
                prompt += "\n\nPlease format your response with the content inside a markdown code fence like this:\n```markdown\n[content here]\n```"

        raise Exception(f"Failed to get properly formatted response after {self.MAX_RETRIES} attempts")


class PromptBuilder:
    """Builds prompts for different LLM operations."""

    @staticmethod
    def build_file_analysis_prompt(file_path: Path, file_content: str, level: str,
                                   dependencies: list = None, context: str = None) -> str:
        """Build prompt for analyzing a single file."""

        level_instructions = {
            'technical': """Provide comprehensive technical documentation that explains:
- What the code does and HOW it works
- Implementation details, algorithms, and data structures
- Near line-by-line equivalent detail
- Function signatures, parameters, and return values
This is for engineers needing complete understanding.""",

            'developer': """Provide function and class level summaries that explain:
- What components do (less focus on how)
- Big-picture understanding for quick comprehension
- High-level interaction patterns
This is for developers working with the code.""",

            'executive': """Provide a brief summary (1-2 paragraphs maximum) that explains:
- What the component accomplishes
- Business value and purpose
- No implementation details or technical jargon
This is for non-technical stakeholders."""
        }

        prompt = f"""Analyze the following code file and create {level} level documentation.

File: {file_path}

{level_instructions[level]}

"""
        if dependencies:
            prompt += f"\nThis file depends on: {', '.join(str(d) for d in dependencies)}\n"

        if context:
            prompt += f"\nProject Context:\n{context}\n"

        prompt += f"""
Code:
```
{file_content}
```

Respond with the documentation in this format:
{file_path}.{level}.md:
```markdown
[your documentation here]
```
"""
        return prompt

    @staticmethod
    def build_edge_analysis_prompt(source: Path, target: Path, source_content: str,
                                   target_content: str, level: str) -> str:
        """Build prompt for analyzing a relationship between files."""

        level_instructions = {
            'technical': """Describe the precise technical relationship:
- Specific function calls, imports, and parameters
- Data flow and return values
- Technical details of how they interact""",

            'developer': """Describe the high-level interaction:
- What kind of functionality is being used
- General interaction patterns
- Component-level relationship""",

            'executive': """Describe the relationship in simple terms:
- How these components work together
- No technical details
- Business-level connection"""
        }

        prompt = f"""Analyze the relationship between these two files at the {level} level.

Source file: {source}
Target file: {target}

{level_instructions[level]}

Source code:
```
{source_content}
```

Target code:
```
{target_content}
```

Respond with the edge description in this format:
{source}--TO--{target}.{level}.md:
```markdown
[your edge description here]
```
"""
        return prompt

    @staticmethod
    def build_project_summary_prompt(files_descriptions: dict, level: str) -> str:
        """Build prompt for creating project-level summary."""

        level_instructions = {
            'technical': """Create comprehensive architectural documentation including:
- Overall architecture and design patterns
- Key packages and libraries used
- How major components fit together technically
- Technical decisions and implementation approach""",

            'developer': """Create a system overview including:
- Main components and their purposes
- How they fit together at a high level
- Development-relevant information""",

            'executive': """Create a brief overview (2-3 paragraphs) including:
- What the project does
- Its purpose and value
- No technical details"""
        }

        prompt = f"""Based on the following file descriptions, create a {level} level project summary.

{level_instructions[level]}

File Descriptions:
"""
        for file_path, desc in files_descriptions.items():
            prompt += f"\n{file_path}:\n{desc}\n"

        prompt += f"""
Respond with the project summary in this format:
description.{level}.md:
```markdown
[your project summary here]
```
"""
        return prompt

    @staticmethod
    def build_update_check_prompt(file_path: Path, old_content: str, new_content: str,
                                  current_level: str) -> str:
        """Build prompt to check if an update is needed at a specific level."""

        prompt = f"""A file has been modified. Determine if the {current_level} level documentation needs to be updated.

File: {file_path}

Old content:
```
{old_content}
```

New content:
```
{new_content}
```

Consider if the changes affect the {current_level} level understanding:
- technical: Any implementation changes
- developer: Changes to function/class interfaces or behavior
- executive: Changes to overall purpose or business value

Respond with ONLY one of: YES or NO
"""
        return prompt

    @staticmethod
    def build_propagation_check_prompt(edge_description: str, source_file: Path,
                                      change_summary: str) -> str:
        """Build prompt to check if changes should propagate through an edge."""

        prompt = f"""A file has changed. Determine if this change affects its relationship with another file.

Changed file: {source_file}
Change summary: {change_summary}

Current relationship description:
{edge_description}

Given the changes, would this relationship description need to be updated?

Respond with ONLY one of: YES or NO
"""
        return prompt
