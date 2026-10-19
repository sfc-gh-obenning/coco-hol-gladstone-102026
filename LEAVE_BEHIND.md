# Gladstone MRM | Data quality HOL | Leave-behind

What we built, and how to take it to every operator database. All lab data was synthetic.

## 1. The pattern

| Layer | Check | Detects |
|---|---|---|
| Bronze (Bifrost merge targets) | `DUPLICATE_COUNT` on keys | Replayed merge batches |
| Bronze | `FRESHNESS ON ()` with an expectation | Stalled sync / merge task |
| Bronze | `NEGATIVE_COUNT` on amounts | Sign bugs in payments and refunds |
| Bronze | `REFERENTIAL_INTEGRITY_COUNT` child -> parent | Partial syncs (orphans) |
| Bronze | `DQ_COMMON.FOREIGN_OPERATOR_ROWS` | Cross-tenant leak (also a GDPR incident) |
| Bronze | `DQ_COMMON.ACTIVE_BUT_LEFT` | Source status drift |
| Silver REPORTING | `DQ_COMMON.REPORTING_LAG_SECONDS` (two-table) | Dynamic Tables falling behind Bronze |
| Gold | metric vs verified query comparison | Two definitions of the same KPI |
| Bronze (baseline) | `ROW_COUNT` / `FRESHNESS` + anomaly detection | Unusual volume or timing (after ~2 weeks of history) |

Containment: a circuit-breaker task suspends REPORTING Dynamic Tables while a Bronze expectation fails, so Nova answers from
the last good state. Alerts: database-level notification settings, with only the critical checks notifying.

## 2. Rolling it out to every `CUST_*` database

1. Create a platform database for shared checks (`DQ_COMMON`) owned by the Platform team.
2. Add the checks to each operator pipeline's DCM project (`ATTACH DATA METRIC FUNCTION ... EXPECTATION`), one target per operator or tier.
3. Use `TRIGGER_ON_CHANGES` on Bifrost-written tables; align REPORTING checks to the Dynamic Table target lag.
4. Add a schema-level `ROW_COUNT` / `FRESHNESS` baseline with anomaly detection in every operator schema.
5. Enable `DATA_QUALITY_MONITORING_SETTINGS` per operator database (scripted), with email or a Slack/Teams webhook integration.
6. One fleet view over `SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS`, filtered to `CUST_%`, plus the Snowsight data quality dashboard.
7. Track DQ cost with `DATA_QUALITY_MONITORING_USAGE_HISTORY` (filter by database) and a tag-based budget per tier.
8. Run `snow dcm test` as a CI gate on every pull request.

## 3. GDPR checklist (not legal advice - confirm with Gladstone's DPO)

- [ ] Controller / processor roles agreed per operator; who receives SARs and erasure requests.
- [ ] Lawful basis recorded per column (tags): contract, legal obligation, consent, explicit consent.
- [ ] Special-category data (health notes, PAR-Q) - is it needed in Snowflake? If so, masked and never in Nova's semantic views.
- [ ] Retention period per table; storage-limitation process (scheduled expiry or retention policies).
- [ ] SAR procedure per operator database, run under a privacy role, logged in a request register; one-month deadline.
- [ ] Erasure procedure: delete vs pseudonymise vs crypto-shred per table; payments kept for tax with identity removed.
- [ ] Data quality check that proves each erasure reached every table.
- [ ] Copies covered: Time Travel retention, Fail-safe (7 days), clones, dev/test copies, exports, Nova caches.
- [ ] Cross-tenant leak treated as a personal-data incident; breach assessment and ICO notification within 72 hours where required.
- [ ] `CORTEX_ENABLED_CROSS_REGION` setting agreed for UK residency.

## 4. Cost controls

- Tag operator databases with `OPERATOR_ID` and `COST_CENTRE`; tag-based custom budgets per tier.
- Resource monitors on shared warehouses (merge / Bifrost, Nova serving) - suspend at 100%.
- Budgets cover serverless (DMFs, serverless tasks); resource monitors cover warehouses only.

## 5. Where the lab assets live

- `dq-lab/sql/` - admin setup, template, procedures, answer keys, reset, teardown
- `dq-lab/sql/bonus/` - B1 / B2 / B3 setup, answer keys, teardowns; `dcm_project/` with a sample GitHub Actions workflow
- `dq-lab/workshop_guide/` - the Streamlit guide
- `dq-lab/ADMIN_PREFLIGHT_QUESTIONNAIRE.md`, `ATTENDEE_PREP.md` and the guide's Lab setup page - reuse them to run the lab again for another team
