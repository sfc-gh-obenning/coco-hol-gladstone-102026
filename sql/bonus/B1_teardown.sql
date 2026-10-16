-- =============================================================================
-- Gladstone MRM | Bonus B1 - Cost controls | B1_teardown.sql (ADMIN)
-- Removes only Bonus B1 objects; the core lab keeps running.
-- =============================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DQ_LAB_WH;
CALL GLADSTONE_DQ_LAB.ADMIN.B1_TEARDOWN();   -- unset cost tags on CUST_ schemas, drop FINOPS (budgets + tags), drop DQ_LAB_RM_DEMO

REVOKE DATABASE ROLE SNOWFLAKE.BUDGET_CREATOR FROM ROLE DQ_LAB_ATTENDEE;
REVOKE DATABASE ROLE SNOWFLAKE.USAGE_VIEWER   FROM ROLE DQ_LAB_ATTENDEE;
REVOKE APPLYBUDGET ON WAREHOUSE DQ_LAB_WH FROM ROLE DQ_LAB_ATTENDEE;
REVOKE USAGE ON INTEGRATION DQ_LAB_EMAIL_INT FROM APPLICATION SNOWFLAKE;

SHOW SCHEMAS LIKE 'FINOPS' IN DATABASE GLADSTONE_DQ_LAB;   -- expect none
SHOW RESOURCE MONITORS LIKE 'DQ_LAB_RM_DEMO';              -- expect none
