# AGENTS Guidelines for This Repository

This repository contains the DocuCat, an AI assistant that generates or updates documents from changes of a Github pull request.

## Description of DocuCat.

DocuCat is an AI assistant that generates or updates documents from changes of a Github pull request.

- DocuCat is a Github repository that contains all codes for generating or updating documents from changes of a Github pull request. Other repositories can include DocuCat as a Github Action that runs after creation of pull requests.
- DocuCat creates a new commit to the pull request if there are documents that need to be changed. It only creates a new commit when running as a Github Action.
- DocuCat can create embeddings for all codes and documents of a repository and store them in a local vector store using Milvus Lite.
- DocuCat can use the local vector store to search codes and documents.
- When running as a Github Action in another repository, DocuCat first reads the file README.md and AGENTS.md to understand the code structure and document structure if they exist.
- DocuCat can also be run locally. It accepts a path to another repository. It also accepts a count parameter that represents the number of past commits counted as new commits.
- DocuCat is implemented with LangGraph.
- DocuCat uses commands and Python file operations to read, create, modify or delete files.

## Steps to Create DocuCat

DocuCat is in construction. You should follow the task list below to create DocuCat. Always do one incomplete task at a time.

[x] Make DocuCat be able to run as a Github Action in another repository. It simply prints the changed files in a pull request.
[x] Use `uv` to manage Python dependencies both locally and in Github Action.
[x] Add an entry file to run DocuCat locally.
[x] Add LangGraph and use Claude Haiku 4.5 to understand the intents of the changes.
[x] Add a tool `run_command` to execute a command and get the result. Modify the LangGraph workflow to be able to call tools. Add the tool `run_command` to the agent workflow.
[ ] Identify the documents to change and make the changes. If there is no document to change, quit.
[ ] Add a command to initialize the local vector store and create embeddings for all codes and documents.
[ ] More tasks to be added...

## Coding Conventions

### Comments

- Do not mention the project name in comments.
