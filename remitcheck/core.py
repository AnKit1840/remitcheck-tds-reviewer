"""Exact layer: no model code runs here. Same input always gives same output."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
BP, ROYALTY, FIS = "BUSINESS_PROFITS_NO_PE", "ROYALTY", "FIS"
CATEGORIES = (BP, ROYALTY, FIS)
FACT_KEYS = (
    "copyright_rights_granted", "program_or_design_transferred", "technical_service",
    "knowhow_transfer", "software_access_only", "usage_training_beyond_initial",
    "india_presence", "mixed_unallocated", "net_of_tax_clause",
)
REQUIRED_AUTHORITIES = {
    BP: ["ART12_4B_MAKE_AVAILABLE", "ENGINEERING_ANALYSIS", "TREATY_RELIEF_DOCS"],
    ROYALTY: ["ART12_RATE", "ART12_3_ROYALTY", "TREATY_RELIEF_DOCS"],
    FIS: ["ART12_RATE", "ART12_4B_MAKE_AVAILABLE", "TREATY_RELIEF_DOCS"],
}


def load_yaml(name):
    return yaml.safe_load((ROOT / "knowledge" / name).read_text())


def d(value) -> Decimal:
    return Decimal(str(value))


@dataclass
class Decision:
    category: str | None
    code: str
    reason: str


def decide(f: dict) -> Decision:
    """Maps verified facts to a treaty category, or to an escalation code."""
    v = lambda k: f.get(k, "silent")
    if v("india_presence") == "yes":
        return Decision(None, "PE_RISK", "Payee presence in India; permanent establishment analysis is out of scope.")
    if v("mixed_unallocated") == "yes":
        return Decision(None, "MIXED_UNALLOCATED", "One price covers items that may have different tax treatment.")
    if v("copyright_rights_granted") == "yes":
        return Decision(ROYALTY, "OK", "Customer receives rights to exploit copyright.")
    if v("program_or_design_transferred") == "yes":
        return Decision(FIS, "OK", "A technical plan, design or modified program is transferred.")
    if v("technical_service") == "yes":
        if v("knowhow_transfer") == "yes":
            return Decision(FIS, "OK", "Technical service enables the customer to apply the technology.")
        if v("knowhow_transfer") != "no":
            return Decision(None, "MISSING_MAKE_AVAILABLE_FACT", "Contract does not settle whether know-how is transferred.")
        if v("usage_training_beyond_initial") == "yes":
            return Decision(None, "CONTESTED_TRAINING", "Later training: MoU Example 8 and Openwave point different ways.")
        return Decision(BP, "OK", "Technical service does not make technology available.")
    if v("software_access_only") == "yes":
        if v("usage_training_beyond_initial") == "yes":
            return Decision(None, "CONTESTED_TRAINING", "Later training: MoU Example 8 and Openwave point different ways.")
        return Decision(BP, "OK", "Use of standard software without copyright rights.")
    return Decision(None, "INSUFFICIENT_FACTS", "Facts do not identify what is being paid for.")


def sensitivity(facts: dict) -> list[dict]:
    """Flips one fact at a time and reports each change in outcome."""
    base = decide(facts)
    changes = []
    for key in FACT_KEYS:
        if key == "net_of_tax_clause":
            continue
        current = facts.get(key, "silent")
        alt = "no" if current == "yes" else "yes"
        new = decide({**facts, key: alt})
        if (new.category, new.code) != (base.category, base.code):
            changes.append({"fact": key, "from": current, "to": alt,
                            "outcome": new.category or f"ESCALATE:{new.code}"})
    return changes


@dataclass
class TaxResult:
    gross_inr: Decimal
    tds_inr: Decimal
    effective_rate_pct: Decimal
    basis: str
    steps: list = field(default_factory=list)
    rule_ids: list = field(default_factory=list)


def rupee(x: Decimal) -> Decimal:
    return x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def regime_for(day: date, rules: dict) -> dict | None:
    for r in rules["regimes"]:
        if date.fromisoformat(r["from"]) <= day and (r["to"] is None or day <= date.fromisoformat(r["to"])):
            return r
    return None


def treaty_docs_gaps(i: dict, category: str, regime: dict) -> list[str]:
    gaps = []
    day = date.fromisoformat(i["remittance_date"])
    if not (i.get("trc_from") and i.get("trc_to")
            and date.fromisoformat(i["trc_from"]) <= day <= date.fromisoformat(i["trc_to"])):
        gaps.append("TRC valid on the remittance date")
    if not i.get("treaty_form_filed"):
        gaps.append(regime["treaty_declaration_form"])
    if not i.get("beneficial_owner_declared"):
        gaps.append("beneficial ownership declaration")
    if category == BP and not i.get("no_pe_declared"):
        gaps.append("no-PE declaration")
    return gaps


def compute_tax(category: str, i: dict, rules: dict, regime: dict, net_of_tax: bool) -> TaxResult | str:
    """Returns the exact TDS, or an escalation code when an input is missing."""
    R = rules["rates"]
    fx = i.get("fx_rate")
    if fx in (None, ""):
        return "FX_RATE_MISSING"
    base = d(i["amount"]) * d(fx)
    steps = [f"{i['amount']} {i['currency']} x {fx} = INR {base:,.2f}"]
    gaps = treaty_docs_gaps(i, category, regime)

    if category == BP:
        if gaps:
            return "TREATY_DOCS_MISSING_FOR_NIL_RATE"
        return TaxResult(rupee(base), Decimal(0), Decimal(0), "treaty_nil", steps + ["No TDS: business profits, no PE"],
                         ["ART12_4B_MAKE_AVAILABLE"])

    if not gaps:
        key = "treaty_royalty_pct" if category == ROYALTY else "treaty_fis_pct"
        rate, basis, ids = d(R[key]["value"]), "treaty", [key]
        steps.append(f"Treaty rate {rate}% (no surcharge or cess)")
    else:
        key = "act_royalty_pct" if category == ROYALTY else "act_fts_pct"
        band = i.get("payee_income_band")
        table = rules["surcharge_bands_pct"]
        if band not in table or band in ("status", "source"):
            return "SURCHARGE_BAND_UNKNOWN"
        surcharge, cess = d(table[band]), d(R["cess_pct"]["value"])
        act = d(R[key]["value"])
        rate = act * (1 + surcharge / 100) * (1 + cess / 100)
        basis, ids = "act", [key, "surcharge_bands_pct", "cess_pct"]
        steps.append(f"Treaty unavailable ({'; '.join(gaps)}). {act}% x (1+{surcharge}%) x (1+{cess}%) = {rate}%")

    floor = d(R["no_pan_floor_pct"]["value"])
    if not i.get("pan") and not i.get("alt_details_furnished") and rate < floor:
        rate, basis = floor, "no_pan_floor"
        ids.append("no_pan_floor_pct")
        steps.append(f"No PAN or alternative details: rate raised to {floor}%")

    gross = base * 100 / (100 - rate) if net_of_tax else base
    if net_of_tax:
        steps.append(f"Net-of-tax gross-up: {base:,.2f} x 100 / (100 - {rate}) = {gross:,.2f}")
    tds = rupee(gross * rate / 100)
    steps.append(f"TDS = {gross:,.2f} x {rate}% = INR {tds:,}")
    return TaxResult(rupee(gross), tds, rate, basis, steps, ids)


def route_forms(result: TaxResult, i: dict, rules: dict, regime: dict) -> dict:
    limit = d(rules["rates"]["certificate_threshold_inr"]["value"])
    decl, cert = regime["declaration_form"], regime["certificate_form"]
    cumulative = d(i.get("ytd_taxable_inr", 0)) + result.gross_inr
    if result.tds_inr == 0:
        return {"route": f"{decl} Part D candidate", "certificate_required": None,
                "flag": f"CA to confirm Part D versus Part C with {cert} when non-chargeability rests on the treaty."}
    if cumulative <= limit:
        return {"route": f"{decl} Part A", "certificate_required": False, "flag": None}
    return {"route": f"{decl} Part C + {cert}", "certificate_required": True, "flag": None}
