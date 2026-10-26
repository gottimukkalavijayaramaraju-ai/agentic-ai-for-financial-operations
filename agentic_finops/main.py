"""Run the finance agent over sample invoices.

Usage:
    python main.py            # rule-based mode (no API key needed)
    python main.py --llm      # Claude-driven mode (set ANTHROPIC_API_KEY)
"""
import argparse
import json

from agent import FinanceAgent
from sample_data import INVOICE_TEXTS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true", help="use Claude to drive tool calls")
    args = parser.parse_args()

    agent = FinanceAgent(use_llm=args.llm)
    print(f"Mode: {'LLM' if agent.use_llm else 'rule-based'}\n")

    summary = {"APPROVE": 0, "ESCALATE": 0, "REJECT": 0}
    for text in INVOICE_TEXTS:
        result = agent.process_invoice(text)
        if "decision" in result:
            inv, d = result["invoice"], result["decision"]
            summary[d["decision"]] += 1
            print(f"{inv['invoice_no']:9} {inv['vendor']:22} ${inv['amount']:>10,.2f}  "
                  f"{result['category']:22} -> {d['decision']:8} ({d['reason']})"
                  + (f" [matched {result['bank_match']}]" if result["bank_match"] else ""))
        else:
            print(result)

    print("\nSummary:", summary)
    with open("audit_log.json", "w") as f:
        json.dump(agent.audit_log, f, indent=2, default=str)
    print("Audit trail saved to audit_log.json")


if __name__ == "__main__":
    main()
