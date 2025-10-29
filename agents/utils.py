from langchain_core.messages import AIMessage


def getResultFromMessages(messages: list) -> str:
    """
    Get the result from the messages.

    Args:
        messages: List of messages

    Returns:
        Result from the messages
    """
    analysis = ""
    documents_updated = []
    no_updates_needed = False

    # Find the final AI response
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content:
            analysis = message.content
            break

    # Check if agent indicated no updates needed
    if "NO_UPDATES_NEEDED" in analysis:
        no_updates_needed = True

    # Find all write_file tool calls to determine which documents were updated
    for message in messages:
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call.get("name") == "write_file":
                    filepath = tool_call.get("args", {}).get("filepath")
                    if filepath and filepath not in documents_updated:
                        documents_updated.append(filepath)
    
    return {
        "analysis": analysis if analysis else "No analysis available",
        "documents_updated": documents_updated,
        "no_updates_needed": no_updates_needed
    }
