"""
Chat agent.
Owner: Person 3

Answers questions using the memory store.
Uses run_memory_session for persistence.
"""

from core import run_memory_session, log_event


def chat(question: str) -> str:
    """Answer a question using institutional memory.

    Uses run_memory_session to access the memory store, enabling knowledge search
    over client interactions, team decisions, and documented processes. Slow
    (container start) but persists insights for future sessions.

    Args:
        question: User's question to answer

    Returns:
        Answer string drawn from institutional memory

    Raises:
        Exception: If memory session fails
    """
    if not question or not question.strip():
        return "Please ask a question."

    log_event("chat", "answer", "running", f"question={question[:50]}")
    try:
        prompt = f"""You are a helpful assistant with access to institutional memory.
Answer the following question based on the information in memory, including client engagements, team decisions, and documented processes.

Question: {question}

Provide a clear, concise answer grounded in the memory. If you don't have information to answer, say so."""

        # Memory session starts a container and searches memory store
        response = run_memory_session(prompt, title=f"Chat: {question[:50]}")
        log_event("chat", "answer", "done")
        return response

    except Exception as e:
        log_event("chat", "answer", "error", str(e))
        raise
