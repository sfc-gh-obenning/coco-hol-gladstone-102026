import re

import streamlit as st

from components import (render_checkpoint, render_execution_context, render_explanation, render_fallback,
                        render_key_concepts, render_prompt, render_real_world_examples, render_references,
                        render_session_header, render_snowsight_route, render_technologies_used, render_what_why,
                        render_what_you_built, sql_file)
from content import links as L


def answer_key(step: str) -> str:
    """One step of sql/day2/D2_answer_key.sql, pointed at the attendee's schema (tested SQL, never retyped)."""
    text = sql_file("day2/D2_answer_key.sql")
    m = re.search(rf"^-- {re.escape(step)}\b.*?(?=^-- D2\.\d|\Z)", text, re.S | re.M)
    body = m.group(0).strip() if m else f"-- {step} not found in sql/day2/D2_answer_key.sql"
    body = body.replace("GLADSTONE_DQ_LAB.CUST_<NAME>", "{FQ_SCHEMA}").replace("DQ_LAB_WH", "{WH}")
    return "USE ROLE {ROLE};\nUSE WAREHOUSE {WH};\nUSE SCHEMA {FQ_SCHEMA};\n\n" + body


render_session_header("Day 2", "AI/ML: predict which members will cancel", "75-90 min",
                      "AISQL features, a registered churn model, a scoring proc, a semantic view and a retention agent")
render_execution_context()

with st.chat_message("Priya", avatar=":material/support_agent:"):
    st.markdown("**Priya, Customer Success:** *\"Sam's operator lost 300 members last quarter. Their front desk says "
                "people complain for weeks before they cancel, but nobody reads the notes. Can Nova tell Sam who is "
                "about to leave, before they do?\"*")

render_what_why(
    "Use **AISQL** to turn free-text member feedback into features, train a **churn model** in Snowflake and "
    "register it, wrap it in a **stored procedure**, put a **semantic view** on the new dataset, and give a "
    "**Cortex Agent** both: the semantic view for *how many* and the model for *who*.",
    "Your operators already hold the signal, in feedback nobody has time to read. AISQL reads it once, in SQL, next "
    "to the data. The model, the agent and the governance all stay in the operator's database, and the same pattern "
    "can be stamped across every operator.",
)

st.markdown("""
| Step | Time | You build |
|---|---|---|
| D2.1 | 5 min | Look at `MEMBERS__FEEDBACK` (new free-text table from your admin) |
| D2.2 | 15 min | `MEMBERS__FEEDBACK_ENRICHED`: sentiment, topic and intent to leave via AISQL |
| D2.3 | 10 min | `MEMBER_CHURN_FEATURES`: one row per member, behaviour + AI features |
| D2.4 | 15 min | `CHURN_MODEL` trained in a warehouse and registered in the Model Registry |
| D2.5 | 10 min | `MEMBER_CHURN_SCORES` and the `GET_CHURN_RISK` stored procedure |
| D2.6 | 10 min | `SV_MEMBER_RETENTION` semantic view |
| D2.7 | 15 min | `RETENTION_AGENT` with the semantic view and the model-backed proc |
""")
st.info(":material/info: Day 2 needs `MEMBERS__FEEDBACK` in your schema. Your admin creates it with "
        "`sql/day2/D2_setup.sql` - see **Lab setup (admin)**. Run D2.1 first to check it's there.", icon=None)

# ── D2.1 ──────────────────────────────────────────────────────────────────────
st.markdown("### D2.1. Meet the feedback")
render_prompt("Prompt D2.1", "What are members telling us?", """In {FQ_SCHEMA}, look at MEMBERS__FEEDBACK.
Show row count by channel, 10 random comments, and how many comments contain the word "cancel".
Then join to MEMBERS__MEMBER and show the share of members with feedback, by status.
In two sentences: why would a keyword search on "cancel" miss most of the members who are about to leave?""")
render_explanation("What to look for", """
About 2,200 comments across front desk notes, app reviews and emails. Very few say *cancel*. People write
*"the Pure Gym in town is half the price"* or *"moving house in the summer"*. A human reads that as a leaver.
A `LIKE '%cancel%'` filter doesn't. That gap is what AISQL closes.
""")

# ── D2.2 ──────────────────────────────────────────────────────────────────────
st.markdown("### D2.2. Turn text into features with AISQL")
render_prompt("Prompt D2.2", "Enrich every comment", """In {FQ_SCHEMA}, create MEMBERS__FEEDBACK_ENRICHED from MEMBERS__FEEDBACK, keeping all columns and adding:
- SENTIMENT: AI_SENTIMENT on feedback_text, as the overall category (positive / negative / neutral / mixed)
- TOPIC: AI_CLASSIFY into exactly one of: price and value, facilities and equipment, classes and booking, staff and service, billing, personal circumstances, general enquiry, praise
- INTENT_TO_LEAVE: AI_FILTER - "Is this member signalling that they might cancel, freeze, downgrade or leave?"
Test on 10 rows first and show me the results next to the text, then run it on the whole table with warehouse {WH}.
Finally, show counts by topic and intent_to_leave, and 5 comments flagged as intent to leave that do NOT contain the word "cancel".""")
render_snowsight_route([
    "Open a worksheet in `{SCHEMA}` with warehouse `{WH}`.",
    "Paste the fallback SQL below and run it; the full table takes about 20-30 seconds on XSMALL.",
    "Check **AI & ML » AI Functions** (or `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AISQL_USAGE_HISTORY`, a few hours later) to see the token cost.",
])
render_explanation("Why preprocess instead of asking an LLM later?", """
The LLM reads each comment **once**, at ingest, and writes typed columns. After that, the model, the semantic view and
the agent all work with cheap SQL over `INTENT_TO_LEAVE`, not with an LLM re-reading text on every question.
In production this SELECT becomes a Dynamic Table, so only new feedback is ever sent to the LLM.
""")
render_fallback(answer_key("D2.2"))

# ── D2.3 ──────────────────────────────────────────────────────────────────────
st.markdown("### D2.3. Build the training dataset")
render_prompt("Prompt D2.3", "One row per member", """In {FQ_SCHEMA}, create MEMBER_CHURN_FEATURES with one row per member:
- From MEMBERS__MEMBER and MEMBERS__MEMBERSHIP: member_id, site_id (home_site_id), status, plan_name, monthly_fee
- From SYSTEM__BOOKING and SYSTEM__ATTENDANCE: bookings_28d, checkins_28d, no_show_rate
- From MEMBERS__FEEDBACK_ENRICHED: feedback_count, negative_feedback_count, intent_to_leave_count, price_complaints, facility_complaints (0 when a member has no feedback)
- Label CHURNED = 1 when status is CANCELLED, else 0
Do NOT use joined_on, left_on or last_paid_on as features (in this data they reveal the status, which would leak the label).
Deduplicate members on member_id in case Bifrost replayed a batch. Show the churn rate and the average of each feature for churned vs not churned.""")
render_explanation("Day 1 meets Day 2", """
This is where data quality pays off. If your operator has the **Bifrost replay** or **status drift** fault from Day 1,
duplicated members or cancelled members re-sent as ACTIVE become **wrong labels** in your training data. Check your
expectations from Session 2 before you train. A model can't be better than its labels.
""")
render_fallback(answer_key("D2.3"))

# ── D2.4 ──────────────────────────────────────────────────────────────────────
st.markdown("### D2.4. Train and register the model")
render_prompt("Prompt D2.4", "Train in Snowflake, log to the Model Registry", """In {FQ_SCHEMA}, create a Python stored procedure TRAIN_CHURN_MODEL() (runtime 3.11, packages snowflake-snowpark-python, snowflake-ml-python, scikit-learn, pandas, EXECUTE AS CALLER) that:
1. Reads MEMBER_CHURN_FEATURES and does a stratified 70/30 train/test split (random_state 42)
2. Trains two GradientBoostingClassifier models: behaviour only (monthly_fee, bookings_28d, checkins_28d, no_show_rate) and behaviour + the five AI feedback features
3. Computes test ROC AUC for both
4. Logs the behaviour + AI model to the Snowflake Model Registry in this schema as CHURN_MODEL, target platform WAREHOUSE, with both AUCs as metrics and a comment
5. Returns the version name, both AUCs and the top 5 feature importances
Call it on warehouse {WH}, then show SHOW VERSIONS IN MODEL CHURN_MODEL and SHOW FUNCTIONS IN MODEL CHURN_MODEL.""")
render_snowsight_route([
    "Run the fallback SQL in a worksheet: it creates and calls the procedure (about 2-3 minutes on XSMALL).",
    "Open **AI & ML » Models** » `CHURN_MODEL` to see the version, its metrics and its functions.",
])
render_checkpoint("Behaviour-only AUC should be about **0.5** (a coin flip), and behaviour + AI about **0.8 or higher**, "
                  "with `INTENT_TO_LEAVE_COUNT` as the top feature. The AISQL features are what make the model work.")
render_explanation("Why a stored procedure, and why the registry?", """
The procedure runs **inside a warehouse**, so there is no laptop Python, no data download and no extra compute pool.
Logging to the **Model Registry** makes the model a governed schema object (`MODEL`), with versions, metrics and RBAC,
that SQL can call directly as `MODEL(CHURN_MODEL, LAST)!PREDICT_PROBA(...)`.
""")
render_fallback(answer_key("D2.4"))

# ── D2.5 ──────────────────────────────────────────────────────────────────────
st.markdown("### D2.5. Score members and wrap the model in a stored procedure")
render_prompt("Prompt D2.5", "Scores table and GET_CHURN_RISK", """In {FQ_SCHEMA}:
1. Create MEMBER_CHURN_SCORES for every ACTIVE or FROZEN member in MEMBER_CHURN_FEATURES, calling the LAST version of CHURN_MODEL's PREDICT_PROBA from SQL. Keep member_id, site_id, status, plan_name, monthly_fee, intent_to_leave_count, negative_feedback_count, checkins_28d, plus CHURN_PROBABILITY (probability of class 1, 3 decimals), RISK_BAND (HIGH >= 0.6, MEDIUM >= 0.3, else LOW) and SCORED_AT.
2. Create a SQL stored procedure GET_CHURN_RISK(SITE_ID VARCHAR, TOP_N NUMBER) RETURNS VARCHAR that returns the TOP_N highest-probability members as a JSON array (all sites when SITE_ID is empty). This is the tool the agent will call.
3. Test it with CALL GET_CHURN_RISK('S01', 5) and show the count of members per risk band.""")
render_explanation("Why return JSON from the procedure?", """
Agent custom tools pass simple arguments in and get a value back. A compact JSON array of members, probabilities and
the reasons (`intent_to_leave_comments`, `checkins_28d`) gives the agent everything it needs to explain *why* a member
is at risk, not only *who*.
""")
render_fallback(answer_key("D2.5"))

# ── D2.6 ──────────────────────────────────────────────────────────────────────
st.markdown("### D2.6. A semantic view on the new dataset")
render_prompt("Prompt D2.6", "SV_MEMBER_RETENTION", """/semantic_studio Create a semantic view {FQ_SCHEMA}.SV_MEMBER_RETENTION over SHARED__SITE, MEMBER_CHURN_SCORES and MEMBERS__FEEDBACK_ENRICHED.
- Relationships: MEMBER_CHURN_SCORES.site_id and MEMBERS__FEEDBACK_ENRICHED.site_id to SHARED__SITE.site_id. Do not set join_type; the fact (many) side is the left table, SHARED__SITE is the right table, and SHARED__SITE declares site_id as its primary key.
- Dimensions: site_name (synonyms centre, leisure centre, club), town, plan_name, risk_band, topic, sentiment, intent_to_leave, channel, feedback_at
- Metrics: members_scored, high_risk_members, avg_churn_probability, monthly_revenue_at_risk (sum of monthly_fee for HIGH risk), feedback_count, negative_feedback, leave_signals
Test it with: "Which site has the most monthly revenue at risk?" and "What are the top 3 topics among comments with intent to leave?\"""")
render_snowsight_route([
    "**AI & ML » Cortex Analyst** » **Create new** » Semantic view in `{SCHEMA}`, add the three tables.",
    "Add the two relationships to `SHARED__SITE`, then the dimensions and metrics above.",
    "Ask the two test questions in the playground.",
])
render_fallback(answer_key("D2.6"))

# ── D2.7 ──────────────────────────────────────────────────────────────────────
st.markdown("### D2.7. The retention agent")
render_prompt("Prompt D2.7", "RETENTION_AGENT with Analyst + the model", """In {FQ_SCHEMA}, create a Cortex Agent RETENTION_AGENT with orchestration model auto and two tools, both on warehouse {WH}:
- member_retention: Cortex Analyst on {FQ_SCHEMA}.SV_MEMBER_RETENTION, for counts, trends, topics and revenue at risk
- churn_risk: a custom tool on the stored procedure {FQ_SCHEMA}.GET_CHURN_RISK(SITE_ID, TOP_N), for "which members" questions (S01 Riverside, S02 Abbey, S03 Kingfisher)
Instructions: help the operator's retention team, be concise, use GBP, and always say which tool each number came from.
Then ask it:
1. "Which site has the most monthly revenue at risk, and who are the 3 members most likely to cancel there?"
2. "What are at-risk members complaining about most?"
Show which tools it called for each question.""")
render_snowsight_route([
    "**AI & ML » Agents » Create agent** in `{SCHEMA}`, orchestration model **auto**.",
    "**Tools » Cortex Analyst** » `SV_MEMBER_RETENTION`, warehouse `{WH}`.",
    "**Tools » Custom tools** » resource type **Procedure** » `GET_CHURN_RISK`, warehouse `{WH}`, describe both parameters.",
    "Ask the questions in the playground and open the trace to see both tools being used.",
])
render_checkpoint("Question 1 should call **member_retention** first (revenue at risk by site), then **churn_risk** "
                  "for that site, and name members with their probability and intent-to-leave comments.")
render_fallback(answer_key("D2.7"))

render_technologies_used([
    {"name": "AISQL", "icon": "auto_awesome", "description": "AI_SENTIMENT, AI_CLASSIFY and AI_FILTER over every row, in SQL"},
    {"name": "Snowpark Python procedure", "icon": "code", "description": "scikit-learn training inside a warehouse"},
    {"name": "Model Registry", "icon": "inventory_2", "description": "Versioned, governed MODEL object, callable from SQL"},
    {"name": "Stored procedure as a tool", "icon": "build", "description": "GET_CHURN_RISK wraps model scores for the agent"},
    {"name": "Semantic view", "icon": "schema", "description": "Retention metrics and AISQL dimensions for Cortex Analyst"},
    {"name": "Cortex Agent", "icon": "smart_toy", "description": "Routes 'how many' to Analyst and 'who' to the model"},
])
render_key_concepts([
    {"term": "Feature leakage", "definition": "A feature that secretly encodes the answer (here, leave dates). It makes a model look perfect in testing and useless in production."},
    {"term": "AUC", "definition": "How well the model ranks churners above non-churners. 0.5 is random, 1.0 is perfect."},
    {"term": "MODEL(...)!PREDICT_PROBA", "definition": "SQL syntax to call a registered model's method. Here it returns an object whose output_feature_1 is the probability of churn."},
    {"term": "Custom tool", "definition": "A stored procedure or UDF an agent can call with typed arguments. The agent runs it with the warehouse in its spec, under owner's or caller's rights as defined on the procedure."},
])
render_what_you_built([
    "`MEMBERS__FEEDBACK_ENRICHED` - every comment scored by AISQL",
    "`MEMBER_CHURN_FEATURES` - a leak-free training dataset",
    "`CHURN_MODEL` - trained in a warehouse, registered with metrics",
    "`MEMBER_CHURN_SCORES` and `GET_CHURN_RISK` - model output as a table and a tool",
    "`SV_MEMBER_RETENTION` - retention metrics for Cortex Analyst",
    "`RETENTION_AGENT` - one conversation over the semantic view and the model",
])

render_real_world_examples([
    {"title": "Retention lists for every operator", "body": "Run D2.2-D2.5 as Dynamic Tables and a weekly task per operator database, and CS gets a ranked at-risk list each Monday."},
    {"title": "Nova's next feature", "body": "Expose RETENTION_AGENT to operators inside Nova: \"who should my front desk call this week, and what should they say?\""},
    {"title": "Feedback triage", "body": "The same AI_CLASSIFY topics route billing complaints to finance and equipment faults to facilities, automatically."},
    {"title": "Governed ML", "body": "Model versions, metrics and access live next to the operator's data, with no exports to a separate ML platform and one RBAC model."},
])
render_references({
    "Quickstarts": [L.QS_AISQL, L.QS_ML, L.QS_SV_BP, L.QS_AGENTS],
    "Docs": [L.AISQL, L.AI_SENTIMENT, L.AI_CLASSIFY, L.AI_FILTER, L.ML_REGISTRY, L.ML_SQL_INFER, L.PY_PROCS,
             L.SV_CREATE, L.AGENTS_MANAGE],
})
