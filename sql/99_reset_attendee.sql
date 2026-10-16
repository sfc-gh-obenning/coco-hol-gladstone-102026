-- =============================================================================
-- Gladstone MRM | Data Quality HOL | 99_reset_attendee.sql
-- Give one attendee a fresh operator (re-clones CUST_<NAME> from the template).
-- Their data quality monitors are removed by the re-clone; they re-run Session 2.
-- =============================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DQ_LAB_WH;

CALL GLADSTONE_DQ_LAB.ADMIN.RESET_ATTENDEE('NIELS');      -- <- attendee short name

-- Optional: re-inject that attendee's fault (same slot -> same fault)
-- CALL GLADSTONE_DQ_LAB.ADMIN.INJECT_FAULTS('NIELS');

-- Reset the whole room back to "start of Session 3" (faults re-applied to everyone):
-- CALL GLADSTONE_DQ_LAB.ADMIN.INJECT_FAULTS('ALL');
