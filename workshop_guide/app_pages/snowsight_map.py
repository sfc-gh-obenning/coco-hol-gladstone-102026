import streamlit as st

from components import render_real_world_examples, render_references
from content import links as L

st.title("Snowsight navigation map")
st.markdown("Where each lab step lives in Snowsight. Menu names can change between releases; if a label differs, use the Snowsight search bar.")

st.markdown("""
| Task | Snowsight location |
|---|---|
| Browse your operator schema, lineage, table details | **Catalog » Database Explorer** » `GLADSTONE_DQ_LAB` » `CUST_<NAME>` |
| Add / view data quality checks on a table | Table » **Data Quality** tab |
| Account-wide DQ incidents, monitored schemas, *Investigate* with CoCo | **Governance & security » Data quality** |
| Dynamic Tables: lag, refresh mode, refresh history, suspend/resume | **Transformation » Dynamic tables** |
| Task run history, return values, suspend/resume | **Transformation » Tasks** |
| Semantic views and verified queries | **AI & ML » Cortex Analyst** |
| Cortex Agents (create, playground) | **AI & ML » Agents** |
| Run SQL | **Projects » Workspaces** (or a worksheet) |
| Budgets, consumption, resource monitors | **Admin » Cost management** |
| Classification, tags, masking and row access policies | **Governance & security » Trust Center**, **Tags & policies** |
| Query and access history | **Monitoring » Query history** |
| DCM projects | **Projects » Workspaces** » DCM project |
""")

render_real_world_examples([
    {"title": "Analysts without CoCo", "body": "Business users and CS can follow the same checks from Snowsight menus, with no prompts needed."},
    {"title": "Incident handover", "body": "On-call shares a Snowsight link to the failing check's Data Quality tab instead of screenshots."},
])
render_references({
    "Docs": [L.DQ_DASH, L.DT_MONITOR, L.LINEAGE, L.BUDGETS, L.TRUST_CENTER, L.DCM],
})
