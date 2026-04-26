"""
app.py — Flask Entry Point for AI Service (Port 5000)
Tool-75: AI Assistant with RAG
AI Developer 2: GroqClient, /categorise, /generate-report, caching
"""

from flask import Flask
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# ── Register Blueprints (routes) ──────────────────────────────────────────────
# AI Developer 1 routes
from routes.describe import describe_bp
from routes.recommend import recommend_bp

# AI Developer 2 routes
from routes.categorise import categorise_bp
from routes.generate_report import generate_report_bp

# AI Developer 3 routes
from routes.analyse_document import analyse_document_bp
from routes.query import query_bp

app.register_blueprint(describe_bp)
app.register_blueprint(recommend_bp)
app.register_blueprint(categorise_bp)
app.register_blueprint(generate_report_bp)
app.register_blueprint(analyse_document_bp)
app.register_blueprint(query_bp)

# ── Health Check Endpoint ─────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    """Basic health check — returns service status."""
    return {
        "status": "ok",
        "service": "ai-service",
        "port": 5000
    }, 200

# ── Run the App ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    print(f"[AI Service] Starting on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=debug)