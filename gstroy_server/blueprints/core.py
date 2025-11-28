from flask import Blueprint, jsonify

bp_core = Blueprint("core", __name__)


@bp_core.route("/", methods=["GET"])
def index():
    return jsonify(
        {
            "service": "GStroy Print Server PRO",
            "status": "running",
            "version": "3.1-pro-date-fix",
        }
    )
