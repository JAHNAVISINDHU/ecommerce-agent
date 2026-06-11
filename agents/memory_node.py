"""
agents/memory_node.py
Memory Update Node — updates follow_up_context after each agent turn.
"""

from state import AgentState


def memory_update_node(state: AgentState) -> AgentState:
    """
    Node: Memory Update
    Inspects last agent response and updates follow_up_context for follow-up questions.
    This node runs AFTER every sub-agent, before returning output.
    """
    last_response = state.get("last_agent_response", "")
    active_agent = state.get("active_sub_agent", "")
    context = dict(state.get("follow_up_context", {}))

    # The sub-agents already update context themselves.
    # This node provides a safety net and logs the state.
    print(f"[MemoryNode] Active agent: {active_agent} | Context: {context}")

    return {
        **state,
        "follow_up_context": context,
    }
