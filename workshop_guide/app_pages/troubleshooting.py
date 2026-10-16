import streamlit as st

from components import render_real_world_examples, fill, render_references
from content import links as L

st.title("Troubleshooting")
st.markdown("Problems seen in the dry run and how to fix them.")

issues = [
    ("Expectations show no results yet",
     "Scheduled checks run every 5 minutes. Evaluate immediately:",
     "SELECT * FROM TABLE(SYSTEM$EVALUATE_DATA_QUALITY_EXPECTATIONS(REF_ENTITY_NAME => '{FQ_SCHEMA}.MEMBERS__MEMBER'));"),
    ("Anomaly detection says TRAINING_IN_PROGRESS",
     "Expected. It needs about two weeks of results before it flags anomalies. Expectations do the detecting in this lab.", None),
    ("'Object does not exist or not authorized' on another schema",
     "Correct behaviour - each operator sees only its own schema. Check your role:",
     "SELECT CURRENT_ROLE(), CURRENT_SECONDARY_ROLES();  -- expect {ROLE}"),
    ("Masked values when you expected real ones (B2)",
     "Masking follows the roles in your session. Run with the privacy role as a secondary role:",
     "USE SECONDARY ROLES DQ_LAB_PII_READER;"),
    ("Unexpected rows visible (or missing) after B2",
     "Secondary roles may still be on. Turn them off to test a single role:",
     "USE SECONDARY ROLES NONE;"),
    ("A check is 'already associated'",
     "The same DMF can be attached to the same column once. Modify it instead:",
     "ALTER TABLE {FQ_SCHEMA}.MEMBERS__MEMBER MODIFY DATA METRIC FUNCTION SNOWFLAKE.CORE.DUPLICATE_COUNT ON (member_id) ADD EXPECTATION ...;"),
    ("Circuit breaker never closes",
     "It must only watch Bronze checks. If it watches a REPORTING check, freezing REPORTING keeps it failing. Check its return value:",
     "SELECT state, return_value FROM TABLE({DB}.INFORMATION_SCHEMA.TASK_HISTORY(TASK_NAME => 'TSK_DQ_CIRCUIT_BREAKER', RESULT_LIMIT => 5));"),
    ("Dynamic table fell back to FULL refresh",
     "A non-deterministic function such as CURRENT_TIMESTAMP in the definition forces full refresh. Check:",
     "SHOW DYNAMIC TABLES IN SCHEMA {FQ_SCHEMA};  -- refresh_mode should be INCREMENTAL"),
    ("Everything is broken - start again",
     "Ask the facilitator to reset your operator (re-clones it in seconds). You'll redo Session 2.", None),
]
for title, body, sql in issues:
    with st.expander(f":material/help: {title}"):
        st.markdown(body)
        if sql:
            st.code(fill(sql), language="sql")

render_real_world_examples([
    {"title": "Rollout runbook", "body": "These fixes become the runbook when the checks are rolled out to every `CUST_*` database."},
    {"title": "Least-privilege checks", "body": "The isolation errors prove the operator-per-database access model is working - keep them in production."},
])
render_references({"Docs": [L.DQ_EXPECT, L.DQ_ANOMALY, L.TAG_MASK, L.DT_MONITOR, L.TASK_HISTORY]})
