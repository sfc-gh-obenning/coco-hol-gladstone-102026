import streamlit as st

from components import doc_file, render_doc_download, render_real_world_examples, render_references
from content import links as L

st.title("Before you start")
st.markdown("What to do, know and expect before the 30-minute lab. Do the first tab **the day before**.")

render_doc_download("ATTENDEE_PREP.md", "Download as a one-page sheet")

# ATTENDEE_PREP.md is the single source: one "## " section per tab.
sections = {}
for chunk in doc_file("ATTENDEE_PREP.md").split("\n## ")[1:]:
    head, _, body = chunk.partition("\n")
    sections[head.strip()] = body

tabs = st.tabs([":material/checklist: Things to do", ":material/info: Things to know", ":material/schedule: What to expect"])
for tab, name in zip(tabs, ["Things to do", "Things to know", "What to expect"]):
    with tab:
        with st.container(border=True):
            st.markdown(sections.get(name, f"_{name} missing from ATTENDEE_PREP.md_"))

st.info("Something not working? See **Troubleshooting**, or tell the facilitator before the start - "
        "login and CoCo issues are quick to fix the day before and slow to fix during the lab.",
        icon=":material/help:")

render_real_world_examples([
    {"title": "Onboarding a new operator team", "body": "The same checklist (login, CoCo, role, a test prompt) works when a new operator's support engineers get access to their `CUST_*` database."},
    {"title": "Safe changes in a shared account", "body": "\"Read the SQL, then approve\" is the habit that matters in production, where one account serves many operators."},
])
render_references({
    "Quickstarts": [L.QS_COCO_DESKTOP, L.QS_COCO_CLI],
    "Docs": [L.COCO, L.COCO_CLI],
})
