# Gladstone MRM | Data quality hands-on lab | Before you start

30 minutes, hands-on, in Gladstone's own Snowflake account. Please do the first section a day before.

## Things to do

**The day before (10 minutes)**

1. **Log in to Snowflake** (`GLADSTONESOFTWARE`) in a browser with your usual sign-in (SSO or MFA). If it fails, tell your admin now, not on the day.
2. **Install and sign in to CoCo** - Cortex Code Desktop or the CoCo CLI. Either works for every step. Connect it to `GLADSTONESOFTWARE`.
3. **Run this test prompt in CoCo:** *"What is my current user, role and warehouse? Run select current_user(), current_role(), current_warehouse()."* If you get an answer back, CoCo is working.
4. **Confirm your operator name** with the facilitator (for example `NIELS`). It names your schema `CUST_<NAME>` and your role `DQ_LAB_<NAME>`.
5. **Bonus B3 only (optional):** install Snowflake CLI 3.17 or later (`snow --version`) and make sure you can reach GitHub.

**On the day (5 minutes before)**

1. Open the lab guide and type your operator name into the sidebar box. Every prompt updates to your schema.
2. Follow **Getting started**: set role `DQ_LAB_<NAME>` and warehouse `DQ_LAB_WH`, then run the check prompt.
3. Not on the attendee list? Tell the facilitator. A spare operator (for example `SPARE01`) takes about a second to hand over.

## Things to know

- **You get your own operator.** Your schema `CUST_<NAME>` stands in for one operator's own database. You own everything in it, and you can't see anyone else's - the same isolation Gladstone has between operators.
- **The data is synthetic.** Members, bookings, payments and check-ins are generated for the lab. No real member data is used.
- **Gladstone's names.** Bronze tables use the Bifrost layout (`MEMBERS__*`, `SHARED__*`, `SYSTEM__*`, `_SYNC_META__*`); Silver is `REPORTING__*` Dynamic Tables; Gold is a semantic view that the Nova agent answers from.
- **CoCo first, Snowsight always.** Every step is a CoCo prompt. Each one also has a *Do it in Snowsight* route and a *Behind? Run this* box with the exact SQL.
- **Read before you approve.** CoCo shows the SQL before running it. You're working in Gladstone's real account, so read it and approve deliberately.
- **Things will break on purpose.** Partway through, the facilitator injects one realistic fault into every operator (a replayed merge batch, a stalled task, a refund sign flip, and so on). Finding yours is the lab.
- **Cost is capped.** One shared warehouse with a 20-credit resource monitor. You can't run up a bill.
- **Availability.** A few features in the stretch and bonus sections are flagged on the *Azure UK South availability* page. The 30-minute core works without them.

## What to expect

| Minutes | Session | You will |
|---|---|---|
| 0-4 | 1. Meet your operator pipeline | See Bronze, REPORTING and the semantic view, and the two "active members" numbers |
| 4-11 | 2. Put monitors on it | Attach data metric functions and expectations - all 7 pass on clean data |
| 11 | Faults injected | The facilitator breaks something in every operator |
| 11-20 | 3. Diagnose a broken answer | Find which check failed, which rows and why |
| 20-26 | 4. Contain and alert | Build a circuit breaker that pauses REPORTING, fix the data, turn on alerts |
| 26-30 | 5. Fleet view across operators | See every operator's health in one view |

- **Short waits are normal.** Scheduled checks run every 5 minutes. When you don't want to wait, the guide shows how to evaluate on demand.
- **CoCo's output varies.** The same prompt can produce slightly different SQL or wording. That's fine - the checkpoint under each step says what "good" looks like.
- **Falling behind is fine.** Every section has a catch-up box. The facilitator can reset your operator in seconds.
- **Afterwards:** the guide stays online, with stretch and bonus labs (budgets, GDPR and governance, DevOps with DCM) and a leave-behind summary. Your schema is kept until the admin runs teardown - ask the facilitator when that will be.
