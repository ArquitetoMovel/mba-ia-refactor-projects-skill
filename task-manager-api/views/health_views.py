from datetime import datetime, timezone

from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })


@health_bp.route('/')
def index():
    return jsonify({'message': 'Task Manager API', 'version': '2.0'})
