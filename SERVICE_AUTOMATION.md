# Service Automation YAML

The YAML files should support two different jobs:

1. Knowledge: facts the assistant can use when generating answers.
2. Automation: structured service flows the app can run predictably.

Use `data/service_automation.yml` for automation. The backend reads this file through `ServiceAutomationService` and returns an `automation` response when a user message matches a configured service intent.

## Automation Shape

Each automation recipe has:

- `id`: stable identifier for logs and debugging.
- `category`: agent/domain, such as `business` or `insurance`.
- `service_id`: stable service identifier.
- `intents.keywords`: phrases used to detect this flow.
- `service`: source, URLs, and review metadata.
- `languages`: response title and summary per language.
- `facts`: controlled facts to show in deterministic replies.
- `fields`: details the service needs before it can proceed.
- `steps`: the service workflow.
- `next_actions`: what the assistant should do next.

## Field Types

Use required fields to make the assistant ask targeted questions instead of giving a generic answer.

```yaml
fields:
  - id: registration_path
    label: Registration path
    type: choice
    required: true
    prompt: "Which path should I prepare: domestic company, enterprise, foreign branch, or name reservation?"
    options:
      - id: domestic_company
        label: Domestic company
        keywords: [domestic company, company, limited]
      - id: enterprise
        label: Enterprise or sole trader
        keywords: [enterprise, sole trader, sole proprietorship]
```

For values like TINs, use regex extraction:

```yaml
extract:
  patterns:
    - "\\bTIN[:\\s-]*([0-9]{9})\\b"
```

## How To Add A New Service

1. Add a new item under `responses`.
2. Give it enough `intents.keywords` to match normal user wording.
3. Add required `fields` so the assistant can ask only what is missing.
4. Add `steps` and `next_actions`.
5. Add `source`, `official_url`, and `last_reviewed`.
6. Test with:

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall .\services
```

For frontend type checks:

```powershell
cd frontend
npx.cmd tsc --noEmit
```

## Tourism Registry Sync

Licensed tourism entities are cached from the official RDB Tourism Regulation registry so the demo can verify entities without asking the LLM to guess.

```powershell
cd backend
.\.venv\Scripts\python.exe .\scripts\sync_tourism_entities.py
```

The sync writes `data/tourism_entities_cache.json` with the entity name, category, sub-category, province, district, status, profile URL, source URL, and sync timestamp.

## Design Rule

Keep official service facts, steps, eligibility, required documents, and review dates in YAML. Let the LLM handle wording and explanation only when needed. This keeps the service automation flexible and easier to audit.
