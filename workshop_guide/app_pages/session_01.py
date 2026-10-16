import streamlit as st

from components import (fill, render_checkpoint, render_execution_context, render_explanation,
                        render_fallback, render_prompt, render_real_world_examples, render_references,
                        render_session_header, render_snowsight_route, render_technologies_used, render_what_why)
from content import links as L

render_session_header("Session 1", "Meet your operator pipeline", "4 min", "Your mental model of one operator's Nova pipeline")
render_execution_context()
render_what_why(
    "Ask CoCo to explain your operator's pipeline end to end, then ask Nova's semantic view the two questions operators ask most.",
    "You cannot monitor what you cannot see. Gladstone runs one database per operator, so every investigation starts by mapping that operator's Bronze, REPORTING and Gold objects.",
)

render_prompt("Prompt 1.1", "Explain the pipeline", """In {FQ_SCHEMA}, explain the data pipeline end to end:
- which tables are Bronze (MEMBERS__, SHARED__, SYSTEM__ prefixes) and what the _SYNC_META__MERGE_BATCH table records
- what task TSK_BIFROST_MERGE does and how often it runs
- what each REPORTING__ dynamic table computes, its target lag, refresh mode, and which Bronze tables feed it
- what semantic view SV_OPERATOR_KPIS exposes (metrics and verified queries)
Draw the lineage as a simple left-to-right diagram. Do not change anything.""")
render_snowsight_route([
    "**Catalog » Database Explorer** » `GLADSTONE_DQ_LAB` » `{SCHEMA}`.",
    "Open `REPORTING__DAILY_REVENUE` » **Lineage** tab to see its upstream Bronze table.",
    "**Transformation » Dynamic tables**: target lag, refresh mode and refresh history.",
    "**Transformation » Tasks** » `TSK_BIFROST_MERGE` » **Run history**.",
    "**AI & ML » Cortex Analyst** » `SV_OPERATOR_KPIS` to browse metrics and verified queries.",
], sql="""USE SCHEMA {FQ_SCHEMA};
SHOW DYNAMIC TABLES;   -- target_lag, refresh_mode, scheduling_state
SHOW TASKS;
DESCRIBE SEMANTIC VIEW SV_OPERATOR_KPIS;""")

render_prompt("Prompt 1.2", "Ask Nova's two KPIs", """Using semantic view {FQ_SCHEMA}.SV_OPERATOR_KPIS, answer:
1. How many active members do we have?
2. What was our net revenue and class utilisation over the last 7 days?
Show me which metric or verified query you used for each answer. If "active members" can be calculated two ways in this semantic view, show both numbers side by side and explain the difference.""")
render_snowsight_route([
    "**AI & ML » Cortex Analyst** » open `SV_OPERATOR_KPIS` » **Playground** and ask the same questions.",
    "Note which answer uses the verified query `vq_active_members`.",
], sql="""SELECT * FROM SEMANTIC_VIEW({FQ_SCHEMA}.SV_OPERATOR_KPIS
  METRICS am.active_members, ms.paid_members_35d);""")

render_checkpoint("You can name the 4 layers and you have seen **two different numbers for active members** (status-based vs paid in the last 35 days). Note them - they matter in Session 3.")
render_explanation("Why two answers?", """
`am.active_members` counts members whose **source status** is `ACTIVE`. The verified query (`vq_active_members`) uses the
**finance definition** - members who **paid in the last 35 days**. About 6% of ACTIVE members haven't paid in more than
35 days, so the two numbers differ even on clean data.

This is the "discrepancy investigation" problem: when an operator says Nova is wrong, first check **which definition** answered.
A semantic-layer quality check (Session 3) compares the two and alerts when the gap moves.
""")
render_fallback("""USE SCHEMA {FQ_SCHEMA};
SHOW DYNAMIC TABLES;
SHOW TASKS;
SELECT * FROM SEMANTIC_VIEW(SV_OPERATOR_KPIS METRICS am.active_members, ms.paid_members_35d);
SELECT * FROM SEMANTIC_VIEW(SV_OPERATOR_KPIS METRICS rev.net_revenue, util.utilisation_pct, util.no_show_rate);""")

render_technologies_used([
    {"name": "Dynamic Tables", "icon": "sync", "description": "REPORTING layer, incremental refresh, 1-minute target lag"},
    {"name": "Tasks", "icon": "schedule", "description": "TSK_BIFROST_MERGE simulates the Bifrost merge"},
    {"name": "Semantic view", "icon": "schema", "description": "Gold layer Nova answers from, with a verified query"},
])

render_real_world_examples([
    {"title": "Customer Success first response", "body": "Before escalating to engineering, CS asks CoCo to map the operator's pipeline and which definition Nova used."},
    {"title": "Onboarding a data engineer", "body": "A new joiner gets a plain-English map of any `CUST_*` database in minutes, from live metadata rather than out-of-date docs."},
])
render_references({
    "Quickstarts": [L.QS_SV, L.QS_DT],
    "Docs": [L.LINEAGE, L.DT_MONITOR, L.SV_CREATE],
})
