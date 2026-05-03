"""
routes/generate_report.py — POST /generate-report (Day 11 — Async Jobs)
Tool-75: AI Assistant with RAG | AI Developer 2

Two modes:
  1. POST /generate-report        → Submit job, returns job_id instantly
  2. GET  /generate-report/<id>   → Poll job status and get result when ready

Flow:
  Client POSTs data
      ↓
  job_id returned in < 50ms
      ↓
  Background thread processes report
      ↓
  Client polls GET /generate-report/<job_id>
      ↓
  When status=COMPLETED, result is in response

Request Body (POST):
    {
        "data"        : "Text to generate report from",
        "title_hint"  : "Optional title hint",
        "webhook_url" : "https://your-server.com/webhook"  (optional)
    }

Immediate Response (POST):
    {
        "job_id"     : "uuid-here",
        "status"     : "PENDING",
        "message"    : "Report generation started. Poll GET /generate-report/<job_id> for result.",
        "poll_url"   : "/generate-report/uuid-here"
    }

Poll Response (GET) when COMPLETED:
    {
        "job_id"       : "uuid-here",
        "status"       : "COMPLETED",
        "created_at"   : "2026-04-28T10:00:00",
        "completed_at" : "2026-04-28T10:00:12",
        "result": {
            "title"             : "...",
            "executive_summary" : "...",
            "overview"          : "...",
            "top_items"         : [...],
            "recommendations"   : [...],
            "meta"              : { ... }
        }
    }
"""

import logging
from flask import Blueprint, request, jsonify
from services.job_manager import create_job, get_job, start_job

logger = logging.getLogger("generate_report")

generate_report_bp = Blueprint("generate_report", __name__)


# ── POST /generate-report — Submit async job ──────────────────────────────────
@generate_report_bp.route("/generate-report", methods=["POST"])
def generate_report():
    """
    POST /generate-report
    Submit a report generation job — returns job_id immediately.
    """

    # ── 1. Validate ───────────────────────────────────────────────────────────
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON", "status": 400}), 400

    input_data = data.get("data", "").strip()

    if not input_data:
        return jsonify({"error": "Field 'data' is required and cannot be empty", "status": 400}), 400

    if len(input_data) > 8000:
        return jsonify({"error": "Field 'data' must be under 8000 characters", "status": 400}), 400

    title_hint  = data.get("title_hint", "").strip()
    webhook_url = data.get("webhook_url", "").strip()

    # ── 2. Create job and start background thread ─────────────────────────────
    job_id = create_job(
        input_data  = input_data,
        title_hint  = title_hint,
        webhook_url = webhook_url
    )

    start_job(job_id)

    # ── 3. Return job_id immediately ──────────────────────────────────────────
    logger.info(f"Job submitted: {job_id}")

    return jsonify({
        "job_id"   : job_id,
        "status"   : "PENDING",
        "message"  : "Report generation started. Poll the poll_url for result.",
        "poll_url" : f"/generate-report/{job_id}"
    }), 202   # 202 Accepted — request received, processing async


# ── GET /generate-report/<job_id> — Poll job status ──────────────────────────
@generate_report_bp.route("/generate-report/<job_id>", methods=["GET"])
def get_report_status(job_id: str):
    """
    GET /generate-report/<job_id>
    Poll job status. Returns result when COMPLETED.
    """

    job = get_job(job_id)

    if not job:
        return jsonify({
            "error"  : f"Job '{job_id}' not found",
            "status" : 404
        }), 404

    status = job["status"]

    # ── PENDING or PROCESSING — still working ─────────────────────────────────
    if status in ("PENDING", "PROCESSING"):
        return jsonify({
            "job_id"      : job_id,
            "status"      : status,
            "message"     : "Report is being generated. Please poll again in a few seconds.",
            "created_at"  : job["created_at"],
            "started_at"  : job["started_at"],
        }), 200

    # ── FAILED ────────────────────────────────────────────────────────────────
    if status == "FAILED":
        return jsonify({
            "job_id"       : job_id,
            "status"       : "FAILED",
            "error"        : job.get("error", "Unknown error"),
            "created_at"   : job["created_at"],
            "completed_at" : job["completed_at"],
        }), 200

    # ── COMPLETED — return full result ────────────────────────────────────────
    return jsonify({
        "job_id"       : job_id,
        "status"       : "COMPLETED",
        "created_at"   : job["created_at"],
        "started_at"   : job["started_at"],
        "completed_at" : job["completed_at"],
        "result"       : job["result"]
    }), 200