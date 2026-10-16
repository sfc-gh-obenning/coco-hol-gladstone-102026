-- =============================================================================
-- Gladstone MRM | Bonus B1 - Cost controls | B1_setup.sql  (ADMIN, run once)
-- Lets each operator role create a custom budget for its own schema, tag its schema
-- with an operator id, and see cost by tag. Objects stay inside GLADSTONE_DQ_LAB.FINOPS.
-- Prereq: core lab set up (00/01/02). Teardown: B1_teardown.sql
-- =============================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DQ_LAB_WH;

CREATE SCHEMA IF NOT EXISTS GLADSTONE_DQ_LAB.FINOPS COMMENT = 'Bonus B1: budgets and cost tags';
GRANT OWNERSHIP ON SCHEMA GLADSTONE_DQ_LAB.FINOPS TO ROLE DQ_LAB_ADMIN COPY CURRENT GRANTS;

-- Cost-attribution tags (one definition, applied to every operator) - owned by the lab admin
USE ROLE DQ_LAB_ADMIN;
CREATE TAG IF NOT EXISTS GLADSTONE_DQ_LAB.FINOPS.OPERATOR_ID COMMENT = 'Operator (customer) that owns this object';
CREATE TAG IF NOT EXISTS GLADSTONE_DQ_LAB.FINOPS.COST_CENTRE ALLOWED_VALUES 'nova', 'reporting', 'platform'
  COMMENT = 'Gladstone product line paying for this object';
GRANT USAGE ON SCHEMA GLADSTONE_DQ_LAB.FINOPS TO ROLE DQ_LAB_ATTENDEE;
GRANT CREATE SNOWFLAKE.CORE.BUDGET ON SCHEMA GLADSTONE_DQ_LAB.FINOPS TO ROLE DQ_LAB_ATTENDEE;
GRANT APPLY, APPLYBUDGET ON TAG GLADSTONE_DQ_LAB.FINOPS.OPERATOR_ID TO ROLE DQ_LAB_ATTENDEE;
GRANT APPLY, APPLYBUDGET ON TAG GLADSTONE_DQ_LAB.FINOPS.COST_CENTRE TO ROLE DQ_LAB_ATTENDEE;
USE ROLE ACCOUNTADMIN;

-- Budget privileges (documented model: BUDGET_CREATOR + CREATE BUDGET on schema + APPLYBUDGET on objects)
GRANT DATABASE ROLE SNOWFLAKE.BUDGET_CREATOR TO ROLE DQ_LAB_ATTENDEE;
GRANT DATABASE ROLE SNOWFLAKE.USAGE_VIEWER   TO ROLE DQ_LAB_ATTENDEE;
GRANT APPLYBUDGET ON WAREHOUSE DQ_LAB_WH TO ROLE DQ_LAB_ATTENDEE;
-- Operators own their CUST_ schema, which includes APPLYBUDGET on it.

-- Budgets send email through a notification integration the SNOWFLAKE application can use
GRANT USAGE ON INTEGRATION DQ_LAB_EMAIL_INT TO APPLICATION SNOWFLAKE;
GRANT USAGE ON INTEGRATION DQ_LAB_EMAIL_INT TO ROLE DQ_LAB_ATTENDEE;

-- Resource monitors can only be created by ACCOUNTADMIN: attendees draft one with CoCo, the admin creates it.
-- Example the admin runs when an attendee shares their draft:
CREATE RESOURCE MONITOR IF NOT EXISTS DQ_LAB_RM_DEMO
  WITH CREDIT_QUOTA = 2 FREQUENCY = DAILY START_TIMESTAMP = IMMEDIATELY
  TRIGGERS ON 50 PERCENT DO NOTIFY
           ON 90 PERCENT DO NOTIFY
           ON 100 PERCENT DO SUSPEND;
-- (Not attached to DQ_LAB_WH: DQ_LAB_RM already caps the lab warehouse. A warehouse has one monitor.)

-- Standalone teardown helper (also called by 98_teardown.sql)
USE ROLE DQ_LAB_ADMIN;
CREATE OR REPLACE PROCEDURE GLADSTONE_DQ_LAB.ADMIN.B1_TEARDOWN()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
  c1 CURSOR FOR SELECT schema_name FROM GLADSTONE_DQ_LAB.INFORMATION_SCHEMA.SCHEMATA
                WHERE schema_name LIKE 'CUST\\_%' ESCAPE '\\';
BEGIN
  FOR r IN c1 DO
    EXECUTE IMMEDIATE 'ALTER SCHEMA GLADSTONE_DQ_LAB.' || r.schema_name ||
                      ' UNSET TAG GLADSTONE_DQ_LAB.FINOPS.OPERATOR_ID, GLADSTONE_DQ_LAB.FINOPS.COST_CENTRE';
  END FOR;
  DROP SCHEMA IF EXISTS GLADSTONE_DQ_LAB.FINOPS;   -- drops every budget instance and tag in it
  DROP RESOURCE MONITOR IF EXISTS DQ_LAB_RM_DEMO;
  RETURN 'Bonus B1 removed (budgets, cost tags, demo resource monitor)';
END;
$$;
