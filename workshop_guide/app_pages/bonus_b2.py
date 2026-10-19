import streamlit as st

from components import (render_checkpoint, render_execution_context, render_explanation, render_fallback,
                        render_prompt, render_real_world_examples, render_references, render_session_header,
                        render_snowsight_route, render_sql_file, render_what_why)
from content import links as L

render_session_header("Bonus B2", "Data governance and GDPR", "40 min, self-paced", "Classification, masking, row access, then SAR, erasure and retention")
render_execution_context()
st.warning(
    "All member data in this lab is synthetic. This exercise shows Snowflake mechanisms; it is not legal advice. "
    "Gladstone's DPO decides controller/processor roles, lawful bases and retention periods for each operator.",
    title="Not legal advice",
)

with st.container(border=True):
    st.markdown("##### :material/admin_panel_settings: Admin: run once before B2")
    st.markdown("""
Creates `GOVERNANCE` (GDPR tags and the `GDPR_REQUESTS` register), the `ERASED_MEMBERS_STILL_PRESENT` check, two test roles
(`DQ_LAB_PII_READER`, `DQ_LAB_OPERATOR_VIEWER`) granted to each attendee user, and lab-only account privileges for classification,
tag-based masking and row access policies.
""")
    render_sql_file("bonus/B2_setup.sql", "Show B2_setup.sql")

tab_a, tab_b = st.tabs([":material/policy: Part A - governance", ":material/gavel: Part B - GDPR exercise"])

with tab_a:
    render_what_why(
        "Find the personal data in your operator's member table, mask it everywhere with **one** tag-based policy, and make sure anyone reading the table sees only **this operator's** rows.",
        "Nova and analysts must never see member health notes or contact details they don't need, and one operator's members must never appear in another's answers. Tag-based policies scale to every `CUST_*` database without per-column work.",
    )
    render_prompt("Prompt B2.1", "Classify", """Classify {FQ_SCHEMA}.MEMBERS__MEMBER for personal and sensitive data. List each column with its suggested semantic and privacy category and confidence. Do not apply any tags yet. Which column would be special-category data under UK GDPR?""")
    render_snowsight_route([
        "**Governance & security » Trust Center » Data security » Sensitive data** (or open the table » **…** » **Classify data**).",
        "Review suggestions per column; apply or reject.",
    ], sql="CALL SYSTEM$CLASSIFY('{FQ_SCHEMA}.MEMBERS__MEMBER', NULL);")

    render_prompt("Prompt B2.2", "Tag-based masking", """In {FQ_SCHEMA}, create a tag PII_TYPE with allowed values email, phone, dob, name, postcode, health. Create a string masking policy that shows the real value only when role DQ_LAB_PII_READER is in the session (keep the email domain visible), and a date masking policy that keeps only the birth year. Attach both policies to the PII_TYPE tag, then tag the email, phone, date_of_birth, first_name, last_name, postcode and health_notes columns of MEMBERS__MEMBER.""")
    render_snowsight_route([
        "**Governance & security » Tags & policies » Policies » + Policy** » Masking policy (string) and (date).",
        "**Tags » + Tag** `PII_TYPE` » **Policies** » attach both masking policies.",
        "Open `MEMBERS__MEMBER` » **Columns** » set `PII_TYPE` on each personal column.",
    ])

    render_prompt("Prompt B2.3", "Row access per operator", """Create a row access policy RAP_OWN_OPERATOR in {FQ_SCHEMA} that only returns rows where operator_id = '{SCHEMA}' (lab admins excepted) and add it to MEMBERS__MEMBER on operator_id. Grant SELECT on MEMBERS__MEMBER to roles DQ_LAB_PII_READER and DQ_LAB_OPERATOR_VIEWER.
Then prove it: query a few member rows with health notes as my role, as DQ_LAB_PII_READER and as DQ_LAB_OPERATOR_VIEWER, and count rows where operator_id is not {SCHEMA}. Explain what each role saw.""")
    render_snowsight_route([
        "**Governance & security » Tags & policies » Policies » + Policy** » Row access policy.",
        "Open `MEMBERS__MEMBER` » **Policies** » add row access policy on `operator_id`.",
        "Switch role in the worksheet's role picker to compare results.",
    ])
    render_checkpoint("Your role sees `*** MASKED ***`; `DQ_LAB_PII_READER` sees real values; nobody sees rows from another operator (this also hides a **tenant leak**).")

    render_prompt("Prompt B2.4", "Does Nova expose personal data? Who read it?", """Check whether semantic view {FQ_SCHEMA}.SV_OPERATOR_KPIS exposes any personal-data columns from MEMBERS__MEMBER. Then show who queried MEMBERS__MEMBER in the last day from SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY (note its latency).""")
    render_snowsight_route([
        "Open `SV_OPERATOR_KPIS` » **Definition**.",
        "**Monitoring » Query history** filtered by object, or query `ACCESS_HISTORY`.",
    ])
    render_explanation("Why tag-based masking at Gladstone scale", """
A masking policy attached to a **tag** protects every column that carries the tag - in every operator database. Classification
(or a classification profile with a tag map) applies the tag; the policy follows automatically. One policy, hundreds of `CUST_*` databases.

**Lab note:** attendees have `APPLY MASKING POLICY` and `APPLY ROW ACCESS POLICY` on the account so each can build their own.
In production give these to a central governance role only.
""")

with tab_b:
    render_what_why(
        "Run the three GDPR workflows Gladstone faces as a processor for leisure operators: record **why** you hold each field, answer a **subject access request**, and carry out an **erasure** you can prove.",
        "Members ask operators for their data and for deletion. With one database per operator, Gladstone needs a repeatable, auditable way to do this in Snowflake - including the copies (Time Travel, clones) that survive a DELETE.",
    )
    st.markdown("##### :material/rule: Things to consider first")
    st.markdown("""
| Topic | Question for Gladstone and each operator |
|---|---|
| Roles | Is Gladstone the processor and the operator the controller for member data? Who receives SARs? |
| Lawful basis | Contract (membership), legal obligation (payments), consent (marketing), explicit consent (health notes)? |
| Special category | PAR-Q / health notes need an Article 9 condition. Should they reach Snowflake or Nova at all? |
| Retention | How long after a membership ends? Payments usually longer (tax). |
| Copies | Time Travel, Fail-safe, clones, dev/test copies, Nova caches, exported files. |
| Residency | UK South storage; Cortex cross-region inference setting (`CORTEX_ENABLED_CROSS_REGION`). |
| Timelines | SAR within one month; breach notification to the ICO within 72 hours where required. |
""")
    st.markdown("##### :material/alt_route: Approaches to erasure")
    st.markdown("""
| Approach | When | Trade-off |
|---|---|---|
| Hard delete | Bookings, attendance, marketing data | Simple; breaks history and aggregates |
| Pseudonymise | Payments you must keep for tax | Keeps finance intact; still personal data if the key/salt can re-identify |
| Crypto-shredding | Per-member keys outside Snowflake | Strong, but complex to run at scale |
| Retention policy | Scheduled expiry of old members | Automates storage limitation; needs agreed periods |
""")

    render_prompt("Prompt B2.5", "Record GDPR categories, lawful basis and retention", """Using tags in GLADSTONE_DQ_LAB.GOVERNANCE (GDPR_CATEGORY, LAWFUL_BASIS, RETENTION_DAYS), tag the columns of {FQ_SCHEMA}.MEMBERS__MEMBER and SYSTEM__PAYMENT: identifiers and contact details under contract (730 days), health_notes as special_category under explicit_consent (30 days), marketing_consent under consent, payment amount as financial under legal_obligation (2190 days). Then list every tagged column as a simple record of processing.""")
    render_snowsight_route([
        "Open each table » **Columns** » **Edit tags** » `GOVERNANCE.GDPR_CATEGORY`, `LAWFUL_BASIS`, `RETENTION_DAYS`.",
    ])

    render_prompt("Prompt B2.6", "Subject access request", """Create a stored procedure {FQ_SCHEMA}.SAR_EXPORT(member_id) with caller's rights that finds every table in {SCHEMA} with a MEMBER_ID column, collects that member's rows into one JSON document grouped by table, and logs the request in GLADSTONE_DQ_LAB.GOVERNANCE.GDPR_REQUESTS (request_type 'SAR', completed now). Run it for member M-01043 with role DQ_LAB_PII_READER as a secondary role so masking lets the real data through, then turn secondary roles off again.""")
    render_snowsight_route([
        "Create the procedure in a worksheet, then run `USE SECONDARY ROLES DQ_LAB_PII_READER; CALL SAR_EXPORT('M-01043');`.",
    ])
    render_explanation("Why caller's rights and a secondary role?", """
An owner's-rights procedure runs as your operator role, so the masking policy masks the export - a useless SAR. With
**caller's rights** and `DQ_LAB_PII_READER` active as a **secondary role**, `IS_ROLE_IN_SESSION` lets real values through,
and only people with the privacy role can produce an unmasked SAR.
""")

    render_prompt("Prompt B2.7", "Erasure you can prove", """Log an ERASURE request for member M-01042 in GLADSTONE_DQ_LAB.GOVERNANCE.GDPR_REQUESTS. Create a procedure {FQ_SCHEMA}.ERASE_MEMBER(member_id) that: replaces member_id with a salted SHA2 token and nulls contact, date of birth, postcode and health notes in MEMBERS__MEMBER; pseudonymises member_id in MEMBERS__MEMBERSHIP and SYSTEM__PAYMENT (keep payments for tax); deletes the member's SYSTEM__BOOKING and SYSTEM__ATTENDANCE rows; and marks the request completed with row counts as evidence. Run it for M-01042.""")

    render_prompt("Prompt B2.8", "A data quality check that proves it", """Attach GLADSTONE_DQ_LAB.DQ_COMMON.ERASED_MEMBERS_STILL_PRESENT to MEMBERS__MEMBER and SYSTEM__PAYMENT in {FQ_SCHEMA}, using GLADSTONE_DQ_LAB.GOVERNANCE.GDPR_REQUESTS(member_id, request_type, completed_at) as the second table, with expectation erasure_complete (value = 0). Evaluate it now.""")
    render_checkpoint("`erasure_complete` passes (0) on both tables. Try it: comment out the payment update in ERASE_MEMBER, erase another member, and watch the check fail.")

    render_prompt("Prompt B2.9", "Copies that survive", """Is member M-01042 still recoverable anywhere? Check Time Travel on {FQ_SCHEMA}.MEMBERS__MEMBER (query the table as it was 2 minutes ago), show the table's retention period, explain Fail-safe, and explain the risk from the template schema this operator was cloned from. Set MEMBERS__MEMBER retention to 1 day. Finally, show the account's CORTEX_ENABLED_CROSS_REGION setting and what it means for UK data residency with Nova.""")
    render_explanation("What the lab shows", """
- **Time Travel** still returns the pre-erasure row until retention passes; **Fail-safe** keeps it 7 more days (permanent tables), recoverable only by Snowflake.
- The **template** (`ADMIN_OPERATOR_TEMPLATE`) still holds M-01042 - just like dev/test clones of a production operator. Erasure has to cover clones.
- Shorter retention on personal-data tables reduces this window; transient tables have no Fail-safe.
- `CORTEX_ENABLED_CROSS_REGION` controls whether Cortex can process prompts outside the account's region. For UK-only processing, the admin restricts it.
""")
    render_fallback("""-- See sql/bonus/B2_answer_key.sql for the full Part A + Part B answer key.
USE SECONDARY ROLES DQ_LAB_PII_READER;
CALL {FQ_SCHEMA}.SAR_EXPORT('M-01043');
USE SECONDARY ROLES NONE;
CALL {FQ_SCHEMA}.ERASE_MEMBER('M-01042');
SELECT COUNT(*) FROM {FQ_SCHEMA}.MEMBERS__MEMBER AT(OFFSET => -120) WHERE member_id = 'M-01042';""")
    with st.expander(":material/description: Full B2 answer key"):
        st.caption("Replace CUST_OPERATOR01 / DQ_LAB_OPERATOR01 with your operator.")
        from components import sql_file
        st.code(sql_file("bonus/B2_answer_key.sql"), language="sql", line_numbers=True)

with st.container(border=True):
    st.markdown("##### :material/delete_sweep: Admin: B2 teardown")
    st.markdown("Detaches every policy from `CUST_*` tables, drops the erasure checks and `GOVERNANCE`, resets retention, revokes the lab-only account privileges and drops the two test roles.")
    render_sql_file("bonus/B2_teardown.sql", "Show B2_teardown.sql")

render_real_world_examples([
    {"title": "Health notes never reach Nova", "body": "Tagged as `health`, masked for every role except a privacy role, and absent from the semantic view."},
    {"title": "SARs for any operator", "body": "One SAR procedure pattern, deployed to every `CUST_*` database, answers within the one-month deadline with an audit trail."},
    {"title": "Erasure with evidence", "body": "The erasure check turns \"we deleted it\" into a scheduled, provable result per operator."},
    {"title": "Tenant leak = data incident", "body": "Row access by operator hides leaked rows immediately, while the DQ check and access history give the evidence for a breach assessment."},
])
render_references({
    "Quickstarts": [L.QS_HORIZON, L.QS_GOV_ADV, L.WAF_SEC],
    "Docs": [L.CLASSIFY, L.CLASSIFY_SP, L.TAG_MASK, L.RAP, L.ACCESS_HIST, L.TIME_TRAVEL, L.FAILSAFE, L.CROSS_REGION, L.AI_REDACT, L.TRUST_CENTER],
    "UK GDPR guidance": [L.ICO_SAR, L.ICO_ERASURE, L.ICO_STORAGE, L.ICO_SPECIAL, L.ICO_BREACH],
})
