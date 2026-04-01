import os
import sys

import structlog
from dotenv import find_dotenv, load_dotenv

logger = structlog.get_logger(__name__)


def load_env():
    env_name = os.environ.get("ENV", "")
    dotenv_path = find_dotenv(f".env.{env_name}") if env_name else None
    load_dotenv(dotenv_path=dotenv_path, override=True)

    env = os.environ

    current_env = env.get("ENV", "").lower()
    is_production = current_env not in ("", "development", "dev", "local")

    required_env_variables = []
    if is_production:
        required_env_variables = [
            "DATABASE_URL",
            "SECRET_KEY",
            "SECRET_ENCRYPTION_KEY",
        ]

    missing_env_variables = [var for var in required_env_variables if var not in env]
    if missing_env_variables:
        MISSING_VARS = ", ".join(missing_env_variables)
        logger.error(
            "The following required environment variables are not defined: %s",
            MISSING_VARS,
        )
        sys.exit(1)

    insecure_defaults = {
        "SECRET_ENCRYPTION_KEY": "my-secret-key-tsmh5r",
    }
    for var, insecure_value in insecure_defaults.items():
        if env.get(var) == insecure_value and is_production:
            logger.error(
                "%s is set to an insecure default value. "
                "Set a strong value in production.",
                var,
            )
            sys.exit(1)
