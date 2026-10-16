# Gladstone MRM | Data quality HOL | Admin preflight questionnaire

For the Gladstone Snowflake admin. Answering these before the day turns a live setup risk into a 15-minute script run.
Items marked **T-5** are needed five working days before the lab; the rest by T-3.

## 1. Access and identity

| # | Question | Why we ask | When |
|---|---|---|---|
| 1 | Who will run setup, and do they have ACCOUNTADMIN (or SYSADMIN plus SECURITYADMIN)? | Setup creates roles, a warehouse, a resource monitor and an email integration, and grants account-level privileges | **T-5** |
| 2 | What are the attendees' exact Snowflake user names (fill in `ATTENDEE_ROSTER.csv`)? Do they sign in with SSO (Entra ID) or password plus MFA? | Roles are granted per user name; a typo is the most common setup failure | **T-5** |
| 3 | Are users provisioned by SCIM? | If SCIM owns user properties, we leave `DEFAULT_ROLE` alone (`"set_defaults": false`) and attendees run `USE ROLE` | T-3 |
| 4 | Can we create a temporary user for a walk-in, or is that blocked by policy? | Decides whether walk-ins without a user pair up or get a spare operator | T-3 |

## 2. CoCo and Cortex readiness (Azure UK South)

| # | Question | Why we ask | When |
|---|---|---|---|
| 5 | Is CoCo Desktop or CLI installed and signed in for each attendee? Who approves installs (IT, managed laptop policy)? | CoCo is the primary route through the lab; installs can take days to approve | **T-5** |
| 6 | What is `CORTEX_ENABLED_CROSS_REGION` set to, and does your data policy allow cross-region inference? | Some models are not hosted in UK South; without cross-region, CoCo and the agent step may fail | **T-5** |
| 7 | Is `SNOWFLAKE.CORTEX_USER` restricted, or are there model allow-lists? | Attendees need Cortex access through the `DQ_LAB_ATTENDEE` role | T-3 |
| 8 | Can you run section 6 (pre-flight checks) of `sql/00_admin_setup.sql` on its own - it is read-only - and send us the output? | Confirms the region and cloud, which system DMFs your account has, and the cross-region setting, so we can adjust the lab before setup | **T-5** |

## 3. Account settings that block scripts

| # | Question | Why we ask | When |
|---|---|---|---|
| 9 | Do you use managed-access schemas, or policies that restrict who can grant on objects? | Setup hands each attendee ownership of their schema | T-3 |
| 10 | Are there account-level resource monitors, budgets or warehouse limits that could conflict with `DQ_LAB_RM` (20 credits)? | Avoids a parent monitor suspending the lab warehouse mid-session | T-3 |
| 11 | Is the account Enterprise Edition or higher? | DMFs, masking, row access and tag-based masking (Bonus B2) need it | T-3 |
| 12 | Which email address should lab notifications go to? It must be a verified email on a Snowflake user. | Required by `DQ_LAB_EMAIL_INT`; replaces `LAB_ADMIN_EMAIL` in `00_admin_setup.sql` | **T-5** |

## 4. Bonus labs (only if offered)

| # | Question | Why we ask | When |
|---|---|---|---|
| 13 | B3: can attendees install Snowflake CLI 3.17+ and reach GitHub? Is key-pair or PAT authentication allowed for CI? | `snow dcm` runs from the CLI; if not, run B3 as a facilitator demo | T-3 |
| 14 | B1: can attendees read `SNOWFLAKE.ACCOUNT_USAGE`? Is the account budget already activated? | Budget and cost views | T-3 |
| 15 | B2: do you have an existing tagging or classification standard for PII? | We mirror your tag names instead of inventing ours | T-3 |

## 5. Logistics

| # | Question | Why we ask | When |
|---|---|---|---|
| 16 | When can we do a 15-minute dry run with one or two attendees at T-1? | Catches login and CoCo issues while there is time to fix them | T-3 |
| 17 | Are the names `GLADSTONE_DQ_LAB`, `DQ_LAB_*` and `CUST_*` acceptable? Any reserved prefixes? | Avoids a rename on the day | T-3 |
| 18 | When should teardown run (straight after, or keep for a week of self-study)? Who signs off? | Bounds cost and data retention | T-3 |

## Copy-paste email (T-5)

> Subject: Data quality hands-on lab - six quick questions before setup
>
> Hi,
>
> Ahead of the data quality lab on <date>, could you help with six things so setup takes 15 minutes rather than an hour?
>
> 1. Who will run the setup scripts, and do they have ACCOUNTADMIN?
> 2. The attendees' exact Snowflake user names (template attached: ATTENDEE_ROSTER.csv), and whether they use SSO or password plus MFA.
> 3. Is CoCo Desktop or CLI installed for each attendee, and who approves installs?
> 4. The value of `CORTEX_ENABLED_CROSS_REGION`, and whether cross-region inference is allowed.
> 5. The output of section 6 (pre-flight checks) of `00_admin_setup.sql` - three read-only statements you can run on their own.
> 6. A verified email address for lab notifications.
>
> Thanks,
> <name>
