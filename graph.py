"""
graph.py - Defines and compiles the LangGraph state machine for the e-commerce chatbot.
"""

import os
from langgraph.graph import StateGraph, END
from state import AgentState
from agents import (
    classify_intent_node,
    route_by_intent,
    order_agent_node,
    product_agent_node,
    return_agent_node,
    recommendation_agent_node,
    fallback_agent_node,
    memory_update_node,
)


def build_graph():
    """
    Build and compile the LangGraph state machine.

    Graph Flow:
    START → intent_classifier
         → (conditional) order_agent | product_agent | return_agent
                        | recommendation_agent | fallback
         → memory_update
         → END
    """
    builder = StateGraph(AgentState)

    # ── Add nodes ─────────────────────────────────────────────────────────────
    builder.add_node("intent_classifier", classify_intent_node)
    builder.add_node("order_agent", order_agent_node)
    builder.add_node("product_agent", product_agent_node)
    builder.add_node("return_agent", return_agent_node)
    builder.add_node("recommendation_agent", recommendation_agent_node)
    builder.add_node("fallback", fallback_agent_node)
    builder.add_node("memory_update", memory_update_node)

    # ── Entry point ───────────────────────────────────────────────────────────
    builder.set_entry_point("intent_classifier")

    # ── Conditional routing from intent classifier ─────────────────────────
    builder.add_conditional_edges(
        "intent_classifier",
        route_by_intent,
        {
            "order_agent": "order_agent",
            "product_agent": "product_agent",
            "return_agent": "return_agent",
            "recommendation_agent": "recommendation_agent",
            "fallback": "fallback",
        },
    )

    # ── All sub-agents → memory update → END ──────────────────────────────
    for node in ["order_agent", "product_agent", "return_agent", "recommendation_agent", "fallback"]:
        builder.add_edge(node, "memory_update")

    builder.add_edge("memory_update", END)

    return builder.compile()


# ── LangSmith Tracing Setup ────────────────────────────────────────────────

def setup_langsmith():
    """Configure LangSmith tracing if API key is available."""
    langsmith_key = os.environ.get("LANGSMITH_API_KEY", "")
    if langsmith_key and langsmith_key not in ("your_langsmith_api_key_here", ""):
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
        os.environ.setdefault("LANGCHAIN_PROJECT", "ecommerce-chatbot")
        print("✓ LangSmith tracing enabled.")
        return True
    else:
        print("  LangSmith tracing disabled (no LANGSMITH_API_KEY). Running locally.")
        return False
