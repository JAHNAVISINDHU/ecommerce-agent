"""
agents/product_agent.py
Product Query Sub-Agent
"""

import os
import json
import re
from langchain_core.messages import AIMessage
from state import AgentState
from prompts.prompts import try_pull_from_hub, get_product_agent_prompt
from tools import search_products, get_product_by_id, get_products_by_category, get_top_rated_products
from utils import get_llm

PRODUCT_TOOLS = [search_products, get_product_by_id, get_products_by_category, get_top_rated_products]


def product_agent_node(state: AgentState) -> AgentState:
    from langgraph.prebuilt import create_react_agent

    llm = get_llm(temperature=0.2)
    follow_up = state.get("follow_up_context", {})
    customer_id = state.get("customer_id", "")
    context_str = json.dumps(follow_up) if follow_up else "None"

    hub_user = os.environ.get("LANGSMITH_HUB_USER", "your-username")
    prompt_template = try_pull_from_hub(f"{hub_user}/product-query-agent-prompt:latest", get_product_agent_prompt)
    messages = prompt_template.invoke({"messages": [], "customer_id": customer_id, "follow_up_context": context_str}).to_messages()
    system_prompt = messages[0].content

    try:
        agent = create_react_agent(llm, PRODUCT_TOOLS, prompt=system_prompt)
        result = agent.invoke({"messages": state["messages"]})
        last_msg = result["messages"][-1]
        response_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    except Exception as e:
        print(f"[ProductAgent] Error: {e}")
        response_text = "I'm having trouble looking up product details right now. Please try again."

    print(f"[ProductAgent] Response: {response_text[:120]}")
    updated_messages = state["messages"] + [AIMessage(content=response_text)]
    updated_context = _extract_product_context(response_text, state.get("follow_up_context", {}))

    return {
        **state,
        "messages": updated_messages,
        "last_agent_response": response_text,
        "db_query_results": {},
        "follow_up_context": updated_context,
        "active_sub_agent": "product_agent",
    }


def _extract_product_context(response: str, existing_context: dict) -> dict:
    context = dict(existing_context)
    match = re.search(r'\b(P\d{4,})\b', response)
    if match:
        context["product_id"] = match.group(1)
    return context
