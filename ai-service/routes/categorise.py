"""
routes/categorise.py — POST /categorise
Tool-75: AI Assistant with RAG | AI Developer 2

Classifies input into predefined categories.
Returns: { category, confidence, reasoning }
"""

from flask import Blueprint, request, jsonify

categorise_bp = Blueprint("categorise", __name__)

@categorise_bp.route("/categorise", methods=["POST"])
def categorise():
    """Stub — Full implementation on Day 3."""
    return jsonify({"message": "categorise endpoint — coming Day 3"}), 200