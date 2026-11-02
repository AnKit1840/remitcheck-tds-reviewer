"""Usage: python -m remitcheck.cli check PACKET.yaml [--reader openrouter|baseline] [--as-of DATE]
          python -m remitcheck.cli review TRACE.json --decision approve --reason TEXT --ca NAME"""
from __future__ import annotations
import argparse, json
from datetime import date, datetime, timezone
from pathlib import Path
import yaml
from .llm import BaselineReader, OpenRouterReader
from .pipeline import render_paper, run_case, sha


def main():
    p = argparse.ArgumentParser(prog="remitcheck")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("packet"); c.add_argument("--reader", choices=["openrouter", "baseline"], default="openrouter")
    c.add_argument("--model"); c.add_argument("--as-of", default=date.today().isoformat()); c.add_argument("--out", default="results/run")
    r = sub.add_parser("review")
    r.add_argument("trace"); r.add_argument("--decision", choices=["approve", "change", "reject"], required=True)
    r.add_argument("--reason", required=True); r.add_argument("--ca", required=True)
    a = p.parse_args()
    if a.cmd == "check":
        pk = yaml.safe_load(Path(a.packet).read_text(encoding="utf-8"))
        reader = BaselineReader() if a.reader == "baseline" else OpenRouterReader(model=a.model)
        t = run_case(pk["contract"], pk["invoice"], pk["intake"], reader, a.as_of)
        out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
        (out / "trace.json").write_text(json.dumps(t, indent=2, default=str), encoding="utf-8")
        (out / "working_paper.md").write_text(render_paper(t), encoding="utf-8")
        print(f"{t['status']} | wrote {out}/working_paper.md and trace.json")
    else:
        raw = Path(a.trace).read_text(encoding="utf-8")
        rec = {"trace_file_sha256": sha(raw), "decision": a.decision, "reason": a.reason, "ca": a.ca,
               "at": datetime.now(timezone.utc).isoformat()}
        log = Path(a.trace).with_name("review_log.jsonl")
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"Recorded in {log}")


if __name__ == "__main__":
    main()
