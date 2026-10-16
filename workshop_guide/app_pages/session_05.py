import streamlit as st

from components import (render_checkpoint, render_execution_context, render_explanation, render_fallback,
                        render_prompt, render_real_world_examples, render_references, render_session_header,
                        render_snowsight_route, render_technologies_used, render_what_why)
from content import links as L

render_session_header("Session 5", "Fleet view across operators", "4 min", "One view of every operator's data quality")
render_execution_context()
render_what_why(
    "Look across every operator in the room at once: which are failing, which check, since when.",
    "Gladstone has hundreds of operator databases. Nobody can open each one. The same results that power your operator's checks roll up into one fleet view - the start of a Gladstone-wide data quality SLA.",
)

render_prompt("Prompt 5.1", "Which operators are broken?", """Query GLADSTONE_DQ_LAB.ADMIN.V_FLEET_DQ_HEALTH. Which operators have failing data quality checks right now, and which checks? Group operators by the type of failure and suggest the most likely root cause for each group. Show me where my operator {SCHEMA} sits.""")
render_snowsight_route([
    "**Governance & security » Data quality**: **Monitored schemas** lists every `CUST_*` schema with failing expectations and coverage.",
    "Select several incidents » **Investigate** opens one CoCo thread with all of them.",
], sql="SELECT * FROM GLADSTONE_DQ_LAB.ADMIN.V_FLEET_DQ_HEALTH;")

render_prompt("Prompt 5.2", "Design the production rollout", """We run one Snowflake database per operator (CUST_*), hundreds of them. Based on what I built in {FQ_SCHEMA}, outline how to roll these data quality checks out to every operator database:
- where the custom DMFs should live and who owns them
- how to attach the same checks to a new operator automatically
- how to aggregate results into one fleet view
- what it costs (DMFs are serverless) and how to keep that cost predictable
Keep it to one page.""")

render_checkpoint("You can see **six different failure signatures** across the room (if six or more operators). Your operator should now show 0 failing checks.")
render_explanation("How the fleet view works", """
`V_FLEET_DQ_HEALTH` reads `SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS`, keeps the latest result per
operator, table and expectation, and counts the failures. It's owned by the lab admin, so you can read the summary but not
other operators' data.

In production the same query, filtered to `table_database LIKE 'CUST_%'`, is the fleet view - one place for Platform and CS
to see every operator. See **Reference » Scaling to every operator**.
""")
render_fallback("SELECT operator, checks, failing_checks, failing, last_measured FROM GLADSTONE_DQ_LAB.ADMIN.V_FLEET_DQ_HEALTH;")

render_technologies_used([
    {"name": "Data quality dashboard", "icon": "dashboard", "description": "Account-wide incidents, monitored schemas, Investigate with CoCo"},
    {"name": "Results views", "icon": "table_view", "description": "One results store across every database in the account"},
    {"name": "Secure summary view", "icon": "visibility", "description": "Owner's-rights view: see the summary, not the data"},
])

render_real_world_examples([
    {"title": "Daily fleet triage", "body": "Platform reviews failing operators each morning; repeat offenders get a Bifrost or source-system ticket."},
    {"title": "Operator health in account reviews", "body": "Data quality pass rate per operator becomes a KPI in operator QBRs."},
    {"title": "Release safety", "body": "After a Bifrost or REPORTING release, the fleet view shows within one schedule whether any operator regressed."},
])
render_references({
    "Quickstarts": [L.QS_DQ, L.QS_DQM],
    "Docs": [L.DQ_DASH, L.DQ_SCHEMA, L.DQ_GROUP],
})
