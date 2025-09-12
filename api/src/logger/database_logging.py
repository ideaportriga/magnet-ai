"""
Utility functions for setting up detailed logging
"""

import logging
import logging.config
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def setup_detailed_logging():
    """Setup detailed logging configuration for database errors"""

    # Try to load detailed logging config
    config_path = Path("config/logging_config_detailed.yaml")
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)
            print(f"Loaded detailed logging configuration from {config_path}")
        except Exception as e:
            print(f"Failed to load logging config: {e}")
            setup_basic_logging()
    else:
        setup_basic_logging()


def setup_basic_logging():
    """Setup basic logging if detailed config is not available"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)s - %(message)s",
    )

    # Set SQLAlchemy loggers to appropriate levels
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine.error").setLevel(logging.ERROR)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.INFO)

    print("Basic logging configuration applied")


def log_database_operation(
    operation: str, table: str, data: Optional[Dict[str, Any]] = None
):
    """Log database operation details"""
    logger = logging.getLogger("database.operations")

    log_msg = f"Database operation: {operation} on table '{table}'"
    if data:
        # Be careful not to log sensitive information
        safe_data = {
            k: v
            for k, v in data.items()
            if not any(
                sensitive in k.lower()
                for sensitive in ["password", "token", "secret", "key"]
            )
        }
        log_msg += f" with data: {safe_data}"

    logger.info(log_msg)
