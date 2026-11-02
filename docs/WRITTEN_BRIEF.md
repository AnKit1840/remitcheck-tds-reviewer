# RemitCheck: AI-Assisted Withholding Tax Review for Indian Companies Paying US Software Vendors

> **Disclaimer:** This brief describes a prototype for evaluation purposes only. It is not tax advice. All contracts, companies and labels used in the prototype are synthetic.

---

## 1. The Area — What I Explored and What Surprised Me

Indian companies increasingly pay US software vendors for SaaS platforms, cloud services, source licences and technical consulting. Each such payment may attract Tax Deducted at Source (TDS) under Indian law and the India-US Double Tax Avoidance Agreement (DTAA). The payer — not the vendor — is legally responsible for withholding the correct amount before remitting funds abroad.

Getting this wrong is costly in both directions. Under-withholding creates a liability for the payer company plus interest and penalty. Over-withholding damages vendor relationships and can involve months of refund proceedings. The decision turns on a careful reading of contract language against the India-US treaty's "make available" doctrine — a distinction that even experienced practitioners find non-obvious.

**What surprised me:** The treaty's legal test and the commercial label on a contract often point in opposite directions. A contract labelled "SaaS" can grant copyright reproduction rights that push the payment into the Royalty category. A contract labelled "consulting" can transfer zero knowledge and belong in Business Profits. The label is irrelevant; the clause language is everything. This makes the problem well-suited for an LLM that reads substance rather than surface, paired with deterministic rules that cannot be overridden by creative labelling.

---

## 2. The Problem

**Who:** Finance controllers and Chartered Accountants (CAs) at Indian companies with US software vendor relationships.

**What task:** For each foreign remittance above a threshold, a CA must: read the contract and invoice, classify the payment under the treaty (Business Profits / Royalty / Fees for Included Services), calculate TDS to the rupee, determine the correct Form 145/Form 146 filing route under the Income-Tax Act 2025, and sign a working paper before the wire clears.

**How often:** The volume varies by company size. Any company with recurring US vendor payments faces this review for each remittance above the certificate threshold (currently ₹5 lakh cumulative per payee per year).

**What it costs today:** Each review involves reading the contract, cross-referencing the treaty text and the India-US MoU examples, retrieving the correct surcharge band, calculating TDS with gross-up where applicable, and drafting the working paper. The time per review depends on contract complexity and the reviewer's familiarity with the treaty. Missed nuances — particularly the "make available" test — are a documented source of incorrect nil-TDS results that Assessing Officers challenge years later.

**What is out of scope:** Permanent establishment analysis, transfer pricing, treaty shopping, splitting mixed contracts, RBI purpose codes, portal filing, other jurisdictions.

---

## 3. The Solution

### Core design principle
> **The model reads. Code decides and calculates. The CA is accountable.**

No model output is trusted until it has passed a chain of verification gates. No tax figure is ever produced by the model. The model's sole job is to extract nine factual answers, with exact quotes, from contract and invoice text.

### What goes in
- The full text of the contract and invoice (pasted or uploaded)
- A finance intake form: vendor name, payment amount, currency, FX rate, remittance date, credit date, payee income band, TRC validity dates, and which treaty documents have been filed

### What the AI does
The LLM answers nine fixed factual questions about the documents:

| Fact | Why it matters |
|---|---|
| `copyright_rights_granted` | Triggers Royalty if yes |
| `program_or_design_transferred` | Triggers FIS if yes |
| `technical_service` | Entry point for "make available" analysis |
| `knowhow_transfer` | Separates FIS from Business Profits |
| `software_access_only` | Supports Business Profits if other facts are no |
| `usage_training_beyond_initial` | Flags the contested MoU Example 8 / Openwave tension |
| `india_presence` | Triggers PE risk escalation |
| `mixed_unallocated` | Flags unsplit prices |
| `net_of_tax_clause` | Triggers gross-up in TDS calculation |

Every answer must be `yes`, `no` or `silent`, accompanied by an **exact verbatim quote** from the supplied document. The model also proposes a category (`ROYALTY`, `FIS`, `BUSINESS_PROFITS_NO_PE` or `UNRESOLVED`).

### What comes out after verification
1. **Quote verification:** Every `yes`/`no` answer is checked by locating its quote character-by-character in the document. Invented quotes cause immediate escalation.
2. **Decision table:** A deterministic function maps the nine verified facts to a category. The same facts always give the same result.
3. **Two-key check:** The model's proposed category is compared with the table's category. Any disagreement triggers escalation.
4. **TDS calculation:** Performed with Python `Decimal` arithmetic (never by the model) using rates, surcharge bands and cess from a versioned, dated rule pack (`knowledge/rules.yaml`).
5. **Form routing:** Based on remittance date (Act 1961 vs Act 2025 regime), gross amount vs the ₹5 lakh certificate threshold, and treaty documents on file.
6. **Sensitivity table:** One fact at a time is flipped; changes in outcome are listed so the CA immediately sees what the result depends on.

### Where human review is needed
Every result is `READY_FOR_CA_REVIEW` or `ESCALATE_TO_CA` — never "approved". The CA reads the working paper, checks the quoted clauses, confirms the facts, and either approves or overrides. Only the CA signs the Form 146 certificate. That signature cannot be delegated to the system.

### How it handles uncertainty and mistakes
- **Uncertain model output** → escalation code (`TWO_KEY_DISAGREEMENT`, `INSUFFICIENT_FACTS`)
- **Hallucinated quote** → escalation (`UNVERIFIED_QUOTE`)
- **Out-of-date rules** → hard stop after `review_by` date (`RULE_PACK_STALE`)
- **Model API failure** → escalation (`READER_FAILED`), never a silent wrong answer
- **Amount conflict between contract, invoice and intake** → escalation (`AMOUNT_CONFLICT`)

### Why AI rather than a simpler approach
A keyword baseline (the prototype includes one) achieves 9/16 on the same 16 cases, with one unsafe wrong answer (C05: a "SaaS" contract that grants reproduction rights, classified as nil tax instead of Royalty). It also fails on cases that require reading substance over labels. The LLM, constrained to answer nine factual questions with direct quotes, approximates a careful reading at scale. The architecture catches many LLM errors through the verification gates and two-key check, but it is not guaranteed to catch all of them: if the model returns a plausible wrong fact with a real quote that happens to support it, the gates will not detect the error.

---

## 4. Architecture Diagram

```
Contract + Invoice
        │
        ▼
┌───────────────────┐
│   LLM Fact Reader │  ← probabilistic; reads substance not labels
│  (9 facts + quote │
│   per fact)       │
└────────┬──────────┘
         │ raw output
         ▼
┌───────────────────┐
│ Verification Gates│  ← exact; distrusts model output
│  · shape check    │
│  · quote locator  │
│  · citation check │
│  · amount check   │
└────────┬──────────┘
         │ verified facts
         ▼
┌───────────────────┐     ┌──────────────────┐
│  Decision Table   │────▶│  Two-Key Check   │
│  (deterministic)  │     │  model vs table  │
└────────┬──────────┘     └────────┬─────────┘
         │ category                │ disagreement → ESCALATE
         ▼
┌───────────────────┐
│  Tax Calculator   │  ← Decimal arithmetic, rates from rule pack
│  · gross-up       │
│  · surcharge/cess │
│  · form routing   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  CA Working Paper │  ← draft only; CA approves and signs
│  + sensitivity    │
│  + trace.json     │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Chartered        │  ← accountable; only CA issues Form 146
│  Accountant       │
└───────────────────┘
```

### Alternatives considered and rejected

| Alternative | Why rejected |
|---|---|
| **Pure LLM classification** | Model does arithmetic unreliably; same facts can give different answers across runs; no audit trail |
| **Pure keyword rules** | 9/16 on the test set; misses substance-over-label cases; brittle to novel phrasing |
| **RAG over treaty text** | The treaty text itself is short and stable; embedding it in a prompt is simpler. RAG would help if the rule base were large and frequently updated |
| **Multi-agent pipeline** | One LLM call for fact extraction is sufficient; adding orchestration adds latency and failure modes without solving the core problem |

---

## 5. What I Added Beyond the AI

The full appendix is in [AI_APPENDIX.md](AI_APPENDIX.md). In summary:

- **Where AI helped:** Domain research on the India-US treaty, iterating on the extraction prompt, and generating the initial `locate()` function for quote verification.
- **What I rejected:** The LLM repeatedly offered to calculate TDS itself. I moved all arithmetic to deterministic Python `Decimal` code with rates read from a versioned rule pack, because a model-generated tax number has no audit trail.
- **What came from me:** The three-valued fact schema (`yes`/`no`/`silent`), the fail-closed rule staleness check, the two-key disagreement as an escalation signal rather than an error to suppress, and the adversarial prompt injection test case (C13).
- **What I'd defend live:** The `decide()` function in `core.py` — why `technical_service = yes` alone does not trigger FIS, and why `knowhow_transfer` needs three states to correctly implement the treaty's "make available" test.

---

## 6. Evaluation Results

| Run | Correct | Unsafe wrong answers | Over-escalated | Wrong escalation reason |
|---|---|---|---|---|
| Hand-labelled facts (gold) | **16 / 16** | 0 | 0 | 0 |
| Keyword baseline | **9 / 16** | 1 | 4 | 2 |
| Live LLM (`nvidia/nemotron-3.5-lightning:free`) | **9 / 16** | 0 | 6 | 1 |

The gold run validates that the rules and tax calculations match the author's own expected answers. The keyword baseline establishes what a non-AI approach achieves — including one unsafe wrong answer on C05, where keyword matching missed a copyright clause and returned nil tax instead of Royalty. 

The live LLM run evaluated all 16 cases on a single model (`nvidia/nemotron-3.5-lightning:free`). Both the baseline and the LLM achieved 9/16 accuracy, but their failure modes differed fundamentally:
- The keyword baseline produced an **unsafe wrong answer** on C05.
- The live LLM produced **zero unsafe wrong answers**. Its failures were conservative over-escalations (C02, C04, C06, C12, C15, C16) where the model proposed an incorrect category or hesitated on fact extraction, triggering the two-key agreement gate or fact gates to route the case to the CA.
- On C13 (the adversarial prompt injection test), the model correctly resisted the contract's instruction and classified the remittance as Royalty.

Thus, the LLM's primary operational advantage over the baseline is safety rather than higher raw accuracy: it fails closed by escalating to the CA rather than emitting unsafe certificates.

---

## 7. Risks

| Risk | How the design handles it |
|---|---|
| **Wrong tax amount** | Calculator uses only code and rule pack; model cannot produce a tax figure |
| **Hallucinated quote** | Quote locator rejects any answer whose quote is not found verbatim in the document |
| **Outdated rules** | `review_by` date in rule pack; every case escalates after that date |
| **Adversarial contract** | System prompt instructs model to ignore document-embedded instructions; verified live on C13 where prompt injection was resisted |
| **Automation bias** | Working paper is always a draft; CA must sign; status is never "approved" |
| **Confidential data** | Prototype uses synthetic data only; production would need a data processing agreement with the model provider |
| **Liability** | Output carries a mandatory disclaimer; Form 146 is signed by the CA, not produced by the system |
| **Source conflict** | Conflicting secondary sources are flagged on the working paper with a note for the CA to confirm |

---

## 8. Things to Consider Before Spending More Time

1. **CA validation of the decision table.** The 9-fact mapping is the prototype's largest unvalidated assumption. A practising CA should review it against the treaty, MoU examples and recent tribunal orders before any production use.
2. **Larger, annotated contract corpus.** The 16 synthetic cases were written by the same person who designed the rules — a consistency check, not an independent test.
3. **Model selection.** The prototype works with any OpenAI-compatible endpoint. Choosing a model with stable versioning and appropriate data retention terms is a pre-production requirement.
4. **Other treaties.** Adding the India-UK or India-Singapore treaty would require a new decision table and different fact questions (many treaties have no "make available" test at all).
5. **Portal integration.** Real production value comes from pre-filling Form 145/146 data. That requires integration with the Income Tax India portal, which is outside this prototype's scope.

