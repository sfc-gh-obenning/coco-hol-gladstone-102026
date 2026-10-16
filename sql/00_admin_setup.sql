-- =============================================================================
-- Gladstone MRM | Data Quality HOL | 00_admin_setup.sql
-- Run ONCE as ACCOUNTADMIN before the lab. Creates only:
--   1 warehouse, 1 resource monitor, 1 email integration, lab roles,
--   1 database (GLADSTONE_DQ_LAB) with ADMIN, DQ_COMMON, ADMIN_OPERATOR_TEMPLATE.
-- Attendee schemas (CUST_<NAME>) are created later by 02_lab_procs.sql -> SETUP_ALL.
-- Teardown: 98_teardown.sql
-- =============================================================================
USE ROLE ACCOUNTADMIN;

-- ---------------------------------------------------------------------------
-- 0. Edit these before running
-- ---------------------------------------------------------------------------
SET LAB_ADMIN_EMAIL = 'replace.me@gladstonesoftware.co.uk';   -- must be a VERIFIED Snowflake user email

-- ---------------------------------------------------------------------------
-- 1. Compute: one shared warehouse + spend cap
-- ---------------------------------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS DQ_LAB_WH
  WAREHOUSE_SIZE    = 'XSMALL'
  AUTO_SUSPEND      = 60
  AUTO_RESUME       = TRUE
  INITIALLY_SUSPENDED = TRUE
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 3          -- multi-cluster (Enterprise+). Set to 1 if the dry run shows no queuing.
  SCALING_POLICY    = 'STANDARD'
  COMMENT = 'Gladstone DQ HOL - shared lab warehouse (DT refresh, tasks, CoCo queries)';

CREATE RESOURCE MONITOR IF NOT EXISTS DQ_LAB_RM
  WITH CREDIT_QUOTA = 20
  FREQUENCY = MONTHLY
  START_TIMESTAMP = IMMEDIATELY
  TRIGGERS ON 75 PERCENT DO NOTIFY
           ON 100 PERCENT DO SUSPEND;
ALTER WAREHOUSE DQ_LAB_WH SET RESOURCE_MONITOR = DQ_LAB_RM;
-- Note: DMFs run on serverless compute and are NOT covered by the resource monitor.
-- Track them in SNOWFLAKE.ACCOUNT_USAGE.DATA_QUALITY_MONITORING_USAGE_HISTORY (see Bonus B1).

-- ---------------------------------------------------------------------------
-- 2. Email integration for data quality notifications
-- ---------------------------------------------------------------------------
CREATE NOTIFICATION INTEGRATION IF NOT EXISTS DQ_LAB_EMAIL_INT
  TYPE = EMAIL
  ENABLED = TRUE
  ALLOWED_RECIPIENTS = ($LAB_ADMIN_EMAIL)
  COMMENT = 'Gladstone DQ HOL - data quality notifications';
-- Add attendee emails later with: ALTER NOTIFICATION INTEGRATION DQ_LAB_EMAIL_INT SET ALLOWED_RECIPIENTS = (...);

-- ---------------------------------------------------------------------------
-- 3. Roles
-- ---------------------------------------------------------------------------
CREATE ROLE IF NOT EXISTS DQ_LAB_ADMIN    COMMENT = 'Gladstone DQ HOL - lab owner / facilitator';
CREATE ROLE IF NOT EXISTS DQ_LAB_ATTENDEE COMMENT = 'Gladstone DQ HOL - shared attendee privileges';
GRANT ROLE DQ_LAB_ATTENDEE TO ROLE DQ_LAB_ADMIN;
GRANT ROLE DQ_LAB_ADMIN    TO ROLE SYSADMIN;

-- Account-level privileges for data quality, tasks and Cortex
GRANT EXECUTE DATA METRIC FUNCTION ON ACCOUNT TO ROLE DQ_LAB_ATTENDEE;
GRANT MANAGE DATA QUALITY          ON ACCOUNT TO ROLE DQ_LAB_ATTENDEE;  -- schema-level DMFs need it on the schema owner
GRANT EXECUTE TASK                 ON ACCOUNT TO ROLE DQ_LAB_ATTENDEE;
GRANT DATABASE ROLE SNOWFLAKE.DATA_METRIC_USER              TO ROLE DQ_LAB_ATTENDEE;
GRANT APPLICATION ROLE SNOWFLAKE.DATA_QUALITY_MONITORING_VIEWER TO ROLE DQ_LAB_ATTENDEE;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER                   TO ROLE DQ_LAB_ATTENDEE;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE             TO ROLE DQ_LAB_ATTENDEE;  -- lineage, task/DT history, access history

-- Facilitator extras: notifications are enabled per DATABASE by its owner
GRANT MANAGE DATA QUALITY ON ACCOUNT TO ROLE DQ_LAB_ADMIN;
GRANT APPLICATION ROLE SNOWFLAKE.DATA_QUALITY_MONITORING_ADMIN TO ROLE DQ_LAB_ADMIN;
GRANT USAGE ON INTEGRATION DQ_LAB_EMAIL_INT TO ROLE DQ_LAB_ADMIN;

-- Warehouse
GRANT USAGE, OPERATE ON WAREHOUSE DQ_LAB_WH TO ROLE DQ_LAB_ATTENDEE;
GRANT OWNERSHIP ON WAREHOUSE DQ_LAB_WH TO ROLE DQ_LAB_ADMIN COPY CURRENT GRANTS;

-- ---------------------------------------------------------------------------
-- 4. Lab database (the only database the lab creates)
-- ---------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS GLADSTONE_DQ_LAB
  COMMENT = 'Gladstone MRM Data Quality HOL - synthetic data only';
CREATE SCHEMA IF NOT EXISTS GLADSTONE_DQ_LAB.ADMIN                   COMMENT = 'Facilitator procs, fleet view';
CREATE SCHEMA IF NOT EXISTS GLADSTONE_DQ_LAB.DQ_COMMON               COMMENT = 'Central custom DMF definitions (define once, attach everywhere)';
CREATE SCHEMA IF NOT EXISTS GLADSTONE_DQ_LAB.ADMIN_OPERATOR_TEMPLATE COMMENT = 'Gold copy of one operator (seed tables only)';

GRANT OWNERSHIP ON DATABASE GLADSTONE_DQ_LAB TO ROLE DQ_LAB_ADMIN COPY CURRENT GRANTS;
GRANT OWNERSHIP ON ALL SCHEMAS IN DATABASE GLADSTONE_DQ_LAB TO ROLE DQ_LAB_ADMIN COPY CURRENT GRANTS;

GRANT USAGE ON DATABASE GLADSTONE_DQ_LAB          TO ROLE DQ_LAB_ATTENDEE;
GRANT USAGE ON SCHEMA GLADSTONE_DQ_LAB.DQ_COMMON  TO ROLE DQ_LAB_ATTENDEE;
GRANT USAGE ON FUTURE FUNCTIONS IN SCHEMA GLADSTONE_DQ_LAB.DQ_COMMON TO ROLE DQ_LAB_ATTENDEE;
GRANT USAGE ON FUTURE DATA METRIC FUNCTIONS IN SCHEMA GLADSTONE_DQ_LAB.DQ_COMMON TO ROLE DQ_LAB_ATTENDEE;

-- ---------------------------------------------------------------------------
-- 5. Database-level data quality notifications (owner = DQ_LAB_ADMIN)
--    Notifications are DATABASE-scoped: one setting covers every CUST_ schema.
--    Attendees control their own checks with
--    ALTER TABLE ... MODIFY DATA METRIC FUNCTION ... SET DATA_QUALITY_NOTIFICATION = TRUE|FALSE
-- ---------------------------------------------------------------------------
USE ROLE DQ_LAB_ADMIN;
ALTER DATABASE GLADSTONE_DQ_LAB SET DATA_QUALITY_MONITORING_SETTINGS = $$
notification:
  enabled: TRUE
  integrations:
    - DQ_LAB_EMAIL_INT
  cooldown_hours: 1
  metadata_included: TRUE
$$;

-- ---------------------------------------------------------------------------
-- 6. Pre-flight checks (record results on the "Azure availability" page)
-- ---------------------------------------------------------------------------
USE ROLE ACCOUNTADMIN;
SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), SYSTEM$GET_SNOWFLAKE_PLATFORM_INFO();
SHOW DATA METRIC FUNCTIONS IN SCHEMA SNOWFLAKE.CORE;          -- confirm DUPLICATE_COUNT, FRESHNESS, ROW_COUNT, REFERENTIAL_INTEGRITY_COUNT, newer DMFs
SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT; -- UK residency (Bonus B2 GDPR)

-- Next: run 01_build_template.sql, then 02_lab_procs.sql, then
--   CALL GLADSTONE_DQ_LAB.ADMIN.SETUP_ALL(PARSE_JSON('[{"user":"NJOHANSEN","name":"NIELS"}]'));
