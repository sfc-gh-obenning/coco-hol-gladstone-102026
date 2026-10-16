# Gladstone MRM | Data quality HOL | Facilitator run sheet

30-minute core lab, one operator per attendee. Times are minutes from the start.

## Timeline

| When | Who | Do |
|---|---|---|
| T-5 working days | Facilitator | Send the admin `ADMIN_PREFLIGHT_QUESTIONNAIRE.md` (the six "send at T-5" items) and ask for `ATTENDEE_ROSTER.csv` filled in. Send attendees `ATTENDEE_PREP.md`. |
| T-5 | Admin | Check every roster user exists: `SHOW USERS LIKE '<user>';`. Fix typos now, not on the day. |
| T-3 | Admin | Run the setup below, including spares. Send back the pre-flight output and `SELECT * FROM GLADSTONE_DQ_LAB.ADMIN.V_ROSTER;`. |
| T-1 | Each attendee | Log in, open CoCo, run the test prompt on the Before you start page. Tell the facilitator if anything fails. |
| T-1 | Facilitator | Check `V_ROSTER`: everyone `ASSIGNED`, a recent `LAST_SUCCESS_LOGIN` (the view can lag up to ~2 hours), and at least 2 `SPARE - free`. |
| T-0 | Facilitator | Walk-ins: `CALL GLADSTONE_DQ_LAB.ADMIN.CLAIM_SPARE('<USER>');` (see below). |

## Setup (admin, T-3, ~15 min)

1. Edit `LAB_ADMIN_EMAIL` and run `sql/00_admin_setup.sql` as ACCOUNTADMIN. Record the pre-flight output (DMF list, cross-region setting).
2. Run `sql/01_build_template.sql`, then `sql/02_lab_procs.sql`.
3. Build one operator per roster row, about 20 seconds per attendee. Any row whose user can't be found is listed under "Check:"; fix the name and bind it with `CALL GLADSTONE_DQ_LAB.ADMIN.BIND_USER('<USER>', '<NAME>', TRUE);`.

   ```sql
   CALL GLADSTONE_DQ_LAB.ADMIN.SETUP_ALL(PARSE_JSON('[{"user":"<USER>","name":"<NAME>"}, ...]'));
   ```

   - If users are managed by SCIM, or you don't want their `DEFAULT_ROLE` changed, add `"set_defaults": false` to the row. Those attendees run `USE ROLE DQ_LAB_<NAME>;` first; Getting started covers this.
   - When defaults are changed, the original role and warehouse are recorded and put back by `98_teardown.sql`.
4. Build spare operators for walk-ins. Use 3, or 10% of the headcount if that's higher.

   ```sql
   CALL GLADSTONE_DQ_LAB.ADMIN.SETUP_SPARES(3);
   ```

5. Smoke test one attendee role (Admin setup page, step 5). Confirm that cross-schema access fails.
6. Optional bonus setups:
   - `sql/bonus/B1_setup.sql`
   - `sql/bonus/B2_setup.sql`, after `SETUP_ALL` (it grants the test roles to attendee users; re-run it after claiming spares)
   - `sql/bonus/B3_setup.sql`
7. Send each attendee their operator name, CoCo connection details and the guide URL.

## Walk-ins (on the day)

| Situation | Action | Time |
|---|---|---|
| Has a Snowflake user, spare free | `CALL GLADSTONE_DQ_LAB.ADMIN.CLAIM_SPARE('<USER>');` then give them the operator name it returns (for example SPARE01) | ~1 s |
| Has a user, no spare left | Same call: it builds a new operator named after the user | ~20 s |
| User name not found | The call returns ERROR and claims nothing. Check `SHOW USERS LIKE '%<part>%';` | - |
| No Snowflake user | Pair them with a neighbour (read along on the neighbour's operator), or create a temporary user if your policy allows, then claim a spare | - |
| Arrives after faults were injected | `CALL GLADSTONE_DQ_LAB.ADMIN.INJECT_FAULTS('<NAME>');` once they finish Session 2 | ~2 s |

Spares get faults from `INJECT_FAULTS('ALL')` like everyone else. An unclaimed spare just carries a fault no one looks at.

## Day of

| Time | What happens | Facilitator |
|---|---|---|
| -10 | Attendees connect CoCo, set role `DQ_LAB_<NAME>`, run the Getting started check | Help with connections |
| 0-4 | Session 1: explain the pipeline, two KPIs | Point out the two "active members" numbers |
| 4-11 | Session 2: monitors and expectations | Everyone's 7 expectations pass |
| 11 | **Inject faults** | `CALL GLADSTONE_DQ_LAB.ADMIN.INJECT_FAULTS('ALL');` |
| 11-20 | Session 3: diagnose | Scheduled checks run every 5 min; tell people to evaluate now if needed. Answer key: `SELECT * FROM GLADSTONE_DQ_LAB.ADMIN.V_FLEET_ANSWER_KEY;` |
| 20-26 | Session 4: circuit breaker, fix, alerts | Fixes per fault are on the Session 4 page |
| 26-30 | Session 5: fleet view | Show `ADMIN.V_FLEET_DQ_HEALTH` on screen; mention the Snowsight data quality dashboard |
| 30 | Wrap up | Point to Stretch and Bonus labs; share `LEAVE_BEHIND.md` |

Fault by setup order (repeats every six attendees): 1 Bifrost replay, 2 merge task stalled, 3 refund sign flip,
4 orphan attendance, 5 tenant leak, 6 status drift.

## Talking points

- Expectations catch invariants on the first bad run; anomaly detection needs about two weeks of history (shows `TRAINING_IN_PROGRESS` today).
- The stalled task shows FRESHNESS failing while Bronze-to-REPORTING lag stays 0: the source stopped, not REPORTING. That's why both checks are needed.
- The status-drift fault is a semantic-layer problem: the agent answers "active members" from the verified query (paid in 35 days), the dashboard from status.
- Tenant leak is also a GDPR incident: row access by operator hides it immediately (Bonus B2).

## If something goes wrong

| Problem | Action |
|---|---|
| Attendee broke their operator | `CALL GLADSTONE_DQ_LAB.ADMIN.RESET_ATTENDEE('<NAME>');` then optionally `INJECT_FAULTS('<NAME>')` |
| Attendee missing | `CALL GLADSTONE_DQ_LAB.ADMIN.SETUP_ATTENDEE('<USER>', '<NAME>');` |
| Warehouse queuing | `ALTER WAREHOUSE DQ_LAB_WH SET MAX_CLUSTER_COUNT = 3;` (already the default) |
| Notification emails flood | `ALTER DATABASE GLADSTONE_DQ_LAB UNSET DATA_QUALITY_MONITORING_SETTINGS;` |

## After

- Run `CALL GLADSTONE_DQ_LAB.ADMIN.SUSPEND_ALL();` immediately after the session to stop compute.
- When bonus labs are done: `sql/98_teardown.sql` (removes everything, including bonuses and spares, and restores attendees' original default role and warehouse). Drop any temporary walk-in users by hand.

## Dry-run results (demo account, 16 Oct 2026)

- 6 operators set up in ~1m45s; all Dynamic Tables INCREMENTAL and owned by the attendee role; cross-schema access denied.
- Clean data: all 7 expectations pass. Faults detected: DUPLICATE_COUNT 150, NEGATIVE_COUNT 40, REFERENTIAL_INTEGRITY_COUNT 60,
  FOREIGN_OPERATOR_ROWS 50, ACTIVE_BUT_LEFT 292, FRESHNESS 408s for the stalled task.
- Circuit breaker suspended 2 REPORTING DTs, then returned "CLOSED: Bronze clean" after the fix.
- B1 budget + tag + linked resource; B2 masking, row access, SAR, erasure, erasure DMF = 0, Time Travel lesson, B2 teardown;
  B3 DCM create / plan / deploy / test 5/5, re-plan of 2 ALTERs, test exits 1 on a failed expectation.

## Say this (story script)

Cast: **Sam** (operator ops manager), **Priya** (Gladstone Customer Success), **you** (on-call data engineer). Read the line, then let the room work. Same words as the chapter cards in the guide.

| When | Say |
|---|---|
| Minute 0 (opener, 60 s) | "It's Monday at Gladstone. Each of you is on call for one operator on Nova. In 30 minutes, something will break in every one of them - and you'll find out before the operator does." |
| Start of chapter 1: Meet the pipeline | "First, learn the pipeline you're on call for, and what its numbers say on a good day." |
| Start of chapter 2: Monitor | "Nothing is broken yet. Put monitors on your operator now." |
| Start of chapter 3: Diagnose | "I've just broken something in every operator - a different thing for each of you. Your operator is on the phone. Find out what happened." |
| Start of chapter 4: Contain | "Now stop it spreading, and make sure the next one emails you instead of the operator calling." |
| Start of chapter 5: Fleet | "Priya's stand-up: which operators do we call first? Let's look at all of you at once." |
| Close | Read the epilogue on the last session page aloud. |
