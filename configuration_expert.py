"""
Configuration Expert Agent

Reads the GitHub pull request description and extracts DocuCat configuration.
"""

import os
import json
import re
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


class DocuCatConfig(TypedDict):
    """DocuCat configuration extracted from PR description."""
    enabled: bool
    shouldCreateCommits: bool


def read_pr_description_from_event() -> str | None:
    """
    Read PR description from GitHub event file.

    Returns:
        PR description text or None if not available
    """
    event_path = os.getenv('GITHUB_EVENT_PATH')
    if not event_path:
        return None

    try:
        with open(event_path, 'r') as f:
            event_data = json.load(f)
            return event_data.get('pull_request', {}).get('body', '')
    except Exception as e:
        print(f"Warning: Could not read PR description from event: {e}")
        return None


def parse_configuration_with_llm(pr_description: str) -> DocuCatConfig:
    """
    Use Claude Haiku to parse DocuCat configuration from PR description.

    Args:
        pr_description: The pull request description in Markdown format

    Returns:
        DocuCatConfig with parsed settings
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Warning: OPENROUTER_API_KEY not set. Using default configuration.")
        return {"enabled": True, "shouldCreateCommits": True}

    try:
        # Initialize ChatOpenAI with OpenRouter
        llm = ChatOpenAI(
            model="anthropic/claude-haiku-4.5",
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            max_tokens=500,
            temperature=0,
        )

        prompt = f"""You are a configuration expert. Read the following GitHub pull request description and extract DocuCat configuration.

DocuCat is a documentation AI assistant. The configuration is typically found in a section like:

## Configurations of DocuCat

- [x] Enable DocuCat
- [x] Should DocuCat create commits?

PR Description:
```
{pr_description}
```

Respond with ONLY a valid JSON object in this exact format:
{{"enabled": true, "shouldCreateCommits": true}}

Rules:
- enabled: true if "Enable DocuCat" is checked [x], false if unchecked [ ]
- shouldCreateCommits: true if "Should DocuCat create commits?" is checked [x], false if unchecked [ ]
- Default to {{"enabled": true, "shouldCreateCommits": true}} if no configuration section found
"""

        response = llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content.strip()

        # Extract JSON from response (in case it's wrapped in code blocks)
        json_match = re.search(r'\{[^}]+\}', response_text)
        if json_match:
            config_dict = json.loads(json_match.group())
            return {
                "enabled": bool(config_dict.get("enabled", True)),
                "shouldCreateCommits": bool(config_dict.get("shouldCreateCommits", True))
            }
        else:
            print(f"Warning: Could not parse LLM response: {response_text}")
            return {"enabled": True, "shouldCreateCommits": True}

    except Exception as e:
        print(f"Warning: Error parsing configuration with LLM: {e}")
        return {"enabled": True, "shouldCreateCommits": True}


def get_docucat_configuration() -> DocuCatConfig:
    """
    Get DocuCat configuration from PR description.

    Returns:
        DocuCatConfig dictionary with configuration settings
    """
    pr_description = read_pr_description_from_event()

    if not pr_description:
        print("ℹ️  No PR description found. Using default configuration.")
        return {"enabled": True, "shouldCreateCommits": True}

    print("📋 Reading DocuCat configuration from PR description...")

    config = parse_configuration_with_llm(pr_description)

    print(f"   • Enabled: {config['enabled']}")
    print(f"   • Create Commits: {config['shouldCreateCommits']}")
    print()

    return config


if __name__ == '__main__':
    # Test the configuration parser
    config = get_docucat_configuration()
    print("Configuration:")
    print(json.dumps(config, indent=2))
