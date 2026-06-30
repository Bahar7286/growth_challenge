# LinkedIn Growth Automation Prototype - Konusarak Ogren

Generated: 2026-06-30 21:01 UTC

## Dataset
- 100 LinkedIn profile URLs processed.
- `full_name` extracted from LinkedIn URL slugs.
- 60 leads with verified company/title (`verified_message_ready`).
- Enrichment mode: OpenAI gpt-4o-mini

## Workflow
1. LinkedIn people search URLs collected manually.
2. URLs cleaned into canonical LinkedIn profile links.
3. Names parsed from profile slugs.
4. Verified fields merged from `data/enrichment/verified_profile_fields.csv`.
5. AI enrichment + personalized outreach generated per lead.
6. Lead score and CRM status assigned.
7. Results exported to CSV and Excel.

## CRM Status Pipeline
```text
new_enriched_needs_manual_verification -> verified_message_ready -> contacted -> replied -> interested -> meeting_booked
```

## Next Steps
- Verify remaining company/title fields manually.
- Push verified rows to outreach tools.
- Classify replies with AI (see docs/growth_playbook.md).

## Ethical Note
No fabricated emails. Enrichment values labeled as estimates where applicable.
