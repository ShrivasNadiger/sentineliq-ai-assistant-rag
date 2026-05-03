"""
services/job_manager.py — Async Job Processing Manager
Tool-75: AI Assistant with RAG | AI Developer 2

Handles background job processing for /generate-report.

Flow:
  1. Request comes in → job_id returned immediately (< 50ms)
  2. Background thread processes the report
  3. Job status updated: PENDING → PROCESSING → COMPLETED / FAILED
  4. Webhook fired on completion (if webhook_url provided)

Job States:
  PENDING    : Job created, not yet started
  PROCESSING : Background thread is working on it
  COMPLETED  : Report ready, result stored
  FAILED     : Something went wrong, error stored
"""

import uuid
import time
import logging
import threading
import requests
from datetime import datetime

logger = logging.getLogger("JobManager")

# ── In-memory job store ───────────────────────────────────────────────────────
# Stores all jobs — { job_id: job_dict }
# In production this would be Redis or a DB table
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()  # Thread-safe access


# ── Job Operations ────────────────────────────────────────────────────────────
def create_job(input_data: str, title_hint: str = "", webhook_url: str = "") -> str:
    """
    Create a new job and return its ID immediately.

    Args:
        input_data  : The report data to process
        title_hint  : Optional title hint for the report
        webhook_url : Optional URL to POST result to when done

    Returns:
        job_id string (UUID)
    """
    job_id = str(uuid.uuid4())

    job = {
        "job_id"      : job_id,
        "status"      : "PENDING",
        "input_data"  : input_data,
        "title_hint"  : title_hint,
        "webhook_url" : webhook_url,
        "result"      : None,
        "error"       : None,
        "created_at"  : datetime.utcnow().isoformat(),
        "started_at"  : None,
        "completed_at": None,
    }

    with _jobs_lock:
        _jobs[job_id] = job

    logger.info(f"Job created: {job_id}")
    return job_id


def get_job(job_id: str) -> dict | None:
    """Get job by ID. Returns None if not found."""
    with _jobs_lock:
        return _jobs.get(job_id)


def update_job(job_id: str, **kwargs):
    """Update job fields safely."""
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update(kwargs)


def get_all_jobs() -> list[dict]:
    """Return all jobs — useful for debugging."""
    with _jobs_lock:
        return list(_jobs.values())


# ── Background Worker ─────────────────────────────────────────────────────────
def _process_job(job_id: str):
    """
    Background thread worker — processes the report generation.
    Runs in a separate thread so the main request returns instantly.
    """
    # Import here to avoid circular imports
    from services.groq_client import call_groq_json, get_fallback_response
    from services.meta_helper import build_meta_from_groq, build_fallback_meta

    logger.info(f"Processing job: {job_id}")

    # Mark as PROCESSING
    update_job(job_id,
        status     = "PROCESSING",
        started_at = datetime.utcnow().isoformat()
    )

    job = get_job(job_id)
    if not job:
        logger.error(f"Job {job_id} not found in store")
        return

    try:
        # Load prompt
        import os
        prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "generate_report_prompt.txt"
        )
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read().strip()
        except FileNotFoundError:
            system_prompt = "Generate a structured business report in JSON format."

        # Build user prompt
        user_prompt = f"Generate a professional report from the following data:\n\n{job['input_data']}"
        if job.get("title_hint"):
            user_prompt += f"\n\nSuggested report title theme: {job['title_hint']}"

        # Call Groq
        result = call_groq_json(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.4
        )

        if not result:
            raise Exception("Groq returned None — possible timeout or rate limit")

        # Extract fields
        groq_meta       = result.pop("_meta", {})
        title           = result.get("title", "Untitled Report")
        exec_summary    = result.get("executive_summary", "No summary available.")
        overview        = result.get("overview", "No overview available.")
        top_items       = result.get("top_items", [])
        recommendations = result.get("recommendations", [])

        if not isinstance(top_items, list):
            top_items = [str(top_items)]
        if not isinstance(recommendations, list):
            recommendations = [str(recommendations)]

        top_items       = [str(i) for i in top_items[:3]]
        recommendations = [str(r) for r in recommendations[:3]]

        while len(top_items) < 3:
            top_items.append("No additional findings identified.")
        while len(recommendations) < 3:
            recommendations.append("Review and monitor the situation.")

        report_result = {
            "title"             : title,
            "executive_summary" : exec_summary,
            "overview"          : overview,
            "top_items"         : top_items,
            "recommendations"   : recommendations,
            "meta"              : build_meta_from_groq(groq_meta, cached=False, confidence=0.9)
        }

        # Mark as COMPLETED
        update_job(job_id,
            status       = "COMPLETED",
            result       = report_result,
            completed_at = datetime.utcnow().isoformat()
        )
        logger.info(f"Job {job_id} completed successfully")

        # Fire webhook if provided
        webhook_url = job.get("webhook_url", "")
        if webhook_url:
            _fire_webhook(job_id, webhook_url, report_result)

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        update_job(job_id,
            status       = "FAILED",
            error        = str(e),
            completed_at = datetime.utcnow().isoformat()
        )


def _fire_webhook(job_id: str, webhook_url: str, result: dict):
    """POST job result to webhook URL when job completes."""
    try:
        payload = {
            "job_id"    : job_id,
            "status"    : "COMPLETED",
            "result"    : result,
            "timestamp" : datetime.utcnow().isoformat()
        }
        response = requests.post(webhook_url, json=payload, timeout=10)
        logger.info(f"Webhook fired for job {job_id} — status: {response.status_code}")
    except Exception as e:
        logger.error(f"Webhook failed for job {job_id}: {e}")


def start_job(job_id: str):
    """
    Launch background thread for a job.
    Thread is daemon=True so it won't block Flask from shutting down.
    """
    thread = threading.Thread(
        target=_process_job,
        args=(job_id,),
        daemon=True,
        name=f"job-{job_id[:8]}"
    )
    thread.start()
    logger.info(f"Background thread started for job {job_id}")