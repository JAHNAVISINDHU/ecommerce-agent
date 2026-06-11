# 🛍️ E-Commerce Support Chatbot
## LangChain + LangGraph + LangSmith Multi-Agent System

A fully stateful, multi-agent conversational chatbot for e-commerce customer support, built with LangChain, LangGraph, and LangSmith.

---

## 📁 Project Structure

```
ecommerce-agent/
├── seed_db.py              # Creates & populates ecommerce.db
├── chatbot.py              # Main interactive chatbot entry point
├── graph.py                # LangGraph state machine definition
├── state.py                # AgentState TypedDict
├── push_prompts.py         # Push prompts to LangSmith Hub
├── requirements.txt
├── .env.example            # Environment variable template
│
├── agents/
│   ├── intent_classifier.py  # Router — classifies intent, manages escalation
│   ├── order_agent.py        # Order status sub-agent
│   ├── product_agent.py      # Product query sub-agent
│   ├── return_agent.py       # Returns sub-agent
│   ├── recommendation_agent.py # Recommendation sub-agent
│   ├── fallback_agent.py     # Escalation / fallback node
│   └── memory_node.py        # Memory update node
│
├── tools/
│   └── db_tools.py           # All database query tools (LangChain @tool)
│
├── prompts/
│   ├── prompts.py            # All system prompts + Hub integration
│   ├── intent_classifier.txt
│   ├── order_status_agent.txt
│   ├── product_query_agent.txt
│   ├── return_agent.txt
│   ├── recommendation_agent.txt
│   └── fallback_agent.txt
│
├── utils/
│   └── llm_factory.py        # LLM provider selection (Anthropic/OpenAI/Ollama)
│
├── evals/
│   ├── eval_dataset.json     # 30 labeled query/intent pairs
│   └── run_evals.py          # Evaluation runner + accuracy scorer
│
└── logs/
    └── escalations.jsonl     # Auto-created escalation audit log
```

---

## ⚡ Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

**LLM Options (choose one):**

| Provider | Setup | Cost |
|----------|-------|------|
| **Anthropic** (recommended) | Set `ANTHROPIC_API_KEY` | Paid (free trial credits) |
| **OpenAI** | Set `OPENAI_API_KEY` | Paid (free trial credits) |
| **Ollama** (local) | Install [Ollama](https://ollama.com) + `ollama pull llama3.2` | Free |

### 3. Seed the Database

```bash
python seed_db.py
```

Expected output:
```
✓ Tables created successfully.
✓ Seeded 60 customers.
✓ Seeded 30 products.
✓ Seeded 120 orders.
✓ Seeded 30 returns.

📊 Database Summary:
  customers      :    60 rows
  products       :    30 rows
  orders         :   120 rows
  returns        :    30 rows
  Out-of-stock products: 5 ✓
  Multi-order customers: 15 ✓
  Returns on non-delivered orders: 0 ✓
```

### 4. Push Prompts to LangSmith Hub (Optional)

```bash
# Set LANGSMITH_API_KEY and LANGSMITH_HUB_USER in .env first
python push_prompts.py
```

### 5. Run the Chatbot

```bash
python chatbot.py
```

### 6. Run Sample Conversation (End-to-End Test)

```bash
python chatbot.py --sample
```

### 7. Run Evaluations

```bash
python evals/run_evals.py
```

---

## 🏗️ Architecture

```
User Input
    ↓
Intent Classifier Node  ← (classifies: order_status | product_query | 
    ↓                         return_request | recommendation | unknown)
    ↓ (conditional routing)
┌───────────────────────────────────────────┐
│  Order Agent  │ Product Agent │ Return    │
│               │               │ Agent     │
│Recommendation Agent│ Fallback/Escalation  │
└───────────────────────────────────────────┘
    ↓
Memory Update Node  ← (updates follow_up_context)
    ↓
Output → User
```

### Shared State (`AgentState`)

```python
{
    "customer_id": "C0001",
    "messages": [...],           # Full conversation history
    "intent": "order_status",    # Current classified intent
    "active_sub_agent": "...",   # Which node is active
    "db_query_results": {},      # Raw DB results
    "follow_up_context": {       # KEY for multi-turn memory
        "order_id": "O1002",
        "product_keyword": "jacket"
    },
    "escalation_flag": False,    # Triggers fallback
    "turn_count": 3, 
    "consecutive_same_intent": 0,
    "last_agent_response": "..."
}
```

---

## 🤖 Sub-Agent Behaviors

### Order Status Agent
| Condition | Response |
|-----------|----------|
| Single shipped order | Returns tracking info + estimated delivery |
| Single processing order | Returns estimated delivery date |
| Multiple active orders | Asks user for clarification |
| Order not found | Asks user to confirm the order ID |
| Cancelled order | Confirms cancellation and refund status |

### Product Query Agent
| Condition | Response |
|-----------|----------|
| Product in stock | Price, rating, stock count |
| Out of stock | States OOS + suggests alternatives |
| Not found | Fuzzy match + suggests similar product |
| Multiple matches | Lists them + asks for clarification |

### Returns Agent
| Condition | Response |
|-----------|----------|
| Return approved | Confirms refund amount + 3-5 day timeline |
| Return pending | Current status update |
| No return + eligible order | Initiates new return flow |
| No return + ineligible | Explains return policy |

### Recommendation Agent
| Condition | Response |
|-----------|----------|
| Has purchase history | Recommends from new categories |
| No history | Top-rated items from full catalog |
| Budget specified | Filtered to price range |
| Category specified | Filtered by category, sorted by rating |

### Escalation Logic
- Triggers if same intent fails **3 consecutive turns**
- Triggers if intent is `unknown` for **2+ consecutive turns**
- Generates polite human handoff with reference number
- Logs to `logs/escalations.jsonl`
- Tags LangSmith trace with `escalated:true`

---

## 🔍 LangSmith Observability

When `LANGSMITH_API_KEY` is configured:

- **Every graph node** appears as a named span in the trace
- **Tags** applied per run: `customer_id`, `intent`, `env`, `escalated`  
- **Metadata**: timestamp, turn count, customer ID
- **Prompts** managed via LangSmith Hub (pulled at runtime)

View traces at: `https://smith.langchain.com`

---

## 🧪 Evaluation

The `evals/` directory contains:
- `eval_dataset.json` — 30 labeled examples (query → expected intent)
- `run_evals.py` — Runner that computes intent accuracy per-intent and overall

```bash
python evals/run_evals.py
```

Output includes:
- Overall accuracy %
- Per-intent breakdown
- Pass/fail per example
- Results saved to `evals/results/`

---

## 🗄️ Database Schema

### `customers`
`customer_id | name | email | phone | address | city | state | zip_code | created_at`

### `products`
`product_id | name | category | price | stock_count | rating | description | created_at`

### `orders`
`order_id | customer_id | product_id | quantity | total_price | status | tracking_number | estimated_delivery | actual_delivery | created_at`

### `returns`
`return_id | order_id | customer_id | reason | status | refund_amount | initiated_at | resolved_at`

---

## 🔧 Troubleshooting

**"No LLM backend available"**
→ Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `.env`, or install Ollama.

**"ecommerce.db not found"**
→ Run `python seed_db.py` first.

**Agent gives wrong intent**
→ Check LangSmith trace to see exact LLM input/output. Improve prompts in `prompts/prompts.py`.

**Tools not working**
→ Ensure `ecommerce.db` exists and `DB_PATH` env var is correct (default: `ecommerce.db` in current dir).

**Enable debug mode:**
```bash
DEBUG=true python chatbot.py
```
