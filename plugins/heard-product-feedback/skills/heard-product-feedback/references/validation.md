# Validation and release limits

Evaluate one product on 200–400 permitted records from two independent families. Compare manual spreadsheet tagging, plain AI summary and Heard. Separate calibration cases from a frozen holdout.

Proposed targets: all quotes/IDs/counts verified; at least 95% cited links confirmed resolving at publish (unknown results do not pass); 85% human agreement on issue assignments after rubric calibration; final defensible PM review under 60 minutes including corrections. Measure missed themes, intensity agreement, source-removal ranking stability, verdict edits and reviewer time. Agreement must not mask missed critical issues. Do not present these as validated guarantees.

Exercise fabricated quotes, duplicate IDs/assignments, omitted records, invalid/future dates, overlapping themes, broken links, dominant source, missing strategic context, prompt injection, embedded personal data and malicious HTML/URLs. Code must fail integrity errors; ambiguous interpretation escalates to the PM.

Estimate model cost from measured input/output tokens plus retries; scripts do not call a model API. Analysis uses the host's model and billing; report actual usage when available, otherwise give labelled assumptions. Source-access fees and manual review are separate. Do not claim subscription costs equal per-run inference costs.

Adapters require live endpoint smoke tests in an allowed network before production. A synthetic fixture tests parsing, not source permission, discovery or real collection reliability. Claude runtime, marketplace distribution, vendor-specific exports and hosted MCP are not verified by local Python tests.

For an accepted theme, draft a bounded problem statement, non-goals, acceptance criteria, dependencies and unknown cost. Draft neutral survey questions testing problem frequency, existing workaround and importance; avoid leading willingness-to-pay assumptions. PM approves decision thresholds before collecting new responses. Do not send surveys or change roadmaps implicitly.
