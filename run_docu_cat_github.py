import os
from agents import agent_docu_cat_github
from langfuse.langchain import CallbackHandler
import uuid


langfuse_handler = CallbackHandler()
langfuse_session_id = uuid.uuid4()

def main():
    """Main entry point for the action."""
    event_name = os.getenv('GITHUB_EVENT_NAME')
    pr_number = os.getenv('PR_NUMBER')
    repository = os.getenv('GITHUB_REPOSITORY')
    token = os.getenv('GITHUB_TOKEN')
    base_sha = os.getenv('BASE_SHA')
    head_sha = os.getenv('HEAD_SHA')

    initial_state = {
        "repo_path": os.getenv('GITHUB_WORKSPACE', os.getcwd()),
        "changed_files": [],
        "messages": [],
        "token": token,
        "repository": repository,
        "pr_number": pr_number,
        "base_sha": base_sha,
        "head_sha": head_sha,
    }

    print(f"Calling the agent with Langfuse session ID: {str(langfuse_session_id)}")
    result = agent_docu_cat_github.invoke(initial_state, config={"callbacks": [langfuse_handler], "metadata": {"langfuse_session_id": str(langfuse_session_id)}})
    print(result)

if __name__ == '__main__':
    main()
