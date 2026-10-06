# Data contracts and scoring v1

## Inputs
Manual imports are JSON arrays. Each record requires `text` (nonempty string), `url` (public HTTPS URL), and optionally `date` (ISO date), `rating` (number), `role` (explicit displayed role, not inferred). Unknown fields including author/name/handle are discarded. Collector assigns `id`, `source`, `family`, `collected_at` and `content_hash`; never supply model-generated source records. IDs hash source plus URL and text. Identical normalized text is deduplicated across sources; duplicate occurrences are recorded in a separate ledger, so breadth can be understated. Review that limitation. Anonymous record counts are not unique-person counts.

Collector output: `{product, collected_at, sources, failures, duplicates, records}`. Sources preserve permission evidence, adapter, endpoint and retrieval counts; raw responses are not stored. Native RSS HTML is converted to plain text deterministically; quotes refer to that immutable extracted text, not HTML markup. Manually supplied text is preserved verbatim.

## Model output
Create this JSON shape. Every record ID must occur exactly once in assignments, including exclusions. Each included assignment can have multiple unique theme IDs. Intensity uses 1=mild inconvenience; 2=recurring friction/workaround; 3=blocked task or material stated loss. Zero is permitted for no stated intensity. Require `rationale` on every assignment. Do not infer financial loss from sentiment.

```json
{
  "brief": "Target segment, goal, capacity/strategy unknowns",
  "blind_spots": ["Public commenters are a self-selected sample"],
  "assignments": [
    {"record_id": "r_ID", "theme_ids": ["t1"], "intensity": 2, "rationale": "Recurring manual workaround"},
    {"record_id": "r_OTHER", "theme_ids": [], "intensity": 0, "rationale": "Praise only"}
  ],
  "themes": [{
    "id": "t1", "title": "Missing export",
    "verdict": "Watch", "review_status": "proposed",
    "reasoning": "Evidence and tradeoffs; delivery cost unknown",
    "beneficiary": "Explicitly evidenced segment or unknown",
    "cost": "Unknown; requires engineering estimate",
    "displaces": "Unknown pending strategy brief",
    "next_test": "Validation experiment and proposed threshold",
    "counterevidence": "Contradictory records or none observed",
    "quotes": [{"record_id": "r_ID", "text": "exact substring"}]
  }]
}
```

Quotes must reference records assigned to that theme. Require at least one quote per theme. A matching quote does not establish source authenticity or validity of a conclusion. Every theme must have evidence; never create empty themes. `review_status` is proposed/accepted/edited; accepted/edited require `reviewer` and `decision_reason` strings. Original model verdict and reasoning remain preserved when importing human decisions.

## Deterministic ranking
Denominator: all deduplicated collected records, including exclusions. Components are 0–1:
- Mention share: distinct assigned records / all records. Not customer reach.
- Intensity: mean assigned intensity / 3. It depends on model labels; human audits remain necessary.
- Recency: mean max(0,1-age_days/365) relative to collection date; unknown dates contribute 0 and are disclosed. Future/invalid dates are rejected.
- Breadth: represented source families / successfully collected source families with records. Not population representativeness.
Score = 45*mention_share + 25*intensity + 20*recency + 10*breadth. This heuristic is unvalidated. Weight sliders normalize weights to total 100; verdicts never change automatically. Theme counts overlap when records express multiple issues. Never sum them as unique customers.

## Commands
`collect PLAN --out records.json`
`prepare records.json --out batches` (default 40 records/batch)
`build records.json analysis.json --out report.html [--decisions decisions.json]`
`links records.json --out link-check.json` (separate optional network check)
All outputs are local. External publishing/integration is separate. Build also writes computed report JSON and a CSV draft beside the HTML. CSV is a generic transfer format, not a guaranteed vendor-specific import.
