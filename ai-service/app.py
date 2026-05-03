"""
app.py — Flask Entry Point (Day 13 — Optimised Startup)
Tool-75: AI Assistant with RAG | AI Developer 2

Day 13 optimisations:
  - Preload Groq client at startup
  - Preload ChromaDB collection at startup
  - Faster first request response times
"""

from flask import Flask
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("App")

app = Flask(__name__)

# ── Register Blueprints ───────────────────────────────────────────────────────
# from routes.describe         import describe_bp
# from routes.recommend        import recommend_bp
from routes.categorise_cached       import categorise_bp
from routes.generate_report  import generate_report_bp
from routes.health_v2          import health_bp
# from routes.analyse_document import analyse_document_bp
from routes.query            import query_bp

# app.register_blueprint(describe_bp)
# app.register_blueprint(recommend_bp)
app.register_blueprint(categorise_bp)
app.register_blueprint(generate_report_bp)
app.register_blueprint(health_bp)
# app.register_blueprint(analyse_document_bp)
app.register_blueprint(query_bp)

# ── Startup Preloading ────────────────────────────────────────────────────────
# Pre-initialise heavy clients so first request is fast
with app.app_context():
    try:
        from services.groq_client import preload as preload_groq
        preload_groq()
        logger.info("✅ Groq client preloaded")
    except Exception as e:
        logger.warning(f"⚠️  Groq preload failed: {e}")

    try:
        from services.chroma_client import get_collection
        get_collection()
        logger.info("✅ ChromaDB collection preloaded")
    except Exception as e:
        logger.warning(f"⚠️  ChromaDB preload failed: {e}")

    try:
        from services.redis_cache import get_redis
        get_redis()
        logger.info("✅ Redis client preloaded")
    except Exception as e:
        logger.warning(f"⚠️  Redis preload failed: {e}")

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port  = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    logger.info(f"Starting AI Service on port {port}...")
    logger.info(f"Health check: http://localhost:{port}/health")
    app.run(host="0.0.0.0", port=port, debug=debug)