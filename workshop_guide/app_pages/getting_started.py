import streamlit as st

from components import ctx, fill, render_real_world_examples, render_references
from content import links as L

st.title("Getting started")
st.markdown("Five minutes before the lab starts. Your admin has already created your operator - you only connect and check.")

st.markdown("#### :material/laptop: Bring")
with st.container(border=True):
    st.markdown("""
| Item | Details |
|---|---|
| **CoCo Desktop or CoCo CLI** | Signed in to Gladstone's Snowflake account (`GLADSTONESOFTWARE`). Either works for every step. |
| **Your operator name** | From your admin, e.g. `NIELS`. Type it in the sidebar - every prompt updates. |
| **Browser** | Snowsight, for the *Do it in Snowsight* routes and the data quality dashboard. |
| **Bonus B3 only** | Snowflake CLI (`snow`) 3.17+ and git. |
""")

c = ctx()
st.markdown("#### :material/checklist: Check your setup")
st.markdown("##### 1. Connect CoCo with your operator role")
with st.container(border=True):
    st.markdown(fill("""
- **CoCo Desktop**: choose the connection to `GLADSTONESOFTWARE`, then set role **`{ROLE}`** and warehouse **`DQ_LAB_WH`**.
- **CoCo CLI**: start `cortex` in a terminal (or `cortex -c <your-connection>`), then ask: *"use role {ROLE} and warehouse DQ_LAB_WH"*.
"""))

st.markdown("##### 2. Paste this into CoCo")
with st.container(border=True):
    st.code(fill("Confirm my current role, warehouse and that I can see schema {FQ_SCHEMA}. List the tables, dynamic tables and tasks in it."), language="text", wrap_lines=True)
    st.markdown(fill("""
You should see:
- role **`{ROLE}`**, warehouse **`DQ_LAB_WH`**
- tables `MEMBERS__MEMBER`, `MEMBERS__MEMBERSHIP`, `SHARED__SITE`, `SHARED__ACTIVITY`, `SYSTEM__BOOKING`, `SYSTEM__ATTENDANCE`, `SYSTEM__PAYMENT`, `_SYNC_META__MERGE_BATCH`
- dynamic tables `REPORTING__ACTIVE_MEMBERS`, `REPORTING__DAILY_REVENUE`, `REPORTING__CLASS_UTILISATION`
- task `TSK_BIFROST_MERGE` (started)
- semantic view `SV_OPERATOR_KPIS`
"""))
    with st.expander(":material/web: Do it in Snowsight"):
        st.code(fill(f"""USE ROLE {c['ROLE']};
USE WAREHOUSE DQ_LAB_WH;
SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE();
SHOW OBJECTS IN SCHEMA {c['FQ_SCHEMA']};
SHOW TASKS IN SCHEMA {c['FQ_SCHEMA']};"""), language="sql")

st.markdown("##### 3. Know the isolation model")
with st.container(border=True):
    st.markdown(fill("""
- One lab database: `GLADSTONE_DQ_LAB`. **Your schema `{SCHEMA}` stands in for one operator's own database** (`CUST_*` in production).
- You own everything in your schema and **cannot see anyone else's** - just like operators.
- Shared, read-only: `DQ_COMMON` (central custom checks), `ADMIN.V_FLEET_DQ_HEALTH` (fleet view, Session 5).
- One shared warehouse `DQ_LAB_WH`, capped by a resource monitor.
"""))

st.markdown("##### 4. How to work in CoCo")
with st.container(border=True):
    st.markdown("""
- Paste the prompt as is. CoCo shows the SQL before it runs anything - **read it, then approve**.
- If CoCo asks a question, answer with the details in the prompt (schema, thresholds).
- Ticking **Done** on a prompt marks the page complete in the sidebar.
- Behind? Every section has a **Behind? Run this** box with the exact SQL.
""")

render_real_world_examples([
    {"title": "Same pattern in production", "body": "A support engineer connects CoCo with a read role for one `CUST_*` database and investigates without touching other operators."},
    {"title": "CLI for repeatable runs", "body": "The CoCo CLI can be scripted, so the same prompts can run across operators from a terminal or a scheduled job."},
])
render_references({
    "Quickstarts": [L.QS_COCO_DESKTOP, L.QS_COCO_CLI, L.QS_COCO_BP],
    "Docs": [L.COCO, L.COCO_CLI],
})
