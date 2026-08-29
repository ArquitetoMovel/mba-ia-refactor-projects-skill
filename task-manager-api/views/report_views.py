from config.settings import Settings
from controllers.report_controller import ReportController
from flask import Blueprint, jsonify
from middlewares.auth import role_required

report_bp = Blueprint('reports', __name__)

_VIEW_ROLES = (Settings.ROLE_ADMIN, Settings.ROLE_MANAGER)


@report_bp.route('/reports/summary', methods=['GET'])
@role_required(*_VIEW_ROLES)
def summary_report():
    return jsonify(ReportController.summary()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
@role_required(*_VIEW_ROLES)
def user_report(user_id):
    return jsonify(ReportController.user_report(user_id)), 200
