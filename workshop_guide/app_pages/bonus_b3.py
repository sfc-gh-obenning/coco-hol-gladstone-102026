import streamlit as st

from components import (render_checkpoint, render_execution_context, render_explanation, render_prompt,
                        render_real_world_examples, render_references, render_session_header,
                        render_snowsight_route, render_sql_file, render_what_why, sql_file)
from content import links as L

render_session_header("Bonus B3", "DevOps with DCM Projects", "30 min, self-paced", "One operator's pipeline and its data quality checks as code")
render_execution_context()
render_what_why(
    "Turn what you built by hand into a **DCM project**: Bronze tables, REPORTING Dynamic Tables and their expectations, declared once, deployed per operator with `plan`, `deploy` and `test`.",
    "Hundreds of operator databases can't be configured by hand. With DCM, onboarding operator N is a new target and a `deploy`; every operator gets the same data quality from day one, and `snow dcm test` is a CI gate.",
)

with st.container(border=True):
    st.markdown("##### :material/admin_panel_settings: Admin: run once before B3")
    st.markdown("Pre-creates an empty `CUST_<NAME>_DCM` schema per attendee, owned by their role. The DCM project lives in it and deploys into it.")
    render_sql_file("bonus/B3_setup.sql", "Show B3_setup.sql")
    st.markdown("**Attendee laptop:** Snowflake CLI (`snow`) 3.17+, git, and a CLI connection to `GLADSTONESOFTWARE`.")

render_prompt("Prompt B3.1", "Create the project", """Create a DCM project for my operator pipeline.
- Project identifier: GLADSTONE_DQ_LAB.CUST_{NAME}_DCM.OPERATOR_PIPELINE, owner role {ROLE}, local folder ./operator_pipeline
- manifest v2 with a target {NAME} and templating variables db, schema (CUST_{NAME}_DCM), operator_id ({SCHEMA}), wh (DQ_LAB_WH), dq_schedule ('5 MINUTE'), reporting_lag ('1 minute')
- Bronze tables MEMBERS__MEMBER and SYSTEM__PAYMENT (same columns as in {FQ_SCHEMA}) with change tracking and DATA_METRIC_SCHEDULE
- dynamic tables REPORTING__DAILY_REVENUE and REPORTING__ACTIVE_MEMBERS, incremental
- expectations: no duplicate member_id, GLADSTONE_DQ_LAB.DQ_COMMON.FOREIGN_OPERATOR_ROWS, DQ_COMMON.ACTIVE_BUT_LEFT, no negative amounts, net_revenue never null
Register the project in Snowflake and validate it. Don't deploy yet.""")
render_snowsight_route([
    "**Projects » Workspaces** » **+ Add new » DCM project** » choose `GLADSTONE_DQ_LAB.CUST_{NAME}_DCM`.",
    "Add the definition files (see the answer key below) to the workspace.",
])

render_prompt("Prompt B3.2", "Plan, then deploy", """Run a plan for target {NAME} and summarise what it will create, alter or drop. Explain any entry you weren't expecting. If it looks right, deploy with the alias first-deploy.""")
render_snowsight_route([
    "In the DCM workspace » **Plan** » review the change set » **Deploy**.",
])
render_checkpoint("Plan shows 4 creates (2 tables, 2 dynamic tables) and an `ALTER ROLE` that only records ownership of the new objects; deploy succeeds.")

render_prompt("Prompt B3.3", "Test, break, test again", """Run snow dcm test for target {NAME}. Then insert two rows with the same member_id into GLADSTONE_DQ_LAB.CUST_{NAME}_DCM.MEMBERS__MEMBER and run the test again. What exit code does the CLI return, and why does that matter for CI?""")
render_checkpoint("First run: 5/5 pass. After the duplicate: `NO_DUPLICATE_MEMBERS` fails and the CLI exits with **1** - a failed pipeline step in CI.")

render_prompt("Prompt B3.4", "Change and onboard", """1. Change reporting_lag to '5 minutes' and plan again - show me that only the two dynamic tables change.
2. Show how I'd onboard a second operator CUST_ACME: what to add to manifest.yml and which commands to run.
3. Write a GitHub Actions workflow that runs plan + test on pull requests and deploy + test on main, using the Snowflake CLI.""")

render_explanation("Why DCM for operator databases", """
- **Declarative**: definitions describe the end state; `plan` shows the diff before anything changes.
- **Templated targets**: one set of definitions, one target per operator (or per tier), different variables.
- **Data quality ships with the pipeline**: `ATTACH DATA METRIC FUNCTION ... EXPECTATION` lives next to the table it protects.
- **Test as a gate**: `snow dcm test` exits non-zero on a failed expectation.
- **Note**: a DCM project can't define its own parent database or schema - they must exist (that's why the admin pre-creates `CUST_<NAME>_DCM`).
""")

st.markdown("##### :material/folder_open: Answer key project (`sql/bonus/dcm_project`)")
for f in ["manifest.yml", "sources/definitions/bronze.sql", "sources/definitions/reporting.sql",
          "sources/definitions/expectations.sql", ".github/workflows/operator-pipeline-dcm.yml"]:
    with st.expander(f":material/description: `{f}`"):
        st.code(sql_file(f"bonus/dcm_project/{f}"), language="yaml" if f.endswith((".yml", ".yaml")) else "sql")
st.code("""cd operator_pipeline
snow dcm create  --target OPERATOR01 -c <conn>
snow dcm plan    --target OPERATOR01 -c <conn> --save-output    # read out/plan/plan_result.json
snow dcm deploy  --target OPERATOR01 -c <conn> --alias first-deploy
snow dcm test    --target OPERATOR01 -c <conn>""", language="bash")

with st.container(border=True):
    st.markdown("##### :material/delete_sweep: Admin: B3 teardown")
    st.markdown("Drops every `CUST_*_DCM` schema (the project object and everything it deployed). `snow dcm drop` alone would leave the objects behind.")
    render_sql_file("bonus/B3_teardown.sql", "Show B3_teardown.sql")

render_real_world_examples([
    {"title": "Operator onboarding as a pull request", "body": "A new operator is a new target in the manifest; review the plan in the PR, merge to deploy."},
    {"title": "Same checks everywhere", "body": "A new expectation added once reaches every operator on the next deploy - no drift between `CUST_*` databases."},
    {"title": "Safer REPORTING changes", "body": "`plan` shows whether a change alters or recreates a dynamic table before it touches production."},
    {"title": "Promotion DEV to PROD", "body": "Separate targets and accounts (dev, reporting, production) with the same definitions."},
])
render_references({
    "Quickstarts": [L.QS_DCM, L.QS_DCM_PIPE, L.QS_DCM_DT, L.QS_DCM_TASKS, L.QS_DEVOPS],
    "Docs": [L.DCM, L.SNOW_CLI, L.DQ_EXPECT],
})
