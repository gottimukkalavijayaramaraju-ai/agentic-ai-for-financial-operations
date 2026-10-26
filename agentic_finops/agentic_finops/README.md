# Agentic AI for Financial Operations (base project)

An agent that processes invoices end to end:
**extract → categorize → anomaly check → payment decision → bank reconciliation → audit log.**

## Run
    pip install -r requirements.txt   # only needed for LLM mode
    python main.py                    # rule-based, works offline
    export ANTHROPIC_API_KEY=...      # then:
    python main.py --llm              # Claude decides which tools to call

## Files
- `sample_data.py` – invoices, approved vendors, history, bank transactions
- `tools.py` – deterministic finance tools + payment policy
- `agent.py` – agent with rule mode and LLM tool-use loop, audit trail
- `main.py` – CLI entry point

## Ideas to extend
PDF/OCR invoice input, ERP/bank API integration, human-approval UI, a database,
more policies (budget limits, tax checks), and tests.
