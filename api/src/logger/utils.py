import logging.config
import os

import yaml


def get_project_root(start_dir=None, marker_dir="src"):
    if start_dir is None:
        start_dir = os.path.dirname(os.path.abspath(__file__))

    current_dir = os.path.abspath(start_dir)

    while not os.path.isdir(os.path.join(current_dir, marker_dir)):
        if current_dir == os.path.dirname(current_dir):
            raise ValueError("Marker directory not found in the directory hierarchy")

        current_dir = os.path.dirname(current_dir)

    return current_dir


config_path = os.path.join(get_project_root(), "config", "logging_config.yaml")
if os.path.exists(config_path):
    with open(config_path) as config_file:
        config = yaml.safe_load(config_file)
    logging.config.dictConfig(config)
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s %(filename)s:%(lineno)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

logger = logging.getLogger(__name__)
logger.info("Logging is configured.")
