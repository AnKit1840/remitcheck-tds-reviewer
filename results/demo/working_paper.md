# Draft working paper: Lumen Stack Inc.

> Draft for Chartered Accountant review. Not tax advice and not a certificate. Only the CA signs.

**Status:** READY_FOR_CA_REVIEW  
**Suggested category:** BUSINESS_PROFITS_NO_PE  
**Remittance:** 50000 USD on 2026-11-15

## Calculated by code
TDS **INR 0** at 0% (treaty_nil)

1. 50000 USD x 88.00 = INR 4,400,000.00
2. No TDS: business profits, no PE

**Forms:** Form 145 Part D candidate

## TDS under each possible category
| Category | TDS (INR) |
|---|---|
| BUSINESS_PROFITS_NO_PE | 0 |
| ROYALTY | 660000 |
| FIS | 660000 |

## Evidence
- `software_access_only` = yes: "SaaS Subscription Agreement." (contract, chars 0-28)

## Facts to check
- If `copyright_rights_granted` were yes: ROYALTY
- If `program_or_design_transferred` were yes: FIS
- If `technical_service` were yes: ESCALATE:MISSING_MAKE_AVAILABLE_FACT
- If `software_access_only` were no: ESCALATE:INSUFFICIENT_FACTS
- If `usage_training_beyond_initial` were yes: ESCALATE:CONTESTED_TRAINING
- If `india_presence` were yes: ESCALATE:PE_RISK
- If `mixed_unallocated` were yes: ESCALATE:MIXED_UNALLOCATED

## Authorities to read
- India-US treaty Art. 12(4)(b) and MoU: make available (official): https://www.llmtax.uzh.ch/dam/jcr:88df95b6-4ebe-4440-9526-0bb2cfbe4614/1.%20India%20USA%20MoU%20concerning%20fees%20for%20included%20services%20in%20Article%2012.pdf
- Engineering Analysis v CIT (Supreme Court, 2 March 2021) (secondary): https://itatonline.org/archives/engineering-analysis-centre-of-excellence-private-limited-vs-cit-supreme-court-taxability-of-sums-received-for-supply-of-software-as-royalty-given-the-definition-of-royalties-contained-in-article/
- Income-tax Act 2025 s.159(8), Rule 75 and Form 41 (official): https://www.incometaxindia.gov.in/documents/d/guest/form-41-faqs

## Confirm before signing
- CA to confirm Part D versus Part C with Form 146 when non-chargeability rests on the treaty.

## Audit
- Rule pack: 2026.11-prototype
- Reader: {'reader': 'baseline_keywords'}
- Contract SHA-256: 3f3399107d90ef9850ebb6e8516bff2806c6afa8a62290c735d08161bad7597a
- Trace SHA-256: b29ac4c5277986b4d5644709fc85e4d20abc4a64be8ab50cc64487352487c365

## CA decision
Approve / Change / Reject: ________  Reason: ________  CA and UDIN: ________
