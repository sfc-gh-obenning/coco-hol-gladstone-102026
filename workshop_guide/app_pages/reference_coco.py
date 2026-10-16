import streamlit as st

from components import render_real_world_examples, fill, render_references
from content import links as L

st.title("CoCo prompt cheat sheet")
st.markdown("Prompts that worked well in the lab, ready to reuse on any operator database. Replace the schema with a real `CUST_*` database in production.")

st.markdown("#### :material/tips_and_updates: How to prompt CoCo for data quality")
st.markdown("""
- **Name the object fully** (`DATABASE.SCHEMA.TABLE`) and the role to use.
- **State the rule and the threshold** ("expect 0", "under 180 seconds") - CoCo turns it into an expectation.
- **Ask to see the SQL first** for anything that changes objects.
- **Ask for evidence**: failing rows, the batch id, the task/DT history - not only "is it broken?".
- **CoCo CLI** in a terminal: `cortex` (interactive) - same prompts, scriptable for many operators.
""")

prompts = {
    "Map a pipeline": "In {FQ_SCHEMA}, explain the pipeline end to end and draw the lineage from Bronze to the semantic view. Don't change anything.",
    "Add standard checks": "Add data quality monitoring to every Bronze table in {FQ_SCHEMA}: duplicates on the primary key, freshness under 3 minutes, row count with anomaly detection, and no rows from another operator using GLADSTONE_DQ_LAB.DQ_COMMON.FOREIGN_OPERATOR_ROWS. Show me the SQL first.",
    "Investigate": "Nova's numbers look wrong for {SCHEMA}. Which expectations are failing, which rows and batch caused it, is the merge task healthy, and which Nova metrics are affected?",
    "Fleet triage": "Which operators have failing data quality checks right now? Group them by failure type and suggest a root cause for each group.",
    "Silence noise": "Keep data quality notifications only for no_other_operator_rows and no_duplicate_members in {FQ_SCHEMA}; turn the rest off.",
    "Cost of checks": "What did data quality monitoring cost for {FQ_SCHEMA} in the last 7 days, and which checks would be cheaper on TRIGGER_ON_CHANGES?",
}
for title, p in prompts.items():
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.code(fill(p), language="text", wrap_lines=True)

render_real_world_examples([
    {"title": "Support playbook", "body": "Save these prompts as a CoCo skill so every CS and data engineer investigates an operator the same way."},
    {"title": "Scripted fleet checks", "body": "Run the same prompts with the CoCo CLI against several operator databases from a terminal or a scheduled job."},
])
render_references({
    "Quickstarts": [L.QS_COCO_BP, L.QS_COCO_DE, L.QS_COCO_CLI],
    "Docs": [L.COCO, L.COCO_CLI, L.DQ_DASH],
})
