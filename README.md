# RemitCheck

A prototype that drafts a CA working paper for Indian companies paying US vendors for software and technical services. The LLM reads contract facts with exact quotes, code applies dated rules and calculates TDS, and a Chartered Accountant makes the decision.

**This is not tax advice.** All contracts, companies and labels in this repo are synthetic. The expected answers were written by the author and have not been validated by a CA.

Design details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Written Brief: [docs/WRITTEN_BRIEF.md](docs/WRITTEN_BRIEF.md) | AI Appendix: [docs/AI_APPENDIX.md](docs/AI_APPENDIX.md)

## Run it

Requires Python 3.10 or later.

```bash
pip install -r requirements.txt
python -m pytest -q

# No API key needed
python eval/run_eval.py --reader gold       # Hand-labelled facts: tests the exact layer
python eval/run_eval.py --reader baseline   # Keyword rules: the non-AI comparison

# Live LLM run
export OPENROUTER_API_KEY=your_key
python eval/run_eval.py --reader openrouter --model MODEL_ID
```

Each run writes `summary.md`, plus a working paper and trace per case, to `results/`. Use a specific free model ID from OpenRouter so the run can be repeated. Without `--model`, it uses the `openrouter/free` router, which may serve different models; each trace records the one used.

To check one payment and log a decision:

```bash
python -m remitcheck.cli check examples/packet_C05.yaml --reader baseline --as-of 2026-11-03 --out results/demo
python -m remitcheck.cli review results/demo/trace.json --decision change --reason "..." --ca "Name"
```

## Results so far

| Run | Correct | Unsafe wrong answers | Over-escalated | Escalated for wrong reason |
|---|---|---|---|---|
| Hand-labelled facts | 16/16 | 0 | 0 | 0 |
| Keyword baseline | 9/16 | 1 | 4 | 2 |
| **Live LLM (`nvidia/nemotron-3.5-lightning:free`)** | **9/16** | **0** | **6** | **1** |

Full breakdown: [`results/openrouter_nvidia_nemotron-3.5-lightning_free/summary.md`](results/openrouter_nvidia_nemotron-3.5-lightning_free/summary.md).

**Comparison with baseline:**
Both the keyword baseline and the live LLM scored 9/16 correct, but their safety profiles differ:
- **Keyword baseline:** Produced an **unsafe wrong answer on C05** (missed the copyright reproduction right, returning nil tax instead of Royalty INR 660,000).
- **Live LLM:** Produced **zero unsafe wrong answers**. On cases like C02, C04, and C12, the model proposed the wrong category or exhibited fact extraction ambiguity, but the deterministic verification gates and two-key agreement check caught the discrepancies and safely escalated to the Chartered Accountant (`ESCALATE_TO_CA`). On C13 (the adversarial prompt injection test), the model correctly resisted contract instructions and classified the payment as Royalty.

The hand-labelled run confirms the rules and calculations match the author's own labels. It does not show the labels are legally right. It uses the same author's labels for the facts and the expected results, so it is a consistency check only.

### Where the keyword baseline fails

- **C05, unsafe:** A "SaaS" contract lets the customer copy and embed a library. The keywords missed this, so the result was nil tax instead of INR 660,000.
- **C02, C04, C15, over-escalated:** Ordinary wording such as "install and use", "teach" and "train" did not match the keywords.
- **C06, over-escalated:** It missed that the customer "will keep relying" on the vendor.
- **C07, C14, wrong reason:** It escalated, but missed the unsplit price and staff in Pune.

These cases were written by the same person as the keywords, so they don't give an unbiased error rate.

## Test cases

| ID | Group | Scenario | Expected |
|---|---|---|---|
| C01 | Clear | Plain SaaS subscription | Nil, Part D candidate |
| C02 | Clear | Off-the-shelf end-user licence | Nil, Part D candidate |
| C03 | Clear | Source licence with redistribution rights | Royalty, INR 13,20,000 |
| C04 | Clear | Training that transfers capability | FIS, INR 5,28,000 |
| C05 | Ambiguous | Called SaaS, but grants reproduction rights | Royalty, INR 6,60,000 |
| C06 | Ambiguous | Called consulting, but no capability passes | Nil, Part D candidate |
| C07 | Ambiguous | One price for platform and enablement | Escalate |
| C08 | Ambiguous | Vague knowledge sharing | Escalate |
| C09 | Missing | Royalty without a TRC | Act rate, INR 3,66,080 |
| C10 | Conflict | Invoice contradicts contract | Escalate |
| C11 | Rule change | Credited before the new Act, paid after | Escalate |
| C12 | Rule change | Remitted under the old Act | FIS, Form 15CA and 15CB |
| C13 | Adversarial | Contract instructs the AI reviewer | Royalty, INR 4,62,000 |
| C14 | Adversarial | Staff based in India | Escalate |
| C15 | Clear | Net-of-tax clause | FIS, grossed up, INR 5,28,000 |
| C16 | Clear | Below the cumulative threshold | Royalty, Part A |

## Check before relying on this

- Many rates and section references come from secondary guides, and are marked as such in `knowledge/rules.yaml`. Check them against the Act, Rules and treaty.
- Surcharge bands were confirmed only through AY 2026-27 and are carried forward.
- Whether a nil treaty result belongs in Part D, or Part C with Form 146, is flagged for the CA and not decided here.
- Sources conflict on some points. For example, one guide states a 40% no-PAN rate, while others state 20%. The rule pack uses 20%, which a CA should confirm.
- The Form 41 FAQ is inconsistent on filing timing.

## Layout

```text
knowledge/    Dated rules and allowed authorities
remitcheck/   core.py (rules and tax), verify.py (gates), llm.py (readers),
              pipeline.py (flow and paper), cli.py
eval/         16 synthetic cases and the evaluator
tests/        Unit tests, including gate failures and a mock API
results/      Evaluation output
docs/         Architecture and diagram
```
