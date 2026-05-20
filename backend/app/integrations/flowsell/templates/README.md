# FlowSell Template System

Isolated template infrastructure for future FlowSell automation scenarios.

This module is intentionally **not connected** to scheduler, moderation, AI generation, or mass sending yet.

## Files

| File | Purpose |
|------|---------|
| `catalog.json` | DB-ready JSON catalog of event/service templates |
| `catalog.py` | Read-only loader and event/service mapper |
| `renderer.py` | Safe `{placeholder}` replacement |
| `models.py` | Small dataclasses for template definitions and rendered output |

## Categories

- `reminders`
- `reviews`
- `appointment_created`
- `appointment_rescheduled`
- `appointment_cancelled`
- `aftercare`

## Supported placeholders

- `{client_name}`
- `{service_name}`
- `{appointment_date}`
- `{appointment_time}`
- `{master_name}`
- `{booking_link}`

Missing values are replaced with deterministic fallbacks and returned in
`RenderedTemplate.missing_placeholders` for logging/QA.

## Usage

```python
from app.integrations.flowsell.templates import load_template_catalog

catalog = load_template_catalog()
rendered = catalog.render(
    event="review_request",
    service_type="hair_coloring",
    values={
        "client_name": "Анна",
        "service_name": "Окрашивание",
        "booking_link": "https://example.com/review",
    },
)
print(rendered.template_id)
print(rendered.text)
```

## Current status

Prepared for P0/P1 work only. Do not route production sends through this system until
FlowSell credentials are tested and the specific task is approved.
