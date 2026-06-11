"""
agents/fallback_agent.py
Fallback / Escalation Node
"""

import os
import json
import uuid
from datetime import datetime
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from state import AgentState
from prompts.prompts import try_pull_from_hub, get_fallback_prompt
from utils import get_llm


def fallback_agent_node(state: AgentState) -> AgentState:
    llm = get_llm(temperature=0.2)

    intent = state.get("intent", "unknown")
    consecutive = state.get("consecutive_same_intent", 0)
    ref_number = f"ESC-{uuid.uuid4().hex[:8].upper()}"

    if state.get("escalation_flag") and consecutive >= 3:
        reason = f"Query about '{intent}' could not be resolved after {consecutive} attempts."
    elif intent == "unknown":
        reason = "The request could not be understood or classified."
    else:
        reason = "Escalated per policy for unresolvable query."

    hub_user = os.environ.get("LANGSMITH_HUB_USER", "your-username")
    prompt_template = try_pull_from_hub(f"{hub_user}/fallback-agent-prompt:latest", get_fallback_prompt)
    messages = prompt_template.invoke({"messages": state["messages"], "customer_id": state.get("customer_id", "Unknown"), "escalation_reason": reason}).to_messages()

    try:
        result = llm.invoke(messages)
        response_text = result.content.strip()
        if "reference" not in response_text.lower():
            response_text += f"\n\nYour reference number: **{ref_number}**"
    except Exception as e:
        print(f"[FallbackAgent] Error: {e}")
        response_text = (
            f"I'm sorry for the inconvenience. I'm connecting you to a human support agent. "
            f"Your reference number is **{ref_number}**. You'll receive a response within 24 hours."
        )

    _log_escalation(state, ref_number, reason)
    print(f"[FallbackAgent] Escalation logged. Ref: {ref_number}")

    updated_messages = state["messages"] + [AIMessage(content=response_text)]
    return {
        **state,
        "messages": updated_messages,
        "last_agent_response": response_text,
        "active_sub_agent": "fallback",
        "escalation_flag": True,
    }


def _log_escalation(state: AgentState, ref_number: str, reason: str):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "ref_number": ref_number,
        "customer_id": state.get("customer_id"),
        "intent": state.get("intent"),
        "turn_count": state.get("turn_count"),
        "reason": reason,
        "follow_up_context": state.get("follow_up_context", {}),
        "escalation_flag": True,
    }
    os.makedirs("logs", exist_ok=True)
    with open("logs/escalations.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
