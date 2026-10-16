import streamlit as st

from components import (render_execution_context, render_explanation, render_fallback, render_prompt,
                        render_real_world_examples, render_references, render_snowsight_route, render_what_why)
from content import links as L

st.title("Stretch: agents, automation, migration")
st.markdown(":material/schedule: **Self-paced** - for anyone ahead of the room, or after the session.")
render_execution_context()

st.markdown("### S1. Put a Nova agent on your semantic view and test its answers")
render_what_why(
    "Create a Cortex Agent over `SV_OPERATOR_KPIS` (a mini Nova), ask it the operator's questions, and check the answer against the data quality results.",
    "Nova's trust problem is at the agent layer: the agent picks a metric or a verified query. Testing agent answers against known-good numbers is the AI-side half of data quality.",
)
render_prompt("Prompt S.1", "Create and question the agent", """Create a Cortex Agent {FQ_SCHEMA}.NOVA_OPERATOR_AGENT that uses semantic view {FQ_SCHEMA}.SV_OPERATOR_KPIS as a Cortex Analyst tool on warehouse DQ_LAB_WH. Instruct it to always say which metric or verified query it used.
Then ask it: "How many active members do we have?" and "What was net revenue yesterday?"
Compare its answers with the active_members metric and the verified query, and with my current data quality results. Would you trust each answer? Why?""")
render_snowsight_route([
    "**AI & ML » Agents** » **Create agent** in `{SCHEMA}`; add a **Cortex Analyst** tool on `SV_OPERATOR_KPIS`, warehouse `DQ_LAB_WH`.",
    "Use the agent's **Playground** to ask the questions; open the thinking trace to see the verified query being used.",
])
render_explanation("What to look for", """
The agent answers *"How many active members?"* from the **verified query** (paid in the last 35 days) - so it disagrees with the
status-based dashboard number. Neither is a bug: they're two definitions. Fix it in the semantic view (rename the metric, document the definition,
or align the verified query), then re-test. For ongoing quality, use **Cortex Agent evaluations** and **AI Observability**.
""")
render_fallback("""CREATE OR REPLACE AGENT {FQ_SCHEMA}.NOVA_OPERATOR_AGENT FROM SPECIFICATION $$
{"instructions": {"response": "Answer for this leisure operator only. Always say which metric or verified query you used.",
                  "orchestration": "Use the operator_kpis tool for members, revenue and utilisation questions."},
 "tools": [{"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "operator_kpis",
                          "description": "Active members, revenue, class utilisation for this operator"}}],
 "tool_resources": {"operator_kpis": {"semantic_view": "{FQ_SCHEMA}.SV_OPERATOR_KPIS",
                    "execution_environment": {"type": "warehouse", "warehouse": "DQ_LAB_WH"}}}}
$$;""")

st.markdown("### S2. A scheduled data quality digest")
render_prompt("Prompt S.2", "Daily digest for Customer Success", """In {FQ_SCHEMA}, create a view V_DQ_DIGEST that lists, for the last 24 hours, every expectation in my schema with: latest value, pass/fail, number of failed runs and first failure time. Then create a task that runs it daily at 07:00 Europe/London and writes the result into a table DQ_DIGEST_HISTORY. Keep the task suspended - show me how I would resume it.""")
render_snowsight_route([
    "Create the view and table in a worksheet, then **Transformation » Tasks » + Task** with a CRON schedule `0 7 * * * Europe/London`.",
])

st.markdown("### S3. Prove a migrated operator matches")
render_prompt("Prompt S.3", "Before/after migration check", """Pretend {FQ_SCHEMA} is an operator that has just been migrated from GCP to Azure, and GLADSTONE_DQ_LAB.ADMIN_OPERATOR_TEMPLATE is not visible to me. Using only my schema, design the reconciliation checks I'd run before cut-over: row counts per Bronze table, sum of payment amounts per day, distinct members per status, and max _loaded_at. Write them as data metric functions or SQL I can run against both copies, and explain which differences are acceptable.""")

render_real_world_examples([
    {"title": "Nova agent regression tests", "body": "A fixed set of operator questions with known answers runs after every semantic-view change, using agent evaluations."},
    {"title": "CS morning digest", "body": "The daily digest goes to Customer Success, so they know about a broken operator before the operator rings."},
    {"title": "GCP to Azure cut-over", "body": "Reconciliation DMFs give a signed-off, repeatable before/after comparison per operator database."},
])
render_references({
    "Quickstarts": [L.QS_AGENTS, L.QS_AGENT_EVAL, L.QS_AI_OBS, L.QS_SV_BP],
    "Docs": [L.AGENTS, L.AI_OBS, L.SV_CREATE, L.TASKS],
})
