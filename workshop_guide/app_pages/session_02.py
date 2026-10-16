import streamlit as st

from components import (render_checkpoint, render_execution_context, render_explanation, render_fallback,
                        render_key_concepts, render_prompt, render_real_world_examples, render_references,
                        render_session_header, render_snowsight_route, render_technologies_used, render_what_why)
from content import links as L
from content import story

render_session_header("Session 2", "Put monitors on it", "7 min", "Data metric functions and expectations on Bronze and REPORTING")
render_execution_context()
story.chapter(2)
render_what_why(
    "Attach Snowflake data metric functions (DMFs) to your Bronze tables and a REPORTING Dynamic Table, and turn each invariant into an **expectation** that passes or fails.",
    "These run serverless inside Snowflake, next to the data, on a schedule - no extra warehouse, no external tool. Defined once, the same checks attach to every operator database.",
)

render_prompt("Prompt 2.1", "Monitor freshness, volume and invariants", """Set up data quality monitoring in {FQ_SCHEMA}. Run every check every 5 minutes.
On MEMBERS__MEMBER:
- no duplicate member_id (expect 0)
- no rows from another operator: use GLADSTONE_DQ_LAB.DQ_COMMON.FOREIGN_OPERATOR_ROWS on operator_id (expect 0)
- no ACTIVE members with a leave date: use GLADSTONE_DQ_LAB.DQ_COMMON.ACTIVE_BUT_LEFT on (status, left_on) (expect 0)
On SYSTEM__PAYMENT:
- no negative amounts (expect 0)
- table updated in the last 3 minutes (FRESHNESS on the table itself, expect under 180 seconds)
- row count with anomaly detection turned on
On SYSTEM__ATTENDANCE:
- every booking_id exists in SYSTEM__BOOKING (referential integrity, expect 0 orphans)
Give each expectation a clear name. Show me the SQL before running it.""")
render_snowsight_route([
    "Open **Catalog » Database Explorer** » `{SCHEMA}` » `MEMBERS__MEMBER` » **Data Quality** tab.",
    "Select **Monitor** » set the schedule to every 5 minutes.",
    "Add **Duplicate count** on `member_id`; add the expectation *Value = 0*.",
    "Add **Custom DMF** `DQ_COMMON.FOREIGN_OPERATOR_ROWS` on `operator_id` with *Value = 0*.",
    "Repeat on `SYSTEM__PAYMENT` (Negative count, Freshness, Row count) and `SYSTEM__ATTENDANCE` (Referential integrity to `SYSTEM__BOOKING.booking_id`).",
    "The table's Data Quality tab lists each check, its schedule, last value and pass/fail.",
])

render_prompt("Prompt 2.2", "Monitor the REPORTING layer and check now", """On dynamic table {FQ_SCHEMA}.REPORTING__DAILY_REVENUE, add an expectation that it trails its Bronze source SYSTEM__PAYMENT by less than 5 minutes: use GLADSTONE_DQ_LAB.DQ_COMMON.REPORTING_LAG_SECONDS on (last_loaded_at) with SYSTEM__PAYMENT(_loaded_at) as the second table, and run it every 5 minutes.
Then evaluate every expectation in my schema right now (do not wait for the schedule) and show a table of check, value and pass/fail.""")
render_snowsight_route([
    "Open `REPORTING__DAILY_REVENUE` » **Data Quality** » add custom DMF `DQ_COMMON.REPORTING_LAG_SECONDS`.",
    "Run the worksheet query below to evaluate expectations immediately.",
], sql="""SELECT * FROM TABLE(SYSTEM$EVALUATE_DATA_QUALITY_EXPECTATIONS(
  REF_ENTITY_NAME => '{FQ_SCHEMA}.MEMBERS__MEMBER'));
SELECT * FROM TABLE(SYSTEM$EVALUATE_DATA_QUALITY_EXPECTATIONS(
  REF_ENTITY_NAME => '{FQ_SCHEMA}.SYSTEM__PAYMENT'));""")

render_checkpoint("All **7 expectations pass** on clean data. FRESHNESS should be under 180 seconds because the merge task runs every minute. Tell the facilitator you're ready - faults go in next.")
story.turn(2)
render_explanation("Why expectations, and not only anomaly detection?", """
**Anomaly detection** (on ROW_COUNT and FRESHNESS) learns normal behaviour and needs **at least two weeks** of history before it
flags anything - during this lab it shows `TRAINING_IN_PROGRESS`. Turn it on now so it's working in two weeks.

**Expectations** encode rules that must **always** hold (no duplicates, no foreign operator rows, no negative payments) and
fail on the first bad run. Use both: expectations for invariants, anomaly detection for "this looks unusual".
""")
render_fallback("""USE SCHEMA {FQ_SCHEMA};
ALTER TABLE MEMBERS__MEMBER    SET DATA_METRIC_SCHEDULE = '5 MINUTE';
ALTER TABLE SYSTEM__PAYMENT    SET DATA_METRIC_SCHEDULE = '5 MINUTE';
ALTER TABLE SYSTEM__ATTENDANCE SET DATA_METRIC_SCHEDULE = '5 MINUTE';
ALTER DYNAMIC TABLE REPORTING__DAILY_REVENUE SET DATA_METRIC_SCHEDULE = '5 MINUTE';
ALTER TABLE SYSTEM__PAYMENT ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.ROW_COUNT ON () ANOMALY_DETECTION = TRUE;
ALTER TABLE MEMBERS__MEMBER ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.DUPLICATE_COUNT ON (member_id)
  EXPECTATION no_duplicate_members (VALUE = 0);
ALTER TABLE MEMBERS__MEMBER ADD DATA METRIC FUNCTION GLADSTONE_DQ_LAB.DQ_COMMON.FOREIGN_OPERATOR_ROWS ON (operator_id)
  EXPECTATION no_other_operator_rows (VALUE = 0);
ALTER TABLE MEMBERS__MEMBER ADD DATA METRIC FUNCTION GLADSTONE_DQ_LAB.DQ_COMMON.ACTIVE_BUT_LEFT ON (status, left_on)
  EXPECTATION no_active_leavers (VALUE = 0);
ALTER TABLE SYSTEM__PAYMENT ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.NEGATIVE_COUNT ON (amount)
  EXPECTATION no_negative_amounts (VALUE = 0);
ALTER TABLE SYSTEM__PAYMENT ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.FRESHNESS ON ()
  EXPECTATION payments_fresh_3min (VALUE < 180);
ALTER TABLE SYSTEM__ATTENDANCE ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.REFERENTIAL_INTEGRITY_COUNT
  ON (booking_id, TABLE({FQ_SCHEMA}.SYSTEM__BOOKING(booking_id)))
  EXPECTATION no_orphan_checkins (VALUE = 0);
ALTER DYNAMIC TABLE REPORTING__DAILY_REVENUE ADD DATA METRIC FUNCTION GLADSTONE_DQ_LAB.DQ_COMMON.REPORTING_LAG_SECONDS
  ON (last_loaded_at, TABLE({FQ_SCHEMA}.SYSTEM__PAYMENT(_loaded_at)))
  EXPECTATION reporting_within_5min (VALUE < 300);""")

render_technologies_used([
    {"name": "System DMFs", "icon": "fact_check", "description": "DUPLICATE_COUNT, NEGATIVE_COUNT, FRESHNESS, ROW_COUNT, REFERENTIAL_INTEGRITY_COUNT"},
    {"name": "Custom DMFs", "icon": "function", "description": "Central DQ_COMMON checks: foreign operator rows, active-but-left, Bronze-to-REPORTING lag"},
    {"name": "Expectations", "icon": "rule", "description": "Pass/fail rules on any DMF; results in SNOWFLAKE.LOCAL views"},
])
render_key_concepts([
    {"term": "Data metric function (DMF)", "definition": "A function attached to a table, view or dynamic table that returns one number on a schedule. Runs on serverless compute."},
    {"term": "Expectation", "definition": "A boolean rule on a DMF's value, e.g. `VALUE = 0`. A violation is recorded in `SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS` and can trigger a notification."},
    {"term": "Multi-table DMF", "definition": "A DMF with two table arguments (REFERENTIAL_INTEGRITY_COUNT, REPORTING_LAG_SECONDS) - compares Bronze with REPORTING, or a child with its parent."},
])

render_real_world_examples([
    {"title": "Replacing homegrown DATA_MONITORING_WH checks", "body": "Checks scheduled on a warehouse become serverless DMFs with history, pass/fail and notifications built in."},
    {"title": "Cross-tenant leak detection", "body": "`FOREIGN_OPERATOR_ROWS` on every operator database turns a GDPR incident into a 5-minute alert."},
    {"title": "Bifrost sync SLAs", "body": "FRESHNESS and Bronze-to-REPORTING lag per operator give CS and engineering one shared definition of \"late\"."},
    {"title": "Payments integrity", "body": "NEGATIVE_COUNT and referential integrity catch sign bugs and partial syncs before revenue dashboards move."},
])
render_references({
    "Quickstarts": [L.QS_DQ, L.QS_DQM],
    "Docs": [L.DQ_SQL, L.DQ_EXPECT, L.DQ_CUSTOM, L.DQ_RI, L.DQ_ANOMALY, L.DQ_SCHEMA],
})
