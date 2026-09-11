# FHIR Resource Validator and Auto-Corrector

A conservative FHIR validation workbench inspired by the HL7 v2 Message Validator and Auto-Corrector. It validates JSON resources or Bundles with local checks and Matchbox, proposes only deterministic repairs, and revalidates each candidate.

## Design principles

- Preserve the original input.
- Never invent clinical data or terminology codes.
- Apply a repair only when the target is unambiguous and the rule is explainable.
- Keep every repair in an auditable manifest.
- Stop when validation passes, no repair is available, or the iteration limit is reached.

## Current MVP

- Flask review UI and JSON API.
- Matchbox `POST /$validate` client with profile and implementation guide support.
- Local Bundle/reference checks.
- Deterministic normalization of unique `ResourceType/id` references to the matching `Bundle.entry.fullUrl`.
- Offline operation when `MATCHBOX_URL` is empty.
- Tests for the first repair rule.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Open <http://127.0.0.1:5000>. The `.env` file must exist for Matchbox validation to run; otherwise the application uses local checks only. Set `MATCHBOX_URL` to the FHIR endpoint, not the Matchbox web page, for example `https://test.ahdis.ch/matchboxv3/fhir`. The application calls `POST /$validate` on that endpoint. Supply the profile URL in the form when validating against IPS/EU-EPS or another implementation guide. The browser result shows the final Matchbox OperationOutcome findings, including diagnostics, severity, location, and FHIRPath expression.

Automatic repairs are deliberately bounded and evidence-based. A repair is applied only when a Bundle reference uniquely maps to one entry `fullUrl`; the candidate is then sent back through Matchbox. Each repair records its validation iteration, source diagnostic, and applied status. Matchbox terminology, profile, clinical-data, and ambiguous-reference findings remain review items.

CLI/offline smoke check:

```powershell
$env:PYTHONPATH = "."
python -c "import json; from fhir_validator.workflow import run_workflow; p=r'..\\FHIR_Bundle2Resounce\\patients\\aoife-byrne\\fhir\\ehds-aligned\\bundle.json'; print(run_workflow(json.load(open(p, encoding='utf-8')))['repairs'][:3])"
pytest
```

## Planned next slices

1. Persist candidate bundles, OperationOutcomes, and repair manifests under `runs/`.
2. Parse Matchbox FHIRPath expressions into precise JSON paths in the UI.
3. Add profile-aware deterministic rules for required Composition references and common JSON shape errors.
4. Add explicit human approval before exporting a repaired validator-facing bundle.
5. Add optional Docker/Matchbox development configuration and CI fixtures.
