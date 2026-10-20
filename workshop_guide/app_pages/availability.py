import streamlit as st

from components import render_real_world_examples, render_references
from content import links as L

st.title("Azure UK South availability")
st.markdown("Gladstone's account `GLADSTONESOFTWARE` is on **Azure UK South**. Feature availability can differ by cloud and region.")
st.warning(
    "Statuses below come from recent Gladstone conversations and the lab dry run, not from a published roadmap. "
    "Timelines can move. The admin should confirm each lab feature in the target account with the pre-flight checks in `00_admin_setup.sql`, "
    "and check the Snowflake release notes for each item before relying on it.",
    title="Verify before the session",
)

st.markdown("#### :material/checklist: Features this lab uses")
st.markdown("""
| Feature | Used in | How to confirm in your account |
|---|---|---|
| Data metric functions, expectations, custom DMFs | Sessions 2-5 | `SHOW DATA METRIC FUNCTIONS IN SCHEMA SNOWFLAKE.CORE;` |
| `NEGATIVE_COUNT`, `REFERENTIAL_INTEGRITY_COUNT` | Session 2 | Same list - check both names appear |
| Anomaly detection (ROW_COUNT / FRESHNESS) | Session 2 | Attach with `ANOMALY_DETECTION = TRUE` |
| DQ notifications | Session 4 | `ALTER DATABASE ... SET DATA_QUALITY_MONITORING_SETTINGS` succeeds |
| Data quality dashboard | Sessions 3, 5 | Snowsight » Governance & security » Data quality |
| Dynamic Tables, Tasks | All | Created by `SETUP_ATTENDEE` |
| Semantic views + verified queries | Sessions 1, 3 | Created by `SETUP_ATTENDEE` |
| Cortex Agents | Day 2 | `CREATE AGENT` in an attendee schema, with a stored-procedure custom tool |
| AISQL (AI_SENTIMENT, AI_CLASSIFY, AI_FILTER) | Day 2 | Native in region, or cross-region routing allowed |
| Snowpark Python procedures + Model Registry | Day 2 | Anaconda terms acknowledged; scikit-learn and snowflake-ml-python available |
| CoCo Desktop / CLI | All | Sign-in to the account |
| Budgets, resource monitors | Bonus B1 | B1 setup runs without error |
| Classification, tag-based masking, row access | Bonus B2 | B2 setup + `SYSTEM$CLASSIFY` |
| DCM Projects + `snow dcm` | Bonus B3 | `snow dcm create` in a `CUST_*_DCM` schema |
""")

st.markdown("#### :material/forum: What came up in Gladstone conversations")
st.caption("As discussed with the account team. Not a commitment - confirm current status before planning on it.")
st.markdown("""
| Item | Status as discussed | Relevance |
|---|---|---|
| DCM Projects | Discussed as generally available | Bonus B3 |
| OpenLineage-based external lineage | Discussed as GA (early September) | End-to-end lineage beyond Snowflake |
| Horizon Context / Cortex Sense | Discussed for September; preview stage not confirmed | Catalog context for agents |
| Select Star capabilities | Expected on Azure later than AWS | Catalog / lineage |
| Kafka streaming ingestion | Public preview discussed for September | Alternative to the Bifrost path |
| Openflow | Requires Private Link in Gladstone's setup | Ingestion |
| Agent code execution, model routing | Discussed as upcoming | Nova agent |
| AI Guard | Not enabled on the account | Agent safety |
""")

st.markdown("#### :material/shield: Residency note for Nova")
st.markdown("""
`CORTEX_ENABLED_CROSS_REGION` decides whether Cortex may process requests outside UK South when a model isn't available locally.
Check it with `SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;` (Bonus B2, Prompt B2.9) and agree the setting with Gladstone's DPO.
""")

render_real_world_examples([
    {"title": "Pre-flight before the workshop", "body": "The admin runs the checks above in `GLADSTONESOFTWARE` the day before and records any gaps on this page."},
    {"title": "Planning Nova features", "body": "Treat preview or upcoming items as roadmap conversations, and design Nova so the core path uses GA features."},
])
render_references({
    "Docs": [L.DQ_INTRO, L.DQ_ANOMALY, L.DCM, L.CROSS_REGION, L.AGENTS],
})
