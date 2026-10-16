-- =============================================================================
-- Gladstone MRM | Data Quality HOL | answer_key_core.sql
-- What CoCo is expected to generate in Sessions 2-4 (facilitator reference and
-- "Behind? run this" fallback). Replace CUST_NIELS with the attendee's schema.
-- Run as the attendee role DQ_LAB_<NAME>.
-- =============================================================================
USE WAREHOUSE DQ_LAB_WH;
USE SCHEMA GLADSTONE_DQ_LAB.CUST_NIELS;

-- ---------------------------------------------------------------------------
-- Session 2.1  Monitors (system DMFs) - schedule every 5 minutes for the lab
-- (production: TRIGGER_ON_CHANGES on Bronze, or align to the DT target lag)
-- ---------------------------------------------------------------------------
ALTER TABLE MEMBERS__MEMBER     SET DATA_METRIC_SCHEDULE = '5 MINUTE';
ALTER TABLE SYSTEM__PAYMENT     SET DATA_METRIC_SCHEDULE = '5 MINUTE';
ALTER TABLE SYSTEM__ATTENDANCE  SET DATA_METRIC_SCHEDULE = '5 MINUTE';
ALTER DYNAMIC TABLE REPORTING__DAILY_REVENUE SET DATA_METRIC_SCHEDULE = '5 MINUTE';

-- Volume + freshness with anomaly detection (needs ~2 weeks of history to start flagging;
-- shows TRAINING_IN_PROGRESS during the lab - this is the long-term safety net).
ALTER TABLE SYSTEM__PAYMENT ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.ROW_COUNT ON () ANOMALY_DETECTION = TRUE;

-- ---------------------------------------------------------------------------
-- Session 2.2  Expectations = the invariants that must always hold (fire today)
-- ---------------------------------------------------------------------------
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
  ON (booking_id, TABLE(GLADSTONE_DQ_LAB.CUST_NIELS.SYSTEM__BOOKING(booking_id)))
  EXPECTATION no_orphan_checkins (VALUE = 0);
ALTER DYNAMIC TABLE REPORTING__DAILY_REVENUE ADD DATA METRIC FUNCTION GLADSTONE_DQ_LAB.DQ_COMMON.REPORTING_LAG_SECONDS
  ON (last_loaded_at, TABLE(GLADSTONE_DQ_LAB.CUST_NIELS.SYSTEM__PAYMENT(_loaded_at)))
  EXPECTATION reporting_within_5min (VALUE < 300);

-- Checkpoint: what is attached?
SELECT metric_name, ref_arguments, schedule, schedule_status
FROM TABLE(INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES(
  REF_ENTITY_NAME => 'GLADSTONE_DQ_LAB.CUST_NIELS.MEMBERS__MEMBER', REF_ENTITY_DOMAIN => 'TABLE'));

-- Run every expectation now (no waiting for the schedule) - single-table, non-grouped expectations
SELECT * FROM TABLE(SYSTEM$EVALUATE_DATA_QUALITY_EXPECTATIONS(REF_ENTITY_NAME => 'GLADSTONE_DQ_LAB.CUST_NIELS.MEMBERS__MEMBER'));
SELECT * FROM TABLE(SYSTEM$EVALUATE_DATA_QUALITY_EXPECTATIONS(REF_ENTITY_NAME => 'GLADSTONE_DQ_LAB.CUST_NIELS.SYSTEM__PAYMENT'));

-- ---------------------------------------------------------------------------
-- Session 3  Diagnose (what CoCo's root-cause workflow queries)
-- ---------------------------------------------------------------------------
-- Latest failing expectations for my operator
SELECT table_name, metric_name, expectation_name, value, measurement_time
FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS
WHERE table_database = 'GLADSTONE_DQ_LAB' AND table_schema = 'CUST_NIELS' AND expectation_violated
QUALIFY ROW_NUMBER() OVER (PARTITION BY table_name, expectation_name ORDER BY measurement_time DESC) = 1;

-- Which rows? (failing-row drill down for a system DMF)
SELECT * FROM TABLE(SYSTEM$DATA_METRIC_SCAN(
  REF_ENTITY_NAME => 'GLADSTONE_DQ_LAB.CUST_NIELS.MEMBERS__MEMBER',
  METRIC_NAME     => 'SNOWFLAKE.CORE.DUPLICATE_COUNT',
  ARGUMENT_NAME   => 'member_id')) LIMIT 20;

-- Which batch caused it?
SELECT batch_id, table_name, COUNT(*) AS times_applied, MIN(loaded_at), MAX(loaded_at)
FROM _SYNC_META__MERGE_BATCH GROUP BY 1, 2 HAVING COUNT(*) > 1;
SELECT _batch_id, COUNT(*) FROM SYSTEM__PAYMENT WHERE amount < 0 GROUP BY 1;

-- Is the pipeline running?
SELECT name, state, scheduled_time, completed_time, error_message
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(TASK_NAME => 'TSK_BIFROST_MERGE', RESULT_LIMIT => 10))
ORDER BY scheduled_time DESC;
SHOW TASKS LIKE 'TSK_BIFROST_MERGE';
SELECT name, state, refresh_action, refresh_trigger, data_timestamp, state_message
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(NAME_PREFIX => 'GLADSTONE_DQ_LAB.CUST_NIELS.'))
ORDER BY data_timestamp DESC LIMIT 20;

-- Nova's two answers to "how many active members?"
SELECT * FROM SEMANTIC_VIEW(SV_OPERATOR_KPIS METRICS am.active_members, ms.paid_members_35d);

-- ---------------------------------------------------------------------------
-- Session 4  Contain + alert
-- ---------------------------------------------------------------------------
-- Circuit breaker: suspend REPORTING while any Bronze invariant is violated; resume when clean.
CREATE OR REPLACE TASK TSK_DQ_CIRCUIT_BREAKER
  WAREHOUSE = DQ_LAB_WH SCHEDULE = '1 MINUTE'
AS
EXECUTE IMMEDIATE $$
DECLARE
  bad NUMBER;
  msg VARCHAR;
BEGIN
  SELECT COUNT(*) INTO :bad FROM (
    SELECT expectation_violated
    FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS
    WHERE table_database = 'GLADSTONE_DQ_LAB' AND table_schema = 'CUST_NIELS'
      AND table_name IN ('MEMBERS__MEMBER', 'SYSTEM__PAYMENT', 'SYSTEM__ATTENDANCE')
    QUALIFY ROW_NUMBER() OVER (PARTITION BY table_name, expectation_name ORDER BY measurement_time DESC) = 1)
  WHERE expectation_violated;
  IF (bad > 0) THEN
    ALTER DYNAMIC TABLE GLADSTONE_DQ_LAB.CUST_NIELS.REPORTING__ACTIVE_MEMBERS SUSPEND;
    ALTER DYNAMIC TABLE GLADSTONE_DQ_LAB.CUST_NIELS.REPORTING__DAILY_REVENUE SUSPEND;
    -- SYSTEM$SET_RETURN_VALUE needs a plain variable or literal, not an expression
    msg := 'OPEN: ' || :bad || ' failing Bronze check(s) - REPORTING frozen at last good state';
    CALL SYSTEM$SET_RETURN_VALUE(:msg);
    RETURN 'OPEN';
  ELSE
    ALTER DYNAMIC TABLE GLADSTONE_DQ_LAB.CUST_NIELS.REPORTING__ACTIVE_MEMBERS RESUME;
    ALTER DYNAMIC TABLE GLADSTONE_DQ_LAB.CUST_NIELS.REPORTING__DAILY_REVENUE RESUME;
    CALL SYSTEM$SET_RETURN_VALUE('CLOSED: Bronze clean');
    RETURN 'CLOSED';
  END IF;
END;
$$;
ALTER TASK TSK_DQ_CIRCUIT_BREAKER RESUME;

-- Notifications are enabled for the whole lab database by the admin (00_admin_setup.sql).
-- Each operator chooses which checks notify:
ALTER TABLE MEMBERS__MEMBER MODIFY DATA METRIC FUNCTION SNOWFLAKE.CORE.DUPLICATE_COUNT ON (member_id)
  SET DATA_QUALITY_NOTIFICATION = TRUE;

-- Fix (example for the Bifrost replay): remove the replayed batch, circuit breaker closes, DTs resume
DELETE FROM MEMBERS__MEMBER WHERE _batch_id = 'B-REPLAY-01';
