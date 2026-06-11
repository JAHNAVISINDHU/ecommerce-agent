"""
agents/recommendation_agent.py
Recommendation Sub-Agent
"""

import os
import json
from langchain_core.messages import AIMessage
from state import AgentState
from prompts.prompts import try_pull_from_hub, get_recommendation_prompt
from tools import (
    get_top_rated_products, get_products_by_category,
    get_recommendations_for_new_categories, get_customer_purchase_categories,
)
from utils import get_llm

RECOMMENDATION_TOOLS = [
    get_top_rated_products, get_products_by_category,
    get_recommendations_for_new_categories, get_customer_purchase_categories,
]


def recommendation_agent_node(state: AgentState) -> AgentState:
    from langgraph.prebuilt import create_react_agent

    llm = get_llm(temperature=0.3)
    follow_up = state.get("follow_up_context", {})
    customer_id = state.get("customer_id", "")
    context_str = json.dumps(follow_up) if follow_up else "None"

    hub_user = os.environ.get("LANGSMITH_HUB_USER", "your-username")
    prompt_template = try_pull_from_hub(f"{hub_user}/recommendation-agent-prompt:latest", get_recommendation_prompt)
    messages = prompt_template.invoke({"messages": [], "customer_id": customer_id, "follow_up_context": context_str}).to_messages()
    system_prompt = messages[0].content

    try:
        agent = create_react_agent(llm, RECOMMENDATION_TOOLS, prompt=system_prompt)
        result = agent.invoke({"messages": state["messages"]})
        last_msg = result["messages"][-1]
        response_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    except Exception as e:
        print(f"[RecommendationAgent] Error: {e}")
        response_text = "I'm having trouble generating recommendations right now. Please try again."

    print(f"[RecommendationAgent] Response: {response_text[:120]}")
    updated_messages = state["messages"] + [AIMessage(content=response_text)]

    return {
        **state,
        "messages": updated_messages,
        "last_agent_response": response_text,
        "db_query_results": {},
        "follow_up_context": follow_up,
        "active_sub_agent": "recommendation_agent",
    }
