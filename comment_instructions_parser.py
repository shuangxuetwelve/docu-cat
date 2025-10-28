"""
Comment Instructions Parser

Parses developer instructions from PR comments to guide DocuCat's behavior.
"""

import os
from typing import Optional, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


class DeveloperInstructions(TypedDict):
    """Developer instructions extracted from PR comments."""
    should_run_docu_cat: bool
    instructions: Optional[str]


def parse_comment_instructions(comments: list[dict]) -> DeveloperInstructions:
    """
    Parse developer instructions from PR comments using LLM.

    Args:
        comments: List of comment dictionaries with 'user', 'body', 'created_at'

    Returns:
        DeveloperInstructions dictionary with parsed instructions
    """
    if not comments:
        return {
            "should_run_docu_cat": True,
            "instructions": None
        }

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Warning: OPENROUTER_API_KEY not set. Cannot parse comment instructions.")
        return {
            "should_run_docu_cat": True,
            "instructions": None
        }

    try:
        # Initialize ChatOpenAI with OpenRouter
        llm = ChatOpenAI(
            model="anthropic/claude-haiku-4.5",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            max_tokens=1000,
            temperature=0,
        )

        # Format comments for the prompt
        comments_text = ""
        for i, comment in enumerate(comments, 1):
            comments_text += f"Comment #{i} by @{comment['user']}:\n{comment['body']}\n\n"

        prompt = f"""You are analyzing GitHub pull request comments to determine if DocuCat (an AI documentation assistant) should run and what instructions to follow.

Look for comments that:
1. Explicitly tell DocuCat NOT to run (e.g., "skip DocuCat", "@DocuCat skip", "no docs needed")
2. Provide instructions for DocuCat on what to document

PR Comments:
```
{comments_text}
```

Analyze these comments and determine:
1. Should DocuCat run? (false only if explicitly told to skip/not run)
2. What instructions should DocuCat follow? (if any)

Examples:
- "@DocuCat skip" → should_run_docu_cat: false
- "No documentation needed" → should_run_docu_cat: false
- "@DocuCat update API docs" → should_run_docu_cat: true, instructions: "Update API documentation"
- "Please update README.md" → should_run_docu_cat: true, instructions: "Update README.md"
- Normal review comments → should_run_docu_cat: true, instructions: null

Respond with ONLY a valid JSON object in this exact format:
{{
  "should_run_docu_cat": true/false,
  "instructions": "natural language summary of instructions" OR null
}}

Rules:
- should_run_docu_cat: false ONLY if explicitly told to skip/not run DocuCat
- should_run_docu_cat: true for normal PRs without skip instructions
- instructions: combined natural language summary of all documentation instructions, or null if none
- Be concise but include all important details in instructions
"""

        response = llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content.strip()

        # Extract JSON from response
        import re
        import json
        json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            should_run = result.get("should_run_docu_cat", True)
            instructions = result.get("instructions")

            # If should_run_docu_cat is false, instructions should be None
            if not should_run:
                instructions = None

            return {
                "should_run_docu_cat": bool(should_run),
                "instructions": instructions
            }
        else:
            print(f"Warning: Could not parse LLM response for comment instructions")
            return {
                "should_run_docu_cat": True,
                "instructions": None
            }

    except Exception as e:
        print(f"Warning: Error parsing comment instructions: {e}")
        return {
            "should_run_docu_cat": True,
            "instructions": None
        }


def format_instructions_for_analysis(instructions: DeveloperInstructions) -> str:
    """
    Format developer instructions for inclusion in the analysis prompt.

    Args:
        instructions: DeveloperInstructions dictionary

    Returns:
        Formatted instructions string for the prompt, or empty string if no instructions
    """
    if not instructions.get('instructions'):
        return ""

    formatted = "\n\n**IMPORTANT - Developer Instructions:**\n"
    formatted += f"{instructions['instructions']}\n"
    formatted += "\nPlease follow these instructions when updating documentation.\n"

    return formatted


if __name__ == '__main__':
    # Test the comment instructions parser
    import json

    test_comments = [
        {
            'user': 'developer1',
            'body': '@DocuCat please make sure to update the API documentation with the new endpoints',
            'created_at': '2024-01-01T10:00:00Z'
        },
        {
            'user': 'developer2',
            'body': 'LGTM! Also update the README with installation steps.',
            'created_at': '2024-01-01T11:00:00Z'
        }
    ]

    instructions = parse_comment_instructions(test_comments)
    print("Parsed Instructions:")
    print(json.dumps(instructions, indent=2))

    if instructions['should_run_docu_cat'] and instructions['instructions']:
        print("\nFormatted for Analysis:")
        print(format_instructions_for_analysis(instructions))
    elif not instructions['should_run_docu_cat']:
        print("\nDocuCat should NOT run (explicitly skipped)")
    else:
        print("\nDocuCat should run with no specific instructions")
