"""Checks that distrust the model's output before the exact layer uses it."""
from __future__ import annotations
import re
from decimal import Decimal, InvalidOperation
from .core import FACT_KEYS, CATEGORIES

_TRANS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-"})


def locate(quote: str, text: str):
    """Finds an exact quote, allowing only whitespace, case and typographic quote differences."""
    tokens = (quote or "").translate(_TRANS).split()
    if len(tokens) < 2:
        return None
    m = re.search(r"\s+".join(map(re.escape, tokens)), text.translate(_TRANS), re.I)
    return (m.start(), m.end()) if m else None


def validate_shape(o) -> list[str]:
    if not isinstance(o, dict):
        return ["output is not an object"]
    errs = []
    facts = o.get("facts")
    if not isinstance(facts, dict):
        return ["facts missing"]
    for k in FACT_KEYS:
        item = facts.get(k)
        if not isinstance(item, dict) or item.get("value") not in ("yes", "no", "silent"):
            errs.append(f"fact {k} invalid")
    if o.get("proposed_category") not in (*CATEGORIES, "UNRESOLVED"):
        errs.append("proposed_category invalid")
    if not isinstance(o.get("citations", []), list):
        errs.append("citations invalid")
    return errs


def verify_quotes(o: dict, docs: dict) -> tuple[dict, list[dict], list[str]]:
    """Every yes/no fact must quote a supplied document. Returns values, evidence and failures."""
    values, evidence, failed = {}, [], []
    for key in FACT_KEYS:
        item = o["facts"][key]
        value = item["value"]
        values[key] = value
        if value == "silent":
            continue
        hit = None
        for name, text in docs.items():
            span = locate(item.get("quote", ""), text)
            if span:
                hit = {"fact": key, "value": value, "document": name, "start": span[0], "end": span[1],
                       "quote": text[span[0]:span[1]]}
                break
        if hit:
            evidence.append(hit)
        else:
            failed.append(key)
    return values, evidence, failed


def amount_conflicts(o: dict, intake: dict, docs: dict) -> list[str]:
    conflicts = []
    expected = Decimal(str(intake["amount"]))
    for field_, doc in (("contract_amount", "contract"), ("invoice_amount", "invoice")):
        item = o.get(field_)
        if not isinstance(item, dict) or item.get("value") in (None, ""):
            continue
        try:
            found = Decimal(str(item["value"]).replace(",", ""))
        except InvalidOperation:
            conflicts.append(f"{field_} unreadable")
            continue
        if not locate(item.get("quote", ""), docs.get(doc, "")):
            conflicts.append(f"{field_} quote not found in {doc}")
        elif found != expected:
            conflicts.append(f"{doc} states {found}; intake states {expected}")
    return conflicts
