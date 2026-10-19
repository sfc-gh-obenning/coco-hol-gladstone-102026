from pathlib import Path

import streamlit as st

from components import render_real_world_examples, render_references
from content import links as L
from content import story

_STATIC = Path(__file__).parent.parent / "static"

with st.container(horizontal=True, vertical_alignment="center", gap="large"):
    st.image(str(_STATIC / "gladstone_logo.jpg"), width=110)
    st.image(str(_STATIC / "snowflake_full_logo.png"), width=180)

st.title("Trust Nova's answers")
st.markdown("Data quality and monitoring for Gladstone MRM's Dynamic Table, Task, semantic layer and agent pipelines - using only prompts in **CoCo**.")
st.space("small")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Core lab", "30 min", help="Sessions 1-5")
c2.metric("Prompts", "10 core", help="Plus stretch and bonus prompts")
c3.metric("Faults to find", "6", help="One per operator, round-robin")
c4.metric("Bonus labs", "3", help="Budgets, governance + GDPR, DCM DevOps")

st.space("medium")
st.markdown("#### :material/groups: Who's in this story")
story.cast()
st.markdown("#### :material/report: The problem")
with st.chat_message("Sam", avatar=":material/storefront:"):
    st.markdown("**Sam, a leisure operator on Nova:** *\"Nova's active members and last week's revenue don't match "
                "what our front desk sees.\"*")
st.markdown("Nova's answer came from a semantic view, reading REPORTING Dynamic Tables, built from Bronze tables that "
            "Bifrost merges in from the operator's Azure SQL. Today Gladstone finds out from the customer, one operator "
            "at a time, across hundreds of operator databases:")
story.timelines()

st.markdown("#### :material/route: What, how and why")
w, h, y = st.columns(3)
with w.container(border=True, height="stretch"):
    st.markdown("##### :material/flag: What")
    st.markdown("""
Each attendee **is one operator**. In 30 minutes you:
1. monitor your operator's Nova pipeline,
2. receive a real fault,
3. let CoCo find the root cause,
4. contain it before Nova answers again,
5. see every operator's health in one fleet view.
""")
with h.container(border=True, height="stretch"):
    st.markdown("##### :material/terminal: How")
    st.markdown("""
- **Prompts only**, in **CoCo Desktop or CoCo CLI**. CoCo loads its data-quality, dynamic-tables, tasks and lineage skills and shows the SQL before running it.
- Every step also shows **how to do it in Snowsight**.
- Synthetic data in **your own schema** `CUST_<NAME>` - a zero-copy clone of one operator.
""")
with y.container(border=True, height="stretch"):
    st.markdown("##### :material/lightbulb: Why this approach")
    st.markdown("""
- It mirrors **Nova's real layers** (MEMBERS / SHARED / SYSTEM, REPORTING DTs, semantic view, agent) and your one-database-per-operator model.
- Native **data metric functions** are serverless - a replacement path for homegrown `DATA_MONITORING_WH` checks.
- The same prompt pattern repeats for every `CUST_*` database - it scales by template, not by people.
""")

st.markdown("#### :material/account_tree: Your operator pipeline")
st.graphviz_chart("""
digraph {
  rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#F0F4F8", color="#29B5E8", fontname="Helvetica"];
  src [label="Operator Azure SQL\\n(source)"];
  task [label="TSK_BIFROST_MERGE\\n(simulated Bifrost, 1 min)"];
  bronze [label="Bronze\\nMEMBERS__* / SHARED__* / SYSTEM__*"];
  dt [label="Silver REPORTING\\nDynamic Tables"];
  sv [label="Gold\\nSV_OPERATOR_KPIS\\n+ verified query"];
  agent [label="Nova agent\\n(Cortex Agent)"];
  dq [label="Data metric functions\\n+ expectations", fillcolor="#E3F5FC"];
  src -> task -> bronze -> dt -> sv -> agent;
  dq -> bronze [style=dashed, arrowhead=none]; dq -> dt [style=dashed, arrowhead=none];
}
""")

st.markdown("#### :material/checklist: What this lab answers")
st.caption("Themes from Gladstone's Nova discovery and workshop-planning conversations.")
st.markdown("""
| Gladstone need | Covered in |
|---|---|
| Trust the data behind Nova before it reaches operators | Sessions 2-4 |
| Quality of semantic views and verified queries; lineage for discrepancy investigations | Sessions 3, 5 |
| Detailed data quality on the pipeline side, not only in BI | Whole lab |
| Detect cross-tenant data in an operator database | Session 2, Bonus B2 |
| Usage monitoring and overage warnings | Bonus B1 |
| Manage pipelines and checks as code with DCM Projects | Bonus B3 |
| Dynamic Table refresh objectives visible and monitored | Sessions 2-3 |
""")

render_real_world_examples([
    {"title": "Before a Nova answer reaches an operator", "body": "Checks on the REPORTING tables the semantic view reads, so a bad sync stops at Silver instead of reaching the Nova Portal."},
    {"title": "Onboarding a new operator", "body": "The same monitors attach to the new `CUST_*` database on day one, so the first Bifrost sync is already checked."},
    {"title": "Customer Success escalations", "body": "\"Nova gave me the wrong number\" becomes a five-minute CoCo root-cause conversation, with evidence to send back to the operator."},
    {"title": "GCP-to-Azure migration", "body": "The same checks prove the migrated operator data matches before cut-over."},
])
render_references({
    "Quickstarts": [L.QS_DQ, L.QS_COCO_DESKTOP, L.QS_COCO_CLI],
    "Docs": [L.DQ_INTRO, L.DT_OVERVIEW, L.SV_OVERVIEW, L.AGENTS, L.COCO],
})
