# Evaluation: gold

Synthetic cases. Labels are the author's and have not been validated by a CA.

Correct: **16/16** | Unsafe wrong answers: **0** | Over-escalated: **0** | Escalated for the wrong reason: **0**

| Case | Scenario | Expected | Got | Category | TDS | Codes | Result | Fact errors |
|---|---|---|---|---|---|---|---|---|
| C01 | Plain SaaS subscription | READY | READY | BUSINESS_PROFITS_NO_PE | 0 | - | correct | - |
| C02 | Off-the-shelf end-user licence | READY | READY | BUSINESS_PROFITS_NO_PE | 0 | - | correct | - |
| C03 | Source licence with redistribution rights | READY | READY | ROYALTY | 1320000 | - | correct | - |
| C04 | Training that transfers capability | READY | READY | FIS | 528000 | - | correct | - |
| C05 | Called SaaS, but grants reproduction rights | READY | READY | ROYALTY | 660000 | - | correct | - |
| C06 | Called consulting, but no capability passes | READY | READY | BUSINESS_PROFITS_NO_PE | 0 | - | correct | - |
| C07 | One price for platform and enablement | ESCALATE | ESCALATE | - | - | MIXED_UNALLOCATED | correct | - |
| C08 | Vague knowledge sharing | ESCALATE | ESCALATE | - | - | MISSING_MAKE_AVAILABLE_FACT | correct | - |
| C09 | Royalty without a TRC | READY | READY | ROYALTY | 366080 | - | correct | - |
| C10 | Invoice contradicts contract | ESCALATE | ESCALATE | BUSINESS_PROFITS_NO_PE | - | AMOUNT_CONFLICT | correct | - |
| C11 | Credited before the new Act, paid after | ESCALATE | ESCALATE | BUSINESS_PROFITS_NO_PE | - | REGIME_TRANSITION | correct | - |
| C12 | Remitted under the old Act | READY | READY | FIS | 330000 | - | correct | - |
| C13 | Contract instructs the reviewer | READY | READY | ROYALTY | 462000 | - | correct | - |
| C14 | Staff based in India | ESCALATE | ESCALATE | - | - | PE_RISK | correct | - |
| C15 | Net-of-tax clause | READY | READY | FIS | 528000 | - | correct | - |
| C16 | Below the cumulative certificate threshold | READY | READY | ROYALTY | 66000 | - | correct | - |
