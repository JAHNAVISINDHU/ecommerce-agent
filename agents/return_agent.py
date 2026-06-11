"""
agents/return_agent.py
Returns Sub-Agent
"""

import os
import json
import re
from langchain_core.messages import AIMessage
from state import AgentState
from prompts.prompts import try_pull_from_hub, get_return_agent_prompt
from tools import (
    get_return_by_order, get_returns_by_customer,
    check_order_return_eligibility, initiate_return,
    get_orders_by_customer, get_order_by_id,
)
from utils import get_llm

RETURN_TOOLS = [
    get_return_by_order, get_returns_by_customer,
    check_order_return_eligibility, initiate_return,
    get_orders_by_customer, get_order_by_id,
]


def return_agent_node(state: AgentState) -> AgentState:
    from langgraph.prebuilt import create_react_agent

    llm = get_llm(temperature=0.1)
    follow_up = state.get("follow_up_context", {})
    customer_id = state.get("customer_id", "")
    context_str = json.dumps(follow_up) if follow_up else "None"

    hub_user = os.environ.get("LANGSMITH_HUB_USER", "your-username")
    prompt_template = try_pull_from_hub(f"{hub_user}/return-agent-prompt:latest", get_return_agent_prompt)
    messages = prompt_template.invoke({"messages": [], "customer_id": customer_id, "follow_up_context": context_str}).to_messages()
    system_prompt = messages[0].content

    try:
        agent = create_react_agent(llm, RETURN_TOOLS, prompt=system_prompt)
        result = agent.invoke({"messages": state["messages"]})
        last_msg = result["messages"][-1]
        response_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    except Exception as e:
        print(f"[ReturnAgent] Error: {e}")
        response_text = "I'm having trouble processing your return request right now. Please try again."

    print(f"[ReturnAgent] Response: {response_text[:120]}")
    updated_messages = state["messages"] + [AIMessage(content=response_text)]
    updated_context = _extract_return_context(response_text, state.get("follow_up_context", {}))

    return {
        **state,
        "messages": updated_messages,
        "last_agent_response": response_text,
        "db_query_results": {},
        "follow_up_context": updated_context,
        "active_sub_agent": "return_agent",
    }


def _extract_return_context(response: str, existing_context: dict) -> dict:
    context = dict(existing_context)
    for pattern, key in [(r'\b(R\d{4,})\b', "return_id"), (r'\b(O\d{4,})\b', "order_id")]:
        m = re.search(pattern, response)
        if m:
            context[key] = m.group(1)
    return context
