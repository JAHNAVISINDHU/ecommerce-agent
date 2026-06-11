"""
state.py - Shared state definition for the LangGraph agent.
"""

from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):
    customer_id: str
    messages: List[Any]          # Full conversation history (HumanMessage / AIMessage)
    intent: str                  # Classified intent for current turn
    active_sub_agent: str        # Which sub-agent is handling the query
    db_query_results: Dict       # Raw results from a DB lookup
    follow_up_context: Dict      # Last order / product / return discussed
    escalation_flag: bool        # True if agent cannot resolve the query
    turn_count: int              # Total turns in the session
    consecutive_same_intent: int # Tracks repeated unresolved intents for escalation
    last_agent_response: str     # The text response from the last active sub-agent
