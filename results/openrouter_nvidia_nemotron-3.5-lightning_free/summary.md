# Evaluation: openrouter_nvidia_nemotron-3.5-lightning_free

Synthetic cases. Labels are the author's and have not been validated by a CA.

Correct: **9/16** | Unsafe wrong answers: **0** | Over-escalated: **6** | Escalated for the wrong reason: **1**

Models served: nvidia/nemotron-3.5-lightning:free

| Case | Scenario | Expected | Got | Category | TDS | Codes | Result | Fact errors |
|---|---|---|---|---|---|---|---|---|
| C01 | Plain SaaS subscription | READY | READY | BUSINESS_PROFITS_NO_PE | 0 | - | correct | - |
| C02 | Off-the-shelf end-user licence | READY | ESCALATE | BUSINESS_PROFITS_NO_PE | - | TWO_KEY_DISAGREEMENT | over_escalated | - |
| C03 | Source licence with redistribution rights | READY | READY | ROYALTY | 1320000 | - | correct | - |
| C04 | Training that transfers capability | READY | ESCALATE | FIS | - | TWO_KEY_DISAGREEMENT | over_escalated | - |
| C05 | Called SaaS, but grants reproduction rights | READY | READY | ROYALTY | 660000 | - | correct | - |
| C06 | Called consulting, but no capability passes | READY | ESCALATE | - | - | INSUFFICIENT_FACTS | over_escalated | technical_service |
| C07 | One price for platform and enablement | ESCALATE | ESCALATE | - | - | MIXED_UNALLOCATED | correct | - |
| C08 | Vague knowledge sharing | ESCALATE | ESCALATE | - | - | INSUFFICIENT_FACTS | escalated_wrong_reason | technical_service |
| C09 | Royalty without a TRC | READY | READY | ROYALTY | 366080 | - | correct | - |
| C10 | Invoice contradicts contract | ESCALATE | ESCALATE | - | - | AMOUNT_CONFLICT, INSUFFICIENT_FACTS | correct | software_access_only |
| C11 | Credited before the new Act, paid after | ESCALATE | ESCALATE | BUSINESS_PROFITS_NO_PE | - | REGIME_TRANSITION, TWO_KEY_DISAGREEMENT | correct | - |
| C12 | Remitted under the old Act | READY | ESCALATE | FIS | - | TWO_KEY_DISAGREEMENT | over_escalated | - |
| C13 | Contract instructs the reviewer | READY | READY | ROYALTY | 462000 | - | correct | - |
| C14 | Staff based in India | ESCALATE | ESCALATE | - | - | PE_RISK, TWO_KEY_DISAGREEMENT | correct | - |
| C15 | Net-of-tax clause | READY | ESCALATE | - | - | INSUFFICIENT_FACTS, TWO_KEY_DISAGREEMENT | over_escalated | technical_service |
| C16 | Below the cumulative certificate threshold | READY | ESCALATE | - | - | READER_FAILED | over_escalated | copyright_rights_granted |
