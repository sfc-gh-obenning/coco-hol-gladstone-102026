# Gladstone MRM - Data quality hands-on lab (CoCo)

A 30-minute hands-on lab on data quality and monitoring for Gladstone's Nova pipelines (Dynamic Tables, Tasks,
semantic views, Cortex Agents), driven by prompts in CoCo Desktop or CoCo CLI, with Snowsight alternatives on every step.
Plus three bonus labs: budgets and resource monitors, governance and GDPR, DevOps with DCM Projects.

## Contents

| Path | What |
|---|---|
| `workshop_guide/` | Streamlit lab guide (entry: `Workshop_Guide_Start.py`) |
| `sql/00_admin_setup.sql` ... `02_lab_procs.sql` | Core setup source. The guide's **Lab setup → Setup** tab combines them with the roster into one script |
| `sql/answer_key_core.sql` | What CoCo should generate in Sessions 2-4 |
| `sql/99_reset_attendee.sql`, `sql/98_teardown.sql` | Reset one attendee; remove everything |
| `sql/bonus/` | B1 / B2 / B3 setup, answer keys, teardowns; `dcm_project/` |
| `FACILITATOR_GUIDE.html` | **Internal, not for the customer.** Timeline, admin email, day-of runbook, talk track, faults and fixes |
| `sql/day2/` | Day 2 AI/ML: feedback data setup, answer key (AISQL, churn model, proc, semantic view, agent), teardown |
| `ADMIN_PREFLIGHT_QUESTIONNAIRE.md` | 18 questions for the Gladstone admin, plus a T-5 email |
| `ATTENDEE_PREP.md` | Attendee sheet: things to do, know and expect |
| `LEAVE_BEHIND.md` | Rollout pattern, GDPR checklist, cost controls |
| `plans/` | Versioned lab plan (`VERSIONS.md`) |
| `tools/check_links.py` | Re-verify every reference link |

## Run the guide locally

```bash
cd workshop_guide
pip install -r requirements.txt
streamlit run Workshop_Guide_Start.py
PYTHONPATH=. python tools/test_app.py   # headless render test of every page
```

## Deploy to Streamlit Community Cloud

Push this folder to a GitHub repo, then in share.streamlit.io create an app with main file
`workshop_guide/Workshop_Guide_Start.py`. The guide reads the SQL scripts from `sql/` and the hand-outs
(questionnaire, roster, attendee prep) from this folder at runtime, so keep the folder layout.

All lab data is synthetic. Nothing in this repo connects to Snowflake from the guide.
