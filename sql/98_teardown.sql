-- =============================================================================
-- Gladstone MRM | Data Quality HOL | 98_teardown.sql
-- Removes EVERYTHING the lab created (core + bonus labs). Run as ACCOUNTADMIN.
-- Safe to re-run: every statement is IF EXISTS / guarded.
-- Each bonus also has a standalone teardown in sql/bonus/ if you only want to remove that bonus.
-- =============================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DQ_LAB_WH;

-- ---------------------------------------------------------------------------
-- 1. Bonus labs first (only matters if they were run; each call is skipped if the proc is absent)
-- ---------------------------------------------------------------------------
EXECUTE IMMEDIATE $$
BEGIN
  IF (EXISTS (SELECT 1 FROM GLADSTONE_DQ_LAB.INFORMATION_SCHEMA.PROCEDURES
              WHERE procedure_schema = 'ADMIN' AND procedure_name = 'B3_TEARDOWN_ALL')) THEN
    CALL GLADSTONE_DQ_LAB.ADMIN.B3_TEARDOWN_ALL();
  END IF;
  IF (EXISTS (SELECT 1 FROM GLADSTONE_DQ_LAB.INFORMATION_SCHEMA.PROCEDURES
              WHERE procedure_schema = 'ADMIN' AND procedure_name = 'B2_UNSET_ALL')) THEN
    CALL GLADSTONE_DQ_LAB.ADMIN.B2_UNSET_ALL();
  END IF;
  IF (EXISTS (SELECT 1 FROM GLADSTONE_DQ_LAB.INFORMATION_SCHEMA.PROCEDURES
              WHERE procedure_schema = 'ADMIN' AND procedure_name = 'B1_TEARDOWN')) THEN
    CALL GLADSTONE_DQ_LAB.ADMIN.B1_TEARDOWN();
  END IF;
  RETURN 'bonus cleanup done';
END;
$$;
DROP RESOURCE MONITOR IF EXISTS DQ_LAB_RM_DEMO;

-- ---------------------------------------------------------------------------
-- 2. Stop all lab compute (tasks, dynamic tables, notifications)
-- ---------------------------------------------------------------------------
CALL GLADSTONE_DQ_LAB.ADMIN.SUSPEND_ALL();

-- Put attendees' original DEFAULT_ROLE / DEFAULT_WAREHOUSE back (recorded at setup).
-- Must run before the database is dropped. Skipped if the proc is absent (older install).
EXECUTE IMMEDIATE $$
BEGIN
  IF (EXISTS (SELECT 1 FROM GLADSTONE_DQ_LAB.INFORMATION_SCHEMA.PROCEDURES
              WHERE procedure_schema = 'ADMIN' AND procedure_name = 'RESTORE_USER_DEFAULTS')) THEN
    CALL GLADSTONE_DQ_LAB.ADMIN.RESTORE_USER_DEFAULTS();
  END IF;
  RETURN 'user defaults restored';
END;
$$;

-- ---------------------------------------------------------------------------
-- 3. Drop the lab database: template, every CUST_* operator schema, DQ_COMMON DMFs,
--    (including CUST_SPARE* walk-in schemas), semantic views, dynamic tables, tasks,
--    roster/claims tables, FINOPS/GOVERNANCE bonus schemas
-- ---------------------------------------------------------------------------
DROP DATABASE IF EXISTS GLADSTONE_DQ_LAB;

-- ---------------------------------------------------------------------------
-- 4. Account-level objects
-- ---------------------------------------------------------------------------
USE WAREHOUSE COMPUTE_WH;   -- any warehouse other than DQ_LAB_WH; change if you don't have COMPUTE_WH
DROP WAREHOUSE IF EXISTS DQ_LAB_WH;
DROP RESOURCE MONITOR IF EXISTS DQ_LAB_RM;
DROP NOTIFICATION INTEGRATION IF EXISTS DQ_LAB_EMAIL_INT;

-- ---------------------------------------------------------------------------
-- 5. Roles: every role named DQ_LAB_* (admin, attendee, per-operator, DQ_LAB_SPARE*, bonus roles)
-- ---------------------------------------------------------------------------
SHOW ROLES LIKE 'DQ_LAB_%';
EXECUTE IMMEDIATE $$
DECLARE
  n NUMBER DEFAULT 0;
  c1 CURSOR FOR SELECT "name" AS role_name FROM TABLE(RESULT_SCAN(LAST_QUERY_ID(-1)));
BEGIN
  FOR r IN c1 DO
    EXECUTE IMMEDIATE 'DROP ROLE IF EXISTS "' || r.role_name || '"';
    n := n + 1;
  END FOR;
  RETURN n || ' role(s) dropped';
END;
$$;

-- ---------------------------------------------------------------------------
-- 6. Verify: every statement below should return zero rows
-- ---------------------------------------------------------------------------
SHOW DATABASES LIKE 'GLADSTONE_DQ_LAB';
SHOW WAREHOUSES LIKE 'DQ_LAB_%';
SHOW RESOURCE MONITORS LIKE 'DQ_LAB_%';
SHOW INTEGRATIONS LIKE 'DQ_LAB_%';
SHOW ROLES LIKE 'DQ_LAB_%';

-- Note: dropped data stays in Time Travel / Fail-safe for the retention period, then is purged.
-- The lab data is synthetic. This is the same retention behaviour Bonus B2 (GDPR) discusses.
-- Attendee defaults were restored in step 2. Users bound with set_defaults = false were never changed.
-- Temporary walk-in users (if the admin created any) are NOT dropped here: DROP USER <u>; by hand.
