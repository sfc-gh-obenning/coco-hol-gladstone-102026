import streamlit as st

from components import render_real_world_examples, render_references
from content import links as L

st.title("Agenda")
st.markdown("30 minutes, one operator each. The facilitator injects the faults between Session 2 and Session 3.")

st.markdown("""
| Time | Section | You do (in CoCo) | Snowflake capability |
|---|---|---|---|
| 0-4 | **1. Meet your operator pipeline** | Explain the pipeline; ask Nova's two KPIs | Lineage, Dynamic Tables, Tasks, semantic view |
| 4-11 | **2. Put monitors on it** | Freshness, volume, duplicates, tenant check, expectations | Data metric functions, expectations, custom DMFs |
| 11 | *Facilitator injects one fault into every operator* | - | - |
| 11-20 | **3. Diagnose a broken answer** | "Nova's numbers look wrong - find out why" | DQ results, failing rows, task & DT history, verified queries |
| 20-26 | **4. Contain and alert** | Circuit breaker task; notification on the critical check | Tasks, `SYSTEM$SET_RETURN_VALUE`, DQ notifications |
| 26-30 | **5. Fleet view across operators** | Which operators are broken right now? | Results across schemas, data quality dashboard |
""")

with st.container(border=True):
    st.markdown("""
**Faster than the room?** Go to **Stretch**: put a Cortex Agent on top of your semantic view and test it, schedule a CoCo-generated DQ report, or check a migrated operator.

**After the session:** three bonus labs, each with its own setup and teardown - **B1** budgets and resource monitors, **B2** governance plus GDPR, **B3** DevOps with DCM Projects.
""")

st.markdown("#### :material/bug_report: The six faults")
st.caption("Each operator gets one, in setup order. The facilitator can see who got what.")
st.markdown("""
| Fault | What happened (in Nova terms) | Symptom in Nova |
|---|---|---|
| Bifrost replay | The same merge batch was applied twice | Active members inflated |
| Merge task stalled | The sync task stopped | Stale revenue, no new bookings |
| Refund sign flip | Refunds arrived as negative payments | Today's revenue collapses |
| Orphan attendance | Check-ins arrived without their bookings | Utilisation over 100% for some classes |
| Tenant leak | Another operator's members routed in | Wrong member count; a GDPR incident |
| Status drift | Cancelled members re-sent as ACTIVE | Two answers to "how many active members?" |
""")

render_real_world_examples([
    {"title": "A real triage rota", "body": "These six are the failure modes of any CDC pipeline: duplicate, late, wrong sign, missing parent, wrong tenant, semantic drift. Each one maps to one check."},
    {"title": "Operator-facing SLAs", "body": "Freshness and completeness expectations become the evidence behind \"Nova data is never more than N minutes old\"."},
])
render_references({
    "Quickstarts": [L.QS_DQ, L.QS_DT],
    "Docs": [L.DQ_EXPECT, L.TASKS],
})
