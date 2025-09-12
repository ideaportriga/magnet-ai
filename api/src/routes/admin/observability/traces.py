from logging import getLogger

from routes.admin.create_entity_controller import create_entity_controller
from stores import get_db_client

logger = getLogger(__name__)
client = get_db_client()


# Renamed to avoid conflict with core.domain.traces.TracesController
ObservabilityTracesController = create_entity_controller(
    path_param="traces",
    collection_name="traces",
    tags_param=["observability/traces"],
)
