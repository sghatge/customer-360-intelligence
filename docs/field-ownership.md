# Field ownership and identity stewardship

| Data element | Proposed authoritative source | AEP representation | Rule |
|---|---|---|---|
| Salesforce Contact ID | Salesforce | CRM identity namespace | Preserve as stable CRM key |
| ECID | Adobe Experience Cloud/web SDK | ECID identity namespace | Do not overwrite with email |
| Email address | Approved CRM/customer preference source | Email identity namespace + profile attribute | Normalize carefully; not sole identity |
| First/last name | Salesforce or governed master data | Profile attribute | Define precedence and freshness |
| Email/SMS consent | Enterprise consent system; Salesforce in the reference design | Consent fields/events | Deny by default when required consent is unknown |
| Cart and product interactions | Web/app commerce event source | Experience events | Event time and schema version required |
| Loyalty tier / LTV | Enterprise loyalty/finance source | Profile attributes | Define refresh cadence and effective date |

## Identity design checklist
- Identify namespace type and uniqueness for every identifier.
- Document deterministic vs probabilistic linking policy.
- Test shared email, changed email, anonymous-to-known transition and duplicate CRM IDs.
- Define merge policy and attribute precedence.
- Establish retention and deletion handling.

This is a proposed lab contract, not a claim that every enterprise should use the same source-of-truth mapping.