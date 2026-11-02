"""Usage: python eval/run_eval.py --reader gold|baseline|openrouter [--model ID]"""
import argparse, json, sys, time
from pathlib import Path
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from remitcheck.llm import BaselineReader, GoldReader, OpenRouterReader
from remitcheck.pipeline import READY, render_paper, run_case

AS_OF = "2026-11-03"


class GoldAmounts(GoldReader):
    def read(self, contract, invoice, authorities):
        r = super().read(contract, invoice, authorities)
        for k in ("contract_amount", "invoice_amount"):
            if k in self.case["gold"]:
                value, quote = self.case["gold"][k]
                r["output"][k] = {"value": value, "quote": quote}
        return r


def norm(value):
    return {True: "yes", False: "no"}.get(value, value)


def score(case, t):
    g = case["gold"]
    got_ready = t["status"] == READY
    row = {"id": case["id"], "group": case["group"], "title": case["title"], "expected": g["route"],
           "got": "READY" if got_ready else "ESCALATE", "category": t.get("category"),
           "tds": (t.get("tax") or {}).get("tds_inr"), "codes": [e["code"] for e in t["escalations"]]}
    if g["route"] == "READY":
        cat_ok = t.get("category") == g["category"]
        tax_ok = got_ready and int(row["tds"] or -1) == g["tds"]
        form_ok = got_ready and g["forms"] in t["forms"]["route"]
        row["result"] = ("correct" if cat_ok and tax_ok and form_ok else "UNSAFE_WRONG_ANSWER") if got_ready else "over_escalated"
    else:
        ok = not got_ready and any(c in row["codes"] for c in g["codes"])
        row["result"] = "UNSAFE_WRONG_ANSWER" if got_ready else ("correct" if ok else "escalated_wrong_reason")
    facts_gold = {k: norm(v[0]) for k, v in g.get("facts", {}).items()}
    got_facts = t.get("facts") or {}
    row["fact_errors"] = [k for k, v in facts_gold.items() if got_facts.get(k) != v]
    return row


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reader", choices=["gold", "baseline", "openrouter"], required=True)
    p.add_argument("--model"); p.add_argument("--pause", type=float, default=4)
    a = p.parse_args()
    root = Path(__file__).resolve().parent.parent
    data = yaml.safe_load((root / "eval/cases.yaml").read_text())
    tag = a.reader if a.reader != "openrouter" else "openrouter_" + (a.model or "default").replace("/", "_").replace(":", "_")
    out = root / "results" / tag
    (out / "papers").mkdir(parents=True, exist_ok=True)
    live = OpenRouterReader(model=a.model) if a.reader == "openrouter" else None
    rows = []
    for case in data["cases"]:
        intake = {**data["defaults"], **case["intake"]}
        reader = live or (BaselineReader() if a.reader == "baseline" else GoldAmounts(case))
        t = run_case(case["contract"], case["invoice"], intake, reader, AS_OF)
        rows.append(score(case, t))
        (out / "papers" / f"{case['id']}.md").write_text(render_paper(t))
        (out / "papers" / f"{case['id']}.trace.json").write_text(json.dumps(t, indent=2, default=str))
        if live:
            time.sleep(a.pause)
    n = len(rows)
    count = lambda r: sum(x["result"] == r for x in rows)
    summary = {"reader": tag, "cases": n, "correct": count("correct"), "unsafe_wrong_answers": count("UNSAFE_WRONG_ANSWER"),
               "over_escalated": count("over_escalated"), "escalated_wrong_reason": count("escalated_wrong_reason")}
    served = sorted({json.loads((out / "papers" / f"{c['id']}.trace.json").read_text()).get("reader", {}).get("served_model") or "" for c in data["cases"]} - {""})
    if served:
        summary["served_models"] = served
    L = [f"# Evaluation: {tag}", "", "Synthetic cases. Labels are the author's and have not been validated by a CA.", "",
         f"Correct: **{summary['correct']}/{n}** | Unsafe wrong answers: **{summary['unsafe_wrong_answers']}** | Over-escalated: **{summary['over_escalated']}** | Escalated for the wrong reason: **{summary['escalated_wrong_reason']}**", ""]
    if served:
        L += [f"Models served: {', '.join(served)}", ""]
    L += ["| Case | Scenario | Expected | Got | Category | TDS | Codes | Result | Fact errors |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['id']} | {r['title']} | {r['expected']} | {r['got']} | {r['category'] or '-'} | {r['tds'] or '-'} | {', '.join(r['codes']) or '-'} | {r['result']} | {', '.join(r['fact_errors']) or '-'} |")
    (out / "summary.md").write_text("\n".join(L) + "\n")
    (out / "summary.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))
    print("\n".join(L))


if __name__ == "__main__":
    main()
