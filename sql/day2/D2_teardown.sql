-- =============================================================================
-- Gladstone MRM | Day 2: AI/ML | D2_teardown.sql (ADMIN)
-- Removes only Day 2 objects from every operator schema; the core lab keeps running.
-- (98_teardown.sql drops the whole database, which also removes all of this.)
-- =============================================================================
USE ROLE DQ_LAB_ADMIN;
USE WAREHOUSE DQ_LAB_WH;

CREATE OR REPLACE PROCEDURE GLADSTONE_DQ_LAB.ADMIN.D2_TEARDOWN_ALL()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
  n NUMBER DEFAULT 0;
  fq VARCHAR;
  c1 CURSOR FOR SELECT schema_name FROM GLADSTONE_DQ_LAB.ADMIN.ATTENDEES;
BEGIN
  FOR r IN c1 DO
    fq := 'GLADSTONE_DQ_LAB.' || r.schema_name;
    EXECUTE IMMEDIATE 'DROP AGENT IF EXISTS ' || :fq || '.RETENTION_AGENT';
    EXECUTE IMMEDIATE 'DROP SEMANTIC VIEW IF EXISTS ' || :fq || '.SV_MEMBER_RETENTION';
    EXECUTE IMMEDIATE 'DROP PROCEDURE IF EXISTS ' || :fq || '.GET_CHURN_RISK(VARCHAR, NUMBER)';
    EXECUTE IMMEDIATE 'DROP PROCEDURE IF EXISTS ' || :fq || '.TRAIN_CHURN_MODEL()';
    EXECUTE IMMEDIATE 'DROP MODEL IF EXISTS ' || :fq || '.CHURN_MODEL';
    EXECUTE IMMEDIATE 'DROP TABLE IF EXISTS ' || :fq || '.MEMBER_CHURN_SCORES';
    EXECUTE IMMEDIATE 'DROP TABLE IF EXISTS ' || :fq || '.MEMBER_CHURN_FEATURES';
    EXECUTE IMMEDIATE 'DROP TABLE IF EXISTS ' || :fq || '.MEMBERS__FEEDBACK_ENRICHED';
    EXECUTE IMMEDIATE 'DROP TABLE IF EXISTS ' || :fq || '.MEMBERS__FEEDBACK';
    n := n + 1;
  END FOR;
  DROP TABLE IF EXISTS GLADSTONE_DQ_LAB.ADMIN_OPERATOR_TEMPLATE.MEMBERS__FEEDBACK;
  RETURN 'Day 2 objects removed from ' || n || ' operator(s)';
END;
$$;

CALL GLADSTONE_DQ_LAB.ADMIN.D2_TEARDOWN_ALL();
