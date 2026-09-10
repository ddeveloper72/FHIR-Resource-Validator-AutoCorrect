"""Conservative, explainable FHIR repairs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def normalize_bundle_references(bundle: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Align local type/id references with the matching Bundle fullUrl.

    This is safe only when the bundle has exactly one matching resource and the
    target fullUrl is present. No clinical values or terminology are invented.
    """
    if bundle.get("resourceType") != "Bundle" or not isinstance(bundle.get("entry"), list):
        return deepcopy(bundle), []

    candidates: dict[str, list[str]] = {}
    for entry in bundle["entry"]:
        if not isinstance(entry, dict):
            continue
        resource = entry.get("resource")
        full_url = entry.get("fullUrl")
        if isinstance(resource, dict) and isinstance(full_url, str):
            key = f"{resource.get('resourceType')}/{resource.get('id')}"
            if resource.get("resourceType") and resource.get("id"):
                candidates.setdefault(key, []).append(full_url)

    repaired = deepcopy(bundle)
    repairs: list[dict[str, Any]] = []
    for container in _walk(repaired):
        reference = container.get("reference")
        if not isinstance(reference, str) or reference.startswith(("http://", "https://", "urn:", "#")):
            continue
        urls = candidates.get(reference, [])
        if len(urls) != 1 or urls[0] == reference:
            continue
        container["reference"] = urls[0]
        repairs.append({
            "rule": "normalize_bundle_reference",
            "path": "reference",
            "before": reference,
            "after": urls[0],
            "reason": "The reference uniquely identifies a resource whose Bundle fullUrl is different.",
        })
    return repaired, repairs


def apply_repairs(resource: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    return normalize_bundle_references(resource)
