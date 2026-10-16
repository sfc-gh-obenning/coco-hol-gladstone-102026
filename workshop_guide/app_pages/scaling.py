import streamlit as st

from components import render_real_world_examples, render_references
from content import links as L

st.title("Scaling to every operator")
st.markdown("Gladstone runs **one Snowflake database per operator**. This lab simulated that with one schema per attendee. Here is how the same pattern scales to hundreds of `CUST_*` databases.")

st.markdown("#### :material/architecture: Recommended pattern")
st.graphviz_chart("""
digraph {
  rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#F0F4F8", color="#29B5E8", fontname="Helvetica"];
  common [label="DQ_COMMON (platform DB)\\ncustom DMFs, owned by Platform"];
  dcm [label="DCM project\\n1 target per operator / tier"];
  ops [label="CUST_001 ... CUST_N\\nBronze, REPORTING, Gold\\n+ attached DMFs"];
  local [label="SNOWFLAKE.LOCAL\\nDQ results (account-wide)"];
  fleet [label="Fleet view\\n+ DQ dashboard + digest"];
  common -> ops [label="attach"]; dcm -> ops [label="deploy"]; ops -> local -> fleet;
}
""", alt="Diagram: central DQ_COMMON functions and a DCM project attach checks to every operator database; results flow to SNOWFLAKE.LOCAL and a fleet view")

st.markdown("#### :material/format_list_numbered: Ten practices")
st.markdown("""
1. **Define once, attach everywhere.** Custom DMFs live in one platform database (`DQ_COMMON`); every operator database references them. Fix a check once.
2. **Attach by code, not by hand.** Put the checks in the operator pipeline's DCM project (Bonus B3) - a new operator gets every check on its first deploy.
3. **Schema-level baseline.** `ALTER SCHEMA ... ADD DATA METRIC FUNCTION ROW_COUNT / FRESHNESS ON () ANOMALY_DETECTION = TRUE` covers every table in an operator schema, including new ones. Add table-level expectations for the invariants.
4. **Schedule to match the data.** `TRIGGER_ON_CHANGES` on Bronze tables Bifrost writes to; align REPORTING checks to the Dynamic Table target lag. Avoid `5 MINUTE` everywhere - it's for the lab.
5. **One results store.** `SNOWFLAKE.LOCAL` results are account-wide - one fleet view covers every operator in the account; filter on `table_database LIKE 'CUST_%'`. Snowflake's DQ dashboard shows the same incidents in Snowsight.
6. **Tiered alerting.** Notifications are per database: enable once per operator database (scripted), then keep only critical checks notifying. Route by tier (enterprise operators to on-call, others to a daily digest).
7. **Contain, don't just detect.** A circuit breaker per operator (Session 4) pauses REPORTING during a bad sync. Run Bronze checks `TRIGGER_ON_CHANGES` and refresh REPORTING only when they pass, so a bad batch never publishes.
8. **Watch the semantic layer.** Compare each headline metric with its verified query on a schedule; alert when the gap moves (Session 3).
9. **Cost is predictable.** DMFs are serverless; track them per operator with `DATA_QUALITY_MONITORING_USAGE_HISTORY` (filter by database) and a tag-based budget (Bonus B1).
10. **Governance by tag.** Classification + tag-based masking + row access by operator work identically in every operator database (Bonus B2).
""")

st.markdown("#### :material/compare_arrows: One database per operator vs a shared schema")
st.markdown("""
| | One DB per operator (Gladstone today) | Shared multi-tenant schema |
|---|---|---|
| Isolation | Strong; simple RBAC | Needs row access policies |
| DQ checks | Same checks attached N times (by DCM) | Attach once; group by operator (`WITHIN GROUP`) |
| Fleet view | `SNOWFLAKE.LOCAL` results across databases | One table's results, grouped |
| Erasure / SAR | Per database | One place, filtered by operator |

Keep one database per operator. Use **group-by DMFs** for shared, cross-operator tables (e.g. a platform-wide events table).
""")

render_real_world_examples([
    {"title": "500 operator databases, one change", "body": "A new expectation added to the DCM project reaches every operator on the next deploy."},
    {"title": "Reporting account", "body": "Results and the fleet view can also be shared to `GLADSTONEREPORTING` for CS and leadership dashboards."},
    {"title": "Migration waves", "body": "Each GCP-to-Azure migration wave runs the same reconciliation checks per operator before cut-over."},
])
render_references({
    "Quickstarts": [L.QS_DQ, L.QS_DCM_PIPE, L.WAF_SEC],
    "Docs": [L.DQ_SCHEMA, L.DQ_GROUP, L.DQ_DASH, L.DQ_USAGE, L.DCM],
})
