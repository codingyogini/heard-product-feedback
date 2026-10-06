# Collection boundaries

Adapters are format implementations, not blanket licenses. Recheck exact terms for each run. Record permission evidence and retrieval date in the plan. Honour robots.txt for automated public endpoint retrieval; fail closed on inaccessible/ambiguous robots. Use HTTPS only, public DNS addresses, no credentials, bounded response sizes, no redirects, no bypasses. Collector has no authenticated API support. Never log credentials.

| Source | Release behavior |
|---|---|
| Public RSS/Atom feedback feed | Parse item/entry text, date and item URL; exact feed and reuse rights must be approved. Generic blog entries are not automatically customer feedback. |
| Public canonical JSON endpoint | Parse a record array with text/date/url/rating/role; approved exact endpoint required. One bounded response; no invented pagination. |
| App Store JSON-format review feed | Parse content/title/date/rating and item link. Supply an approved exact endpoint; no automatic store discovery or pagination. Use product listing URL only as explicitly labelled fallback when an individual review URL is missing. |
| Google Play | Manual canonical JSON import in this version; no unofficial scraper. |
| Public ideas portal | RSS/Atom or canonical JSON where explicitly permitted; otherwise manual import. |
| Reddit | Disabled for automatic collection in this version. Import only when processing, reuse and retention are permitted; omit from permanent reports unless deletion/retraction requirements can be met. |
| G2 | Excluded under the product brief; do not collect or import. |
| Capterra / TrustRadius / Trustpilot | Manual import only under the product brief, subject to actual reuse permission; never treat manual copying as exemption from terms. |

RSS 2.0 format reference: https://www.rssboard.org/rss-specification . A feed specification is not a license.
Reddit source rules checked 2026-10-06: https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki and https://redditinc.com/policies/data-api-terms . Eligible OAuth limits are not permission for commercial use; deletion obligations affect retained static reports.

The runtime network may block otherwise permitted sources. Report this separately from source permission and content availability. Do not substitute invented records. Import source exports as a reproducible fallback. Count independent source families, not URLs; two pages of one portal are one family. Record date window, language, retrieval limits and missing channels as blind spots. A user name/handle may occur inside body text or URL even though author fields are dropped; require a privacy review before sharing.
