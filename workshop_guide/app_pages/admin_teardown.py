import streamlit as st

from components import render_real_world_examples, render_references, render_sql_file
from content import links as L

st.title("Lab teardown (admin)")
st.markdown("Remove everything the lab created, in one script. Safe to re-run - every statement is `IF EXISTS` or guarded.")

st.markdown("#### :material/format_list_numbered: What 98_teardown.sql does, in order")
st.markdown("""
1. Runs the **bonus teardowns** if the bonus labs were used (B3 DCM schemas, B2 policies/GOVERNANCE, B1 tags/FINOPS) and drops the demo resource monitor.
2. `SUSPEND_ALL()` - stops every task and dynamic table, turns notifications off.
3. `DROP DATABASE GLADSTONE_DQ_LAB` - template, every `CUST_*` schema, DMFs, semantic views, agents, budgets.
4. Drops `DQ_LAB_WH`, `DQ_LAB_RM`, `DQ_LAB_EMAIL_INT`.
5. Drops **every role named `DQ_LAB_*`**.
6. Verification: every `SHOW` returns zero rows.
""")
st.info("Teardown switches to `COMPUTE_WH` before dropping the lab warehouse. Edit that line if the account uses another warehouse.", icon=":material/info:")

render_sql_file("98_teardown.sql", ":material/description: 98_teardown.sql", expanded=True)

st.markdown("#### :material/layers_clear: Bonus-only teardowns")
st.caption("Use these to remove one bonus lab and keep the core lab running.")
for f in ["bonus/B1_teardown.sql", "bonus/B2_teardown.sql", "bonus/B3_teardown.sql"]:
    render_sql_file(f)

st.markdown("#### :material/rule: After teardown")
st.markdown("""
- Attendees' original `DEFAULT_ROLE` and `DEFAULT_WAREHOUSE` are restored automatically (step 2 of `98_teardown.sql`). Users set up with `set_defaults: false` were never changed.
- Temporary walk-in users, if you created any, are not dropped by the script: `DROP USER <u>;`
- Dropped data stays in Time Travel and then Fail-safe for the retention period before it is purged. All lab data is synthetic.
- Attendee laptops keep their local DCM project folders (Bonus B3).
""")

render_real_world_examples([
    {"title": "Clean sandboxes", "body": "One teardown script keeps training accounts free of stray roles, warehouses and cost."},
    {"title": "Erasure thinking", "body": "Dropping data still leaves Time Travel and Fail-safe copies - the same point as Bonus B2's GDPR exercise."},
])
render_references({"Docs": [L.TIME_TRAVEL, L.FAILSAFE, L.RES_MON]})
