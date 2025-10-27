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
[x] Identify the documents to change and make the changes. If there is no document to change, quit.
[x] When running as a Github Action, if there is any documents changed, create a Git commit and push it back to the pull request.
[x] Add a new agent that reads the description of the Github pull request. The description is in Markdown format and contains configurations of DocuCat. The agent should read the description and respond with a JSON object like `{ "enabled": true/false, "shouldCreateCommits": true/false }`. Name the file of the agent as configuration_expert.py.
[x] When running as a Github action, the agent should create a comment summarizing the document changes to the pull request. If there is no document change, the agent should still create a comment explaining there is no document change to commit.
[x] When running as a Github action, the agent should be aware of all comments of a pull request. The tasks of the agent should be subject to the instructions of the comments of the developers.
[x] DocuCat should be triggered by a new comment mentioning @DocuCat.
[x] Add a command to initialize the local vector store. The command runs locally and take an argument to the path of the target repository. It creates an empty Milvus Lite store inside the folder .docucat.
[x] When initializing the local vector store, it actually scans for all files in the repository whose file types are supported by langchain_text_splitters. It uses RecursiveCharacterTextSplitter to split chunks with chunk_size=200 and chunk_overlap=30. Files with file types that are not supported by langchain_text_splitters are not scanned. Store each chunk in the local vector store. In this task, leave the field `embedding` empty.
[x] Modify the command `init_vector_store`. The command name should be `rag`. The command of initializing a vector store is `rag --init`. The command to force initialing a vector store should be `rag --force-init`. The command to display the info is `rag --info`.
[x] The file vector_store should not contain anything that are related to the command: 1. it cannot be run as a command, i.e., do not use argparse to accept arguments. 2. The functions should not print any user-facing messages. The functions can return important data and the `rag` command use those data to print user-facing messages.
[x] When storing each chunk into the vector store, use Gemini embedding with task type `RETRIEVAL_DOCUMENT` to generate an embedding for each chunk. Use an embedding size of 1536. Use environment variable `GEMINI_API_KEY` for Gemini.
[x] Add a new tool for agents in the folder tools. The tool should accept a query to query chunks from the local vector store and returns the top 10 chunks that are more relevant to the query. The query should be embeded using Gemini embedding model `models/gemini-embedding-001` with a dimension 1536 and task type `RETRIEVAL_QUERY`. The new tool should be given to the agent analyzer if there are local vector store available.
[ ] Change the avatar and name of the automatic commit.
[ ] More tasks to be added...

## Coding Conventions

### Comments

- Do not mention the project name in comments.
