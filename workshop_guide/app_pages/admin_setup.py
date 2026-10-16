import streamlit as st

from components import (doc_file, render_doc_download, render_real_world_examples,
                        render_references, render_sql_file)
from content import links as L

st.title("Lab setup (admin)")
st.markdown("For the Gladstone Snowflake admin. Questions go out five working days ahead and setup takes about "
            "15 minutes, three days before. Everything lives in **one database**, **one warehouse** and a set of "
            "`DQ_LAB_*` roles.")

st.markdown("#### :material/route: What, how and why")
w, h, y = st.columns(3)
with w.container(border=True, height="stretch"):
    st.markdown("##### What gets created")
    st.markdown("""
- Warehouse `DQ_LAB_WH` (XS, 1-3 clusters, auto-suspend 60s) + monitor `DQ_LAB_RM` (20 credits)
- Email integration `DQ_LAB_EMAIL_INT`
- Roles `DQ_LAB_ADMIN`, `DQ_LAB_ATTENDEE`, one `DQ_LAB_<NAME>` per attendee and per spare
- Database `GLADSTONE_DQ_LAB`: `ADMIN`, `DQ_COMMON`, `ADMIN_OPERATOR_TEMPLATE`, one `CUST_<NAME>` per attendee, `CUST_SPARE01..` for walk-ins
""")
with h.container(border=True, height="stretch"):
    st.markdown("##### How")
    st.markdown("""
1. `00_admin_setup.sql` - account objects, roles, DB
2. `01_build_template.sql` - synthetic gold-copy operator + central DMFs
3. `02_lab_procs.sql` - setup / spare / fault / reset procs and views
4. `CALL SETUP_ALL(...)` then `SETUP_SPARES(3)` - zero-copy clone each (~20 s)
""")
with y.container(border=True, height="stretch"):
    st.markdown("##### Why this design")
    st.markdown("""
- A schema per attendee mirrors **a database per operator** - real isolation, no collisions.
- **Zero-copy clones**: seconds to create, no storage until changed.
- **Spares** make a walk-in a grant (~1 s), not a build.
- One warehouse with a cap keeps cost bounded; DMFs are serverless.
- One DB makes teardown a single `DROP DATABASE`.
""")

before, setup, walkins, during = st.tabs([
    ":material/event: Before the day", ":material/play_circle: Setup",
    ":material/person_add: Walk-ins", ":material/sports: During the session",
])

# ── Before the day ───────────────────────────────────────────────────────────
with before:
    st.markdown("#### Timeline")
    st.markdown("""
| When | Who | Do |
|---|---|---|
| T-5 working days | Facilitator | Send the questionnaire's six **T-5** items (email below) and the roster template. Send attendees the prep sheet. |
| T-5 | Admin | Check every roster user exists: `SHOW USERS LIKE '<user>';` |
| T-3 | Admin | Run the **Setup** tab, including spares. Send back the pre-flight output and `V_ROSTER`. |
| T-1 | Attendees | Log in, open CoCo, run the test prompt on **Before you start**. |
| T-1 | Facilitator | `V_ROSTER`: everyone `ASSIGNED`, recent `LAST_SUCCESS_LOGIN`, at least 2 `SPARE - free`. |
""")
    st.caption("`LAST_SUCCESS_LOGIN` comes from ACCOUNT_USAGE and can lag up to about 2 hours - check it the day before, not at kick-off.")
    c1, c2, c3 = st.columns(3)
    with c1:
        render_doc_download("ADMIN_PREFLIGHT_QUESTIONNAIRE.md", "Admin questionnaire")
    with c2:
        render_doc_download("ATTENDEE_ROSTER.csv", "Roster template (CSV)", mime="text/csv")
    with c3:
        render_doc_download("ATTENDEE_PREP.md", "Attendee prep sheet")
    st.markdown("#### Questionnaire")
    body = doc_file("ADMIN_PREFLIGHT_QUESTIONNAIRE.md").split("\n", 1)[-1]   # drop the H1, the page has a title
    with st.container(border=True):
        st.markdown(body)

# ── Setup ────────────────────────────────────────────────────────────────────
with setup:
    st.markdown("#### :material/checklist: Prerequisites")
    st.markdown("""
| Requirement | Why |
|---|---|
| **ACCOUNTADMIN** for setup and teardown | Creates roles, warehouse, monitor, integration; alters users |
| **Enterprise Edition or higher** | Data metric functions, classification, masking and row access |
| Attendee Snowflake **users** exist, with CoCo access | `SETUP_ALL` grants roles (and optionally sets defaults) |
| Your **verified email** | Email integration for DQ and budget notifications |
| A warehouse other than `DQ_LAB_WH` (e.g. `COMPUTE_WH`) | Used by teardown before dropping the lab warehouse |
| Cortex enabled in the account | Cortex Agents (stretch) and CoCo |
| Bonus B3 only: attendees have Snowflake CLI 3.17+ | `snow dcm` commands |
""")

    st.markdown("#### Run order")
    st.markdown("##### 1. Account objects, roles and the lab database")
    st.caption("Edit `LAB_ADMIN_EMAIL` at the top first.")
    render_sql_file("00_admin_setup.sql")
    st.markdown("##### 2. The gold-copy operator and central checks")
    render_sql_file("01_build_template.sql")
    st.markdown("##### 3. Facilitator procedures and views")
    render_sql_file("02_lab_procs.sql")
    st.markdown("##### 4. Create one operator per attendee, plus spares")
    st.code("""USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DQ_LAB_WH;
CALL GLADSTONE_DQ_LAB.ADMIN.SETUP_ALL(PARSE_JSON('[
  {"user": "NJOHANSEN", "name": "NIELS"},
  {"user": "ASMITH",    "name": "AMY", "set_defaults": false}
]'));
CALL GLADSTONE_DQ_LAB.ADMIN.SETUP_SPARES(3);          -- walk-ins: CUST_SPARE01..03
SELECT * FROM GLADSTONE_DQ_LAB.ADMIN.V_ROSTER;""", language="sql")
    st.markdown("""
- `user` = Snowflake user name; `name` = short operator name (letters, digits, underscore). Tell each attendee their `name`.
- A user that can't be found is reported under **Check:** in the result. The operator is still built, so fix the name and bind it (instant): `CALL GLADSTONE_DQ_LAB.ADMIN.BIND_USER('<USER>', '<NAME>', TRUE);`
- `set_defaults` (default `true`) sets the user's `DEFAULT_ROLE` and `DEFAULT_WAREHOUSE` to the lab's. Use `false` if SCIM manages users; those attendees run `USE ROLE DQ_LAB_<NAME>` first. Changed defaults are recorded and restored by teardown.
""")

    st.markdown("##### 5. Smoke test (as one attendee role)")
    st.code("""USE ROLE DQ_LAB_NIELS; USE SECONDARY ROLES NONE; USE WAREHOUSE DQ_LAB_WH;
SHOW DYNAMIC TABLES IN SCHEMA GLADSTONE_DQ_LAB.CUST_NIELS;         -- 3, refresh_mode INCREMENTAL
SELECT COUNT(*) FROM GLADSTONE_DQ_LAB.CUST_NIELS._SYNC_META__MERGE_BATCH
 WHERE batch_id <> 'B-SEED';                                        -- grows every minute
SELECT * FROM SEMANTIC_VIEW(GLADSTONE_DQ_LAB.CUST_NIELS.SV_OPERATOR_KPIS
  METRICS am.active_members, ms.paid_members_35d);
SELECT COUNT(*) FROM GLADSTONE_DQ_LAB.CUST_AMY.MEMBERS__MEMBER;     -- must FAIL: not authorized""", language="sql")

    st.markdown("#### :material/extension: Bonus labs")
    st.markdown("Each bonus has its own setup and teardown. Run setup only for the bonuses you offer - see each bonus page. "
                "B2 grants its test roles to attendee users at setup time, so re-run `B2_setup.sql` after claiming spares.")

# ── Walk-ins ─────────────────────────────────────────────────────────────────
with walkins:
    st.markdown("Someone turns up who wasn't on the roster. Pick the row that matches:")
    st.markdown("""
| Situation | Action | Time |
|---|---|---|
| Has a Snowflake user, a spare is free | `CLAIM_SPARE('<USER>')` - tell them the operator name it returns (e.g. `SPARE01`) | ~1 s |
| Has a user, no spare left | Same call - it builds a new operator named after the user | ~20 s |
| User name not found | The call returns ERROR and claims nothing. Find the name: `SHOW USERS LIKE '%<part>%';` | - |
| No Snowflake user | Pair with a neighbour (read along on their operator), or create a temporary user if policy allows, then claim a spare | - |
| Arrives after faults were injected | `INJECT_FAULTS('<NAME>')` once they finish Session 2 | ~2 s |
""")
    st.code("""USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DQ_LAB_WH;
CALL GLADSTONE_DQ_LAB.ADMIN.CLAIM_SPARE('JDOE');          -- or CLAIM_SPARE('JDOE', FALSE) to keep their defaults
SELECT * FROM GLADSTONE_DQ_LAB.ADMIN.V_ROSTER WHERE status LIKE 'SPARE%';
CALL GLADSTONE_DQ_LAB.ADMIN.SETUP_SPARES(2);              -- top up if you're running low""", language="sql")
    st.info("The attendee types their operator name (for example `SPARE01`) into the sidebar box. Every prompt in "
            "the guide then points at their schema and role.", icon=":material/info:")

# ── During the session ───────────────────────────────────────────────────────
with during:
    st.markdown("""
| When | Run | Effect |
|---|---|---|
| End of Session 2 (min 11) | `CALL GLADSTONE_DQ_LAB.ADMIN.INJECT_FAULTS('ALL');` | One fault per operator (spares included), by setup order |
| Anytime | `SELECT * FROM GLADSTONE_DQ_LAB.ADMIN.V_FLEET_ANSWER_KEY;` | Who got which fault (facilitator only) |
| Session 5 | `SELECT * FROM GLADSTONE_DQ_LAB.ADMIN.V_FLEET_DQ_HEALTH;` | Fleet view (attendees can read it) |
| Attendee stuck | `CALL GLADSTONE_DQ_LAB.ADMIN.RESET_ATTENDEE('NIELS');` | Fresh operator in seconds; user binding kept |
| End | `CALL GLADSTONE_DQ_LAB.ADMIN.SUSPEND_ALL();` | Stops tasks and DTs, notifications off |
""")
    render_sql_file("answer_key_core.sql", ":material/key: Core answer key (Sessions 2-4)")
    render_sql_file("99_reset_attendee.sql")

    st.markdown("#### :material/savings: Cost")
    st.markdown("""
- `DQ_LAB_WH` runs while merge tasks and 1-minute Dynamic Tables run - expect it to stay warm during the lab. Run `SUSPEND_ALL()` when the session ends.
- Each spare runs its own merge task, like an attendee. Three spares add little, but suspend unclaimed ones if you set up many: `ALTER TASK GLADSTONE_DQ_LAB.CUST_SPARE03.TSK_BIFROST_MERGE SUSPEND;`
- DMFs run on serverless compute (not covered by the resource monitor); a 5-minute schedule on a few small tables per attendee is small. Check with `DATA_QUALITY_MONITORING_USAGE_HISTORY`.
""")

render_real_world_examples([
    {"title": "Repeatable training environment", "body": "The same scripts stand up a sandbox for new data engineers or for operator-facing demos."},
    {"title": "Template for production rollout", "body": "`SETUP_ATTENDEE` is a small model of operator onboarding: clone, own, attach checks, register. Spares are the same idea as a pre-provisioned pool for new operators."},
])
render_references({
    "Docs": [L.DQ_SQL, L.DQ_NOTIFY, L.RES_MON, L.DT_OVERVIEW, L.TASKS, L.COCO],
})
