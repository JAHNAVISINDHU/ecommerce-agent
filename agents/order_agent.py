"""
agents/order_agent.py
Order Status Sub-Agent — handles order tracking and status queries.
Uses modern langgraph.prebuilt.create_react_agent approach.
"""

import os
import json
import re
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from state import AgentState
from prompts.prompts import try_pull_from_hub, get_order_agent_prompt
from tools import get_orders_by_customer, get_order_by_id, get_active_orders_by_customer
from utils import get_llm

ORDER_TOOLS = [get_orders_by_customer, get_order_by_id, get_active_orders_by_customer]


def order_agent_node(state: AgentState) -> AgentState:
    """Node: Order Status Sub-Agent"""
    from langgraph.prebuilt import create_react_agent

    llm = get_llm(temperature=0.1)
    follow_up = state.get("follow_up_context", {})
    customer_id = state.get("customer_id", "")
    context_str = json.dumps(follow_up) if follow_up else "None"

    hub_user = os.environ.get("LANGSMITH_HUB_USER", "your-username")
    prompt_template = try_pull_from_hub(f"{hub_user}/order-status-agent-prompt:latest", get_order_agent_prompt)
    messages = prompt_template.invoke({"messages": [], "customer_id": customer_id, "follow_up_context": context_str}).to_messages()
    system_prompt = messages[0].content

    try:
        agent = create_react_agent(llm, ORDER_TOOLS, prompt=system_prompt)
        # Feed the conversation as messages
        agent_input = {"messages": state["messages"]}
        result = agent.invoke(agent_input)
        # Last message from the agent
        last_msg = result["messages"][-1]
        response_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    except Exception as e:
        print(f"[OrderAgent] Error: {e}")
        response_text = "I'm having trouble accessing your order details right now. Please try again."

    print(f"[OrderAgent] Response: {response_text[:120]}")
    updated_messages = state["messages"] + [AIMessage(content=response_text)]
    updated_context = _extract_order_context(response_text, state.get("follow_up_context", {}))

    return {
        **state,
        "messages": updated_messages,
        "last_agent_response": response_text,
        "db_query_results": {},
        "follow_up_context": updated_context,
        "active_sub_agent": "order_agent",
    }


def _extract_order_context(response: str, existing_context: dict) -> dict:
    context = dict(existing_context)
    match = re.search(r'\b(O\d{4,})\b', response)
    if match:
        context["order_id"] = match.group(1)
    for kw in ["jacket", "shoes", "headphones", "laptop", "phone", "book", "mat", "keyboard"]:
        if kw.lower() in response.lower():
            context["product_keyword"] = kw
            break
    return context
