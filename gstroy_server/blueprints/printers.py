import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

from ..services.label import build_unit_info, generate_list_label, generate_pro_product_label
from ..services.printer import check_printer_online, send_zpl_to_socket

logger = logging.getLogger("gstroy.printers")

bp_printers = Blueprint("printers", __name__, url_prefix="/printers")


@bp_printers.route("/<ip>/status", methods=["GET"])
def printer_status(ip):
    try:
        online = check_printer_online(ip)
        logger.info("Printer %s status requested -> %s", ip, "online" if online else "offline")
        return jsonify(
            {
                "ip": ip,
                "online": online,
                "checked_at": datetime.now().strftime("%H:%M:%S"),
            }
        )
    except ValueError as exc:
        logger.warning("Invalid status request for %s: %s", ip, exc)
        return jsonify({"error": str(exc)}), 400


@bp_printers.route("/<ip>/print-product-label", methods=["POST"])
def print_product_label(ip):
    if not request.is_json:
        logger.warning("Print product called without JSON for %s", ip)
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json(silent=True) or {}
    try:
        unit_info = build_unit_info(
            data.get("unit_info"),
            data.get("quantity"),
            data.get("quantities"),
        )
        zpl = generate_pro_product_label(
            name=data.get("name", ""),
            barcode=data.get("barcode", ""),
            unit_info=unit_info,
            copies=data.get("copies", 1),
        )
        send_zpl_to_socket(ip, zpl)
        logger.info("Product label sent to %s", ip)
        return jsonify({"success": True, "message": "Pro Product Label Sent"})
    except Exception as exc:
        logger.exception("Failed to send product label to %s", ip)
        return jsonify({"success": False, "error": str(exc)}), 500


@bp_printers.route("/<ip>/print-list-label", methods=["POST"])
def print_list_label(ip):
    if not request.is_json:
        logger.warning("Print list called without JSON for %s", ip)
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json(silent=True) or {}
    try:
        zpl = generate_list_label(
            title=data.get("name", ""),
            qr_data=data.get("qr_data", ""),
            copies=data.get("copies", 1),
        )
        send_zpl_to_socket(ip, zpl)
        logger.info("List label sent to %s", ip)
        return jsonify({"success": True, "message": "List Label Sent"})
    except Exception as exc:
        logger.exception("Failed to send list label to %s", ip)
        return jsonify({"success": False, "error": str(exc)}), 500
