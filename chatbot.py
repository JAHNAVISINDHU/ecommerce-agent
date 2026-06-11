"""
chatbot.py - Main entry point for the e-commerce support chatbot.
Runs an interactive conversation loop with LangSmith tracing.
"""

import os
import sys
import uuid
from datetime import datetime
from langchain_core.messages import HumanMessage

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Loaded .env file")
except ImportError:
    pass

from graph import build_graph, setup_langsmith
from state import AgentState


def get_langsmith_metadata(customer_id: str, intent: str = "", environment: str = "development") -> dict:
    """Build LangSmith run metadata/tags."""
    return {
        "tags": [
            f"customer:{customer_id}",
            f"intent:{intent}" if intent else "intent:unknown",
            f"env:{environment}",
            f"session:{datetime.now().strftime('%Y%m%d')}",
        ],
        "metadata": {
            "customer_id": customer_id,
            "intent": intent,
            "environment": environment,
            "timestamp": datetime.now().isoformat(),
        }
    }


def create_initial_state(customer_id: str) -> AgentState:
    """Create the initial agent state for a new conversation."""
    return {
        "customer_id": customer_id,
        "messages": [],
        "intent": "",
        "active_sub_agent": "",
        "db_query_results": {},
        "follow_up_context": {},
        "escalation_flag": False,
        "turn_count": 0,
        "consecutive_same_intent": 0,
        "last_agent_response": "",
    }


def run_turn(graph, state: AgentState, user_input: str, langsmith_enabled: bool) -> AgentState:
    """Process one conversational turn through the graph."""
    # Add human message to state
    state["messages"] = state["messages"] + [HumanMessage(content=user_input)]

    config = {
        "run_name": f"ecommerce-chatbot-turn-{state['turn_count'] + 1}",
    }

    if langsmith_enabled:
        metadata = get_langsmith_metadata(
            customer_id=state["customer_id"],
            intent=state.get("intent", "unknown"),
            environment=os.environ.get("ENVIRONMENT", "development"),
        )
        config["tags"] = metadata["tags"]
        config["metadata"] = metadata["metadata"]

        # If escalated, add escalation tag
        if state.get("escalation_flag"):
            config["tags"].append("escalated:true")

    result = graph.invoke(state, config=config)
    return result


def print_banner():
    print("\n" + "="*60)
    print("   🛍️  ShopBot — E-Commerce Customer Support")
    print("   Powered by LangChain + LangGraph + LangSmith")
    print("="*60)
    print("Type 'quit' or 'exit' to end the conversation.")
    print("Type 'reset' to start a new session.")
    print("Type 'context' to view current conversation context.")
    print("="*60 + "\n")


def main():
    """Main interactive chatbot loop."""
    print_banner()

    # Setup LangSmith
    langsmith_enabled = setup_langsmith()

    # Build graph
    print("Building agent graph...")
    graph = build_graph()
    print("✓ Agent graph ready.\n")

    # Get customer ID
    customer_id = input("Enter your Customer ID (e.g., C0001): ").strip()
    if not customer_id:
        customer_id = "C0001"
    print(f"\nWelcome! I'm here to help you, customer {customer_id}.\n")

    # Initialize state
    state = create_initial_state(customer_id)

    print("ShopBot: Hello! I'm your ShopBot assistant. I can help you with:")
    print("  • Order status and tracking")
    print("  • Product information and availability")
    print("  • Returns and refunds")
    print("  • Product recommendations")
    print("\nHow can I assist you today?\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nShopBot: Thank you for shopping with us. Goodbye! 👋")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "bye", "goodbye"):
            print("ShopBot: Thank you for shopping with us. Have a great day! 👋")
            break

        if user_input.lower() == "reset":
            state = create_initial_state(customer_id)
            print("ShopBot: Session reset. How can I help you?\n")
            continue

        if user_input.lower() == "context":
            print(f"\n[Debug] Follow-up context: {state.get('follow_up_context')}")
            print(f"[Debug] Last intent: {state.get('intent')}")
            print(f"[Debug] Turn count: {state.get('turn_count')}")
            print(f"[Debug] Escalation: {state.get('escalation_flag')}\n")
            continue

        # Run the conversation turn
        try:
            state = run_turn(graph, state, user_input, langsmith_enabled)
            response = state.get("last_agent_response", "I'm sorry, I couldn't process that.")
            print(f"\nShopBot: {response}\n")

            # If escalated, offer to start fresh
            if state.get("escalation_flag"):
                print("  [A human agent will follow up via email]\n")

        except Exception as e:
            print(f"\nShopBot: I encountered an error: {e}")
            print("Please try rephrasing your question.\n")
            if os.environ.get("DEBUG", "").lower() == "true":
                import traceback
                traceback.print_exc()



if __name__ == '__main__':
    main()