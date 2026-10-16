-- Bronze (Nova MEMBERS / SYSTEM) - the tables Bifrost merges into
DEFINE TABLE {{db}}.{{schema}}.MEMBERS__MEMBER (
    MEMBER_ID     VARCHAR,
    OPERATOR_ID   VARCHAR,
    HOME_SITE_ID  VARCHAR,
    STATUS        VARCHAR,
    JOINED_ON     DATE,
    LEFT_ON       DATE,
    _BATCH_ID     VARCHAR,
    _LOADED_AT    TIMESTAMP_LTZ
)
CHANGE_TRACKING = TRUE
DATA_METRIC_SCHEDULE = '{{dq_schedule}}'
COMMENT = 'Bronze MEMBERS for {{operator_id}} (managed by DCM)';

DEFINE TABLE {{db}}.{{schema}}.SYSTEM__PAYMENT (
    PAYMENT_ID    VARCHAR,
    OPERATOR_ID   VARCHAR,
    MEMBER_ID     VARCHAR,
    PAYMENT_DATE  DATE,
    AMOUNT        NUMBER(10,2),
    PAYMENT_TYPE  VARCHAR,
    _BATCH_ID     VARCHAR,
    _LOADED_AT    TIMESTAMP_LTZ
)
CHANGE_TRACKING = TRUE
DATA_METRIC_SCHEDULE = '{{dq_schedule}}'
COMMENT = 'Bronze SYSTEM payments for {{operator_id}} (managed by DCM)';
