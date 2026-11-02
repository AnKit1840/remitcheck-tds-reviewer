# Evaluation: baseline

Synthetic cases. Labels are the author's and have not been validated by a CA.

Correct: **9/16** | Unsafe wrong answers: **1** | Over-escalated: **4** | Escalated for the wrong reason: **2**

| Case | Scenario | Expected | Got | Category | TDS | Codes | Result | Fact errors |
|---|---|---|---|---|---|---|---|---|
| C01 | Plain SaaS subscription | READY | READY | BUSINESS_PROFITS_NO_PE | 0 | - | correct | copyright_rights_granted |
| C02 | Off-the-shelf end-user licence | READY | ESCALATE | - | - | INSUFFICIENT_FACTS | over_escalated | software_access_only, copyright_rights_granted |
| C03 | Source licence with redistribution rights | READY | READY | ROYALTY | 1320000 | - | correct | - |
| C04 | Training that transfers capability | READY | ESCALATE | - | - | INSUFFICIENT_FACTS | over_escalated | technical_service, knowhow_transfer |
| C05 | Called SaaS, but grants reproduction rights | READY | READY | BUSINESS_PROFITS_NO_PE | 0 | - | UNSAFE_WRONG_ANSWER | copyright_rights_granted |
| C06 | Called consulting, but no capability passes | READY | ESCALATE | - | - | MISSING_MAKE_AVAILABLE_FACT | over_escalated | knowhow_transfer |
| C07 | One price for platform and enablement | ESCALATE | ESCALATE | - | - | INSUFFICIENT_FACTS | escalated_wrong_reason | mixed_unallocated |
| C08 | Vague knowledge sharing | ESCALATE | ESCALATE | - | - | MISSING_MAKE_AVAILABLE_FACT | correct | - |
| C09 | Royalty without a TRC | READY | READY | ROYALTY | 366080 | - | correct | - |
| C10 | Invoice contradicts contract | ESCALATE | ESCALATE | - | - | AMOUNT_CONFLICT, INSUFFICIENT_FACTS | correct | software_access_only, copyright_rights_granted |
| C11 | Credited before the new Act, paid after | ESCALATE | ESCALATE | - | - | REGIME_TRANSITION, INSUFFICIENT_FACTS | correct | software_access_only, copyright_rights_granted |
| C12 | Remitted under the old Act | READY | READY | FIS | 330000 | - | correct | - |
| C13 | Contract instructs the reviewer | READY | READY | ROYALTY | 462000 | - | correct | - |
| C14 | Staff based in India | ESCALATE | ESCALATE | - | - | INSUFFICIENT_FACTS | escalated_wrong_reason | india_presence |
| C15 | Net-of-tax clause | READY | ESCALATE | - | - | INSUFFICIENT_FACTS | over_escalated | technical_service, knowhow_transfer, net_of_tax_clause |
| C16 | Below the cumulative certificate threshold | READY | READY | ROYALTY | 66000 | - | correct | - |
