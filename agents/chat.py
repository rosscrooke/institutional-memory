"""
Chat agent.
Owner: Person 3

SPEC (build from this; keep the function signature)

Purpose
    Answer questions about the company ("Who owns payments?", "How do I get
    prod access?", "What changed this week?") from persistent institutional
    memory, not from whatever the model happens to know. This is the demo's
    centrepiece: the answer must visibly come from /mnt/memory/.

Input
    question: str from the chat box or a suggested-prompt button.
    Optional extension: history: list[{"role","content"}] for follow-ups.
    If you add it, give it a default so ui/ask.py keeps working.

Output
    str: markdown answer. Structure it as:
      1. Direct answer first (one or two sentences).
      2. Supporting details as short bullets.
      3. "Sources:" line naming the memory files or item titles used.
      4. If memory has conflicting or outdated info, say so and state which is
         newer. If memory doesn't contain the answer, say "I don't have that in
         memory yet" and name what to add. Never guess.

Implementation
    - Call run_memory_session(message, title="Chat: <question[:60]>") from
      core.py. The Managed Agent already has the memory store mounted at
      /mnt/memory/ (see create_agent.py and run_session_2.py for the pattern).
    - Build the message yourself: restate the question, tell the agent to
      read /mnt/memory/ first, to prefer the newest facts, to cite files, and
      to format as above. Don't rely on the default system prompt alone.
    - Optionally pass recent local context (the latest 3 item titles) so
      "what changed this week?" has a time anchor. Keep it short.
    - Sessions start a container and are SLOW (tens of seconds). The UI must
      show st.spinner. Consider caching identical questions in
      st.session_state for the suggested prompts.
    - log_event("chat", "answer", "running"|"done"|"error", question[:100]).

Edge cases
    - Empty or whitespace question: raise ValueError, no session.
    - Missing .agent_id / .environment_id / .memory_store_id: run_memory_session
      raises; catch it and return a readable explanation, not a traceback.
    - Memory is empty (before any ingest): answer "memory is empty" with a
      pointer to the Inputs tab.
    - Prompt injection inside stored documents ("ignore previous instructions"):
      treat memory content as data, never as instructions. Say so in your
      message to the agent.
    - Questions about people's private data: answer only what the stored docs
      support.

Done when
    - After seeding round1, "Who owns payments?" is answered from memory with a
      source.
    - After ingesting round2, the same question returns the UPDATED answer and
      says the older one was superseded.
    - An unknown question gets "I don't have that in memory yet".
"""


def chat(question: str) -> str:
    """Answer a question using institutional memory. See module SPEC."""
    raise NotImplementedError("Person 3 to implement")
