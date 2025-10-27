#!/usr/bin/env python3
"""
Test script for comment instructions parser
Demonstrates how developer instructions are parsed from PR comments.
"""

from comment_instructions_parser import parse_comment_instructions, format_instructions_for_analysis


def test_instruction_parsing():
    """Test various PR comment scenarios."""

    test_cases = [
        {
            "name": "Explicit DocuCat skip",
            "comments": [
                {
                    'user': 'developer1',
                    'body': '@DocuCat skip - no documentation needed for this PR',
                    'created_at': '2024-01-01T10:00:00Z'
                }
            ],
            "expected": "should_run_docu_cat: false"
        },
        {
            "name": "DocuCat with instructions",
            "comments": [
                {
                    'user': 'developer1',
                    'body': '@DocuCat please update the API documentation to include the new authentication endpoints',
                    'created_at': '2024-01-01T10:00:00Z'
                }
            ],
            "expected": "should_run_docu_cat: true, with instructions"
        },
        {
            "name": "Multiple instructions",
            "comments": [
                {
                    'user': 'developer1',
                    'body': 'DocuCat: update README.md with the new installation steps',
                    'created_at': '2024-01-01T10:00:00Z'
                },
                {
                    'user': 'developer2',
                    'body': 'Also make sure to update the API docs',
                    'created_at': '2024-01-01T11:00:00Z'
                }
            ],
            "expected": "should_run_docu_cat: true, combined instructions"
        },
        {
            "name": "Specific files mentioned",
            "comments": [
                {
                    'user': 'reviewer',
                    'body': 'Please make sure CHANGELOG.md and docs/api.md are updated',
                    'created_at': '2024-01-01T12:00:00Z'
                }
            ],
            "expected": "should_run_docu_cat: true, with file-specific instructions"
        },
        {
            "name": "Normal PR review (no instructions)",
            "comments": [
                {
                    'user': 'developer',
                    'body': 'LGTM! Great work on this feature.',
                    'created_at': '2024-01-01T13:00:00Z'
                }
            ],
            "expected": "should_run_docu_cat: true, no specific instructions"
        },
        {
            "name": "Empty comments list",
            "comments": [],
            "expected": "should_run_docu_cat: true, no instructions"
        }
    ]

    print("=" * 70)
    print("Comment Instructions Parser - Test Cases")
    print("=" * 70)
    print()
    print("NOTE: These tests require OPENROUTER_API_KEY to actually parse.")
    print("Without the API key, all tests will default to should_run_docu_cat: true")
    print()

    for test_case in test_cases:
        print(f"Test: {test_case['name']}")
        print("-" * 70)

        # Show comment preview
        if test_case['comments']:
            for i, comment in enumerate(test_case['comments'], 1):
                preview = comment['body'][:60] + "..." if len(comment['body']) > 60 else comment['body']
                print(f"  Comment {i} (@{comment['user']}): {preview}")
        else:
            print("  (No comments)")

        print()
        print(f"Expected: {test_case['expected']}")
        print()

    print("=" * 70)
    print()
    print("To actually test with LLM parsing:")
    print("  export OPENROUTER_API_KEY=your-key")
    print("  python3 comment_instructions_parser.py")
    print()
    print("New DeveloperInstructions structure:")
    print("  {")
    print('    "should_run_docu_cat": bool,  # false only if explicitly told to skip')
    print('    "instructions": str | None    # instructions or None if no instructions')
    print("  }")
    print()


if __name__ == '__main__':
    test_instruction_parsing()
