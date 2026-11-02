"""Connects reader, checks and exact layer. Every result goes to a CA; nothing is auto-approved."""
from __future__ import annotations
import hashlib, json
from datetime import date
from .core import (CATEGORIES, REQUIRED_AUTHORITIES, BP, FIS, ROYALTY, compute_tax, decide, load_yaml,
                   regime_for, route_forms, sensitivity, TaxResult)
from .verify import amount_conflicts, validate_shape, verify_quotes

READY, ESCALATE = "READY_FOR_CA_REVIEW", "ESCALATE_TO_CA"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _used_rule_flags(ids, rules, authorities):
    flags = []
    for rid in ids:
        status = rules["rates"].get(rid, rules.get(rid, {})).get("status")
        if status and status != "official":
            flags.append(f"Rule {rid} rests on a {status} source; CA to confirm.")
    return flags


def run_case(contract: str, invoice: str, intake: dict, reader, as_of: str, rules=None, authorities=None) -> dict:
    rules = rules or load_yaml("rules.yaml")
    authorities = authorities or load_yaml("authorities.yaml")
    trace = {
        "disclaimer": "Draft working paper for CA review. Not tax advice and not a certificate.",
        "as_of": as_of, "rule_pack": rules["pack_version"], "contract_sha256": sha(contract),
        "invoice_sha256": sha(invoice), "intake": intake, "gates": [], "escalations": [], "flags": [],
    }

    def gate(name, passed, detail=""):
        trace["gates"].append({"gate": name, "passed": passed, "detail": detail})

    def esc(code, reason):
        trace["escalations"].append({"code": code, "reason": reason})

    # Gates that do not depend on the model.
    today = date.fromisoformat(as_of)
    stale = today > date.fromisoformat(rules["review_by"])
    gate("rule_pack_current", not stale, f"review_by {rules['review_by']}")
    if stale:
        esc("RULE_PACK_STALE", "Rule pack is past its review date.")
    day = date.fromisoformat(intake["remittance_date"])
    regime = regime_for(day, rules)
    gate("rule_covers_date", regime is not None, intake["remittance_date"])
    if regime is None:
        esc("NO_RULE_FOR_DATE", "No rule set covers this remittance date.")
    credit = intake.get("credit_date")
    if regime and credit and regime_for(date.fromisoformat(credit), rules) != regime:
        gate("single_regime", False, f"credit {credit}, remittance {intake['remittance_date']}")
        esc("REGIME_TRANSITION", "Credit and remittance fall under different Acts; which rule governs deduction needs CA judgment.")
    else:
        gate("single_regime", True)
    if intake.get("ao_certificate"):
        esc("AO_CERTIFICATE", "An Assessing Officer certificate is outside the prototype.")
    if intake.get("payee_country") != "US" or intake.get("payee_type") != "company":
        esc("OUT_OF_SCOPE_PAYEE", "Prototype covers US companies only.")

    # Probabilistic read, then checks on the output.
    docs = {"contract": contract, "invoice": invoice}
    read = reader.read(contract, invoice, list(authorities))
    trace["reader"] = read["meta"]
    output = read.get("output")
    errors = validate_shape(output) if output is not None else [read.get("error") or "reader failed"]
    gate("output_valid", not errors, "; ".join(errors))
    if errors:
        esc("READER_FAILED", "; ".join(errors))
        return _finish(trace, None, None, None, rules)

    values, evidence, failed = verify_quotes(output, docs)
    trace["facts"], trace["evidence"] = values, evidence
    gate("quotes_found", not failed, ", ".join(failed))
    if failed:
        esc("UNVERIFIED_QUOTE", "Quotes not found in the documents for: " + ", ".join(failed))

    bad_cites = [c for c in output.get("citations", []) if c not in authorities]
    gate("citations_allowed", not bad_cites, ", ".join(map(str, bad_cites)))
    if bad_cites:
        esc("UNKNOWN_CITATION", "Unknown authorities cited: " + ", ".join(map(str, bad_cites)))

    conflicts = amount_conflicts(output, intake, docs)
    gate("amounts_agree", not conflicts, "; ".join(conflicts))
    if conflicts:
        esc("AMOUNT_CONFLICT", "; ".join(conflicts))

    decision = decide(values)
    trace["decision"] = {"category": decision.category, "code": decision.code, "reason": decision.reason}
    trace["model_reasoning_unverified"] = output.get("reasoning", "")
    if decision.category is None:
        esc(decision.code, decision.reason)
    proposed = output.get("proposed_category")
    agree = proposed == (decision.category or "UNRESOLVED")
    gate("two_key_agreement", agree, f"model {proposed}; table {decision.category}")
    if not agree:
        esc("TWO_KEY_DISAGREEMENT", f"Model proposed {proposed}; fact table gave {decision.category or 'UNRESOLVED'}.")

    trace["what_would_change"] = sensitivity(values)
    net = values.get("net_of_tax_clause") == "yes"
    if decision.category and regime:
        result = compute_tax(decision.category, intake, rules, regime, net)
        if isinstance(result, str):
            esc(result, "Exact layer lacks an input it needs.")
            result = None
    else:
        result = None
    trace["exposure_scenarios"] = _scenarios(intake, rules, regime, net) if regime else {}
    return _finish(trace, decision, result, regime, rules, authorities)


def _scenarios(intake, rules, regime, net):
    out = {}
    for category in CATEGORIES:
        r = compute_tax(category, intake, rules, regime, net)
        out[category] = str(r.tds_inr) if isinstance(r, TaxResult) else f"cannot compute: {r}"
    return out


def _finish(trace, decision, result, regime, rules, authorities=None):
    trace["status"] = ESCALATE if trace["escalations"] else READY
    trace["category"] = decision.category if decision else None
    # An escalated case carries scenarios, never a single recommended number.
    if result is not None and regime is not None and not trace["escalations"]:
        trace["tax"] = {"gross_inr": str(result.gross_inr), "tds_inr": str(result.tds_inr),
                        "effective_rate_pct": str(result.effective_rate_pct), "basis": result.basis,
                        "steps": result.steps, "rules_used": result.rule_ids}
        forms = route_forms(result, trace["intake"], rules, regime)
        trace["forms"] = forms
        if forms["flag"]:
            trace["flags"].append(forms["flag"])
        trace["flags"] += _used_rule_flags(result.rule_ids, rules, authorities or {})
    if decision and decision.category and authorities:
        trace["authorities"] = {k: authorities[k] for k in REQUIRED_AUTHORITIES[decision.category]}
    trace["trace_sha256"] = sha(json.dumps(trace, sort_keys=True, default=str))
    return trace


def render_paper(t: dict) -> str:
    i = t["intake"]
    L = [f"# Draft working paper: {i.get('payee', 'Payee')}", "",
         "> Draft for Chartered Accountant review. Not tax advice and not a certificate. Only the CA signs.", "",
         f"**Status:** {t['status']}  ", f"**Suggested category:** {t.get('category') or 'Unresolved'}  ",
         f"**Remittance:** {i['amount']} {i['currency']} on {i['remittance_date']}", ""]
    if t["escalations"]:
        L += ["## Why this needs your judgment", *[f"- **{e['code']}:** {e['reason']}" for e in t["escalations"]], ""]
    if t.get("tax"):
        x = t["tax"]
        L += ["## Calculated by code", f"TDS **INR {int(x['tds_inr']):,}** at {x['effective_rate_pct']}% ({x['basis']})", "",
              *[f"{n}. {s}" for n, s in enumerate(x["steps"], 1)], "", f"**Forms:** {t['forms']['route']}", ""]
    if t.get("exposure_scenarios"):
        L += ["## TDS under each possible category", "Uses the intake amount. These are scenarios, not recommendations.", "", "| Category | TDS (INR) |", "|---|---|",
              *[f"| {k} | {v} |" for k, v in t["exposure_scenarios"].items()], ""]
    if t.get("evidence"):
        L += ["## Evidence", *[f"- `{e['fact']}` = {e['value']}: \"{e['quote']}\" ({e['document']}, chars {e['start']}-{e['end']})" for e in t["evidence"]], ""]
    if t.get("what_would_change"):
        L += ["## Facts to check", *[f"- If `{c['fact']}` were {c['to']}: {c['outcome']}" for c in t["what_would_change"]], ""]
    if t.get("authorities"):
        L += ["## Authorities to read", *[f"- {a['title']} ({a['status']}): {a['source']}" for a in t["authorities"].values()], ""]
    if t["flags"]:
        L += ["## Confirm before signing", *[f"- {f}" for f in t["flags"]], ""]
    L += ["## Audit", f"- Rule pack: {t['rule_pack']}", f"- Reader: {t.get('reader', {})}",
          f"- Contract SHA-256: {t['contract_sha256']}", f"- Trace SHA-256: {t['trace_sha256']}", "",
          "## CA decision", "Approve / Change / Reject: ________  Reason: ________  CA and UDIN: ________", ""]
    return "\n".join(L)
