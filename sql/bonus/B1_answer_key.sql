-- =============================================================================
-- Gladstone MRM | Bonus B1 - Cost controls | B1_answer_key.sql (attendee role)
-- Replace CUST_NIELS / NIELS with your operator.
-- =============================================================================
USE WAREHOUSE DQ_LAB_WH;

-- B1.1  What does my operator pipeline cost? (warehouse time from DT refreshes + task, serverless DMFs)
SELECT DATE_TRUNC('hour', start_time) AS hour, SUM(credits_used) AS dmf_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_QUALITY_MONITORING_USAGE_HISTORY
WHERE database_name = 'GLADSTONE_DQ_LAB' AND schema_name = 'CUST_NIELS'
GROUP BY 1 ORDER BY 1 DESC;     -- ACCOUNT_USAGE lags up to ~3h; INFORMATION_SCHEMA functions are near real time

SELECT name, COUNT(*) AS refreshes, SUM(DATEDIFF(second, refresh_start_time, refresh_end_time)) AS refresh_seconds
FROM TABLE(GLADSTONE_DQ_LAB.INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(NAME_PREFIX => 'GLADSTONE_DQ_LAB.CUST_NIELS.'))
GROUP BY 1;

-- B1.2  Tag my operator for cost attribution (schema tag is inherited by every table / DT inside)
ALTER SCHEMA GLADSTONE_DQ_LAB.CUST_NIELS SET TAG
  GLADSTONE_DQ_LAB.FINOPS.OPERATOR_ID = 'CUST_NIELS',
  GLADSTONE_DQ_LAB.FINOPS.COST_CENTRE = 'nova';

-- B1.3  Custom budget for my operator: 5 credits / month, email at 80% projected
USE SCHEMA GLADSTONE_DQ_LAB.FINOPS;
CREATE SNOWFLAKE.CORE.BUDGET CUST_NIELS_BUDGET();
CALL CUST_NIELS_BUDGET!SET_SPENDING_LIMIT(5);
CALL CUST_NIELS_BUDGET!ADD_RESOURCE(
  SYSTEM$REFERENCE('SCHEMA', 'GLADSTONE_DQ_LAB.CUST_NIELS', 'SESSION', 'applybudget'));
CALL CUST_NIELS_BUDGET!SET_EMAIL_NOTIFICATIONS('DQ_LAB_EMAIL_INT', 'replace.me@gladstonesoftware.co.uk');
CALL CUST_NIELS_BUDGET!SET_NOTIFICATION_THRESHOLD(80);
CALL CUST_NIELS_BUDGET!GET_LINKED_RESOURCES();

-- Tag-driven alternative (how you'd do it for every operator in a tier): one budget, many operators
-- CALL CUST_NIELS_BUDGET!ADD_RESOURCE_TAG(
--   SYSTEM$REFERENCE('TAG', 'GLADSTONE_DQ_LAB.FINOPS.COST_CENTRE', 'SESSION', 'applybudget'), 'nova');

-- B1.4  Spend so far (budget data populates after the budget's serverless refresh runs - can take hours)
CALL CUST_NIELS_BUDGET!GET_SPENDING_HISTORY(
  TIME_LOWER_BOUND => DATEADD('days', -7, CURRENT_TIMESTAMP()),
  TIME_UPPER_BOUND => CURRENT_TIMESTAMP());

-- B1.5  Draft (do not run - ACCOUNTADMIN only): resource monitor for a Nova operator warehouse
-- CREATE RESOURCE MONITOR NOVA_WH_CUST_NIELS_RM WITH CREDIT_QUOTA = 30 FREQUENCY = MONTHLY
--   START_TIMESTAMP = IMMEDIATELY TRIGGERS ON 75 PERCENT DO NOTIFY ON 100 PERCENT DO SUSPEND;
-- ALTER WAREHOUSE NOVA_WH_CUST_NIELS SET RESOURCE_MONITOR = NOVA_WH_CUST_NIELS_RM;
