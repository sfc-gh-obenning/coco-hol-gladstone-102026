import streamlit as st

from components import (render_checkpoint, render_execution_context, render_explanation, render_fallback,
                        render_prompt, render_real_world_examples, render_references, render_session_header,
                        render_snowsight_route, render_technologies_used, render_what_why)
from content import links as L
from content import story

render_session_header("Session 3", "Diagnose a broken answer", "9 min", "A root-cause investigation, start to finish, from one prompt")
render_execution_context()
story.chapter(3)
story.ticket("s3")
render_what_why(
    "Give CoCo the complaint the way an operator would phrase it. Let it find which check failed, which rows and batch caused it, and whether the pipeline itself is healthy.",
    "This is the Customer Success escalation Gladstone handles today by hand. CoCo's data-quality skill follows the same evidence trail an engineer would, in minutes, and shows its working.",
)

render_prompt("Prompt 3.1", "Investigate the complaint", """My operator says Nova's numbers are wrong this week. Investigate {FQ_SCHEMA}:
1. Which data quality expectations are failing right now? Use the latest scheduled results, and evaluate now if results are stale.
2. For each failing check, show me sample failing rows and the merge batch (_batch_id / _SYNC_META__MERGE_BATCH) that introduced them.
3. Is the pipeline healthy? Check TSK_BIFROST_MERGE run history and the REPORTING__ dynamic table refresh history.
4. Which Nova metrics in SV_OPERATOR_KPIS are affected, and by roughly how much?
Give me a one-paragraph root cause I could send to the operator.""")
render_snowsight_route([
    "**Governance & security » Data quality**: open incidents across the account. Select your failing check » **Investigate** opens CoCo with the incident loaded.",
    "Open the failing table » **Data Quality** tab » select the check to see value history.",
    "**Transformation » Tasks** » `TSK_BIFROST_MERGE` » **Run history** (suspended? no runs?).",
    "**Transformation » Dynamic tables** » refresh history for each `REPORTING__` table.",
], sql="""SELECT table_name, metric_name, expectation_name, value, measurement_time
FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS
WHERE table_database = 'GLADSTONE_DQ_LAB' AND table_schema = '{SCHEMA}' AND expectation_violated
QUALIFY ROW_NUMBER() OVER (PARTITION BY table_name, expectation_name ORDER BY measurement_time DESC) = 1;""")

render_prompt("Prompt 3.2", "Check the semantic layer", """Compare the two definitions of active members in {FQ_SCHEMA}.SV_OPERATOR_KPIS: the active_members metric (source status) and the verified query vq_active_members (paid in the last 35 days). How big is the gap now, in members and percent? On clean data it was about 6%. If it has moved, which Bronze change explains it?""")
render_snowsight_route([
    "**AI & ML » Cortex Analyst** » `SV_OPERATOR_KPIS` » ask *How many active members do we have?* and compare with the `am.active_members` metric.",
], sql="""SELECT * FROM SEMANTIC_VIEW({FQ_SCHEMA}.SV_OPERATOR_KPIS
  METRICS am.active_members, ms.paid_members_35d);""")

render_checkpoint("You can state your fault in one sentence (which check, which batch, which Nova metric). Compare with your neighbour - each of you got a different fault.")
story.turn(3)
render_explanation("What each fault looks like", """
| If CoCo finds... | It's the... | Notice |
|---|---|---|
| `DUPLICATE_COUNT(member_id)` > 0, batch `B-REPLAY-01` applied twice | Bifrost replay | Active members inflated |
| `FRESHNESS` over 180s, task SUSPENDED | Merge task stalled | REPORTING lag stays **0** - REPORTING isn't behind its source; the **source** stopped. That's why you need both checks. |
| `NEGATIVE_COUNT(amount)` > 0, batch `B-SIGNBUG-01` | Refund sign flip | Today's net revenue drops |
| `REFERENTIAL_INTEGRITY_COUNT` > 0, `BK-GHOST-*` | Orphan attendance | Utilisation can exceed 100% |
| `FOREIGN_OPERATOR_ROWS` > 0, `CUST_NEIGHBOUR` | Tenant leak | Also a **GDPR** incident - see Bonus B2 |
| `ACTIVE_BUT_LEFT` > 0, gap between definitions grows | Status drift | A semantic-layer problem, not a pipeline failure |
""")
render_fallback("""USE SCHEMA {FQ_SCHEMA};
-- failing checks
SELECT table_name, metric_name, expectation_name, value, measurement_time
FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS
WHERE table_database = 'GLADSTONE_DQ_LAB' AND table_schema = '{SCHEMA}' AND expectation_violated
QUALIFY ROW_NUMBER() OVER (PARTITION BY table_name, expectation_name ORDER BY measurement_time DESC) = 1;
-- failing rows (example: duplicates)
SELECT * FROM TABLE(SYSTEM$DATA_METRIC_SCAN(
  REF_ENTITY_NAME => '{FQ_SCHEMA}.MEMBERS__MEMBER',
  METRIC_NAME => 'SNOWFLAKE.CORE.DUPLICATE_COUNT', ARGUMENT_NAME => 'member_id')) LIMIT 20;
-- suspicious batches
SELECT batch_id, table_name, COUNT(*) times_applied FROM _SYNC_META__MERGE_BATCH GROUP BY 1, 2 HAVING COUNT(*) > 1;
SELECT _batch_id, COUNT(*) FROM SYSTEM__PAYMENT WHERE amount < 0 GROUP BY 1;
SELECT operator_id, _batch_id, COUNT(*) FROM MEMBERS__MEMBER GROUP BY 1, 2 ORDER BY 3 DESC;
-- pipeline health
SHOW TASKS LIKE 'TSK_BIFROST_MERGE';
SELECT name, state, scheduled_time, error_message
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(TASK_NAME => 'TSK_BIFROST_MERGE', RESULT_LIMIT => 10))
ORDER BY scheduled_time DESC;
-- Nova impact
SELECT * FROM SEMANTIC_VIEW(SV_OPERATOR_KPIS METRICS am.active_members, ms.paid_members_35d);""")

render_technologies_used([
    {"name": "DQ results views", "icon": "table_view", "description": "SNOWFLAKE.LOCAL expectation status and results history"},
    {"name": "SYSTEM$DATA_METRIC_SCAN", "icon": "search", "description": "Returns the rows that made a system DMF fail"},
    {"name": "Task and DT history", "icon": "history", "description": "TASK_HISTORY and DYNAMIC_TABLE_REFRESH_HISTORY"},
])

render_real_world_examples([
    {"title": "CS escalation in five minutes", "body": "The one-paragraph root cause from Prompt 3.1 is what goes back to the operator - with the batch id and the fix."},
    {"title": "Bifrost incident review", "body": "Batch-level evidence (`_SYNC_META`) shows whether a replay or partial sync hit one operator or many."},
    {"title": "Verified query drift", "body": "Comparing a metric with its verified query catches semantic-layer drift that no row-level check would."},
])
render_references({
    "Quickstarts": [L.QS_DQ, L.QS_COCO_DE],
    "Docs": [L.DQ_DASH, L.DQ_SCAN, L.TASK_HISTORY, L.DT_MONITOR, L.SV_CREATE],
})
