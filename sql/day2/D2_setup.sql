-- =============================================================================
-- Gladstone MRM | Day 2: AI/ML | D2_setup.sql (ADMIN, run once, after SETUP_ALL)
-- Adds the one thing Day 2 needs that the Bronze tables don't have: free text.
--   1. ADMIN_OPERATOR_TEMPLATE.MEMBERS__FEEDBACK  - synthetic member feedback
--      (front-desk notes, app reviews, emails). Deterministic (HASH, no RANDOM).
--   2. ADMIN.D2_SETUP_ALL()  - copies it into every CUST_<NAME>, owned by DQ_LAB_<NAME>.
-- Signal design: cancelled and frozen members wrote more negative feedback and
-- more "thinking of leaving" comments, usually WITHOUT the word "cancel", so a
-- keyword search misses them and AI_FILTER / AI_SENTIMENT / AI_CLASSIFY don't.
-- Feedback is dated BEFORE left_on, so it is a fair (non-leaky) churn feature.
-- No personal data goes to the LLM: feedback text holds no names or contact details.
-- Teardown: D2_teardown.sql (or 98_teardown.sql drops everything).
-- =============================================================================
USE ROLE DQ_LAB_ADMIN;
USE WAREHOUSE DQ_LAB_WH;
USE SCHEMA GLADSTONE_DQ_LAB.ADMIN_OPERATOR_TEMPLATE;

CREATE OR REPLACE TABLE MEMBERS__FEEDBACK (
  feedback_id    VARCHAR,
  operator_id    VARCHAR,
  member_id      VARCHAR,
  site_id        VARCHAR,
  channel        VARCHAR,        -- FRONT_DESK / APP_REVIEW / EMAIL
  feedback_at    TIMESTAMP_LTZ,
  feedback_text  VARCHAR,
  _loaded_at     TIMESTAMP_LTZ
) COMMENT = 'Bronze MEMBERS: free-text member feedback (synthetic). Day 2 AI/ML input.';

INSERT INTO MEMBERS__FEEDBACK
WITH m AS (
  SELECT member_id, operator_id, home_site_id, status, left_on, ABS(HASH(member_id, 'fb')) AS h
  FROM MEMBERS__MEMBER
),
n AS (   -- 0, 1 or 2 comments per member (cancelled/frozen members comment more often)
  SELECT m.*, g.k
  FROM m, (SELECT SEQ4() AS k FROM TABLE(GENERATOR(ROWCOUNT => 2))) g
  WHERE g.k < CASE WHEN status = 'ACTIVE' THEN MOD(h, 3) ELSE 1 + MOD(h, 2) END
),
c AS (
  SELECT n.*, ABS(HASH(member_id, k, 'c')) AS hc, ABS(HASH(member_id, k, 't')) AS ht,
         CASE status
           WHEN 'CANCELLED' THEN CASE WHEN MOD(ABS(HASH(member_id, k, 'c')), 100) < 55 THEN 'LEAVE'
                                      WHEN MOD(ABS(HASH(member_id, k, 'c')), 100) < 80 THEN 'NEG'
                                      WHEN MOD(ABS(HASH(member_id, k, 'c')), 100) < 92 THEN 'NEU' ELSE 'POS' END
           WHEN 'FROZEN'    THEN CASE WHEN MOD(ABS(HASH(member_id, k, 'c')), 100) < 30 THEN 'LEAVE'
                                      WHEN MOD(ABS(HASH(member_id, k, 'c')), 100) < 55 THEN 'NEG'
                                      WHEN MOD(ABS(HASH(member_id, k, 'c')), 100) < 80 THEN 'NEU' ELSE 'POS' END
           ELSE                  CASE WHEN MOD(ABS(HASH(member_id, k, 'c')), 100) < 7  THEN 'LEAVE'
                                      WHEN MOD(ABS(HASH(member_id, k, 'c')), 100) < 25 THEN 'NEG'
                                      WHEN MOD(ABS(HASH(member_id, k, 'c')), 100) < 55 THEN 'NEU' ELSE 'POS' END
         END AS kind
  FROM n
)
SELECT 'FB-' || SUBSTR(member_id, 3) || '-' || k,
       operator_id,
       member_id,
       home_site_id,
       DECODE(MOD(hc, 3), 0, 'FRONT_DESK', 1, 'APP_REVIEW', 'EMAIL'),
       CASE WHEN left_on IS NOT NULL THEN DATEADD(hour, -(24 * (5 + MOD(ht, 50)) + MOD(hc, 24)), left_on::TIMESTAMP_LTZ)
            ELSE DATEADD(hour, -(24 * MOD(ht, 90) + MOD(hc, 24)), CURRENT_TIMESTAMP()) END,
       CASE kind
         WHEN 'LEAVE' THEN GET(ARRAY_CONSTRUCT(
           'Honestly not sure the Premium Plus is worth it any more. The Pure Gym in town is half the price.',
           'Starting a new job in Reading next month so probably won''t be able to get here much after that.',
           'Third time this month the spin class was full. I''m paying for classes I can''t get into. Reconsidering my membership.',
           'Can you tell me what the notice period is on my contract? Just want to understand my options.',
           'Knee surgery means I won''t be training for a while. Is there a way to stop paying until I''m back?',
           'Member asked at reception how to end the direct debit and whether there is an exit fee.',
           'Moving house in the summer, the new place is nowhere near any of your centres.',
           'The price went up again and nothing has improved. I''ll be looking elsewhere when my contract is up.',
           'Pool has been closed for maintenance for weeks. If it is not open soon I don''t see the point in staying.',
           'Asked about switching to off-peak or freezing - money is tight at the moment.'), MOD(ht, 10))::VARCHAR
         WHEN 'NEG' THEN GET(ARRAY_CONSTRUCT(
           'Changing rooms were dirty again this evening and two of the showers were cold.',
           'The app keeps logging me out when I try to book a class.',
           'Treadmill 4 has had an out of order sign on it for two weeks.',
           'Car park was full at 6pm, had to park on the road and got a ticket.',
           'Instructor was 15 minutes late for HIIT and didn''t apologise.',
           'Way too busy after work, waited 10 minutes for a squat rack.',
           'Got charged twice this month, still waiting for the refund.',
           'Aqua Fit was cancelled with no notice. Third time this term.'), MOD(ht, 8))::VARCHAR
         WHEN 'NEU' THEN GET(ARRAY_CONSTRUCT(
           'Could you add a later Pilates class on Thursdays?',
           'What time does the pool open on bank holidays?',
           'Member asked for a copy of the class timetable for next month.',
           'Is there a guest pass I can use for my brother when he visits?',
           'Lost a water bottle in the studio on Monday, has anyone handed it in?',
           'Please update my postcode, I''ve moved within Oxford.'), MOD(ht, 6))::VARCHAR
         ELSE GET(ARRAY_CONSTRUCT(
           'Love the new spin bikes, great class with Jess this morning!',
           'Staff on reception are always friendly and helpful.',
           'Swim lessons have been brilliant for my daughter, thank you.',
           'Gym floor is so much better since the refurb.',
           'Yoga on Sunday mornings is the highlight of my week.',
           'Thanks for sorting out my booking so quickly yesterday.'), MOD(ht, 6))::VARCHAR
       END,
       CURRENT_TIMESTAMP()
FROM c;

SELECT channel, COUNT(*) FROM MEMBERS__FEEDBACK GROUP BY 1;   -- expect ~1,900 rows

-- ---------------------------------------------------------------------------
-- Copy into every operator. Attendee procs run as the operator role, which owns its schema,
-- so CREATE TABLE / PROCEDURE / MODEL / SEMANTIC VIEW / AGENT need no extra grants.
-- ---------------------------------------------------------------------------
USE SCHEMA GLADSTONE_DQ_LAB.ADMIN;
CREATE OR REPLACE PROCEDURE GLADSTONE_DQ_LAB.ADMIN.D2_SETUP_ALL()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
  n NUMBER DEFAULT 0;
  fq VARCHAR;
  c1 CURSOR FOR SELECT schema_name, role_name FROM GLADSTONE_DQ_LAB.ADMIN.ATTENDEES;
BEGIN
  FOR r IN c1 DO
    fq := 'GLADSTONE_DQ_LAB.' || r.schema_name;
    EXECUTE IMMEDIATE 'CREATE OR REPLACE TABLE ' || :fq || '.MEMBERS__FEEDBACK AS
       SELECT * REPLACE (''' || r.schema_name || ''' AS operator_id)
       FROM GLADSTONE_DQ_LAB.ADMIN_OPERATOR_TEMPLATE.MEMBERS__FEEDBACK';
    EXECUTE IMMEDIATE 'GRANT OWNERSHIP ON TABLE ' || :fq || '.MEMBERS__FEEDBACK TO ROLE ' || r.role_name || ' COPY CURRENT GRANTS';
    n := n + 1;
  END FOR;
  RETURN n || ' operator(s) have MEMBERS__FEEDBACK';
END;
$$;

CALL GLADSTONE_DQ_LAB.ADMIN.D2_SETUP_ALL();

-- ---------------------------------------------------------------------------
-- Pre-flight (record on the "Azure UK South availability" page)
-- ---------------------------------------------------------------------------
USE ROLE ACCOUNTADMIN;
-- AI_SENTIMENT / AI_CLASSIFY / AI_FILTER / AI_AGG: check native availability in this region,
-- or whether CORTEX_ENABLED_CROSS_REGION must allow EU routing (a UK-residency decision for Gladstone).
SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;
-- The training proc uses Anaconda packages scikit-learn and snowflake-ml-python:
-- the Anaconda terms must be acknowledged once in Admin » Billing & Terms.
SELECT COUNT(*) AS sklearn_versions FROM INFORMATION_SCHEMA.PACKAGES
 WHERE language = 'python' AND package_name IN ('scikit-learn', 'snowflake-ml-python');
