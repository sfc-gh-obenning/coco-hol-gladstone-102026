import streamlit as st

from components import (render_checkpoint, render_execution_context, render_explanation, render_fallback,
                        render_prompt, render_real_world_examples, render_references, render_session_header,
                        render_snowsight_route, render_sql_file, render_what_why)
from content import links as L

render_session_header("Bonus B1", "Budgets and resource monitors", "20 min, self-paced", "Cost attribution, a budget per operator, and a hard cap")
render_execution_context()
render_what_why(
    "See what your operator pipeline costs, tag it for cost attribution, put a monthly **budget** on it with an alert, and draft a **resource monitor** the admin would apply.",
    "Data quality and Nova run per operator. Without per-operator cost visibility, overages show up at month-end. Budgets warn early (and cover serverless DMFs); resource monitors hard-stop warehouses.",
)

with st.container(border=True):
    st.markdown("##### :material/admin_panel_settings: Admin: run once before B1")
    st.markdown("Creates `FINOPS` (tags + budgets live here), grants the budget roles and APPLYBUDGET, lets the SNOWFLAKE app use the email integration, and creates a demo resource monitor.")
    render_sql_file("bonus/B1_setup.sql", "Show B1_setup.sql")

render_prompt("Prompt B1.1", "What does my operator cost?", """Show what my operator pipeline in {FQ_SCHEMA} costs: data quality (serverless DMF credits from SNOWFLAKE.ACCOUNT_USAGE.DATA_QUALITY_MONITORING_USAGE_HISTORY, filtered to my database and schema), and dynamic table refresh counts and duration from INFORMATION_SCHEMA. Explain which costs land on DQ_LAB_WH and which are serverless, and note any ACCOUNT_USAGE latency.""")
render_snowsight_route([
    "**Admin » Cost management » Consumption**: filter by warehouse `DQ_LAB_WH` and service type.",
    "**Admin » Cost management » Consumption** » service type *Data quality monitoring* for serverless DMF credits.",
])

render_prompt("Prompt B1.2", "Tag my operator for cost attribution", """Tag schema {FQ_SCHEMA} with GLADSTONE_DQ_LAB.FINOPS.OPERATOR_ID = '{SCHEMA}' and GLADSTONE_DQ_LAB.FINOPS.COST_CENTRE = 'nova'. Explain how objects inside the schema inherit the tags and how long until tag-based cost views reflect them.""")
render_snowsight_route([
    "**Catalog » Database Explorer** » `{SCHEMA}` » **…** » **Edit tags** » add `FINOPS.OPERATOR_ID` and `FINOPS.COST_CENTRE`.",
])

render_prompt("Prompt B1.3", "A budget for my operator", """Create a custom budget GLADSTONE_DQ_LAB.FINOPS.{SCHEMA}_BUDGET with a spending limit of 5 credits per month. Add my schema {FQ_SCHEMA} to it as a resource. Send email notifications through integration DQ_LAB_EMAIL_INT to my verified email address, at 80% of projected spend. Then list the budget's linked resources and show how to query its spending history.""")
render_snowsight_route([
    "**Admin » Cost management » Budgets » + Budget**.",
    "Location `GLADSTONE_DQ_LAB.FINOPS`, name `{SCHEMA}_BUDGET`, 5 credits, threshold 80%, your email.",
    "**Budget scope** » Resources » Schemas » `{SCHEMA}`. (Or Tags » `COST_CENTRE = nova` for every operator in a tier.)",
])
render_checkpoint("`GET_LINKED_RESOURCES` lists your schema. Spending history fills after the budget's background refresh (can take hours).")

render_prompt("Prompt B1.4", "Draft a resource monitor (admin applies it)", """Draft, but do not run, a resource monitor for a Nova operator warehouse NOVA_WH_{NAME}: 30 credits per month, notify at 75% and 90%, suspend at 100%. Explain why a resource monitor and a budget are both useful, what each one covers (warehouses vs serverless), and why only ACCOUNTADMIN can create the monitor.""")
render_snowsight_route([
    "**Admin » Cost management » Resource monitors » + Resource monitor** (ACCOUNTADMIN).",
])
render_explanation("Budgets vs resource monitors", """
| | Budget | Resource monitor |
|---|---|---|
| Covers | Warehouses **and serverless** (DMFs, serverless tasks, DT background work) | Warehouses only |
| Action | Notify (projected overspend) | Notify, **suspend** |
| Scope | Objects, schemas, databases, **tags** | One or more warehouses / account |
| Who creates | Any role with BUDGET_CREATOR + CREATE BUDGET | ACCOUNTADMIN |

At Gladstone scale: a **tag-based budget per tier** (e.g. `COST_CENTRE = nova`) plus a **resource monitor per shared warehouse**.
""")
render_fallback("""ALTER SCHEMA {FQ_SCHEMA} SET TAG
  GLADSTONE_DQ_LAB.FINOPS.OPERATOR_ID = '{SCHEMA}',
  GLADSTONE_DQ_LAB.FINOPS.COST_CENTRE = 'nova';
USE SCHEMA GLADSTONE_DQ_LAB.FINOPS;
CREATE SNOWFLAKE.CORE.BUDGET {SCHEMA}_BUDGET();
CALL {SCHEMA}_BUDGET!SET_SPENDING_LIMIT(5);
CALL {SCHEMA}_BUDGET!ADD_RESOURCE(SYSTEM$REFERENCE('SCHEMA', '{FQ_SCHEMA}', 'SESSION', 'applybudget'));
CALL {SCHEMA}_BUDGET!SET_EMAIL_NOTIFICATIONS('DQ_LAB_EMAIL_INT', '<your verified email>');
CALL {SCHEMA}_BUDGET!SET_NOTIFICATION_THRESHOLD(80);
CALL {SCHEMA}_BUDGET!GET_LINKED_RESOURCES();""")

with st.container(border=True):
    st.markdown("##### :material/delete_sweep: Admin: B1 teardown")
    st.markdown("Removes cost tags from every `CUST_*` schema, drops `FINOPS` (budgets and tags), the demo monitor and the B1 grants. The core lab keeps running.")
    render_sql_file("bonus/B1_teardown.sql", "Show B1_teardown.sql")

render_real_world_examples([
    {"title": "Usage and overage warnings per operator", "body": "A budget per operator (or per tag) emails before an operator's Nova or DQ usage runs over its contract."},
    {"title": "Showback to product lines", "body": "`COST_CENTRE` tags split Snowflake spend between Nova, reporting and platform without separate accounts."},
    {"title": "Hard stop on runaway sync", "body": "A resource monitor on the Bifrost/merge warehouse suspends it if a replay loop burns credits overnight."},
    {"title": "Cost of data quality itself", "body": "`DATA_QUALITY_MONITORING_USAGE_HISTORY` shows what checks cost per operator - and whether a schedule should move to TRIGGER_ON_CHANGES."},
])
render_references({
    "Quickstarts": [L.QS_COST, L.QS_QUERY_COST, L.WAF_COST],
    "Docs": [L.BUDGETS, L.BUDGETS_CUSTOM, L.BUDGETS_TUT, L.RES_MON, L.COST_ATTR, L.DQ_USAGE],
})
