# Heard — a product feedback Claude Skill
A Claude skill that collects **permitted public** product feedback, clusters it into themes, checks every quote and count against the records, and produces a decision report with proposed **Build / Watch / Ignore** calls. The PM keeps the final decision.

By [Irene Pylypenko](https://irenepylypenko.com).

## See a real report

**[Open the SurveyMonkey example report →](https://codingyogini.github.io/heard-product-feedback/examples/surveymonkey/report.html)**

It was built from 218 public App Store and Google Play reviews. It has eight themes, each with a proposed Build / Watch / Ignore call, the reasoning and counterevidence behind it, verbatim quotes linked to their sources, and a final decision that stays with a human reviewer. Files and method: [`examples/surveymonkey/`](examples/surveymonkey/).

[![Heard report for SurveyMonkey: evidence boundaries, ranking weights, and the top theme with its Build call, counterevidence, quotes and human decision field](examples/surveymonkey/screenshot.png)](https://codingyogini.github.io/heard-product-feedback/examples/surveymonkey/report.html)

## Install in Claude Code

```
/plugin marketplace add codingyogini/heard-product-feedback
/plugin install heard-product-feedback@irene-pylypenko
```

## Two editions

| Edition | Where | Verification |
|---|---|---|
| **Directory** (plugin) | `plugins/heard-product-feedback/` | Instructions only. The model runs the verification checklist, or computes with code written at run time when the host can execute code. |
| **Full** | [v1.0.0 skill folder](https://github.com/codingyogini/heard-product-feedback/tree/5308cac81707f71499c83083db3a976e12544f87/plugins/heard-product-feedback/skills/heard-product-feedback) | Ships `scripts/heard.py`, which enforces quote substrings, IDs, coverage, intensity bounds, counts and ranking in code and renders a self-contained HTML report. |

The Claude plugin directory accepts bundled scripts only from verified organizations, so the directory edition carries no code. Use the full edition when a decision needs code-enforced verification: download that v1.0.0 skill folder into your skills folder, or zip it and upload it as a custom skill.

## What it does

1. **Scope & source plan** — confirms product, segment and approved public sources (RSS/Atom, App Store JSON, canonical JSON, manual import). No sign-in walls, no private CRM or support data.
2. **Collect & prepare** — pulls approved records, strips author fields, dedupes and batches (`heard.py collect` / `prepare` in the full edition).
3. **Analyze** — the model assigns every record to themes or excludes it with a reason, and proposes a verdict per theme with counterevidence.
4. **Verify & report** — checks quote substrings, IDs, coverage and intensity bounds, computes counts and ranking, and produces the report (code-enforced by `heard.py build` in the full edition).
5. **Validate** — drafts a bounded spec and falsifiable validation questions for the accepted top theme.

Licensed under MIT. See [PRIVACY.md](PRIVACY.md) for data handling.

Full edition requires Python 3 and file access in the host. Tests: `cd scripts && python -m unittest test_heard` inside that folder.

## Layout

```
.claude-plugin/marketplace.json          # marketplace: irene-pylypenko
plugins/heard-product-feedback/
  .claude-plugin/plugin.json
  skills/heard-product-feedback/         # directory edition (SKILL.md, references, assets; no code)
```
