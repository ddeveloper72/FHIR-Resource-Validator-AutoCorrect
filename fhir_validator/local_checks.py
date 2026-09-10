"""Local checks that run before and after Matchbox validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("FHIR input must be a JSON object")
    return value


def _references(value: Any):
    if isinstance(value, dict):
        reference = value.get("reference")
        if isinstance(reference, str):
            yield reference
        for child in value.values():
            yield from _references(child)
    elif isinstance(value, list):
        for child in value:
            yield from _references(child)


def check_resource(resource: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    resource_type = resource.get("resourceType")
    if not isinstance(resource_type, str):
        issues.append({"severity": "error", "code": "structure", "diagnostics": "resourceType is required"})
        return issues

    if resource_type == "Bundle":
        entries = resource.get("entry", [])
        if not isinstance(entries, list):
            issues.append({"severity": "error", "code": "structure", "diagnostics": "Bundle.entry must be an array"})
            return issues
        full_urls = {entry.get("fullUrl") for entry in entries if isinstance(entry, dict) and entry.get("fullUrl")}
        type_ids = {
            f"{item.get('resourceType')}/{item.get('id')}"
            for item in (entry.get("resource", {}) for entry in entries if isinstance(entry, dict))
            if isinstance(item, dict) and item.get("resourceType") and item.get("id")
        }
        for reference in _references(resource):
            if reference.startswith("urn:uuid:") and reference not in full_urls:
                issues.append({"severity": "error", "code": "reference", "diagnostics": f"Unresolved bundle reference: {reference}"})
            elif "/" in reference and not reference.startswith(("http://", "https://", "#", "urn:")) and reference not in type_ids:
                issues.append({"severity": "error", "code": "reference", "diagnostics": f"Unresolved resource reference: {reference}"})
    return issues
