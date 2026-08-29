"""Application entrypoint."""

from __future__ import annotations

import logging

from src.app import create_app
from src.config.settings import load_settings
from src.db.database import init_db

logger = logging.getLogger(__name__)

settings = load_settings()
init_db(settings)
app = create_app(settings)

if __name__ == "__main__":
    logger.info("Servidor iniciado em http://%s:%s", settings.host, settings.port)
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
