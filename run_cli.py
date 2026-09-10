from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from fhir_validator.local_checks import load_json
from fhir_validator.matchbox_client import MatchboxClient
from fhir_validator.workflow import run_workflow


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Validate and conservatively repair a FHIR JSON resource")
    parser.add_argument("input", type=Path)
    parser.add_argument("--profile")
    parser.add_argument("--matchbox-url", default=os.getenv("MATCHBOX_URL", ""))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--max-iterations", type=int, default=int(os.getenv("MAX_REPAIR_ITERATIONS", "3")))
    args = parser.parse_args()
    client = MatchboxClient(args.matchbox_url, verify_ssl=os.getenv("VERIFY_SSL", "true").lower() in {"1", "true", "yes"}) if args.matchbox_url else None
    result = run_workflow(load_json(args.input), client=client, profile=args.profile, max_iterations=args.max_iterations)
    if args.output:
        args.output.write_text(json.dumps(result["candidate"], indent=2) + "\n", encoding="utf-8")
    if args.manifest:
        args.manifest.write_text(json.dumps({"passed": result["passed"], "repairs": result["repairs"], "iterations": result["iterations"]}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "repairs": len(result["repairs"]), "iterations": len(result["iterations"])}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
