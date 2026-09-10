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
        passed = (matchbox["passed"] if matchbox else not any(i["severity"] in {"error", "fatal"} for i in local_issues))
        record: dict[str, Any] = {"iteration": iteration, "local_issues": local_issues, "matchbox": matchbox, "repairs": []}
        if passed:
            iterations.append(record)
            break
        if iteration == max_iterations:
            iterations.append(record)
            break
        candidate, repairs = apply_repairs(candidate)
        record["repairs"] = repairs
        iterations.append(record)
        if not repairs:
            break
    return {"passed": bool(iterations and ((iterations[-1]["matchbox"] or {}).get("passed", not iterations[-1]["local_issues"]))), "candidate": candidate, "original": resource, "iterations": iterations, "repairs": [repair for item in iterations for repair in item["repairs"]]}
