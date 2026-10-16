-- =============================================================================
-- Gladstone MRM | Bonus B2 - Data governance + GDPR | B2_teardown.sql (ADMIN)
-- Removes only Bonus B2 objects; the core lab keeps running.
-- Attendee-created objects inside CUST_ schemas (PII_TYPE tag, masking/row access policies,
-- SAR_EXPORT / ERASE_MEMBER procs) are detached here and dropped with the database in 98_teardown.sql.
-- =============================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DQ_LAB_WH;

CALL GLADSTONE_DQ_LAB.ADMIN.B2_UNSET_ALL();   -- detach row access / masking / projection policies,
                                              -- drop erasure DMFs, reset retention, drop GOVERNANCE schema

REVOKE APPLY MASKING POLICY    ON ACCOUNT FROM ROLE DQ_LAB_ATTENDEE;
REVOKE APPLY ROW ACCESS POLICY ON ACCOUNT FROM ROLE DQ_LAB_ATTENDEE;
REVOKE APPLY TAG               ON ACCOUNT FROM ROLE DQ_LAB_ATTENDEE;
REVOKE DATABASE ROLE SNOWFLAKE.CLASSIFICATION_ADMIN FROM ROLE DQ_LAB_ATTENDEE;
DROP ROLE IF EXISTS DQ_LAB_PII_READER;
DROP ROLE IF EXISTS DQ_LAB_OPERATOR_VIEWER;

-- Verify
SHOW SCHEMAS LIKE 'GOVERNANCE' IN DATABASE GLADSTONE_DQ_LAB;   -- expect none
SHOW ROLES LIKE 'DQ_LAB_PII_READER';                            -- expect none
-- GDPR note: rows changed by ERASE_MEMBER remain recoverable through Time Travel for the table's
-- retention period and then Fail-safe (7 days, permanent tables). This is synthetic data.
