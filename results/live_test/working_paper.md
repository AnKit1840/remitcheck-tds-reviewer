# Draft working paper: Lumen Stack Inc.

> Draft for Chartered Accountant review. Not tax advice and not a certificate. Only the CA signs.

**Status:** ESCALATE_TO_CA  
**Suggested category:** ROYALTY  
**Remittance:** 50000 USD on 2026-11-15

## Why this needs your judgment
- **TWO_KEY_DISAGREEMENT:** Model proposed UNRESOLVED; fact table gave ROYALTY.

## TDS under each possible category
Uses the intake amount. These are scenarios, not recommendations.

| Category | TDS (INR) |
|---|---|
| BUSINESS_PROFITS_NO_PE | 0 |
| ROYALTY | 660000 |
| FIS | 660000 |

## Evidence
- `copyright_rights_granted` = yes: "Customer may copy the Lumen client library, embed it in apps sold to Customer's own customers, and create adapted versions of it." (contract, chars 100-229)
- `program_or_design_transferred` = yes: "Customer may copy the Lumen client library, embed it in apps sold to Customer's own customers, and create adapted versions of it." (contract, chars 100-229)
- `technical_service` = no: "Customer subscribes to the Lumen service." (contract, chars 29-70)
- `knowhow_transfer` = yes: "Customer may copy the Lumen client library, embed it in apps sold to Customer's own customers, and create adapted versions of it." (contract, chars 100-229)
- `software_access_only` = yes: "Customer subscribes to the Lumen service." (contract, chars 29-70)
- `usage_training_beyond_initial` = no: "As part of the subscription" (contract, chars 71-98)
- `india_presence` = no: "Customer subscribes to the Lumen service." (contract, chars 29-70)
- `mixed_unallocated` = no: "Subscription fee: USD 50,000." (contract, chars 230-259)
- `net_of_tax_clause` = no: "Subscription fee: USD 50,000." (contract, chars 230-259)

## Facts to check
- If `copyright_rights_granted` were no: FIS
- If `india_presence` were yes: ESCALATE:PE_RISK
- If `mixed_unallocated` were yes: ESCALATE:MIXED_UNALLOCATED

## Authorities to read
- India-US treaty Art. 12(2): source-country tax on royalties and included services (secondary): https://beaconfiling.com/dtaa/fts-tax-rate-india-usa
- India-US treaty Art. 12(3): royalties (secondary): https://jurigram.com/blog/corporate-law/india-us-tax-treaty-dtaa-for-businesses-royalty-and-fts-withholding
- Income-tax Act 2025 s.159(8), Rule 75 and Form 41 (official): https://www.incometaxindia.gov.in/documents/d/guest/form-41-faqs

## Audit
- Rule pack: 2026.11-prototype
- Reader: {'reader': 'openrouter', 'requested_model': 'openrouter/free', 'prompt_version': 'v1', 'prompt_sha256': '00afa14f0ea2f7f49f31d69b36a7dbde9157c8fa272c28a89065725aef75fedb', 'served_model': 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free'}
- Contract SHA-256: 3f3399107d90ef9850ebb6e8516bff2806c6afa8a62290c735d08161bad7597a
- Trace SHA-256: f55aa92fa83a466bbf59b8521477bcba6749b734995276f3c672a4536dc55190

## CA decision
Approve / Change / Reject: ________  Reason: ________  CA and UDIN: ________
