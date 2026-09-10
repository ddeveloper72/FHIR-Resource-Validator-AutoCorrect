from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from fhir_validator.matchbox_client import MatchboxClient, MatchboxError
from fhir_validator.workflow import run_workflow

load_dotenv()
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


def _client() -> MatchboxClient | None:
    url = os.getenv("MATCHBOX_URL", "").strip()
    return MatchboxClient(url, verify_ssl=os.getenv("VERIFY_SSL", "true").lower() in {"1", "true", "yes"}) if url else None


@app.get("/")
def index():
    return render_template("index.html", default_profile=request.args.get("profile", ""), matchbox_url=os.getenv("MATCHBOX_URL", ""))


@app.post("/api/validate")
def validate_api():
    try:
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "Send a FHIR JSON object"}), 400
        profile = request.args.get("profile") or payload.pop("_profile", None)
        result = run_workflow(payload, client=_client(), profile=profile, max_iterations=int(os.getenv("MAX_REPAIR_ITERATIONS", "3")))
        return jsonify(result)
    except (ValueError, MatchboxError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/validate-file")
def validate_file():
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "Choose a JSON file"}), 400
    try:
        payload = json.loads(uploaded.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("FHIR input must be a JSON object")
        profile = request.form.get("profile", "").strip() or None
        result = run_workflow(payload, client=_client(), profile=profile, max_iterations=int(os.getenv("MAX_REPAIR_ITERATIONS", "3")))
        result["filename"] = Path(uploaded.filename).name
        return jsonify(result)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, MatchboxError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/health")
def health():
    return jsonify({"status": "ok", "matchbox_configured": bool(os.getenv("MATCHBOX_URL", "").strip())})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=True)
