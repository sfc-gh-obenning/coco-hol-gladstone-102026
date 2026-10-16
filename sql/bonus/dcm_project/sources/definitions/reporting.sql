-- Silver REPORTING - what Nova's semantic layer reads
DEFINE DYNAMIC TABLE {{db}}.{{schema}}.REPORTING__DAILY_REVENUE
WAREHOUSE = {{wh}}
TARGET_LAG = '{{reporting_lag}}'
REFRESH_MODE = 'INCREMENTAL'
INITIALIZE = 'ON_CREATE'
DATA_METRIC_SCHEDULE = '{{dq_schedule}}'
COMMENT = 'Silver REPORTING net revenue for {{operator_id}} (managed by DCM)'
AS
SELECT OPERATOR_ID,
       PAYMENT_DATE,
       SUM(IFF(PAYMENT_TYPE = 'REFUND', -AMOUNT, AMOUNT)) AS NET_REVENUE,
       COUNT(*)                                           AS TRANSACTIONS,
       MAX(_LOADED_AT)                                    AS LAST_LOADED_AT
FROM {{db}}.{{schema}}.SYSTEM__PAYMENT
GROUP BY OPERATOR_ID, PAYMENT_DATE;

DEFINE DYNAMIC TABLE {{db}}.{{schema}}.REPORTING__ACTIVE_MEMBERS
WAREHOUSE = {{wh}}
TARGET_LAG = '{{reporting_lag}}'
REFRESH_MODE = 'INCREMENTAL'
INITIALIZE = 'ON_CREATE'
COMMENT = 'Silver REPORTING active members for {{operator_id}} (managed by DCM)'
AS
SELECT OPERATOR_ID,
       HOME_SITE_ID                  AS SITE_ID,
       COUNT_IF(STATUS = 'ACTIVE')   AS ACTIVE_MEMBERS,
       MAX(_LOADED_AT)               AS LAST_LOADED_AT
FROM {{db}}.{{schema}}.MEMBERS__MEMBER
GROUP BY OPERATOR_ID, HOME_SITE_ID;
