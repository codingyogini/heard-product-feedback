# Example run: SurveyMonkey

A real report produced by this skill from public feedback, not a mock-up.

**[Open the report](https://codingyogini.github.io/heard-product-feedback/examples/surveymonkey/report.html)** (a self-contained page you can also download as [`report.html`](report.html) and open locally).

| | |
|---|---|
| Product | SurveyMonkey iOS and Android apps |
| Records | 218 public reviews: 150 Apple App Store, 68 Google Play (1–3★ only) |
| Themes | 8: four Build, three Watch, one Ignore. All are still `proposed` and waiting for a PM decision |
| Excluded | 10 records, each with a reason. They stay in the denominator |
| Verified | Every quote is a verbatim substring of the record it cites. IDs, coverage and intensity bounds were checked by `heard.py build` |

## Files

- `records.json` is the collector output. Author fields were never stored.
- `analysis.json` is the model's judgment: theme assignments, intensity, verdicts, reasoning, counterevidence and quotes. It holds no counts.
- `report.html` is built by `heard.py` from the two files above. Every count, score and source breakdown is computed in code.

Rebuild it from the skill directory:

```bash
python scripts/heard.py build ../../../../examples/surveymonkey/records.json \
  ../../../../examples/surveymonkey/analysis.json --out /tmp/report.html
```

## How it was collected

The reviews were collected on 2026-09-22 for [Heard](https://heard-liart.vercel.app), using Apple's public customer-reviews feed and the public Google Play listing. They were then brought into this skill through its `manual` adapter. Recency is measured from the import date (2026-11-13). The report's "Evidence boundaries" section lists what this data cannot see. The most important limit: only 1–3★ reviews were kept, so satisfied users are absent by design.

Independent project, not affiliated with or endorsed by SurveyMonkey.
