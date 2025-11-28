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

    # TODO - Define required env variables
    required_env_variables = []
    missing_env_variables = [var for var in required_env_variables if var not in env]
    if missing_env_variables:
        MISSING_VARS = ", ".join(missing_env_variables)
        logger.error(
            "The following required environment variables are not defined: %s",
            MISSING_VARS,
        )
        sys.exit(0)
