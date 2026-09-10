from fhir_validator.repair_engine import apply_repairs
from fhir_validator.local_checks import check_resource


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
