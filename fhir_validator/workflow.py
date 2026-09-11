"""Validation and repair orchestration."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .local_checks import check_resource
from .matchbox_client import MatchboxClient, summarize_outcome
from .repair_engine import apply_repairs


def run_workflow(resource: dict[str, Any], client: MatchboxClient | None = None, profile: str | None = None, ig: str | None = None, max_iterations: int = 3) -> dict[str, Any]:
    candidate = deepcopy(resource)
    iterations: list[dict[str, Any]] = []
    for iteration in range(max_iterations + 1):
        local_issues = check_resource(candidate)
        matchbox = None
        if client:
            matchbox = summarize_outcome(client.validate(candidate, profile=profile, ig=ig))
        passed = matchbox["passed"] if matchbox else not any(issue["severity"] in {"error", "fatal"} for issue in local_issues)
        record: dict[str, Any] = {"iteration": iteration, "local_issues": local_issues, "matchbox": matchbox, "repairs": []}
        if passed:
            iterations.append(record)
            break
        if iteration == max_iterations:
            iterations.append(record)
            break
        candidate, repairs = apply_repairs(candidate)
        for repair in repairs:
            repair["validation_iteration"] = iteration
            repair["source_diagnostic"] = (
                (next((issue.get("diagnostics", "") for issue in matchbox.get("issues", []) if issue.get("severity") in {"error", "fatal"}), "") if matchbox else None)
                or next((issue.get("diagnostics", "") for issue in local_issues if issue["severity"] in {"error", "fatal"}), "")
            )
            repair["applied"] = True
        record["repairs"] = repairs
        iterations.append(record)
        if not repairs:
            break
    passed = bool(iterations and ((iterations[-1]["matchbox"] or {}).get("passed", not iterations[-1]["local_issues"])))
    final_matchbox = iterations[-1]["matchbox"] if iterations else None
    final_local_issues = iterations[-1]["local_issues"] if iterations else []
    return {
        "passed": passed,
        "candidate": candidate,
        "original": resource,
        "iterations": iterations,
        "repairs": [repair for item in iterations for repair in item["repairs"]],
        "summary": {
            "validator": "Matchbox" if client else "Local checks",
            "status": "passed" if passed else "review required",
            "profile": profile or "Default FHIR validation",
            "cycles": len(iterations),
            "errors": final_matchbox["error_count"] if final_matchbox else sum(issue["severity"] in {"error", "fatal"} for issue in final_local_issues),
            "warnings": final_matchbox["warning_count"] if final_matchbox else sum(issue["severity"] == "warning" for issue in final_local_issues),
            "information": final_matchbox["info_count"] if final_matchbox else sum(issue["severity"] == "information" for issue in final_local_issues),
        },
    }
