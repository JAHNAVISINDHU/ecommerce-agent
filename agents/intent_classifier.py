"""
agents/intent_classifier.py
Classifies user intent and manages escalation logic.
"""

from langchain_core.messages import SystemMessage, HumanMessage
import os
from state import AgentState
from prompts.prompts import try_pull_from_hub, get_intent_classifier_prompt
from utils import get_llm

VALID_INTENTS = {"order_status", "product_query", "return_request", "recommendation", "unknown"}
ESCALATION_THRESHOLD = 3


def classify_intent_node(state: AgentState) -> AgentState:
    llm = get_llm(temperature=0.0)

    hub_user = os.environ.get("LANGSMITH_HUB_USER", "your-username")
    prompt_template = try_pull_from_hub(f"{hub_user}/intent-classifier-prompt:latest", get_intent_classifier_prompt)
    formatted_prompt = prompt_template.invoke({"messages": state["messages"]})
    messages = formatted_prompt.to_messages()
    messages.append(HumanMessage(content="Classify the intent of the LAST user message. Reply with ONLY the intent label."))

    try:
        result = llm.invoke(messages)
        raw = result.content.strip().lower().replace(".", "").replace(",", "").strip()
        intent = "unknown"
        for valid in VALID_INTENTS:
            if valid in raw:
                intent = valid
                break
    except Exception as e:
        print(f"[IntentClassifier] Error: {e}")
        intent = "unknown"

    prev_intent = state.get("intent", "")
    consecutive = state.get("consecutive_same_intent", 0)

    if intent == prev_intent and intent not in ("", "unknown"):
        consecutive += 1
    elif intent != prev_intent:
        consecutive = 0

    escalation_flag = state.get("escalation_flag", False)
    if consecutive >= ESCALATION_THRESHOLD:
        escalation_flag = True

    # Escalate on unknown for 2+ consecutive turns
    if intent == "unknown" and prev_intent == "unknown":
        escalation_flag = True

    print(f"[IntentClassifier] intent='{intent}' consecutive={consecutive} escalation={escalation_flag}")

    return {
        **state,
        "intent": intent,
        "active_sub_agent": intent,
        "consecutive_same_intent": consecutive,
        "escalation_flag": escalation_flag,
        "turn_count": state.get("turn_count", 0) + 1,
    }


def route_by_intent(state: AgentState) -> str:
    if state.get("escalation_flag", False):
        return "fallback"
    routing = {
        "order_status": "order_agent",
        "product_query": "product_agent",
        "return_request": "return_agent",
        "recommendation": "recommendation_agent",
        "unknown": "fallback",
    }
    return routing.get(state.get("intent", "unknown"), "fallback")
