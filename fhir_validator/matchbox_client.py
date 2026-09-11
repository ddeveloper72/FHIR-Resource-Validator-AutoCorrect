"""Small HTTP client for Matchbox's FHIR $validate operation."""

from __future__ import annotations

from typing import Any

import requests


class MatchboxError(RuntimeError):
    """Raised when Matchbox cannot return a usable OperationOutcome."""


class MatchboxClient:
    def __init__(self, base_url: str, timeout: float = 60, verify_ssl: bool = True):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    def validate(self, resource: dict[str, Any], profile: str | None = None, ig: str | None = None) -> dict[str, Any]:
        params: dict[str, str] = {}
        if profile:
            params["profile"] = profile
        if ig:
            params["ig"] = ig
        response = requests.post(
            f"{self.base_url}/$validate",
            params=params,
            json=resource,
            headers={"Accept": "application/fhir+json", "Content-Type": "application/fhir+json"},
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        if response.status_code >= 400:
            raise MatchboxError(f"Matchbox returned HTTP {response.status_code}: {response.text[:500]}")
        try:
            outcome = response.json()
        except ValueError as exc:
            raise MatchboxError("Matchbox returned invalid JSON") from exc
        if not isinstance(outcome, dict) or outcome.get("resourceType") != "OperationOutcome":
            raise MatchboxError("Matchbox response was not an OperationOutcome")
        return outcome


def summarize_outcome(outcome: dict[str, Any]) -> dict[str, Any]:
    issues = outcome.get("issue", [])
    if not isinstance(issues, list):
        issues = []
    normalized = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        details = issue.get("details") if isinstance(issue.get("details"), dict) else {}
        normalized.append({
            "severity": issue.get("severity", "information"),
            "code": issue.get("code", "unknown"),
            "diagnostics": issue.get("diagnostics") or details.get("text", ""),
            "details": details.get("text", ""),
            "location": issue.get("location", []),
            "expression": issue.get("expression", []),
        })
    errors = [issue for issue in normalized if issue["severity"] in {"error", "fatal"}]
    return {
        "passed": not errors,
        "issues": normalized,
        "error_count": len(errors),
        "warning_count": sum(issue["severity"] == "warning" for issue in normalized),
        "info_count": sum(issue["severity"] == "information" for issue in normalized),
    }
