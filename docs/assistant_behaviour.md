# 🧭 Assistant Behavior & Intent Guide

This document describes how the **AI Financial Assistant** interprets, resolves, and responds to user messages.  
It summarizes supported intents, period handling, fallbacks, and conversational tone.

---

## 🎯 Overview

The assistant interprets natural language finance-related questions such as:

> “How much did I spend on groceries last month?”  
> “What’s my highest budget this year?”  
> “Compare my income and expenses since June.”

It uses a **hybrid approach**:

- **LLM-first interpretation** → natural intent extraction and parameter parsing.  
- **Rule-based fallback** → ensures reliability for predictable phrases.  
- **Deterministic range resolution** → correct date handling for “this month”, “since June”, “between March and July”, etc.

---

## 🧩 Supported Intents

| Intent | Description | Example |
|--------|--------------|----------|
| `spend_in_period` | Total expenses in a given period. | “How much did I spend this week?” |
| `spend_in_category_period` | Total expenses in a specific category. | “How much did I spend on groceries last month?” |
| `income_in_period` | Total income for a period. | “What’s my income in September?” |
| `income_expense_overview_period` | Compare income vs expenses and compute net balance. | “Compare my cash in vs cash out since June.” |
| `budget_status_category_period` | Check if you’re over or under budget for a specific category. | “Am I over budget on transport this month?” |
| `budget_status_period` | Check total budget vs total spending. | “What’s my total budget this quarter?” |
| `highest_budget_period` | Find the category with the largest budget in a period. | “What’s my highest budget this year?” |
| `lowest_budget_period` | Find the category with the smallest budget in a period. | “What’s my lowest budget this year?” |
| `top_category_in_period` | Find the category with the highest spending in a period. | “What’s my top category this quarter?” |

---

## ⏰ Period Resolution Logic

### Priority Order

1. **Explicit Dates** →  
   If both `start` and `end` are provided (from LLM or user), use them.

2. **Relative Phrases** →  
   Phrases like “this month”, “last week”, “this quarter” are resolved deterministically via `period_range()`.

3. **Heuristics (Free-form Ranges)** →  
   Handles flexible phrases such as:
   - “since June”  
   - “between June 2024 and March 2025”  
   - “from July until now”  
   - “last 20 days”

4. **Fallback Default** →  
   Defaults to **this month** if no explicit time frame is detected.

---

## 🧮 Budget Logic

- Budgets are matched by **period** (`monthly`, `yearly`, etc.) and **category**.
- `_pick_budget()` selects the most recent applicable budget before the `end` date.
- Period mapping:\
week → weekly\
month → monthly \
quarter → quarterly \
half_year → half-yearly \
year → yearly
---
- The assistant always assumes *monthly* budgets if no period is specified.

---

## 🧠 Heuristic Examples

| User Input | Resolved Range | Example Label |
|-------------|----------------|----------------|
| “since June” | 2025-06-01 → today | “since June” |
| “between March and July” | Mar 1 → Jul 31 | “Mar–Jul 2025” |
| “last 30 days” | 30-day rolling window | “last 30 days” |
| “from July until now” | Jul 1 → today | “since July” |

---

## 💬 Tone & Style

- **Polite, factual, and clear.**
- Always includes **period context** (e.g. “in this month”, “in Sep–Oct 2025”).
- Uses **consistent currency formatting** via `_euro()` (e.g. `€1,250.00`).
- Provides **short actionable follow-ups** (e.g. “See expenses”, “Show chart”).
- Avoids technical language — focuses on user clarity.

---

## ⚙️ Developer Notes

- `ai_intent_debug` → Quick test of the intent parser output.  
- `ai_range_debug` → Inspect resolved date ranges before full assistant execution.  
- Logging (`logger.info`) traces resolved periods and totals for debugging.  
- The assistant is stateless — context resets per query.  
- Budget results depend on user specificity: *ambiguous “total budget” questions default to monthly.*

---

## 🧾 Fallback Examples

| User Query | Behavior | Reason |
|-------------|-----------|--------|
| “Total budget” | Defaults to monthly total budget. | No period or category specified. |
| “Total budget this year” | Computes sum of all yearly budgets. | Explicit period provided. |
| “My budget for groceries” | Uses the most recent monthly budget for that category. | Category present, period omitted. |
| “Budget on transport last quarter” | Fetches transport budget in the last quarter. | Specific period and category. |

---

## ✅ Summary

The assistant prioritizes **accuracy**, **clarity**, and **explainability**.  
It avoids guessing — when uncertain, it defaults to “this month” and politely tells the user.  
Every response is traceable and logged, ensuring transparent decision logic for every query.

---

---

## 🧩 Assistant Logic Flow (Mermaid Diagram)

```mermaid
flowchart TD
    A[💬 User Query] --> B{LLM Intent Extraction}
    B -->|Success| C[Parse intent + params (period/category/start/end)]
    B -->|Fail / Fallback| D[Rule-based Intent Parser (parse_intent)]

    C --> E{Has explicit start/end?}
    D --> E

    E -->|✅ Yes| F[Trust explicit start/end dates]
    E -->|❌ No| G{Contains relative phrase? (this/last/etc.)}

    G -->|✅ Yes| H[Use canonical period_range()]
    G -->|❌ No| I{Heuristic phrase? (since/between/from/last N days)}

    I -->|✅ Yes| J[Derive start/end via _heuristic_range_from_text()]
    I -->|❌ No| K[Default to this month]

    F --> L[Compute SQL totals (spending/income/budget)]
    H --> L
    J --> L
    K --> L

    L --> M{Intent Type?}
    M -->|spend_in_period| N[💰 Total spend reply]
    M -->|spend_in_category_period| O[🛒 Category spend reply]
    M -->|income_in_period| P[💵 Income summary]
    M -->|income_expense_overview_period| Q[⚖️ Income vs Expense overview]
    M -->|budget_status_category_period| R[📊 Category budget status]
    M -->|budget_status_period| S[📈 Total budget status]
    M -->|highest_budget_period| T[🏆 Highest budget category]
    M -->|lowest_budget_period| U[📉 Lowest budget category]
    M -->|top_category_in_period| V[🔥 Top spending category]
    M -->|unknown| W[❓ Suggest clearer phrasing]

    N --> X[🗣️ Reply + Actions]
    O --> X
    P --> X
    Q --> X
    R --> X
    S --> X
    T --> X
    U --> X
    V --> X
    W --> X
```
🗺️ Reading the Diagram\
	1.	LLM tries to interpret the user’s intent first.\
	2.	If it fails, the rule-based parser (parse_intent) takes over.\
	3.	The assistant then resolves time periods by priority:\
	•	Explicit start/end\
	•	Relative phrases (this/last)\
	•	Heuristics (since/between/from)\
	•	Default month\
	4.	Once the range is resolved, it runs SQL aggregations for the chosen intent.\
	5.	Finally, it crafts a natural-language reply with context (period, category, totals, etc.).

⸻

🧩 Design Principles\
	•	Deterministic over generative: predictable logic wins over creativity.\
	•	Transparent reasoning: every step is logged and explainable.\
	•	Polite fallback behavior when uncertain.\
	•	Extensible: easily add new intents without breaking period logic.\

⸻
