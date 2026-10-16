import streamlit as st

from components import (render_checkpoint, render_execution_context, render_explanation, render_fallback,
                        render_prompt, render_real_world_examples, render_references, render_session_header,
                        render_snowsight_route, render_technologies_used, render_what_why, render_what_you_built)
from content import links as L

render_session_header("Session 4", "Contain and alert", "6 min", "A circuit breaker task and a notification on the critical check")
render_execution_context()
render_what_why(
    "Stop bad Bronze data reaching Nova: a task that freezes the REPORTING Dynamic Tables while any Bronze expectation fails, and resumes them when it's clean. Then decide which checks should email you.",
    "Detection alone still lets Nova serve a wrong number. Freezing REPORTING keeps Nova on the last good state - stale beats wrong. Notifications on only the critical checks avoid alert fatigue across hundreds of operators.",
)

render_prompt("Prompt 4.1", "Build a circuit breaker", """In {FQ_SCHEMA}, create a task TSK_DQ_CIRCUIT_BREAKER on warehouse DQ_LAB_WH that runs every minute and:
- reads the latest result per expectation from SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS for tables MEMBERS__MEMBER, SYSTEM__PAYMENT and SYSTEM__ATTENDANCE in schema {SCHEMA}
- if any is violated: suspends dynamic tables REPORTING__ACTIVE_MEMBERS and REPORTING__DAILY_REVENUE
- otherwise: resumes them
- records what it did with SYSTEM$SET_RETURN_VALUE (for example "OPEN: 1 failing check" or "CLOSED: Bronze clean"); build the message in a variable first, because SYSTEM$SET_RETURN_VALUE does not accept an expression
Resume the task, wait for one run, and show me its return value and the dynamic tables' scheduling state.""")
render_snowsight_route([
    "**Projects » Workspaces** (or a worksheet): paste the task SQL from *Behind? Run this* and run it.",
    "**Transformation » Tasks** » `TSK_DQ_CIRCUIT_BREAKER` » **Run history** shows each return value.",
    "**Transformation » Dynamic tables** shows `REPORTING__*` as **Suspended** while the breaker is open.",
])

render_prompt("Prompt 4.2", "Fix the fault, close the breaker, choose alerts", """Based on the root cause you found in Session 3, fix the Bronze data in {FQ_SCHEMA} (for example delete the bad batch, or resume a suspended task). Show me the SQL first.
Then re-evaluate the expectations, confirm the circuit breaker closes and the REPORTING dynamic tables resume.
Finally, notifications are already enabled for this database by the admin: keep email notifications ON only for no_other_operator_rows and no_duplicate_members, and turn them OFF for every other check in my schema.""")
render_snowsight_route([
    "Open the table » **Data Quality** » select a check » **Notifications** toggle.",
    "Re-check: **Transformation » Tasks** » breaker run history should read *CLOSED: Bronze clean*.",
], sql="""ALTER TABLE {FQ_SCHEMA}.SYSTEM__PAYMENT
  MODIFY DATA METRIC FUNCTION SNOWFLAKE.CORE.NEGATIVE_COUNT ON (amount)
  SET DATA_QUALITY_NOTIFICATION = FALSE;""")

render_checkpoint("Breaker run history shows **OPEN** then **CLOSED: Bronze clean**, and `REPORTING__*` are active again.", sql="""SELECT state, return_value, completed_time
FROM TABLE({DB}.INFORMATION_SCHEMA.TASK_HISTORY(TASK_NAME => 'TSK_DQ_CIRCUIT_BREAKER', RESULT_LIMIT => 5))
WHERE state <> 'SCHEDULED' ORDER BY completed_time DESC;""")
render_explanation("Fixes by fault", """
| Fault | Fix |
|---|---|
| Bifrost replay | `DELETE FROM MEMBERS__MEMBER WHERE _batch_id = 'B-REPLAY-01';` |
| Merge task stalled | `ALTER TASK TSK_BIFROST_MERGE RESUME;` (FRESHNESS recovers within a minute) |
| Refund sign flip | `DELETE FROM SYSTEM__PAYMENT WHERE _batch_id = 'B-SIGNBUG-01';` (in production: reload as REFUND with positive amount) |
| Orphan attendance | `DELETE FROM SYSTEM__ATTENDANCE WHERE booking_id LIKE 'BK-GHOST-%';` (in production: re-sync the bookings) |
| Tenant leak | `DELETE FROM MEMBERS__MEMBER WHERE operator_id <> '{SCHEMA}';` - then treat it as a personal-data incident (Bonus B2) |
| Status drift | `UPDATE MEMBERS__MEMBER SET status = 'CANCELLED' WHERE status = 'ACTIVE' AND left_on IS NOT NULL;` |

**Why only the circuit breaker on Bronze checks?** The breaker freezes the REPORTING tables. If it also watched REPORTING checks,
freezing REPORTING could keep it failing - so it would never close.

**How notifications work:** the database owner turns them on once for the whole database (`DATA_QUALITY_MONITORING_SETTINGS`);
each table owner then chooses which checks notify. In production that's one setting per operator database, with the same email or Slack/Teams webhook integration.
""")
render_fallback("""USE SCHEMA {FQ_SCHEMA};
CREATE OR REPLACE TASK TSK_DQ_CIRCUIT_BREAKER WAREHOUSE = DQ_LAB_WH SCHEDULE = '1 MINUTE'
AS
EXECUTE IMMEDIATE $$
DECLARE bad NUMBER; msg VARCHAR;
BEGIN
  SELECT COUNT(*) INTO :bad FROM (
    SELECT expectation_violated FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS
    WHERE table_database = 'GLADSTONE_DQ_LAB' AND table_schema = '{SCHEMA}'
      AND table_name IN ('MEMBERS__MEMBER', 'SYSTEM__PAYMENT', 'SYSTEM__ATTENDANCE')
    QUALIFY ROW_NUMBER() OVER (PARTITION BY table_name, expectation_name ORDER BY measurement_time DESC) = 1)
  WHERE expectation_violated;
  IF (bad > 0) THEN
    ALTER DYNAMIC TABLE {FQ_SCHEMA}.REPORTING__ACTIVE_MEMBERS SUSPEND;
    ALTER DYNAMIC TABLE {FQ_SCHEMA}.REPORTING__DAILY_REVENUE SUSPEND;
    msg := 'OPEN: ' || :bad || ' failing Bronze check(s)';   -- SET_RETURN_VALUE needs a variable, not an expression
    CALL SYSTEM$SET_RETURN_VALUE(:msg);
  ELSE
    ALTER DYNAMIC TABLE {FQ_SCHEMA}.REPORTING__ACTIVE_MEMBERS RESUME;
    ALTER DYNAMIC TABLE {FQ_SCHEMA}.REPORTING__DAILY_REVENUE RESUME;
    CALL SYSTEM$SET_RETURN_VALUE('CLOSED: Bronze clean');
  END IF;
END;
$$;
ALTER TASK TSK_DQ_CIRCUIT_BREAKER RESUME;

-- notifications: keep the two critical checks, silence the rest (repeat SET ... FALSE per check)
ALTER TABLE MEMBERS__MEMBER MODIFY DATA METRIC FUNCTION SNOWFLAKE.CORE.DUPLICATE_COUNT ON (member_id)
  SET DATA_QUALITY_NOTIFICATION = TRUE;
ALTER TABLE SYSTEM__PAYMENT MODIFY DATA METRIC FUNCTION SNOWFLAKE.CORE.FRESHNESS ON ()
  SET DATA_QUALITY_NOTIFICATION = FALSE;""")

render_technologies_used([
    {"name": "Tasks", "icon": "schedule", "description": "Serverful task with a Snowflake Scripting body and a return value"},
    {"name": "Dynamic Table suspend / resume", "icon": "pause_circle", "description": "Freeze REPORTING at its last good state"},
    {"name": "DQ notifications", "icon": "notifications", "description": "Database-level setting, per-check toggle, email or webhook"},
])
render_what_you_built([
    "Seven monitors and expectations on `{SCHEMA}`",
    "A root-cause analysis of a real fault",
    "A circuit breaker protecting Nova's REPORTING layer",
    "Alerts on the two checks that matter most",
])

render_real_world_examples([
    {"title": "Protect Nova before month-end", "body": "Operators run finance reports at month-end. A breaker keeps Nova answering from yesterday's good data during a bad sync."},
    {"title": "Slack or Teams for the on-call engineer", "body": "Swap the email integration for a webhook integration so tenant-leak alerts page the right channel."},
    {"title": "Per-tier alert policies", "body": "Enterprise operators get notifications on every invariant; smaller operators on the critical two."},
])
render_references({
    "Quickstarts": [L.QS_STREAMS_TASKS, L.QS_TRAIL],
    "Docs": [L.TASKS, L.TASK_RETURN, L.DT_MONITOR, L.DQ_NOTIFY],
})
