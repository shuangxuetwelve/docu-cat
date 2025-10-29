import os
from agents import agent_docu_cat_github


def main():
    """Main entry point for the action."""
    event_name = os.getenv('GITHUB_EVENT_NAME')
    pr_number = os.getenv('PR_NUMBER')
    repository = os.getenv('GITHUB_REPOSITORY')
    token = os.getenv('GITHUB_TOKEN')
    base_sha = os.getenv('BASE_SHA')
    head_sha = os.getenv('HEAD_SHA')

    initial_state = {
        "repo_path": repository,
        "changed_files": [],
        "messages": [],
    }

    result = agent_docu_cat_github.invoke(initial_state)
    print(result)

if __name__ == '__main__':
    main()
