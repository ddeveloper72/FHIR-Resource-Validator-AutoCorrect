from fhir_validator.repair_engine import apply_repairs
from fhir_validator.local_checks import check_resource
from fhir_validator.matchbox_client import summarize_outcome
from fhir_validator.workflow import run_workflow


def test_normalizes_unique_bundle_reference_to_full_url():
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {"fullUrl": "urn:uuid:patient-1", "resource": {"resourceType": "Patient", "id": "patient-1"}},
            {"fullUrl": "urn:uuid:composition-1", "resource": {"resourceType": "Composition", "id": "composition-1", "subject": {"reference": "Patient/patient-1"}}},
        ],
    }
    repaired, changes = apply_repairs(bundle)
    assert repaired["entry"][1]["resource"]["subject"]["reference"] == "urn:uuid:patient-1"
    assert changes[0]["rule"] == "normalize_bundle_reference"
    assert bundle["entry"][1]["resource"]["subject"]["reference"] == "Patient/patient-1"


def test_local_check_detects_unresolved_uuid():
    issues = check_resource({"resourceType": "Bundle", "entry": [{"resource": {"resourceType": "Patient", "id": "p1", "link": [{"other": {"reference": "urn:uuid:missing"}}]}}]})
    assert any(issue["code"] == "reference" for issue in issues)


def test_matchbox_outcome_preserves_issue_details_and_counts():
    outcome = {
        "resourceType": "OperationOutcome",
        "issue": [
            {"severity": "error", "code": "invalid", "diagnostics": "Required field is missing", "location": ["Patient.name"]},
            {"severity": "warning", "code": "invariant", "details": {"text": "Review this value"}},
            {"severity": "information", "code": "informational", "diagnostics": "Validation completed"},
        ],
    }
    summary = summarize_outcome(outcome)

    assert summary["error_count"] == 1
    assert summary["warning_count"] == 1
    assert summary["info_count"] == 1
    assert summary["issues"][0]["location"] == ["Patient.name"]
    assert summary["issues"][1]["diagnostics"] == "Review this value"


def test_matchbox_failure_repair_is_revalidated_and_audited():
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {"fullUrl": "urn:uuid:patient-1", "resource": {"resourceType": "Patient", "id": "patient-1"}},
            {"fullUrl": "urn:uuid:composition-1", "resource": {"resourceType": "Composition", "id": "composition-1", "subject": {"reference": "Patient/patient-1"}}},
        ],
    }

    class FakeMatchbox:
        def __init__(self):
            self.calls = []

        def validate(self, resource, profile=None, ig=None):
            self.calls.append(resource)
            reference = resource["entry"][1]["resource"]["subject"]["reference"]
            return {"resourceType": "OperationOutcome", "issue": [] if reference.startswith("urn:") else [{"severity": "error", "code": "invariant", "diagnostics": "Reference must use the Bundle fullUrl"}]}

    client = FakeMatchbox()
    result = run_workflow(bundle, client=client, max_iterations=2)

    assert len(client.calls) == 2
    assert result["passed"] is True
    assert result["repairs"][0]["validation_iteration"] == 0
    assert result["repairs"][0]["source_diagnostic"] == "Reference must use the Bundle fullUrl"
    assert result["repairs"][0]["applied"] is True
    assert bundle["entry"][1]["resource"]["subject"]["reference"] == "Patient/patient-1"
