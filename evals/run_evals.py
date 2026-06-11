"""
evals/run_evals.py
Runs the agent against the evaluation dataset and computes intent classification accuracy.
Optionally integrates with LangSmith for experiment tracking.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from langchain_core.messages import HumanMessage
from graph import build_graph, setup_langsmith
from state import AgentState


DATASET_PATH = Path(__file__).parent / "eval_dataset.json"
RESULTS_DIR = Path(__file__).parent / "results"


def load_dataset():
    with open(DATASET_PATH) as f:
        return json.load(f)


def create_initial_state(customer_id: str = "C0001") -> AgentState:
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


def run_single_eval(graph, example: dict) -> dict:
    """Run a single eval example through the graph and return result."""
    state = create_initial_state()
    state["messages"] = [HumanMessage(content=example["query"])]

    start = time.time()
    try:
        result = graph.invoke(state, config={
            "run_name": f"eval-{example['id']}",
            "tags": ["evaluation", "intent-classification"],
            "metadata": {"eval_id": example["id"]},
        })
        elapsed = time.time() - start
        actual_intent = result.get("intent", "unknown")
        agent_response = result.get("last_agent_response", "")

        return {
            "id": example["id"],
            "query": example["query"],
            "expected_intent": example["expected_intent"],
            "actual_intent": actual_intent,
            "intent_match": actual_intent == example["expected_intent"],
            "agent_response": agent_response[:200] + "..." if len(agent_response) > 200 else agent_response,
            "elapsed_seconds": round(elapsed, 2),
            "error": None,
        }
    except Exception as e:
        return {
            "id": example["id"],
            "query": example["query"],
            "expected_intent": example["expected_intent"],
            "actual_intent": "error",
            "intent_match": False,
            "agent_response": "",
            "elapsed_seconds": round(time.time() - start, 2),
            "error": str(e),
        }


def score_intent_accuracy(results: list) -> dict:
    """Compute intent classification accuracy metrics."""
    total = len(results)
    correct = sum(1 for r in results if r["intent_match"])
    errors = sum(1 for r in results if r["error"])

    # Per-intent breakdown
    intent_breakdown = {}
    all_intents = set(r["expected_intent"] for r in results)
    for intent in all_intents:
        intent_results = [r for r in results if r["expected_intent"] == intent]
        intent_correct = sum(1 for r in intent_results if r["intent_match"])
        intent_breakdown[intent] = {
            "total": len(intent_results),
            "correct": intent_correct,
            "accuracy": round(intent_correct / len(intent_results), 3) if intent_results else 0,
        }

    return {
        "total": total,
        "correct": correct,
        "errors": errors,
        "overall_accuracy": round(correct / total, 3) if total else 0,
        "intent_breakdown": intent_breakdown,
    }


def push_to_langsmith(results: list, scores: dict):
    """Optionally push evaluation results to LangSmith."""
    try:
        from langsmith import Client
        api_key = os.environ.get("LANGSMITH_API_KEY", "")
        if not api_key or api_key == "your_langsmith_api_key_here":
            print("  Skipping LangSmith dataset push (no API key)")
            return

        client = Client()
        dataset_name = f"ecommerce-intent-eval-{datetime.now().strftime('%Y%m%d')}"

        # Create or get dataset
        try:
            dataset = client.create_dataset(dataset_name, description="E-commerce chatbot intent classification eval")
        except Exception:
            dataset = client.read_dataset(dataset_name=dataset_name)

        # Add examples
        for r in results:
            try:
                client.create_example(
                    inputs={"query": r["query"]},
                    outputs={
                        "expected_intent": r["expected_intent"],
                        "actual_intent": r["actual_intent"],
                        "intent_match": r["intent_match"],
                    },
                    dataset_id=dataset.id,
                )
            except Exception:
                pass

        print(f"✓ Results pushed to LangSmith dataset: {dataset_name}")
    except ImportError:
        print("  langsmith package not installed — skipping Hub push")
    except Exception as e:
        print(f"  LangSmith push error: {e}")


def print_report(results: list, scores: dict):
    """Print a formatted evaluation report."""
    print("\n" + "="*70)
    print("  📊  INTENT CLASSIFICATION EVALUATION REPORT")
    print("="*70)
    print(f"  Date:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Total:    {scores['total']} examples")
    print(f"  Correct:  {scores['correct']}")
    print(f"  Errors:   {scores['errors']}")
    print(f"  Accuracy: {scores['overall_accuracy']*100:.1f}%")
    print()
    print("  Per-Intent Breakdown:")
    print("  " + "-"*50)
    for intent, stats in scores["intent_breakdown"].items():
        bar = "█" * int(stats["accuracy"] * 20)
        print(f"  {intent:20s}: {stats['correct']:2}/{stats['total']:2}  {bar}")
    print()
    print("  Detailed Results:")
    print("  " + "-"*70)
    print(f"  {'ID':<12} {'Expected':<20} {'Actual':<20} {'Match'}")
    print("  " + "-"*70)
    for r in results:
        match_icon = "✓" if r["intent_match"] else "✗"
        err = " [ERROR]" if r["error"] else ""
        print(f"  {r['id']:<12} {r['expected_intent']:<20} {r['actual_intent']:<20} {match_icon}{err}")
    print("="*70)


def main():
    print("🧪 Starting Evaluation Suite...\n")
    langsmith_enabled = setup_langsmith()

    print("Building agent graph...")
    graph = build_graph()
    print("✓ Graph ready. Running evaluations...\n")

    dataset = load_dataset()
    results = []

    for i, example in enumerate(dataset, 1):
        print(f"  [{i:02d}/{len(dataset)}] {example['id']}: \"{example['query'][:50]}...\"", end=" ", flush=True)
        result = run_single_eval(graph, example)
        results.append(result)
        status = "✓" if result["intent_match"] else "✗"
        print(f"→ {result['actual_intent']} [{status}] ({result['elapsed_seconds']}s)")

    # Compute scores
    scores = score_intent_accuracy(results)

    # Print report
    print_report(results, scores)

    # Save results
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = RESULTS_DIR / f"eval_results_{timestamp}.json"
    with open(results_path, "w") as f:
        json.dump({"scores": scores, "results": results, "timestamp": timestamp}, f, indent=2)
    print(f"\n✓ Results saved to: {results_path}")

    # Push to LangSmith if enabled
    if langsmith_enabled:
        push_to_langsmith(results, scores)

    # Exit with error code if accuracy < 70%
    if scores["overall_accuracy"] < 0.70:
        print(f"\n⚠️  Accuracy {scores['overall_accuracy']*100:.1f}% is below 70% threshold.")
        sys.exit(1)
    else:
        print(f"\n✅ Evaluation passed! Accuracy: {scores['overall_accuracy']*100:.1f}%")


if __name__ == "__main__":
    main()
