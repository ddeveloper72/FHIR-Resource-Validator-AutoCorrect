# Copilot Instructions

This repository is the FHIR Resource Validator and Auto-Corrector, a Python
workbench inspired by the HL7 v2 Message Validator and Auto-Corrector.

## Project Goal

Validate FHIR R4 resources and Bundles using local structural checks and the
Matchbox `$validate` API. Interpret validation outcomes, propose or apply only
safe deterministic repairs, and revalidate every candidate while preserving an
auditable record of changes.

## Repository Layout

```text
fhir_validator/
  local_checks.py       Local structural and reference checks
  matchbox_client.py    Matchbox HTTP client
  repair_engine.py      Deterministic repair rules
  workflow.py           Validate, repair, and revalidate orchestration

tests/                   Focused unit and workflow tests
static/                  Web UI assets
templates/              Flask templates
app.py                   Flask application
run_cli.py               Command-line entry point
requirements.txt         Runtime and test dependencies
.env.example             Environment configuration template
```

## Core Safety Rules

- Never overwrite the original FHIR resource or Bundle.
- Never invent clinical data, patient identifiers, terminology codes, dates, or
  medication details.
- Apply an automatic repair only when the target and replacement are uniquely
  determined from the input Bundle or validator result.
- Treat terminology corrections, missing clinical facts, ambiguous references,
  profile slice choices, and clinical interpretation as human-review items.
- Write candidate output, validation outcomes, and repair manifests separately.
- Revalidate every repaired candidate with the same profile and configuration.
- Stop after a bounded number of repair iterations or when progress stops.
- Preserve the exact before/after values and reason for every proposed or
  applied repair.

## FHIR and Matchbox

- Use structured JSON parsing and object traversal, never ad hoc text
  replacement for FHIR resources.
- Matchbox returns a FHIR `OperationOutcome`; preserve severity, code,
  diagnostics, details, expression, and location information.
- Keep profile URLs and implementation guide versions explicit.
- Distinguish FHIR syntax, base specification, implementation guide, slicing,
  reference, and terminology errors.
- Prefer FHIRPath expressions from Matchbox when locating an issue, but do not
  assume every expression can be converted directly into a writable JSON path.
- Treat Matchbox and terminology endpoints as external services: use timeouts,
  clear errors, and no credentials in source control.
- Do not silently suppress Matchbox warnings or errors. Any suppression must be
  explicit, documented, and configuration-scoped.

## Repair Design

Each repair rule should be small, deterministic, explainable, and independently
tested. A repair record should include:

- rule name
- resource or Bundle path
- original value
- replacement value
- reason and source diagnostic
- validation iteration
- whether the change was proposed or applied

Reference normalization may be automatic when a `ResourceType/id` reference
matches exactly one Bundle resource and its `fullUrl` is unambiguous. Do not
normalize ambiguous or external references automatically.

## Development Workflow

Use the project virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies with the repository requirements file. If the local
machine requires the existing PyPI certificate workaround, use narrowly scoped
trusted hosts rather than disabling TLS globally:

```powershell
python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

Run tests with:

```powershell
python -m pytest -q
```

Run the Flask application with:

```powershell
python app.py
```

Use `MATCHBOX_URL` from `.env` for a Matchbox FHIR endpoint. Keep `.env`, API
keys, downloaded packages, patient data, and generated run artefacts out of
version control.

## Testing Expectations

- Add or update focused tests for every repair rule.
- Test both successful validation and failed validation paths.
- Test that original input remains unchanged.
- Test bounded iteration and no-progress termination.
- Test malformed Matchbox responses and network failures.
- Use synthetic FHIR data only.
- Prefer offline tests with fixtures; do not make the test suite depend on the
  public Matchbox server.

## Code Style

- Keep changes small and local to the owning module.
- Preserve public APIs unless a change is required by the task.
- Use clear descriptive names and type hints where they improve correctness.
- Keep comments concise and explain only non-obvious reasoning.
- Avoid broad refactors, generated metadata churn, and unrelated fixes.
- Do not commit changes or create branches unless explicitly requested.
