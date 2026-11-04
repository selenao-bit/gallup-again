# Database completeness and task-completion display

User-authorized update: load the prepared email/Q12 records, correct six Q12
statements, enrich actual narrative gaps, select direct OpenAI, and make task
completion visible for every employee. No corporate schema changes were needed.

## Applied and verified

- 12,634 email messages and 12,634 recipient rows, matching approved CSVs exactly.
  All 2,500 employees participate in at least one generated thread.
- 2 survey waves, 1,534 Q12 aggregate rows and six complete question statements.
  All 78 suppressed rows retain NULL statistics. Question text, arithmetic and
  stored rows match the prepared fixtures.
- Filled missing narrative text only: 203 position descriptions, 240 project
  descriptions, 13,208 task descriptions and 26,551 goal context notes. All 40,202
  values are labelled synthetic summaries of existing fields. Existing text and
  every other column in those four tables were checked unchanged using ordered
  hashes and direct comparisons. Q00's element is now Overall Satisfaction.
- Read-only database audit found no empty or placeholder text strings. Remaining
  NULLs were classified instead of replaced with false dates, scores or links.

## Intentional NULLs that must remain

| Source | Reason |
| --- | --- |
| `email_records.reply_to_id` | First message of a thread has no parent reply (6,317 rows). |
| `employee_history.end_date` | Current history assignment remains open (2,500 rows). |
| Task/training `start_date` | Not-started assignments have no actual start date. |
| Task/training completion dates | Unfinished/cancelled/expired assignments have no completion event. All completed records have their completion dates. |
| Training assessment scores | Incomplete/expired assignments have no assessment result. All completed training has scores. |
| Training certification expiry | No certification was awarded. Every awarded certification has an expiry. |
| Project `actual_end_date` | Active/suspended/cancelled work has no completed end event. All Complete projects have dates. |
| Q12 group foreign keys | Company/department/team groups do not all have a team, department or manager key. Do not invent hierarchy links. |
| Q00 engagement need/description | Overall satisfaction is separate from the twelve engagement needs. |
| Suppressed Q12 statistics | Scores and counts must stay undisclosed under the suppression rule. |
| Review task-completion percentage | No tasks assigned in that review quarter; all 22,956 missing rates were verified to have no denominator. |

`recognition_logs` has zero columns and no defined record model. Creating useful
recognition records requires a separately approved schema design; no columns or
rows were invented for this table.

## Task-rate definitions and coverage

A shared backend calculation drives both employee self-view and manager overview:
Complete tasks / non-Cancelled assigned tasks, including Suspended tasks in the
denominator. It uses all scoped records, not the 200-row evidence display cap.

- 1,307 employees have a numeric all-time rate.
- 1,181 have no assigned tasks: show **No assigned tasks**.
- 12 have only cancelled tasks: show **No eligible tasks**.
- A real zero with eligible unfinished tasks displays **0%**.

All 2,500 metrics were checked; employee API representatives cover each state.
No extra task assignments have been generated. A user question about whether to
prepare additional assignments remains pending.

Stored historical reviews retain the generator's different definition: completed
by the quarter end / all tasks attributed to that quarter, including cancelled
tasks. All 3,375 populated stored percentages match that definition. They were not
overwritten with the all-time denominator. The UI describes an unavailable
historical percentage rather than displaying a blank or a false zero.

## OpenAI and verification limits

GW/Azure mode is now configured privately using the verified gpt-5.4-mini
deployment. Live employee and manager requests through the app passed with email
and Q12 citations on November 4. Retrieval/context bounds were reduced after an
actual shared-sandbox rate-limit failure. Prompt source omissions are disclosed;
rate limits return sanitized 429 responses. No source data was changed by that fix.
These functional smoke results do not constitute broad answer-quality evaluation.

Audit and verification commands (SELECT-only):

```sh
.venv/bin/python scripts/audit_database_blanks.py
.venv/bin/python scripts/verify_loaded_fixtures.py
.venv/bin/python scripts/check_task_rates.py
.venv/bin/python scripts/check_integration.py
```

Import/enrichment scripts have explicit write modes and are not startup steps.
Do not rerun the fixture importer after loading: it deliberately refuses nonempty
destinations. Generated local data/evidence and private configuration remain ignored.
