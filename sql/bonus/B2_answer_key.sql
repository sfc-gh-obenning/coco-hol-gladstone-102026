-- =============================================================================
-- Gladstone MRM | Bonus B2 - Data governance + GDPR | B2_answer_key.sql (attendee role)
-- Replace CUST_NIELS with your operator. Synthetic data only. Not legal advice.
-- =============================================================================
USE WAREHOUSE DQ_LAB_WH;
USE SCHEMA GLADSTONE_DQ_LAB.CUST_NIELS;

-- =========================== PART A: governance ==============================
-- A1. Classify the member table (suggestions only - nothing is tagged yet)
CALL SYSTEM$CLASSIFY('GLADSTONE_DQ_LAB.CUST_NIELS.MEMBERS__MEMBER', NULL);

-- A2. Tag-based masking: one masking policy on a tag protects every column that carries the tag
CREATE TAG IF NOT EXISTS PII_TYPE ALLOWED_VALUES 'email', 'phone', 'dob', 'name', 'postcode', 'health'
  COMMENT = 'Personal data type (drives masking)';

CREATE OR REPLACE MASKING POLICY MASK_PII_STRING AS (val STRING) RETURNS STRING ->
  CASE WHEN IS_ROLE_IN_SESSION('DQ_LAB_PII_READER') THEN val
       WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('GLADSTONE_DQ_LAB.CUST_NIELS.PII_TYPE') = 'email'
         THEN REGEXP_REPLACE(val, '^[^@]+', '*****')
       ELSE '*** MASKED ***' END;
CREATE OR REPLACE MASKING POLICY MASK_PII_DATE AS (val DATE) RETURNS DATE ->
  CASE WHEN IS_ROLE_IN_SESSION('DQ_LAB_PII_READER') THEN val ELSE DATE_FROM_PARTS(YEAR(val), 1, 1) END;  -- keep birth year only

ALTER TAG PII_TYPE SET MASKING POLICY MASK_PII_STRING, MASKING POLICY MASK_PII_DATE;

ALTER TABLE MEMBERS__MEMBER MODIFY
  COLUMN email         SET TAG PII_TYPE = 'email',
  COLUMN phone         SET TAG PII_TYPE = 'phone',
  COLUMN date_of_birth SET TAG PII_TYPE = 'dob',
  COLUMN first_name    SET TAG PII_TYPE = 'name',
  COLUMN last_name     SET TAG PII_TYPE = 'name',
  COLUMN postcode      SET TAG PII_TYPE = 'postcode',
  COLUMN health_notes  SET TAG PII_TYPE = 'health';

-- A3. Row access: anyone reading this operator's data sees ONLY this operator's rows
--     (also hides rows leaked from another operator - the TENANT_LEAK fault)
CREATE OR REPLACE ROW ACCESS POLICY RAP_OWN_OPERATOR AS (operator_id VARCHAR) RETURNS BOOLEAN ->
  operator_id = 'CUST_NIELS' OR IS_ROLE_IN_SESSION('DQ_LAB_ADMIN');
ALTER TABLE MEMBERS__MEMBER ADD ROW ACCESS POLICY RAP_OWN_OPERATOR ON (operator_id);

-- Allowed / denied tests
GRANT USAGE ON SCHEMA GLADSTONE_DQ_LAB.CUST_NIELS TO ROLE DQ_LAB_PII_READER;
GRANT USAGE ON SCHEMA GLADSTONE_DQ_LAB.CUST_NIELS TO ROLE DQ_LAB_OPERATOR_VIEWER;
GRANT SELECT ON TABLE MEMBERS__MEMBER TO ROLE DQ_LAB_PII_READER;
GRANT SELECT ON TABLE MEMBERS__MEMBER TO ROLE DQ_LAB_OPERATOR_VIEWER;

SELECT member_id, first_name, email, date_of_birth, health_notes FROM MEMBERS__MEMBER WHERE health_notes IS NOT NULL LIMIT 3;  -- as owner: masked
USE ROLE DQ_LAB_PII_READER;      USE SECONDARY ROLES NONE;
SELECT member_id, first_name, email, date_of_birth, health_notes FROM GLADSTONE_DQ_LAB.CUST_NIELS.MEMBERS__MEMBER WHERE health_notes IS NOT NULL LIMIT 3;  -- clear
USE ROLE DQ_LAB_OPERATOR_VIEWER; USE SECONDARY ROLES NONE;
SELECT COUNT(*), COUNT_IF(operator_id <> 'CUST_NIELS') AS foreign_rows_visible FROM GLADSTONE_DQ_LAB.CUST_NIELS.MEMBERS__MEMBER;  -- 0 foreign
USE ROLE DQ_LAB_NIELS;           USE SECONDARY ROLES NONE;

-- A4. Does Nova's semantic view expose personal data? (it reads REPORTING aggregates - no member columns)
DESCRIBE SEMANTIC VIEW SV_OPERATOR_KPIS;

-- A5. Who read my member table? (ACCESS_HISTORY lags up to ~3h)
SELECT query_start_time, user_name, direct_objects_accessed
FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY,
     LATERAL FLATTEN(base_objects_accessed) f
WHERE f.value:objectName::STRING = 'GLADSTONE_DQ_LAB.CUST_NIELS.MEMBERS__MEMBER'
  AND query_start_time > DATEADD(day, -1, CURRENT_TIMESTAMP())
ORDER BY query_start_time DESC LIMIT 20;

-- ============================ PART B: GDPR ===================================
-- B1. Record GDPR categories, lawful basis and retention on the columns (drives SAR + retention)
ALTER TABLE MEMBERS__MEMBER MODIFY
  COLUMN member_id     SET TAG GLADSTONE_DQ_LAB.GOVERNANCE.GDPR_CATEGORY = 'identifier', GLADSTONE_DQ_LAB.GOVERNANCE.LAWFUL_BASIS = 'contract',  GLADSTONE_DQ_LAB.GOVERNANCE.RETENTION_DAYS = '730',
  COLUMN email         SET TAG GLADSTONE_DQ_LAB.GOVERNANCE.GDPR_CATEGORY = 'contact',    GLADSTONE_DQ_LAB.GOVERNANCE.LAWFUL_BASIS = 'contract',  GLADSTONE_DQ_LAB.GOVERNANCE.RETENTION_DAYS = '730',
  COLUMN phone         SET TAG GLADSTONE_DQ_LAB.GOVERNANCE.GDPR_CATEGORY = 'contact',    GLADSTONE_DQ_LAB.GOVERNANCE.LAWFUL_BASIS = 'contract',  GLADSTONE_DQ_LAB.GOVERNANCE.RETENTION_DAYS = '730',
  COLUMN health_notes  SET TAG GLADSTONE_DQ_LAB.GOVERNANCE.GDPR_CATEGORY = 'special_category', GLADSTONE_DQ_LAB.GOVERNANCE.LAWFUL_BASIS = 'explicit_consent', GLADSTONE_DQ_LAB.GOVERNANCE.RETENTION_DAYS = '30',
  COLUMN marketing_consent SET TAG GLADSTONE_DQ_LAB.GOVERNANCE.GDPR_CATEGORY = 'behavioural', GLADSTONE_DQ_LAB.GOVERNANCE.LAWFUL_BASIS = 'consent';
ALTER TABLE SYSTEM__PAYMENT MODIFY
  COLUMN amount SET TAG GLADSTONE_DQ_LAB.GOVERNANCE.GDPR_CATEGORY = 'financial', GLADSTONE_DQ_LAB.GOVERNANCE.LAWFUL_BASIS = 'legal_obligation', GLADSTONE_DQ_LAB.GOVERNANCE.RETENTION_DAYS = '2190';

SELECT * FROM TABLE(INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS('GLADSTONE_DQ_LAB.CUST_NIELS.MEMBERS__MEMBER', 'table'))
WHERE tag_schema = 'GOVERNANCE';

-- B2. Subject access request: find every row about one member, wherever it lives in this operator
CREATE OR REPLACE PROCEDURE SAR_EXPORT(MEMBER_ID VARCHAR)
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS CALLER   -- runs with the caller's roles: masking policies see DQ_LAB_PII_READER
AS
$$
DECLARE
  report OBJECT DEFAULT OBJECT_CONSTRUCT();
  rows_found VARIANT;
  c1 CURSOR FOR SELECT table_name FROM GLADSTONE_DQ_LAB.INFORMATION_SCHEMA.COLUMNS
                WHERE table_schema = 'CUST_NIELS' AND column_name = 'MEMBER_ID' ORDER BY table_name;
BEGIN
  FOR t IN c1 DO
    LET tbl VARCHAR := t.table_name;
    LET rs RESULTSET := (EXECUTE IMMEDIATE
      'SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*)) AS r FROM GLADSTONE_DQ_LAB.CUST_NIELS.' || :tbl || ' WHERE member_id = ?'
      USING (MEMBER_ID));
    LET c2 CURSOR FOR rs;
    FOR x IN c2 DO
      rows_found := x.r;
    END FOR;
    IF (ARRAY_SIZE(:rows_found) > 0) THEN
      report := OBJECT_INSERT(:report, :tbl, :rows_found);
    END IF;
  END FOR;
  INSERT INTO GLADSTONE_DQ_LAB.GOVERNANCE.GDPR_REQUESTS (operator_id, member_id, request_type, completed_at, completed_by, evidence)
    SELECT 'CUST_NIELS', :MEMBER_ID, 'SAR', CURRENT_TIMESTAMP(), CURRENT_USER(), OBJECT_KEYS(:report);
  RETURN OBJECT_CONSTRUCT('operator', 'CUST_NIELS', 'member_id', :MEMBER_ID, 'generated_at', CURRENT_TIMESTAMP(),
                          'note', 'REPORTING dynamic tables hold aggregates only (no member_id)', 'data', :report);
END;
$$;
-- A SAR must contain the real data, so it runs under the privacy role (masking lets it through):
USE SECONDARY ROLES DQ_LAB_PII_READER;
CALL SAR_EXPORT('M-01043');
USE SECONDARY ROLES NONE;

-- B3. Erasure: pseudonymise identity, keep financial records required by law, prove completion
INSERT INTO GLADSTONE_DQ_LAB.GOVERNANCE.GDPR_REQUESTS (operator_id, member_id, request_type)
  VALUES ('CUST_NIELS', 'M-01042', 'ERASURE');

CREATE OR REPLACE PROCEDURE ERASE_MEMBER(MEMBER_ID VARCHAR)
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
  token VARCHAR DEFAULT 'ERASED-' || SUBSTR(SHA2(:MEMBER_ID || '|lab-salt-rotate-me'), 1, 16);
  n_mem NUMBER; n_pay NUMBER; n_bk NUMBER; n_at NUMBER;
BEGIN
  UPDATE GLADSTONE_DQ_LAB.CUST_NIELS.MEMBERS__MEMBER
     SET member_id = :token, first_name = 'ERASED', last_name = 'ERASED', email = NULL, phone = NULL,
         date_of_birth = NULL, postcode = NULL, health_notes = NULL, marketing_consent = FALSE
   WHERE member_id = :MEMBER_ID;
  n_mem := SQLROWCOUNT;
  UPDATE GLADSTONE_DQ_LAB.CUST_NIELS.MEMBERS__MEMBERSHIP SET member_id = :token WHERE member_id = :MEMBER_ID;
  UPDATE GLADSTONE_DQ_LAB.CUST_NIELS.SYSTEM__PAYMENT SET member_id = :token WHERE member_id = :MEMBER_ID;   -- keep money, drop identity
  n_pay := SQLROWCOUNT;
  DELETE FROM GLADSTONE_DQ_LAB.CUST_NIELS.SYSTEM__ATTENDANCE WHERE member_id = :MEMBER_ID;
  n_at := SQLROWCOUNT;
  DELETE FROM GLADSTONE_DQ_LAB.CUST_NIELS.SYSTEM__BOOKING WHERE member_id = :MEMBER_ID;
  n_bk := SQLROWCOUNT;
  UPDATE GLADSTONE_DQ_LAB.GOVERNANCE.GDPR_REQUESTS
     SET completed_at = CURRENT_TIMESTAMP(), completed_by = CURRENT_USER(),
         evidence = OBJECT_CONSTRUCT('member_rows', :n_mem, 'payments_pseudonymised', :n_pay,
                                     'bookings_deleted', :n_bk, 'attendance_deleted', :n_at, 'token', :token)
   WHERE operator_id = 'CUST_NIELS' AND member_id = :MEMBER_ID AND request_type = 'ERASURE' AND completed_at IS NULL;
  RETURN OBJECT_CONSTRUCT('member_rows', :n_mem, 'payments_pseudonymised', :n_pay, 'bookings_deleted', :n_bk, 'attendance_deleted', :n_at);
END;
$$;
CALL ERASE_MEMBER('M-01042');

-- B4. Data quality proof that the erasure reached every table (expect 0)
ALTER TABLE MEMBERS__MEMBER ADD DATA METRIC FUNCTION GLADSTONE_DQ_LAB.DQ_COMMON.ERASED_MEMBERS_STILL_PRESENT
  ON (member_id, TABLE(GLADSTONE_DQ_LAB.GOVERNANCE.GDPR_REQUESTS(member_id, request_type, completed_at)))
  EXPECTATION erasure_complete (VALUE = 0);
ALTER TABLE SYSTEM__PAYMENT ADD DATA METRIC FUNCTION GLADSTONE_DQ_LAB.DQ_COMMON.ERASED_MEMBERS_STILL_PRESENT
  ON (member_id, TABLE(GLADSTONE_DQ_LAB.GOVERNANCE.GDPR_REQUESTS(member_id, request_type, completed_at)))
  EXPECTATION erasure_complete (VALUE = 0);
SELECT * FROM TABLE(SYSTEM$EVALUATE_DATA_QUALITY_EXPECTATIONS(REF_ENTITY_NAME => 'GLADSTONE_DQ_LAB.CUST_NIELS.MEMBERS__MEMBER'));

-- B5. Copies that survive the erasure
SHOW TABLES LIKE 'MEMBERS__MEMBER' IN SCHEMA GLADSTONE_DQ_LAB.CUST_NIELS;           -- retention_time column
SELECT COUNT(*) AS still_in_time_travel
FROM MEMBERS__MEMBER AT(OFFSET => -120) WHERE member_id = 'M-01042';                -- Time Travel still holds the old row
-- The gold copy this operator was cloned from (dev/test clones of prod) still has the member:
-- SELECT COUNT(*) FROM GLADSTONE_DQ_LAB.ADMIN_OPERATOR_TEMPLATE.MEMBERS__MEMBER WHERE member_id = 'M-01042';  -- admin only
ALTER TABLE MEMBERS__MEMBER SET DATA_RETENTION_TIME_IN_DAYS = 1;   -- shorter Time Travel; Fail-safe (7 days) still applies to permanent tables

-- B6. Special-category data stays away from Nova: health_notes is tagged 'health' and masked by A2;
--     it is not referenced by SV_OPERATOR_KPIS (verify with DESCRIBE SEMANTIC VIEW above).

-- B7. UK residency for AI: is Cortex allowed to process outside this region? (read-only; ACCOUNTADMIN owns it)
SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;
