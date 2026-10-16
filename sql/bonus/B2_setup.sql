-- =============================================================================
-- Gladstone MRM | Bonus B2 - Data governance + GDPR | B2_setup.sql (ADMIN, run once)
-- Synthetic data only. Not legal advice: Gladstone's DPO decides controller/processor
-- roles, lawful bases and retention periods.
-- Teardown: B2_teardown.sql (standalone) or 98_teardown.sql (everything)
-- =============================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DQ_LAB_WH;

-- ---------------------------------------------------------------------------
-- 1. Governance schema: central GDPR tags + request register (define once, use for every operator)
-- ---------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS GLADSTONE_DQ_LAB.GOVERNANCE COMMENT = 'Bonus B2: governance tags, GDPR register';
GRANT OWNERSHIP ON SCHEMA GLADSTONE_DQ_LAB.GOVERNANCE TO ROLE DQ_LAB_ADMIN COPY CURRENT GRANTS;

-- Roles used to prove masking and row access (granted to attendee USERS, not to roles,
-- so they are only active when the attendee explicitly switches to them)
CREATE ROLE IF NOT EXISTS DQ_LAB_PII_READER      COMMENT = 'Bonus B2: may see member personal data';
CREATE ROLE IF NOT EXISTS DQ_LAB_OPERATOR_VIEWER COMMENT = 'Bonus B2: operator staff, no personal data';
GRANT ROLE DQ_LAB_PII_READER      TO ROLE DQ_LAB_ADMIN;
GRANT ROLE DQ_LAB_OPERATOR_VIEWER TO ROLE DQ_LAB_ADMIN;
GRANT USAGE ON DATABASE GLADSTONE_DQ_LAB TO ROLE DQ_LAB_PII_READER;
GRANT USAGE ON DATABASE GLADSTONE_DQ_LAB TO ROLE DQ_LAB_OPERATOR_VIEWER;
GRANT USAGE ON WAREHOUSE DQ_LAB_WH TO ROLE DQ_LAB_PII_READER;
GRANT USAGE ON WAREHOUSE DQ_LAB_WH TO ROLE DQ_LAB_OPERATOR_VIEWER;

-- Classification (SYSTEM$CLASSIFY) and tagging
GRANT DATABASE ROLE SNOWFLAKE.CLASSIFICATION_ADMIN TO ROLE DQ_LAB_ATTENDEE;
GRANT APPLY TAG ON ACCOUNT TO ROLE DQ_LAB_ATTENDEE;             -- write classification tags
GRANT APPLY MASKING POLICY ON ACCOUNT TO ROLE DQ_LAB_ATTENDEE;    -- tag-based masking (ALTER TAG ... SET MASKING POLICY)
GRANT APPLY ROW ACCESS POLICY ON ACCOUNT TO ROLE DQ_LAB_ATTENDEE; -- row access policies on their own tables
-- These three are account-wide privileges: fine for a time-boxed lab, but in production give them to a
-- central governance role only, and let operators inherit policies via tags. B2_teardown.sql revokes them.

USE ROLE DQ_LAB_ADMIN;
USE SCHEMA GLADSTONE_DQ_LAB.GOVERNANCE;

CREATE TAG IF NOT EXISTS GDPR_CATEGORY
  ALLOWED_VALUES 'identifier', 'contact', 'financial', 'special_category', 'behavioural', 'none'
  COMMENT = 'UK/EU GDPR data category of this column';
CREATE TAG IF NOT EXISTS LAWFUL_BASIS
  ALLOWED_VALUES 'contract', 'legal_obligation', 'consent', 'legitimate_interest', 'explicit_consent'
  COMMENT = 'Lawful basis recorded for processing (confirm with DPO)';
CREATE TAG IF NOT EXISTS RETENTION_DAYS COMMENT = 'Agreed retention period in days after membership ends';

GRANT USAGE ON SCHEMA GLADSTONE_DQ_LAB.GOVERNANCE TO ROLE DQ_LAB_ATTENDEE;
GRANT APPLY ON TAG GDPR_CATEGORY  TO ROLE DQ_LAB_ATTENDEE;
GRANT APPLY ON TAG LAWFUL_BASIS   TO ROLE DQ_LAB_ATTENDEE;
GRANT APPLY ON TAG RETENTION_DAYS TO ROLE DQ_LAB_ATTENDEE;

-- Central GDPR request register (one row per subject request, any operator)
CREATE TABLE IF NOT EXISTS GDPR_REQUESTS (
  request_id     VARCHAR DEFAULT UUID_STRING(),
  operator_id    VARCHAR,
  member_id      VARCHAR,
  request_type   VARCHAR,          -- SAR / ERASURE / RECTIFICATION
  received_at    TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
  due_at         TIMESTAMP_LTZ DEFAULT DATEADD(month, 1, CURRENT_TIMESTAMP()),   -- UK GDPR: one month (extendable)
  completed_at   TIMESTAMP_LTZ,
  completed_by   VARCHAR,
  evidence       VARIANT
) COMMENT = 'Bonus B2: data subject request register (synthetic)';
GRANT SELECT, INSERT, UPDATE ON TABLE GDPR_REQUESTS TO ROLE DQ_LAB_ATTENDEE;

-- Central DMF: proves an erasure actually reached a table (expect 0)
USE SCHEMA GLADSTONE_DQ_LAB.DQ_COMMON;
CREATE OR REPLACE DATA METRIC FUNCTION ERASED_MEMBERS_STILL_PRESENT(
    t   TABLE(member_id VARCHAR),
    req TABLE(member_id VARCHAR, request_type VARCHAR, completed_at TIMESTAMP_LTZ))
RETURNS NUMBER
COMMENT = 'Rows still holding a member_id whose erasure request is completed. Expect 0.'
AS $$
  SELECT COUNT(*) FROM t
  WHERE t.member_id IN (SELECT member_id FROM req WHERE request_type = 'ERASURE' AND completed_at IS NOT NULL)
$$;
GRANT USAGE ON ALL DATA METRIC FUNCTIONS IN SCHEMA GLADSTONE_DQ_LAB.DQ_COMMON TO ROLE DQ_LAB_ATTENDEE;

-- ---------------------------------------------------------------------------
-- 2. Give each attendee USER the two test roles (role switching proves masking / row access)
-- ---------------------------------------------------------------------------
USE ROLE ACCOUNTADMIN;
EXECUTE IMMEDIATE $$
DECLARE
  c1 CURSOR FOR SELECT user_name FROM GLADSTONE_DQ_LAB.ADMIN.ATTENDEES WHERE user_name IS NOT NULL AND user_name <> '';
BEGIN
  FOR r IN c1 DO
    EXECUTE IMMEDIATE 'GRANT ROLE DQ_LAB_PII_READER TO USER "' || r.user_name || '"';
    EXECUTE IMMEDIATE 'GRANT ROLE DQ_LAB_OPERATOR_VIEWER TO USER "' || r.user_name || '"';
  END FOR;
  RETURN 'granted';
END;
$$;

-- ---------------------------------------------------------------------------
-- 3. Standalone teardown helper (also called by 98_teardown.sql)
--    Removes B2 artefacts from every CUST_ schema without touching the core lab.
-- ---------------------------------------------------------------------------
USE ROLE DQ_LAB_ADMIN;
CREATE OR REPLACE PROCEDURE GLADSTONE_DQ_LAB.ADMIN.B2_UNSET_ALL()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
  n NUMBER DEFAULT 0;
  sch VARCHAR;
  rs RESULTSET;
  c1 CURSOR FOR SELECT schema_name FROM GLADSTONE_DQ_LAB.INFORMATION_SCHEMA.SCHEMATA
                WHERE schema_name LIKE 'CUST\\_%' ESCAPE '\\' AND schema_name NOT LIKE '%\\_DCM' ESCAPE '\\';
BEGIN
  FOR r IN c1 DO
    sch := 'GLADSTONE_DQ_LAB.' || r.schema_name;
    -- policies attached to member/payment tables (row access, column masking, tag-based masking)
    rs := (SELECT policy_kind, policy_db || '.' || policy_schema || '.' || policy_name AS pol,
                  ref_entity_name, ref_column_name, tag_database, tag_schema, tag_name
           FROM TABLE(GLADSTONE_DQ_LAB.INFORMATION_SCHEMA.POLICY_REFERENCES(
                  REF_ENTITY_NAME => :sch || '.MEMBERS__MEMBER', REF_ENTITY_DOMAIN => 'table')));
    FOR p IN rs DO
      IF (p.policy_kind = 'ROW_ACCESS_POLICY') THEN
        EXECUTE IMMEDIATE 'ALTER TABLE ' || :sch || '.MEMBERS__MEMBER DROP ROW ACCESS POLICY ' || p.pol;
      ELSEIF (p.policy_kind = 'MASKING_POLICY' AND p.tag_name IS NOT NULL) THEN
        EXECUTE IMMEDIATE 'ALTER TAG ' || p.tag_database || '.' || p.tag_schema || '.' || p.tag_name ||
                          ' UNSET MASKING POLICY ' || p.pol;
      ELSEIF (p.policy_kind = 'MASKING_POLICY') THEN
        EXECUTE IMMEDIATE 'ALTER TABLE ' || :sch || '.MEMBERS__MEMBER MODIFY COLUMN ' || p.ref_column_name || ' UNSET MASKING POLICY';
      ELSEIF (p.policy_kind = 'PROJECTION_POLICY') THEN
        EXECUTE IMMEDIATE 'ALTER TABLE ' || :sch || '.MEMBERS__MEMBER MODIFY COLUMN ' || p.ref_column_name || ' UNSET PROJECTION POLICY';
      END IF;
    END FOR;
    -- erasure-proof DMFs (two-table, reference GOVERNANCE.GDPR_REQUESTS)
    FOR i IN 0 TO 3 DO
      LET tbl VARCHAR := DECODE(:i, 0, 'MEMBERS__MEMBER', 1, 'SYSTEM__PAYMENT', 2, 'SYSTEM__BOOKING', 'SYSTEM__ATTENDANCE');
      BEGIN
        EXECUTE IMMEDIATE 'ALTER TABLE ' || :sch || '.' || :tbl || ' DROP DATA METRIC FUNCTION ' ||
          'GLADSTONE_DQ_LAB.DQ_COMMON.ERASED_MEMBERS_STILL_PRESENT ON (member_id, ' ||
          'TABLE(GLADSTONE_DQ_LAB.GOVERNANCE.GDPR_REQUESTS(member_id, request_type, completed_at)))';
      EXCEPTION WHEN OTHER THEN NULL;   -- not attached on this table
      END;
    END FOR;
    -- retention back to default
    EXECUTE IMMEDIATE 'ALTER TABLE ' || :sch || '.MEMBERS__MEMBER UNSET DATA_RETENTION_TIME_IN_DAYS';
    n := n + 1;
  END FOR;
  DROP SCHEMA IF EXISTS GLADSTONE_DQ_LAB.GOVERNANCE;   -- tags, GDPR_REQUESTS
  RETURN 'Bonus B2 removed from ' || n || ' operator schema(s)';
END;
$$;
