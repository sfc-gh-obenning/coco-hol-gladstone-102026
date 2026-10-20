-- =============================================================================
-- Gladstone MRM | Day 2: AI/ML | D2_answer_key.sql
-- What CoCo should produce for Prompts D2.1 - D2.6. Run as your operator role in
-- your own schema: replace CUST_<NAME> below, or run USE SCHEMA first.
-- =============================================================================
-- USE ROLE DQ_LAB_<NAME>; USE WAREHOUSE DQ_LAB_WH; USE SCHEMA GLADSTONE_DQ_LAB.CUST_<NAME>;

-- D2.2  AISQL: turn free text into features (one LLM pass per comment, then it's just columns)
CREATE OR REPLACE TABLE MEMBERS__FEEDBACK_ENRICHED AS
SELECT f.feedback_id, f.member_id, f.site_id, f.channel, f.feedback_at, f.feedback_text,
       AI_SENTIMENT(f.feedback_text):categories[0]:sentiment::VARCHAR                         AS sentiment,
       AI_CLASSIFY(f.feedback_text,
         ['price and value', 'facilities and equipment', 'classes and booking', 'staff and service',
          'billing', 'personal circumstances', 'general enquiry', 'praise'])
         :labels[0]::VARCHAR                                                                   AS topic,
       AI_FILTER(PROMPT('Is this member signalling that they might cancel, freeze, downgrade or leave? {0}',
                        f.feedback_text))                                                      AS intent_to_leave
FROM MEMBERS__FEEDBACK f;

-- D2.3  One row per member: behaviour from Bronze + AI features. Label = CANCELLED.
-- No dates from MEMBERS__MEMBER / MEMBERS__MEMBERSHIP: in this synthetic data joined_on, left_on and
-- last_paid_on all encode the status, so they would leak the label.
CREATE OR REPLACE TABLE MEMBER_CHURN_FEATURES AS
WITH fb AS (
  SELECT member_id,
         COUNT(*)                                                    AS feedback_count,
         COUNT_IF(sentiment = 'negative')                            AS negative_feedback_count,
         COUNT_IF(intent_to_leave)                                   AS intent_to_leave_count,
         COUNT_IF(topic = 'price and value')                         AS price_complaints,
         COUNT_IF(topic = 'facilities and equipment')                AS facility_complaints
  FROM MEMBERS__FEEDBACK_ENRICHED GROUP BY member_id
),
bk AS (SELECT member_id, COUNT(*) AS bookings_28d FROM SYSTEM__BOOKING GROUP BY member_id),
at AS (SELECT member_id, COUNT(*) AS checkins_28d FROM SYSTEM__ATTENDANCE GROUP BY member_id)
SELECT m.member_id, m.home_site_id AS site_id, m.status, ms.plan_name, ms.monthly_fee,
       COALESCE(bk.bookings_28d, 0)                                         AS bookings_28d,
       COALESCE(at.checkins_28d, 0)                                         AS checkins_28d,
       IFF(COALESCE(bk.bookings_28d, 0) = 0, 0,
           1 - COALESCE(at.checkins_28d, 0) / bk.bookings_28d)              AS no_show_rate,
       COALESCE(fb.feedback_count, 0)                                       AS feedback_count,
       COALESCE(fb.negative_feedback_count, 0)                              AS negative_feedback_count,
       COALESCE(fb.intent_to_leave_count, 0)                                AS intent_to_leave_count,
       COALESCE(fb.price_complaints, 0)                                     AS price_complaints,
       COALESCE(fb.facility_complaints, 0)                                  AS facility_complaints,
       IFF(m.status = 'CANCELLED', 1, 0)                                    AS churned
FROM MEMBERS__MEMBER m
JOIN MEMBERS__MEMBERSHIP ms ON ms.member_id = m.member_id
LEFT JOIN fb ON fb.member_id = m.member_id
LEFT JOIN bk ON bk.member_id = m.member_id
LEFT JOIN at ON at.member_id = m.member_id
QUALIFY ROW_NUMBER() OVER (PARTITION BY m.member_id ORDER BY m._loaded_at DESC) = 1;   -- survive a Bifrost replay

-- D2.4  Train two models in a warehouse, compare, register the better one
CREATE OR REPLACE PROCEDURE TRAIN_CHURN_MODEL()
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'snowflake-ml-python', 'scikit-learn', 'pandas')
HANDLER = 'run'
EXECUTE AS CALLER
AS
$$
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from snowflake.ml.registry import Registry

BEHAVIOUR = ["MONTHLY_FEE", "BOOKINGS_28D", "CHECKINS_28D", "NO_SHOW_RATE"]
AI = ["FEEDBACK_COUNT", "NEGATIVE_FEEDBACK_COUNT", "INTENT_TO_LEAVE_COUNT", "PRICE_COMPLAINTS", "FACILITY_COMPLAINTS"]

def run(session):
    df = session.table("MEMBER_CHURN_FEATURES").to_pandas()
    X = df[BEHAVIOUR + AI].astype(float)
    y = df["CHURNED"].astype(int)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

    base = GradientBoostingClassifier(random_state=42).fit(X_tr[BEHAVIOUR], y_tr)
    full = GradientBoostingClassifier(random_state=42).fit(X_tr, y_tr)
    auc_base = roc_auc_score(y_te, base.predict_proba(X_te[BEHAVIOUR])[:, 1])
    auc_full = roc_auc_score(y_te, full.predict_proba(X_te)[:, 1])

    reg = Registry(session=session, database_name=session.get_current_database(),
                   schema_name=session.get_current_schema())
    mv = reg.log_model(
        full, model_name="CHURN_MODEL",
        sample_input_data=X_tr.head(50), target_platforms=["WAREHOUSE"],
        conda_dependencies=["scikit-learn"],
        metrics={"auc_behaviour_only": round(auc_base, 3), "auc_with_ai_features": round(auc_full, 3),
                 "train_rows": len(X_tr), "test_rows": len(X_te)},
        comment="Gradient boosting churn model: behaviour + AISQL feedback features")
    imp = sorted(zip(X.columns, full.feature_importances_), key=lambda t: -t[1])
    return {"model": "CHURN_MODEL", "version": mv.version_name,
            "auc_behaviour_only": round(auc_base, 3), "auc_with_ai_features": round(auc_full, 3),
            "top_features": [[n, round(float(v), 3)] for n, v in imp[:5]]}
$$;

CALL TRAIN_CHURN_MODEL();
SHOW VERSIONS IN MODEL CHURN_MODEL;
SHOW FUNCTIONS IN MODEL CHURN_MODEL;

-- D2.5  Score every current member with the registered model; a proc the agent can call
CREATE OR REPLACE TABLE MEMBER_CHURN_SCORES AS
SELECT member_id, site_id, status, plan_name, monthly_fee, intent_to_leave_count, negative_feedback_count,
       checkins_28d,
       ROUND(MODEL(CHURN_MODEL, LAST)!PREDICT_PROBA(
               monthly_fee, bookings_28d, checkins_28d, no_show_rate,
               feedback_count, negative_feedback_count, intent_to_leave_count,
               price_complaints, facility_complaints):output_feature_1::FLOAT, 3)          AS churn_probability,
       CASE WHEN churn_probability >= 0.6 THEN 'HIGH' WHEN churn_probability >= 0.3 THEN 'MEDIUM' ELSE 'LOW' END
                                                                                            AS risk_band,
       CURRENT_TIMESTAMP()                                                                  AS scored_at
FROM MEMBER_CHURN_FEATURES
WHERE status IN ('ACTIVE', 'FROZEN');

CREATE OR REPLACE PROCEDURE GET_CHURN_RISK(SITE_ID VARCHAR, TOP_N NUMBER)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
  res VARCHAR;
BEGIN
  SELECT TO_JSON(ARRAY_AGG(OBJECT_CONSTRUCT(
           'member_id', member_id, 'site_id', site_id, 'plan', plan_name, 'monthly_fee', monthly_fee,
           'churn_probability', churn_probability, 'risk_band', risk_band,
           'intent_to_leave_comments', intent_to_leave_count, 'checkins_28d', checkins_28d)))
    INTO :res
    FROM (SELECT * FROM MEMBER_CHURN_SCORES
           WHERE (:SITE_ID IS NULL OR :SITE_ID = '' OR site_id = UPPER(:SITE_ID))
           ORDER BY churn_probability DESC
           LIMIT :TOP_N);
  RETURN COALESCE(:res, '[]');
END;
$$;

CALL GET_CHURN_RISK('S01', 5);

-- D2.6  Semantic view over the new dataset
CREATE OR REPLACE SEMANTIC VIEW SV_MEMBER_RETENTION
  TABLES (
    sites    AS SHARED__SITE        PRIMARY KEY (site_id)  COMMENT = 'Operator sites',
    scores   AS MEMBER_CHURN_SCORES PRIMARY KEY (member_id) COMMENT = 'Current members scored by CHURN_MODEL',
    feedback AS MEMBERS__FEEDBACK_ENRICHED PRIMARY KEY (feedback_id) COMMENT = 'Member feedback with AISQL sentiment, topic and intent to leave'
  )
  RELATIONSHIPS (
    scores_to_sites   AS scores (site_id)   REFERENCES sites,
    feedback_to_sites AS feedback (site_id) REFERENCES sites
  )
  FACTS (
    scores.churn_probability AS churn_probability,
    scores.monthly_fee AS monthly_fee
  )
  DIMENSIONS (
    sites.site_name AS site_name WITH SYNONYMS = ('centre', 'leisure centre', 'club'),
    sites.town AS town,
    scores.member_id AS member_id,
    scores.plan_name AS plan_name,
    scores.risk_band AS risk_band COMMENT = 'HIGH >= 0.6, MEDIUM >= 0.3, else LOW',
    feedback.topic AS topic,
    feedback.sentiment AS sentiment,
    feedback.intent_to_leave AS intent_to_leave,
    feedback.channel AS channel,
    feedback.feedback_at AS feedback_at
  )
  METRICS (
    scores.members_scored AS COUNT(scores.member_id),
    scores.high_risk_members AS COUNT_IF(scores.risk_band = 'HIGH'),
    scores.avg_churn_probability AS AVG(scores.churn_probability),
    scores.monthly_revenue_at_risk AS SUM(IFF(scores.risk_band = 'HIGH', scores.monthly_fee, 0))
      COMMENT = 'Monthly fees of HIGH-risk members',
    feedback.feedback_count AS COUNT(feedback.feedback_id),
    feedback.negative_feedback AS COUNT_IF(feedback.sentiment = 'negative'),
    feedback.leave_signals AS COUNT_IF(feedback.intent_to_leave)
  )
  COMMENT = 'Day 2: member retention - churn scores and AISQL-enriched feedback';

-- D2.7  Agent with the semantic view and the model-backed proc
CREATE OR REPLACE AGENT RETENTION_AGENT
  COMMENT = 'Day 2: retention agent for this operator'
  FROM SPECIFICATION
$$
models:
  orchestration: auto
instructions:
  response: "You help the operator's retention team. Be concise, use GBP, and always say which tool your numbers came from."
  orchestration: "Use member_retention for counts, trends, topics and revenue at risk across sites. Use churn_risk to list the specific members most likely to cancel, optionally for one site (S01 Riverside, S02 Abbey, S03 Kingfisher)."
  sample_questions:
    - question: "Which site has the most monthly revenue at risk?"
    - question: "Who are the 5 members most likely to cancel at Riverside, and why?"
tools:
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: member_retention
      description: "Churn risk bands, revenue at risk, and AISQL-classified member feedback (sentiment, topic, intent to leave) by site."
  - tool_spec:
      type: generic
      name: churn_risk
      description: "Returns the members with the highest churn probability from the registered CHURN_MODEL, as JSON. Use for 'who' questions."
      input_schema:
        type: object
        properties:
          SITE_ID:
            type: string
            description: "Site ID S01, S02 or S03. Empty string for all sites."
          TOP_N:
            type: number
            description: "How many members to return, e.g. 10."
        required: [SITE_ID, TOP_N]
tool_resources:
  member_retention:
    semantic_view: "GLADSTONE_DQ_LAB.CUST_<NAME>.SV_MEMBER_RETENTION"
    execution_environment: {type: warehouse, warehouse: DQ_LAB_WH}
  churn_risk:
    type: procedure
    identifier: "GLADSTONE_DQ_LAB.CUST_<NAME>.GET_CHURN_RISK"
    execution_environment: {type: warehouse, warehouse: DQ_LAB_WH}
$$;
