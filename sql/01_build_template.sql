-- =============================================================================
-- Gladstone MRM | Data Quality HOL | 01_build_template.sql
-- Builds the gold-copy operator in GLADSTONE_DQ_LAB.ADMIN_OPERATOR_TEMPLATE
-- (seed TABLES only - tasks, dynamic tables and the semantic view are created
--  per attendee by ADMIN.SETUP_ATTENDEE so they point at the attendee's own tables).
-- Also creates the central custom DMFs in DQ_COMMON.
--
-- Naming mirrors Nova's layers (customer diagram "Layers at a glance"):
--   Bronze schemas MEMBERS / SHARED / SYSTEM  -> table prefixes MEMBERS__ / SHARED__ / SYSTEM__
--   Sync metadata _SYNC_META._MERGE_BATCH     -> _SYNC_META__MERGE_BATCH
--   Silver REPORTING (dynamic tables)          -> REPORTING__*
-- All data is synthetic. Values are derived with HASH() of the row sequence,
-- not RANDOM(), so every rebuild produces the same distributions.
-- =============================================================================
USE ROLE DQ_LAB_ADMIN;
USE WAREHOUSE DQ_LAB_WH;
USE SCHEMA GLADSTONE_DQ_LAB.ADMIN_OPERATOR_TEMPLATE;

SET OP = 'CUST_TEMPLATE';

-- ---------------------------------------------------------------------------
-- Bronze: SHARED
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE SHARED__SITE (
  site_id      VARCHAR,
  operator_id  VARCHAR,
  site_name    VARCHAR,
  town         VARCHAR,
  _loaded_at   TIMESTAMP_LTZ
) COMMENT = 'Bronze SHARED: operator sites';

INSERT INTO SHARED__SITE
SELECT column1, $OP, column2, column3, CURRENT_TIMESTAMP()
FROM VALUES ('S01','Riverside Leisure Centre','Oxford'),
            ('S02','Abbey Pool & Gym','Abingdon'),
            ('S03','Kingfisher Sports Hub','Banbury');

CREATE OR REPLACE TABLE SHARED__ACTIVITY (
  activity_id  VARCHAR,
  operator_id  VARCHAR,
  site_id      VARCHAR,
  class_name   VARCHAR,
  class_date   DATE,
  capacity     NUMBER,
  _loaded_at   TIMESTAMP_LTZ
) COMMENT = 'Bronze SHARED: scheduled classes';

INSERT INTO SHARED__ACTIVITY
SELECT 'A' || LPAD(seq::VARCHAR, 5, '0'),
       $OP,
       'S0' || (1 + MOD(seq, 3)),
       DECODE(MOD(HASH(seq, 'cls'), 6), 0,'Spin',1,'Yoga',2,'Aqua Fit',3,'HIIT',4,'Pilates','Swim Lessons'),
       DATEADD(day, -MOD(seq, 28), CURRENT_DATE()),
       DECODE(MOD(HASH(seq, 'cap'), 3), 0, 12, 1, 20, 30),
       CURRENT_TIMESTAMP()
FROM (SELECT SEQ4() AS seq FROM TABLE(GENERATOR(ROWCOUNT => 600)));

-- ---------------------------------------------------------------------------
-- Bronze: MEMBERS (includes synthetic personal data for Bonus B2 / GDPR)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE MEMBERS__MEMBER (
  member_id          VARCHAR,
  operator_id        VARCHAR,
  home_site_id       VARCHAR,
  first_name         VARCHAR,
  last_name          VARCHAR,
  email              VARCHAR,
  phone              VARCHAR,
  date_of_birth      DATE,
  postcode           VARCHAR,
  status             VARCHAR,   -- ACTIVE / FROZEN / CANCELLED  (source-system status)
  joined_on          DATE,
  left_on            DATE,
  marketing_consent  BOOLEAN,
  health_notes       VARCHAR,   -- special-category data (PAR-Q style), synthetic
  last_activity_at   TIMESTAMP_LTZ,
  _batch_id          VARCHAR,
  _loaded_at         TIMESTAMP_LTZ
) COMMENT = 'Bronze MEMBERS: member master (synthetic personal data)';

INSERT INTO MEMBERS__MEMBER
WITH s AS (SELECT SEQ4() AS seq, ABS(HASH(SEQ4(), 'm')) AS h FROM TABLE(GENERATOR(ROWCOUNT => 2000)))
SELECT 'M-' || LPAD((1000 + seq)::VARCHAR, 5, '0'),
       $OP,
       'S0' || (1 + MOD(h, 3)),
       DECODE(MOD(h, 10), 0,'Amelia',1,'Oliver',2,'Isla',3,'George',4,'Ava',5,'Harry',6,'Mia',7,'Noah',8,'Freya','Jack'),
       DECODE(MOD(FLOOR(h / 10), 10), 0,'Smith',1,'Jones',2,'Taylor',3,'Brown',4,'Williams',5,'Wilson',6,'Evans',7,'Thomas',8,'Roberts','Walker'),
       'member' || (1000 + seq) || '@example.co.uk',
       '07700 9' || LPAD(MOD(h, 100000)::VARCHAR, 5, '0'),
       DATEADD(day, -(6570 + MOD(h, 18250)), CURRENT_DATE()),           -- 18 to 68 years old
       DECODE(MOD(h, 4), 0,'OX1 ',1,'OX14 ',2,'OX16 ','OX4 ') || (1 + MOD(h, 9)) || 'AB',
       CASE WHEN MOD(h, 100) < 78 THEN 'ACTIVE' WHEN MOD(h, 100) < 84 THEN 'FROZEN' ELSE 'CANCELLED' END,
       DATEADD(day, -(30 + MOD(h, 1400)), CURRENT_DATE()),
       CASE WHEN MOD(h, 100) >= 84 THEN DATEADD(day, -MOD(h, 120), CURRENT_DATE()) END,
       MOD(h, 3) <> 0,
       CASE WHEN MOD(h, 25) = 0 THEN 'Asthma - inhaler on poolside'
            WHEN MOD(h, 31) = 0 THEN 'Recent knee surgery - low impact only' END,
       DATEADD(hour, -MOD(h, 24 * 60), CURRENT_TIMESTAMP()),
       'B-SEED',
       CURRENT_TIMESTAMP()
FROM s;

CREATE OR REPLACE TABLE MEMBERS__MEMBERSHIP (
  membership_id  VARCHAR,
  member_id      VARCHAR,
  operator_id    VARCHAR,
  plan_name      VARCHAR,
  monthly_fee    NUMBER(10,2),
  start_date     DATE,
  end_date       DATE,
  last_paid_on   DATE,
  _loaded_at     TIMESTAMP_LTZ
) COMMENT = 'Bronze MEMBERS: membership contracts';

INSERT INTO MEMBERS__MEMBERSHIP
SELECT 'MS-' || SUBSTR(member_id, 3),
       member_id,
       operator_id,
       DECODE(MOD(ABS(HASH(member_id, 'p')), 3), 0,'Off-Peak',1,'Standard','Premium Plus'),
       DECODE(MOD(ABS(HASH(member_id, 'p')), 3), 0, 24.99, 1, 34.99, 49.99),
       joined_on,
       left_on,
       -- Deliberately NOT the same as status: ~6% of ACTIVE members have not paid in > 35 days (gap vs status-based count: 78 members, ~5%).
       -- This is the "two definitions of active member" trap.
       CASE WHEN status = 'ACTIVE' AND MOD(ABS(HASH(member_id, 'lp')), 100) < 6
              THEN DATEADD(day, -(40 + MOD(ABS(HASH(member_id, 'd')), 60)), CURRENT_DATE())
            WHEN status = 'ACTIVE'
              THEN DATEADD(day, -MOD(ABS(HASH(member_id, 'd')), 30), CURRENT_DATE())
            ELSE DATEADD(day, -(45 + MOD(ABS(HASH(member_id, 'd')), 200)), CURRENT_DATE()) END,
       CURRENT_TIMESTAMP()
FROM MEMBERS__MEMBER;

-- ---------------------------------------------------------------------------
-- Bronze: SYSTEM
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE SYSTEM__BOOKING (
  booking_id   VARCHAR,
  operator_id  VARCHAR,
  activity_id  VARCHAR,
  member_id    VARCHAR,
  booked_at    TIMESTAMP_LTZ,
  _loaded_at   TIMESTAMP_LTZ
) COMMENT = 'Bronze SYSTEM: class bookings';

INSERT INTO SYSTEM__BOOKING
WITH s AS (SELECT SEQ4() AS seq, ABS(HASH(SEQ4(), 'b')) AS h FROM TABLE(GENERATOR(ROWCOUNT => 9000)))
SELECT 'BK-' || LPAD(seq::VARCHAR, 6, '0'),
       $OP,
       'A' || LPAD(MOD(h, 600)::VARCHAR, 5, '0'),
       'M-' || LPAD((1000 + MOD(FLOOR(h / 600), 2000))::VARCHAR, 5, '0'),
       DATEADD(minute, -MOD(h, 28 * 24 * 60), CURRENT_TIMESTAMP()),
       CURRENT_TIMESTAMP()
FROM s;

CREATE OR REPLACE TABLE SYSTEM__ATTENDANCE (
  attendance_id  VARCHAR,
  operator_id    VARCHAR,
  booking_id     VARCHAR,
  member_id      VARCHAR,
  checked_in_at  TIMESTAMP_LTZ,
  _loaded_at     TIMESTAMP_LTZ
) COMMENT = 'Bronze SYSTEM: turnstile / class check-ins';

INSERT INTO SYSTEM__ATTENDANCE
SELECT 'AT-' || SUBSTR(booking_id, 4), operator_id, booking_id, member_id,
       DATEADD(minute, 5, booked_at), CURRENT_TIMESTAMP()
FROM SYSTEM__BOOKING
WHERE MOD(ABS(HASH(booking_id, 'show')), 100) < 82;      -- ~18% no-show rate

CREATE OR REPLACE TABLE SYSTEM__PAYMENT (
  payment_id    VARCHAR,
  operator_id   VARCHAR,
  member_id     VARCHAR,
  payment_date  DATE,
  amount        NUMBER(10,2),   -- always positive; direction comes from payment_type
  payment_type  VARCHAR,        -- PAYMENT / REFUND
  _batch_id     VARCHAR,
  _loaded_at    TIMESTAMP_LTZ
) COMMENT = 'Bronze SYSTEM: payments and refunds';

INSERT INTO SYSTEM__PAYMENT
WITH s AS (SELECT SEQ4() AS seq, ABS(HASH(SEQ4(), 'pay')) AS h FROM TABLE(GENERATOR(ROWCOUNT => 6000)))
SELECT 'PY-' || LPAD(seq::VARCHAR, 7, '0'),
       $OP,
       'M-' || LPAD((1000 + MOD(h, 2000))::VARCHAR, 5, '0'),
       DATEADD(day, -MOD(seq, 28), CURRENT_DATE()),
       DECODE(MOD(h, 3), 0, 24.99, 1, 34.99, 49.99),
       IFF(MOD(h, 40) = 0, 'REFUND', 'PAYMENT'),
       'B-SEED',
       CURRENT_TIMESTAMP()
FROM s;

-- ---------------------------------------------------------------------------
-- Sync metadata (stands in for Bifrost / Snowpipe Streaming merge batches)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE _SYNC_META__MERGE_BATCH (
  batch_id     VARCHAR,
  operator_id  VARCHAR,
  table_name   VARCHAR,
  row_count    NUMBER,
  loaded_at    TIMESTAMP_LTZ
) COMMENT = 'Sync metadata: one row per merge batch';

INSERT INTO _SYNC_META__MERGE_BATCH
SELECT 'B-SEED', $OP, column1, column2, CURRENT_TIMESTAMP()
FROM VALUES ('MEMBERS__MEMBER', 2000), ('SYSTEM__PAYMENT', 6000), ('SYSTEM__BOOKING', 9000);

-- ---------------------------------------------------------------------------
-- Central custom DMFs (define once, attach to every operator)
-- ---------------------------------------------------------------------------
USE SCHEMA GLADSTONE_DQ_LAB.DQ_COMMON;

-- Tenant isolation: an operator database should only ever contain its own OPERATOR_ID.
-- Returns the number of rows whose operator_id differs from the table's dominant operator.
CREATE OR REPLACE DATA METRIC FUNCTION FOREIGN_OPERATOR_ROWS(t TABLE(operator_id VARCHAR))
RETURNS NUMBER
COMMENT = 'Rows belonging to an operator other than the table''s own (cross-tenant leak). Expect 0.'
AS $$
  SELECT COUNT_IF(operator_id <> (SELECT MODE(operator_id) FROM t)) FROM t
$$;

-- Bronze -> Silver lag: seconds between the newest Bronze load and the newest load reflected in REPORTING.
CREATE OR REPLACE DATA METRIC FUNCTION REPORTING_LAG_SECONDS(
    silver TABLE(last_loaded_at TIMESTAMP_LTZ),
    bronze TABLE(_loaded_at TIMESTAMP_LTZ))
RETURNS NUMBER
COMMENT = 'How far a REPORTING dynamic table trails its Bronze source, in seconds. Expect < 300.'
AS $$
  SELECT GREATEST(0, DATEDIFF(second,
           (SELECT MAX(last_loaded_at) FROM silver),
           (SELECT MAX(_loaded_at) FROM bronze)))
$$;

-- Business rule: a member with a leave date cannot be ACTIVE (catches source status drift).
CREATE OR REPLACE DATA METRIC FUNCTION ACTIVE_BUT_LEFT(t TABLE(status VARCHAR, left_on DATE))
RETURNS NUMBER
COMMENT = 'Members marked ACTIVE that have a leave date. Expect 0.'
AS $$
  SELECT COUNT_IF(status = 'ACTIVE' AND left_on IS NOT NULL) FROM t
$$;

GRANT USAGE ON ALL DATA METRIC FUNCTIONS IN SCHEMA GLADSTONE_DQ_LAB.DQ_COMMON TO ROLE DQ_LAB_ATTENDEE;

-- Sanity check
SELECT 'members' t, COUNT(*) FROM GLADSTONE_DQ_LAB.ADMIN_OPERATOR_TEMPLATE.MEMBERS__MEMBER
UNION ALL SELECT 'bookings', COUNT(*) FROM GLADSTONE_DQ_LAB.ADMIN_OPERATOR_TEMPLATE.SYSTEM__BOOKING
UNION ALL SELECT 'attendance', COUNT(*) FROM GLADSTONE_DQ_LAB.ADMIN_OPERATOR_TEMPLATE.SYSTEM__ATTENDANCE
UNION ALL SELECT 'payments', COUNT(*) FROM GLADSTONE_DQ_LAB.ADMIN_OPERATOR_TEMPLATE.SYSTEM__PAYMENT;
