"""Finance agent: plans, calls tools, and keeps an audit trail.

Two modes:
  - rule mode : fixed deterministic plan (no API key needed)
  - llm mode  : Claude chooses which tools to call (needs ANTHROPIC_API_KEY)
"""
import json
import os

import tools
from sample_data import BANK_TRANSACTIONS

LLM_MODEL = "claude-sonnet-5-5"

TOOL_SCHEMAS = [
    {"name": "extract_invoice", "description": "Parse raw invoice text into structured fields.",
     "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "categorize_expense", "description": "Categorize an expense from its description.",
     "input_schema": {"type": "object", "properties": {"description": {"type": "string"}}, "required": ["description"]}},
    {"name": "detect_anomalies", "description": "Detect fraud/anomaly flags for a parsed invoice.",
     "input_schema": {"type": "object", "properties": {"invoice": {"type": "object"}}, "required": ["invoice"]}},
    {"name": "decide_payment", "description": "Apply payment policy: APPROVE, ESCALATE or REJECT.",
     "input_schema": {"type": "object", "properties": {"invoice": {"type": "object"}, "flags": {"type": "array", "items": {"type": "string"}}},
                      "required": ["invoice", "flags"]}},
    {"name": "reconcile", "description": "Match an invoice with a bank transaction.",
     "input_schema": {"type": "object", "properties": {"invoice": {"type": "object"}}, "required": ["invoice"]}},
]


class FinanceAgent:
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm and bool(os.getenv("ANTHROPIC_API_KEY"))
        self.audit_log: list[dict] = []

    def log(self, step: str, data):
        self.audit_log.append({"step": step, "data": data})

    # ---------- rule-based plan ----------
    def _process_rule(self, text: str) -> dict:
        invoice = tools.extract_invoice(text)
        self.log("extract_invoice", invoice)
        category = tools.categorize_expense(invoice["description"])
        self.log("categorize_expense", category)
        flags = tools.detect_anomalies(invoice)
        self.log("detect_anomalies", flags)
        decision = tools.decide_payment(invoice, flags)
        self.log("decide_payment", decision)
        match = tools.reconcile(invoice, BANK_TRANSACTIONS) if decision["decision"] == "APPROVE" else None
        self.log("reconcile", match["id"] if match else None)
        return {"invoice": invoice, "category": category, "flags": flags,
                "decision": decision, "bank_match": match["id"] if match else None}

    # ---------- LLM plan ----------
    def _call_tool(self, name: str, args: dict):
        if name == "extract_invoice":
            return tools.extract_invoice(args["text"])
        if name == "categorize_expense":
            return tools.categorize_expense(args["description"])
        if name == "detect_anomalies":
            return tools.detect_anomalies(args["invoice"])
        if name == "decide_payment":
            return tools.decide_payment(args["invoice"], args["flags"])
        if name == "reconcile":
            return tools.reconcile(args["invoice"], BANK_TRANSACTIONS)
        return {"error": f"unknown tool {name}"}

    def _process_llm(self, text: str) -> dict:
        import anthropic
        client = anthropic.Anthropic()
        system = ("You are a financial operations agent. For the invoice given, call tools in order: "
                  "extract_invoice, categorize_expense, detect_anomalies, decide_payment, and reconcile "
                  "(only if approved). Never override decide_payment. Finish with a one-line JSON summary: "
                  '{"decision": ..., "category": ..., "reason": ...}.')
        messages = [{"role": "user", "content": f"Process this invoice:\n\n{text}"}]
        for _ in range(10):  # safety cap on steps
            resp = client.messages.create(model=LLM_MODEL, max_tokens=1000, system=system,
                                          tools=TOOL_SCHEMAS, messages=messages)
            messages.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                final = "".join(b.text for b in resp.content if b.type == "text")
                self.log("llm_final", final)
                return {"llm_summary": final}
            results = []
            for block in resp.content:
                if block.type == "tool_use":
                    out = self._call_tool(block.name, block.input)
                    self.log(block.name, out)
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": json.dumps(out, default=str)})
            messages.append({"role": "user", "content": results})
        return {"error": "step limit reached"}

    def process_invoice(self, text: str) -> dict:
        return self._process_llm(text) if self.use_llm else self._process_rule(text)
